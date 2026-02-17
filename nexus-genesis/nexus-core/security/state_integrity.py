"""
NEXUS State Integrity Checksum — Phase 11 (F)
================================================

Every 60 seconds:
    - Hash internal state snapshot (risk state, positions, mode)
    - Compare to previous hash
    - Detect unexpected mutation

If mismatch detected without a corresponding logged action:
    Trigger watchdog review.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)

logger = logging.getLogger("nexus.state_integrity")

CHECK_INTERVAL_SECONDS = 60
MAX_UNEXPECTED_MUTATIONS = 3  # 3 consecutive unexplained mutations triggers alert


class StateIntegrityMonitor:
    """
    Periodically hashes critical system state and detects unexpected mutations.
    """

    _instance = None

    def __init__(self):
        self._previous_hash: Optional[str] = None
        self._previous_state: Optional[Dict[str, Any]] = None
        self._expected_mutations: int = 0  # Counter of legitimate changes
        self._unexpected_count: int = 0
        self._total_checks: int = 0
        self._anomalies: List[Dict[str, Any]] = []
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._sec = get_security_logger()

    @classmethod
    def get_instance(cls) -> "StateIntegrityMonitor":
        if cls._instance is None:
            cls._instance = StateIntegrityMonitor()
        return cls._instance

    def notify_expected_change(self):
        """Call this before making a legitimate state change."""
        self._expected_mutations += 1

    def _collect_state(self) -> Dict[str, Any]:
        """Collect critical state for hashing."""
        state = {}

        # Risk Governor state
        try:
            from app.services.risk_governor import get_risk_status
            risk = get_risk_status()
            state["risk"] = {
                "risk_level": risk.get("risk_level"),
                "trading_enabled": risk.get("trading_enabled"),
                "circuit_breaker": risk.get("circuit_breaker_active"),
                "drawdown": risk.get("drawdown", {}).get("current"),
                "positions_count": risk.get("open_positions_count"),
            }
        except Exception:
            state["risk"] = "UNAVAILABLE"

        # Failsafe mode
        try:
            from security.failsafe import get_failsafe
            state["failsafe_mode"] = get_failsafe().mode.value
        except Exception:
            state["failsafe_mode"] = "UNAVAILABLE"

        # Capital lock
        try:
            from security.capital_lock import get_capital_lock
            state["capital_locked"] = get_capital_lock().is_locked
        except Exception:
            state["capital_locked"] = "UNAVAILABLE"

        return state

    def _hash_state(self, state: Dict[str, Any]) -> str:
        """Deterministic hash of state dict."""
        serialized = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def check(self) -> bool:
        """
        Run a state integrity check.

        Returns True if state is consistent, False if unexpected mutation detected.
        """
        self._total_checks += 1
        current_state = self._collect_state()
        current_hash = self._hash_state(current_state)

        if self._previous_hash is None:
            # First check — set baseline
            self._previous_hash = current_hash
            self._previous_state = current_state
            return True

        if current_hash == self._previous_hash:
            # No change — consistent
            self._unexpected_count = 0
            return True

        # State changed — was it expected?
        if self._expected_mutations > 0:
            # Legitimate change
            self._expected_mutations -= 1
            self._previous_hash = current_hash
            self._previous_state = current_state
            self._unexpected_count = 0
            return True

        # UNEXPECTED mutation detected
        self._unexpected_count += 1
        anomaly = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_hash": self._previous_hash,
            "current_hash": current_hash,
            "consecutive_unexpected": self._unexpected_count,
            "diff": self._compute_diff(self._previous_state, current_state),
        }
        self._anomalies.append(anomaly)

        severity = (
            SecuritySeverity.CRITICAL
            if self._unexpected_count >= MAX_UNEXPECTED_MUTATIONS
            else SecuritySeverity.WARNING
        )

        self._sec.log(
            SecurityEventCategory.STATE_CORRUPTION,
            severity,
            f"Unexpected state mutation #{self._unexpected_count}: {anomaly['diff']}",
            details=anomaly,
            source="STATE_INTEGRITY",
        )

        logger.warning(
            f"STATE INTEGRITY: Unexpected mutation detected "
            f"(#{self._unexpected_count}): {anomaly['diff']}"
        )

        self._previous_hash = current_hash
        self._previous_state = current_state

        if self._unexpected_count >= MAX_UNEXPECTED_MUTATIONS:
            self._trigger_watchdog()

        return False

    def _compute_diff(
        self, old: Optional[Dict], new: Dict
    ) -> Dict[str, Any]:
        """Compute simplified diff between two state snapshots."""
        if old is None:
            return {"change": "initial_state"}

        diff = {}
        all_keys = set(list(old.keys()) + list(new.keys()))
        for key in all_keys:
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                diff[key] = {"was": old_val, "now": new_val}
        return diff

    def _trigger_watchdog(self):
        """Trigger watchdog review after repeated unexpected mutations."""
        self._sec.emergency(
            SecurityEventCategory.STATE_CORRUPTION,
            f"WATCHDOG: {MAX_UNEXPECTED_MUTATIONS} consecutive unexpected state mutations",
            details={
                "recent_anomalies": self._anomalies[-5:],
                "total_checks": self._total_checks,
            },
            source="STATE_INTEGRITY_WATCHDOG",
        )
        logger.critical("STATE INTEGRITY WATCHDOG TRIGGERED — Review required")

    async def start(self):
        """Start the periodic integrity check loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("State integrity monitor started")

    async def stop(self):
        """Stop the monitor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Periodic integrity check loop."""
        while self._running:
            try:
                self.check()
            except Exception as e:
                logger.error(f"State integrity check error: {e}")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_checks": self._total_checks,
            "current_hash": self._previous_hash,
            "unexpected_mutations": self._unexpected_count,
            "total_anomalies": len(self._anomalies),
            "recent_anomalies": self._anomalies[-5:],
        }


def get_state_integrity() -> StateIntegrityMonitor:
    return StateIntegrityMonitor.get_instance()
