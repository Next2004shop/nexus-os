"""
NEXUS Execution Lock - Trade Deduplication & Symbol Locking
============================================================

Prevents:
1. Duplicate trades on the same symbol within a cooldown window
2. Concurrent pipeline executions for the same symbol
3. Re-entry during failover (primary+secondary double execution)

Uses threading locks for in-process safety.
"""

import logging
import threading
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger("nexus.execution_lock")

# Cooldown between trades on the same symbol (seconds)
DEFAULT_SYMBOL_COOLDOWN = 30


class ExecutionLock:
    """
    Per-symbol execution lock with cooldown enforcement.

    Guarantees:
    - Only one pipeline execution per symbol at a time
    - Minimum cooldown between consecutive trades on a symbol
    - Global processing lock for system-wide operations (kill switch)
    """

    def __init__(self, symbol_cooldown: float = DEFAULT_SYMBOL_COOLDOWN):
        self._symbol_cooldown = symbol_cooldown
        # Per-symbol reentrant locks (so the same thread can re-acquire)
        self._symbol_locks: Dict[str, threading.Lock] = {}
        self._lock_registry_mu = threading.Lock()
        # Last execution timestamp per symbol
        self._last_trade_ts: Dict[str, float] = {}
        self._ts_mu = threading.Lock()
        # Global halt flag (kill switch)
        self._global_halt = threading.Event()

    # ── public API ─────────────────────────────────────────────

    def acquire_symbol(self, symbol: str) -> Tuple[bool, str]:
        """
        Attempt to acquire the execution lock for *symbol*.

        Returns (acquired, reason).
        If acquired is True, the caller MUST call release_symbol() when done.
        """
        if self._global_halt.is_set():
            return False, "GLOBAL_HALT_ACTIVE"

        # Cooldown check (non-blocking)
        with self._ts_mu:
            last = self._last_trade_ts.get(symbol, 0.0)
            elapsed = time.monotonic() - last
            if last > 0 and elapsed < self._symbol_cooldown:
                remaining = self._symbol_cooldown - elapsed
                return False, f"SYMBOL_COOLDOWN: {remaining:.1f}s remaining for {symbol}"

        lock = self._get_lock(symbol)
        acquired = lock.acquire(blocking=False)
        if not acquired:
            return False, f"SYMBOL_LOCKED: {symbol} pipeline already in progress"

        logger.debug(f"LOCK_ACQUIRED: {symbol}")
        return True, "OK"

    def release_symbol(self, symbol: str, trade_executed: bool = False):
        """
        Release the execution lock for *symbol*.

        Args:
            trade_executed: If True, record timestamp for cooldown enforcement.
        """
        if trade_executed:
            with self._ts_mu:
                self._last_trade_ts[symbol] = time.monotonic()

        lock = self._get_lock(symbol)
        try:
            lock.release()
            logger.debug(f"LOCK_RELEASED: {symbol}")
        except RuntimeError:
            # Lock was not held — defensive, should not happen
            logger.warning(f"LOCK_RELEASE_SPURIOUS: {symbol}")

    def global_halt(self):
        """Set global halt flag — blocks all future acquisitions."""
        self._global_halt.set()
        logger.critical("EXECUTION_LOCK: GLOBAL_HALT set")

    def global_resume(self):
        """Clear global halt flag."""
        self._global_halt.clear()
        logger.info("EXECUTION_LOCK: GLOBAL_HALT cleared")

    @property
    def is_halted(self) -> bool:
        return self._global_halt.is_set()

    # ── internals ──────────────────────────────────────────────

    def _get_lock(self, symbol: str) -> threading.Lock:
        with self._lock_registry_mu:
            if symbol not in self._symbol_locks:
                self._symbol_locks[symbol] = threading.Lock()
            return self._symbol_locks[symbol]


# ── singleton ──────────────────────────────────────────────────
_instance: Optional[ExecutionLock] = None
_init_mu = threading.Lock()


def get_execution_lock() -> ExecutionLock:
    global _instance
    if _instance is None:
        with _init_mu:
            if _instance is None:
                _instance = ExecutionLock()
    return _instance
