"""
NEXUS Capital Lock System — Phase 11 (C)
==========================================

Emergency capital protection:
    If equity drops > X% in Y minutes → lock trading.

Behavior:
    - Monitors equity snapshots over rolling window
    - Detects rapid equity drops
    - Transitions system to SAFE_MODE or LOCKDOWN
    - Requires MANUAL unlock — no exceptions

Does NOT modify RiskGovernor — acts as an independent safety net.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)
from security.failsafe import get_failsafe, SystemMode

logger = logging.getLogger("nexus.capital_lock")

# Thresholds
RAPID_DROP_THRESHOLD_PCT = 2.0     # 2% drop triggers SAFE_MODE
CRITICAL_DROP_THRESHOLD_PCT = 3.5  # 3.5% drop triggers LOCKDOWN
MONITORING_WINDOW_SECONDS = 300    # 5-minute monitoring window
SNAPSHOT_INTERVAL_SECONDS = 10     # Equity snapshot every 10s


@dataclass
class EquitySnapshot:
    timestamp: float
    equity: float


class CapitalLock:
    """
    Monitors equity for rapid drops and locks trading when triggered.

    Independent of RiskGovernor — acts as an additional safety layer.
    """

    _instance = None

    def __init__(self):
        self._snapshots: deque = deque(maxlen=500)
        self._locked: bool = False
        self._lock_reason: str = ""
        self._lock_timestamp: Optional[float] = None
        self._peak_equity: float = 0.0
        self._events: List[Dict[str, Any]] = []
        self._sec = get_security_logger()

    @classmethod
    def get_instance(cls) -> "CapitalLock":
        if cls._instance is None:
            cls._instance = CapitalLock()
        return cls._instance

    def record_equity(self, equity: float):
        """
        Record an equity snapshot and check for rapid drops.

        Call this periodically (every telemetry cycle).
        """
        now = time.time()
        self._snapshots.append(EquitySnapshot(timestamp=now, equity=equity))

        if equity > self._peak_equity:
            self._peak_equity = equity

        if self._locked:
            return  # Already locked, no further checks

        # Find the equity at the start of the monitoring window
        window_start = now - MONITORING_WINDOW_SECONDS
        window_snapshots = [s for s in self._snapshots if s.timestamp >= window_start]

        if len(window_snapshots) < 2:
            return

        window_peak = max(s.equity for s in window_snapshots)
        if window_peak <= 0:
            return

        drop_pct = ((window_peak - equity) / window_peak) * 100

        # CRITICAL DROP → LOCKDOWN
        if drop_pct >= CRITICAL_DROP_THRESHOLD_PCT:
            self._trigger_lock(
                f"Critical equity drop: {drop_pct:.2f}% in {MONITORING_WINDOW_SECONDS}s",
                equity,
                window_peak,
                drop_pct,
                SystemMode.LOCKDOWN,
            )

        # RAPID DROP → SAFE_MODE
        elif drop_pct >= RAPID_DROP_THRESHOLD_PCT:
            self._trigger_lock(
                f"Rapid equity drop: {drop_pct:.2f}% in {MONITORING_WINDOW_SECONDS}s",
                equity,
                window_peak,
                drop_pct,
                SystemMode.SAFE_MODE,
            )

    def _trigger_lock(
        self,
        reason: str,
        current_equity: float,
        window_peak: float,
        drop_pct: float,
        target_mode: SystemMode,
    ):
        """Engage capital lock."""
        self._locked = True
        self._lock_reason = reason
        self._lock_timestamp = time.time()

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "current_equity": current_equity,
            "window_peak": window_peak,
            "drop_pct": round(drop_pct, 3),
            "target_mode": target_mode.value,
        }
        self._events.append(event)

        # Transition failsafe
        failsafe = get_failsafe()
        failsafe.transition_to(target_mode, reason, source="CAPITAL_LOCK")

        # Security log
        self._sec.emergency(
            SecurityEventCategory.CAPITAL_LOCK,
            reason,
            details=event,
            source="CAPITAL_LOCK",
        )

        logger.critical(f"CAPITAL LOCK ENGAGED: {reason}")

        # Attempt Telegram alert
        self._notify_capital_lock(event)

    def _notify_capital_lock(self, event: Dict[str, Any]):
        """Send capital lock alert via Telegram."""
        try:
            from app.services.telegram_bot import get_telegram_service
            import asyncio

            telegram = get_telegram_service()
            message = (
                "CAPITAL LOCK ENGAGED\n\n"
                f"Reason: {event['reason']}\n"
                f"Equity: {event['current_equity']:.2f}\n"
                f"Drop: {event['drop_pct']:.2f}%\n"
                f"Mode: {event['target_mode']}\n\n"
                "Trading DISABLED. Manual unlock required."
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(telegram.send_message(message))
            except RuntimeError:
                pass
        except ImportError:
            pass

    def manual_unlock(self, admin_reason: str = "Manual admin unlock") -> bool:
        """
        Manual unlock — requires explicit admin action.

        Returns True if successfully unlocked.
        """
        if not self._locked:
            return True

        self._locked = False
        unlock_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "MANUAL_UNLOCK",
            "reason": admin_reason,
            "was_locked_for_seconds": (
                round(time.time() - self._lock_timestamp, 1)
                if self._lock_timestamp else 0
            ),
        }
        self._events.append(unlock_event)

        self._sec.info(
            SecurityEventCategory.CAPITAL_LOCK,
            f"Capital lock released: {admin_reason}",
            details=unlock_event,
            source="ADMIN",
        )

        logger.info(f"CAPITAL LOCK RELEASED: {admin_reason}")

        # Transition failsafe to SAFE_MODE (not directly to NORMAL)
        failsafe = get_failsafe()
        failsafe.transition_to(
            SystemMode.SAFE_MODE,
            "Post-capital-lock cautious mode",
            source="CAPITAL_LOCK",
        )

        return True

    @property
    def is_locked(self) -> bool:
        return self._locked

    def get_status(self) -> Dict[str, Any]:
        return {
            "locked": self._locked,
            "lock_reason": self._lock_reason,
            "lock_timestamp": self._lock_timestamp,
            "peak_equity": self._peak_equity,
            "snapshot_count": len(self._snapshots),
            "recent_events": self._events[-10:],
            "thresholds": {
                "rapid_drop_pct": RAPID_DROP_THRESHOLD_PCT,
                "critical_drop_pct": CRITICAL_DROP_THRESHOLD_PCT,
                "window_seconds": MONITORING_WINDOW_SECONDS,
            },
        }


def get_capital_lock() -> CapitalLock:
    return CapitalLock.get_instance()
