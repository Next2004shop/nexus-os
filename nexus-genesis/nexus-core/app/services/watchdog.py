"""
NEXUS Watchdog Service - System Health Monitor
================================================

Monitors:
1. Broker connectivity heartbeat
2. Execution hang detection
3. Position desync (internal vs broker)
4. Consecutive-failure auto-safe-mode
5. System state registry

If a desync or critical failure is detected, trading is halted
automatically until manual review.
"""

import asyncio
import logging
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("nexus.watchdog")


class SystemMode(Enum):
    RUNNING = "RUNNING"
    SAFE = "SAFE"          # No new trades, monitoring only
    HALTED = "HALTED"      # All operations suspended
    EMERGENCY = "EMERGENCY" # Kill switch active


@dataclass
class SystemState:
    """Central system state registry."""
    mode: SystemMode = SystemMode.RUNNING
    open_positions_count: int = 0
    daily_pnl: float = 0.0
    pending_orders: int = 0
    last_execution_time: Optional[str] = None
    last_heartbeat: Optional[str] = None
    broker_connected: bool = False
    consecutive_failures: int = 0
    desync_detected: bool = False
    startup_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "open_positions_count": self.open_positions_count,
            "daily_pnl": round(self.daily_pnl, 2),
            "pending_orders": self.pending_orders,
            "last_execution_time": self.last_execution_time,
            "last_heartbeat": self.last_heartbeat,
            "broker_connected": self.broker_connected,
            "consecutive_failures": self.consecutive_failures,
            "desync_detected": self.desync_detected,
            "startup_time": self.startup_time,
        }


# Thresholds
MAX_CONSECUTIVE_FAILURES = 3
HEARTBEAT_TIMEOUT_SECS = 120  # 2 minutes without heartbeat → concern
EXECUTION_HANG_SECS = 60      # 1 minute for a single pipeline execution


class Watchdog:
    """
    Centralized health monitor.

    Tracks system state and enforces safe-mode transitions.
    Thread-safe: all state mutations go through a lock.
    """

    def __init__(self):
        self._state = SystemState()
        self._mu = threading.Lock()
        self._active_executions: Dict[str, float] = {}  # symbol → start_time (monotonic)

    # ── state access ───────────────────────────────────────────

    def get_state(self) -> SystemState:
        with self._mu:
            return self._state

    def get_mode(self) -> SystemMode:
        with self._mu:
            return self._state.mode

    # ── mode transitions ───────────────────────────────────────

    def set_mode(self, mode: SystemMode, reason: str = ""):
        with self._mu:
            old = self._state.mode
            self._state.mode = mode
        if old != mode:
            logger.warning(f"WATCHDOG_MODE_CHANGE: {old.value} → {mode.value} | {reason}")

    def enter_safe_mode(self, reason: str):
        self.set_mode(SystemMode.SAFE, reason)

    def enter_emergency(self, reason: str):
        self.set_mode(SystemMode.EMERGENCY, reason)

    def resume(self):
        with self._mu:
            self._state.consecutive_failures = 0
            self._state.desync_detected = False
        self.set_mode(SystemMode.RUNNING, "Manual resume")

    # ── trading guards ─────────────────────────────────────────

    def is_trading_allowed(self) -> bool:
        with self._mu:
            return self._state.mode == SystemMode.RUNNING

    # ── heartbeat ──────────────────────────────────────────────

    def record_heartbeat(self):
        with self._mu:
            self._state.last_heartbeat = datetime.now(timezone.utc).isoformat()

    def record_broker_status(self, connected: bool):
        with self._mu:
            was_connected = self._state.broker_connected
            self._state.broker_connected = connected
        if was_connected and not connected:
            logger.error("WATCHDOG: Broker connection LOST")
            self.enter_safe_mode("Broker disconnected")
        elif not was_connected and connected:
            logger.info("WATCHDOG: Broker connection restored")

    # ── execution tracking ─────────────────────────────────────

    def execution_started(self, symbol: str):
        with self._mu:
            self._active_executions[symbol] = time.monotonic()

    def execution_finished(self, symbol: str, success: bool):
        with self._mu:
            self._active_executions.pop(symbol, None)
            if success:
                self._state.consecutive_failures = 0
                self._state.last_execution_time = datetime.now(timezone.utc).isoformat()
            else:
                self._state.consecutive_failures += 1
                failures = self._state.consecutive_failures

        if not success and failures >= MAX_CONSECUTIVE_FAILURES:
            self.enter_safe_mode(
                f"{failures} consecutive execution failures"
            )

    def check_execution_hangs(self) -> list[str]:
        """Return list of symbols whose execution has been running too long."""
        now = time.monotonic()
        hung = []
        with self._mu:
            for symbol, start in self._active_executions.items():
                if now - start > EXECUTION_HANG_SECS:
                    hung.append(symbol)
        return hung

    # ── position desync ────────────────────────────────────────

    def report_desync(self, reason: str):
        """Report a position desync between internal state and broker."""
        with self._mu:
            self._state.desync_detected = True
        logger.critical(f"WATCHDOG_DESYNC: {reason}")
        self.enter_safe_mode(f"Position desync: {reason}")

    # ── sync counters ──────────────────────────────────────────

    def update_position_count(self, count: int):
        with self._mu:
            self._state.open_positions_count = count

    def update_pending_orders(self, count: int):
        with self._mu:
            self._state.pending_orders = count

    def update_daily_pnl(self, pnl: float):
        with self._mu:
            self._state.daily_pnl = pnl


# ── singleton ──────────────────────────────────────────────────
_instance: Optional[Watchdog] = None
_init_mu = threading.Lock()


def get_watchdog() -> Watchdog:
    global _instance
    if _instance is None:
        with _init_mu:
            if _instance is None:
                _instance = Watchdog()
    return _instance
