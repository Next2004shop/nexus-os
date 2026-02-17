"""
NEXUS Position Shadow Tracker — Phase 11 (I)
===============================================

Maintains an internal mirror of expected open positions
and compares against broker-reported positions.

If mismatch persists > 2 cycles → Emergency halt.

This catches:
    - Ghost positions (broker has, we don't know about)
    - Phantom positions (we think we have, broker doesn't)
    - Volume discrepancies
    - Side mismatches
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)
from security.failsafe import get_failsafe, SystemMode

logger = logging.getLogger("nexus.position_shadow")

RECONCILIATION_INTERVAL_SECONDS = 30
MAX_MISMATCH_CYCLES = 2  # 2 consecutive mismatches triggers halt


@dataclass
class ShadowPosition:
    """Internal mirror of an expected position."""
    symbol: str
    side: str
    volume: float
    entry_price: float
    ticket: Optional[str] = None
    opened_at: str = ""


class PositionShadowTracker:
    """
    Keeps an internal shadow of expected positions.
    Periodically reconciles against broker-reported positions.
    """

    _instance = None

    def __init__(self):
        self._shadow: Dict[str, ShadowPosition] = {}  # symbol -> position
        self._consecutive_mismatches: int = 0
        self._reconciliation_count: int = 0
        self._mismatches_log: List[Dict[str, Any]] = []
        self._halted: bool = False
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._sec = get_security_logger()

    @classmethod
    def get_instance(cls) -> "PositionShadowTracker":
        if cls._instance is None:
            cls._instance = PositionShadowTracker()
        return cls._instance

    # ---- Shadow management (called by execution engine) ----

    def register_position(
        self,
        symbol: str,
        side: str,
        volume: float,
        entry_price: float,
        ticket: Optional[str] = None,
    ):
        """Register a new expected position in the shadow."""
        self._shadow[symbol] = ShadowPosition(
            symbol=symbol,
            side=side,
            volume=volume,
            entry_price=entry_price,
            ticket=ticket,
            opened_at=datetime.now(timezone.utc).isoformat(),
        )
        logger.info(f"Shadow position registered: {symbol} {side} {volume}")

    def close_position(self, symbol: str):
        """Remove a position from the shadow (trade closed)."""
        if symbol in self._shadow:
            del self._shadow[symbol]
            logger.info(f"Shadow position closed: {symbol}")

    def get_shadow(self) -> Dict[str, Dict[str, Any]]:
        """Get current shadow positions."""
        return {
            sym: {
                "symbol": p.symbol,
                "side": p.side,
                "volume": p.volume,
                "entry_price": p.entry_price,
                "ticket": p.ticket,
                "opened_at": p.opened_at,
            }
            for sym, p in self._shadow.items()
        }

    # ---- Reconciliation ----

    def reconcile(self, broker_positions: List[Dict[str, Any]]) -> bool:
        """
        Reconcile shadow positions against broker-reported positions.

        Args:
            broker_positions: List of dicts with keys: symbol, side, volume, ticket

        Returns:
            True if reconciliation passes, False if mismatch detected.
        """
        self._reconciliation_count += 1

        # Build broker position map
        broker_map: Dict[str, Dict[str, Any]] = {}
        for pos in broker_positions:
            sym = pos.get("symbol", "")
            broker_map[sym] = pos

        mismatches = []

        # Check 1: Positions we expect but broker doesn't have (PHANTOM)
        for sym, shadow in self._shadow.items():
            if sym not in broker_map:
                mismatches.append({
                    "type": "PHANTOM",
                    "symbol": sym,
                    "detail": "Expected position not found at broker",
                    "shadow": {"side": shadow.side, "volume": shadow.volume},
                })

        # Check 2: Positions broker has that we don't expect (GHOST)
        for sym, broker in broker_map.items():
            if sym not in self._shadow:
                mismatches.append({
                    "type": "GHOST",
                    "symbol": sym,
                    "detail": "Broker position not in shadow",
                    "broker": {
                        "side": broker.get("side"),
                        "volume": broker.get("volume"),
                    },
                })

        # Check 3: Volume/side mismatches on matched positions
        for sym in set(self._shadow.keys()) & set(broker_map.keys()):
            shadow = self._shadow[sym]
            broker = broker_map[sym]

            broker_vol = broker.get("volume", 0)
            if abs(shadow.volume - broker_vol) > 0.001:
                mismatches.append({
                    "type": "VOLUME_MISMATCH",
                    "symbol": sym,
                    "shadow_volume": shadow.volume,
                    "broker_volume": broker_vol,
                })

            broker_side = (broker.get("side") or "").lower()
            shadow_side = shadow.side.lower()
            if broker_side and shadow_side and broker_side != shadow_side:
                mismatches.append({
                    "type": "SIDE_MISMATCH",
                    "symbol": sym,
                    "shadow_side": shadow.side,
                    "broker_side": broker.get("side"),
                })

        if mismatches:
            self._consecutive_mismatches += 1
            mismatch_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cycle": self._reconciliation_count,
                "consecutive": self._consecutive_mismatches,
                "mismatches": mismatches,
            }
            self._mismatches_log.append(mismatch_record)

            severity = (
                SecuritySeverity.CRITICAL
                if self._consecutive_mismatches >= MAX_MISMATCH_CYCLES
                else SecuritySeverity.WARNING
            )

            self._sec.log(
                SecurityEventCategory.POSITION_MISMATCH,
                severity,
                f"Position reconciliation failed: {len(mismatches)} mismatches "
                f"(cycle {self._consecutive_mismatches}/{MAX_MISMATCH_CYCLES})",
                details=mismatch_record,
                source="POSITION_SHADOW",
            )

            logger.warning(
                f"POSITION MISMATCH: {len(mismatches)} issues "
                f"(consecutive: {self._consecutive_mismatches})"
            )

            # Emergency halt after MAX_MISMATCH_CYCLES
            if self._consecutive_mismatches >= MAX_MISMATCH_CYCLES:
                self._emergency_halt(mismatches)

            return False
        else:
            # Clean reconciliation — reset counter
            self._consecutive_mismatches = 0
            return True

    def _emergency_halt(self, mismatches: List[Dict[str, Any]]):
        """Emergency halt due to persistent position mismatch."""
        if self._halted:
            return

        self._halted = True

        self._sec.emergency(
            SecurityEventCategory.POSITION_MISMATCH,
            f"EMERGENCY HALT: Position mismatch persisted for {MAX_MISMATCH_CYCLES} cycles",
            details={"mismatches": mismatches},
            source="POSITION_SHADOW",
        )

        logger.critical("POSITION SHADOW: EMERGENCY HALT — Persistent mismatch detected")

        # Engage lockdown
        failsafe = get_failsafe()
        failsafe.enter_lockdown(
            f"Position shadow mismatch persisted {MAX_MISMATCH_CYCLES} cycles",
            source="POSITION_SHADOW",
        )

        # Telegram alert
        try:
            from app.services.telegram_bot import get_telegram_service
            import asyncio

            telegram = get_telegram_service()
            msg = (
                "EMERGENCY HALT - POSITION MISMATCH\n\n"
                f"Mismatches: {len(mismatches)}\n"
                f"Persisted: {MAX_MISMATCH_CYCLES} cycles\n\n"
                "System LOCKED DOWN. Manual review required."
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(telegram.send_message(msg))
            except RuntimeError:
                pass
        except ImportError:
            pass

    async def start(self):
        """Start periodic reconciliation (requires broker position feed)."""
        if self._running:
            return
        self._running = True
        logger.info("Position shadow tracker started")

    async def stop(self):
        """Stop the tracker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "shadow_positions": len(self._shadow),
            "reconciliation_count": self._reconciliation_count,
            "consecutive_mismatches": self._consecutive_mismatches,
            "halted": self._halted,
            "total_mismatch_events": len(self._mismatches_log),
            "recent_mismatches": self._mismatches_log[-5:],
            "positions": self.get_shadow(),
        }


def get_position_shadow() -> PositionShadowTracker:
    return PositionShadowTracker.get_instance()
