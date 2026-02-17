"""
NEXUS Execution Guard — Phase 11 (A)
======================================

Execution isolation layer that sits BEFORE the execution engine.

Responsibilities:
    - Prevent duplicate order execution
    - Block race conditions via per-symbol locks
    - Enforce max 1 execution per symbol per X seconds
    - Verify order ticket confirmation before state update
    - Block execution if MT5 response is incomplete

This module does NOT modify the execution engine — it wraps it.
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set, Tuple

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)
from security.failsafe import get_failsafe

logger = logging.getLogger("nexus.execution_guard")

# Constraints
MIN_EXECUTION_INTERVAL_SECONDS = 5.0   # Max 1 execution per symbol per 5s
DUPLICATE_WINDOW_SECONDS = 30.0        # Reject identical orders within 30s
ORDER_CONFIRMATION_TIMEOUT = 10.0      # MT5 must confirm within 10s


@dataclass
class ExecutionRecord:
    """Tracks a recent execution for dedup and rate limiting."""
    symbol: str
    side: str
    quantity: float
    timestamp: float
    order_id: Optional[str] = None
    confirmed: bool = False


class ExecutionGuard:
    """
    Prevents duplicate orders, race conditions, and unconfirmed executions.
    Must be checked BEFORE any trade reaches the execution engine.
    """

    _instance = None

    def __init__(self):
        self._symbol_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._last_execution: Dict[str, float] = {}   # symbol -> timestamp
        self._recent_orders: Dict[str, ExecutionRecord] = {}  # dedup key -> record
        self._pending_confirmations: Dict[str, ExecutionRecord] = {}  # order_id -> record
        self._blocked_count: int = 0
        self._passed_count: int = 0
        self._sec = get_security_logger()

    @classmethod
    def get_instance(cls) -> "ExecutionGuard":
        if cls._instance is None:
            cls._instance = ExecutionGuard()
        return cls._instance

    def _dedup_key(self, symbol: str, side: str, quantity: float) -> str:
        """Generate a deduplication key for an order."""
        return f"{symbol}:{side}:{quantity}"

    async def pre_execution_check(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> Tuple[bool, str]:
        """
        Run all pre-execution safety checks.

        Returns:
            (allowed, reason)
        """
        # Gate 0: Failsafe mode
        failsafe = get_failsafe()
        if not failsafe.is_trading_allowed:
            self._blocked_count += 1
            return False, f"BLOCKED_BY_FAILSAFE: System in {failsafe.mode.value}"

        # Gate 1: Rate limiting — max 1 execution per symbol per interval
        now = time.time()
        last = self._last_execution.get(symbol, 0.0)
        elapsed = now - last

        if elapsed < MIN_EXECUTION_INTERVAL_SECONDS:
            self._blocked_count += 1
            self._sec.warning(
                SecurityEventCategory.RACE_CONDITION,
                f"Rate limit: {symbol} executed {elapsed:.1f}s ago (min {MIN_EXECUTION_INTERVAL_SECONDS}s)",
                details={"symbol": symbol, "elapsed": elapsed},
                source="EXECUTION_GUARD",
            )
            return False, f"RATE_LIMITED: {symbol} cooldown ({elapsed:.1f}s < {MIN_EXECUTION_INTERVAL_SECONDS}s)"

        # Gate 2: Duplicate detection
        dedup = self._dedup_key(symbol, side, quantity)
        existing = self._recent_orders.get(dedup)
        if existing and (now - existing.timestamp) < DUPLICATE_WINDOW_SECONDS:
            self._blocked_count += 1
            self._sec.critical(
                SecurityEventCategory.DUPLICATE_EXECUTION,
                f"Duplicate order blocked: {dedup}",
                details={
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "original_timestamp": existing.timestamp,
                    "seconds_since": now - existing.timestamp,
                },
                source="EXECUTION_GUARD",
            )
            return False, f"DUPLICATE_BLOCKED: Identical order within {DUPLICATE_WINDOW_SECONDS}s"

        # Gate 3: Acquire per-symbol lock (blocks concurrent execution on same symbol)
        lock = self._symbol_locks[symbol]
        if lock.locked():
            self._blocked_count += 1
            self._sec.warning(
                SecurityEventCategory.RACE_CONDITION,
                f"Concurrent execution blocked: {symbol} lock held",
                details={"symbol": symbol},
                source="EXECUTION_GUARD",
            )
            return False, f"CONCURRENT_BLOCKED: {symbol} execution already in progress"

        self._passed_count += 1
        return True, "EXECUTION_GUARD_PASSED"

    async def acquire_lock(self, symbol: str) -> asyncio.Lock:
        """Acquire the execution lock for a symbol. Caller must release."""
        lock = self._symbol_locks[symbol]
        await lock.acquire()
        return lock

    def release_lock(self, symbol: str):
        """Release the execution lock for a symbol."""
        lock = self._symbol_locks.get(symbol)
        if lock and lock.locked():
            lock.release()

    def register_execution(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_id: Optional[str] = None,
    ):
        """Register a successful execution for dedup and rate tracking."""
        now = time.time()
        self._last_execution[symbol] = now

        record = ExecutionRecord(
            symbol=symbol,
            side=side,
            quantity=quantity,
            timestamp=now,
            order_id=order_id,
            confirmed=False,
        )

        dedup = self._dedup_key(symbol, side, quantity)
        self._recent_orders[dedup] = record

        if order_id:
            self._pending_confirmations[order_id] = record

        # Cleanup old entries
        self._cleanup()

    def confirm_execution(self, order_id: str) -> bool:
        """
        Mark an order as confirmed by the broker.

        Returns True if the order was found and confirmed.
        """
        record = self._pending_confirmations.get(order_id)
        if not record:
            self._sec.warning(
                SecurityEventCategory.EXECUTION_MISMATCH,
                f"Confirmation for unknown order: {order_id}",
                source="EXECUTION_GUARD",
            )
            return False

        record.confirmed = True
        del self._pending_confirmations[order_id]
        return True

    def validate_response_complete(self, response: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that an MT5/broker response is complete enough to trust.

        A response is considered incomplete if missing critical fields.
        """
        required_fields = ["order_id", "status"]

        missing = [f for f in required_fields if f not in response or response[f] is None]
        if missing:
            self._sec.critical(
                SecurityEventCategory.EXECUTION_MISMATCH,
                f"Incomplete broker response: missing {missing}",
                details={"response": response, "missing_fields": missing},
                source="EXECUTION_GUARD",
            )
            return False, f"INCOMPLETE_RESPONSE: Missing {missing}"

        if response.get("status") in ("FAILED", "REJECTED", "ERROR"):
            return False, f"BROKER_REJECTED: {response.get('reason', 'unknown')}"

        return True, "RESPONSE_VALID"

    def get_pending_confirmations(self) -> Dict[str, Any]:
        """Get orders awaiting broker confirmation."""
        now = time.time()
        result = {}
        for order_id, record in self._pending_confirmations.items():
            age = now - record.timestamp
            result[order_id] = {
                "symbol": record.symbol,
                "side": record.side,
                "quantity": record.quantity,
                "age_seconds": round(age, 1),
                "timed_out": age > ORDER_CONFIRMATION_TIMEOUT,
            }
        return result

    def _cleanup(self):
        """Remove stale entries from tracking dicts."""
        now = time.time()
        cutoff = now - 120  # 2 minute cleanup window

        stale_dedup = [
            k for k, v in self._recent_orders.items()
            if v.timestamp < cutoff
        ]
        for k in stale_dedup:
            del self._recent_orders[k]

        stale_exec = [
            k for k, v in self._last_execution.items()
            if v < cutoff
        ]
        for k in stale_exec:
            del self._last_execution[k]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "blocked_count": self._blocked_count,
            "passed_count": self._passed_count,
            "active_locks": sum(1 for l in self._symbol_locks.values() if l.locked()),
            "pending_confirmations": len(self._pending_confirmations),
            "recent_orders": len(self._recent_orders),
        }


def get_execution_guard() -> ExecutionGuard:
    return ExecutionGuard.get_instance()
