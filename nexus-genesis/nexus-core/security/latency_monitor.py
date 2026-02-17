"""
NEXUS Latency Monitor — Phase 11 (H)
=======================================

Measures:
    - Signal → Execution delay
    - Execution → Broker confirm delay
    - Average MT5 response time

If latency spikes:
    - Reduce execution frequency
    - Warn via Telegram
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)

logger = logging.getLogger("nexus.latency_monitor")

# Thresholds
SIGNAL_TO_EXEC_MAX_MS = 500       # Signal → Execution should be < 500ms
EXEC_TO_CONFIRM_MAX_MS = 5000     # Execution → Broker confirm < 5s
MT5_RESPONSE_MAX_MS = 3000        # MT5 response should be < 3s
SPIKE_CONSECUTIVE_THRESHOLD = 3   # 3 consecutive spikes triggers alert
HISTORY_SIZE = 200                # Rolling history size


@dataclass
class LatencyRecord:
    timestamp: float
    label: str
    duration_ms: float
    breached: bool


class LatencyMonitor:
    """
    Tracks execution latencies and detects degradation patterns.
    """

    _instance = None

    def __init__(self):
        self._signal_to_exec: deque = deque(maxlen=HISTORY_SIZE)
        self._exec_to_confirm: deque = deque(maxlen=HISTORY_SIZE)
        self._mt5_response: deque = deque(maxlen=HISTORY_SIZE)
        self._consecutive_spikes: int = 0
        self._throttle_active: bool = False
        self._alert_sent: bool = False
        self._total_breaches: int = 0
        self._sec = get_security_logger()

    @classmethod
    def get_instance(cls) -> "LatencyMonitor":
        if cls._instance is None:
            cls._instance = LatencyMonitor()
        return cls._instance

    def record_signal_to_exec(self, duration_ms: float):
        """Record signal-to-execution latency."""
        breached = duration_ms > SIGNAL_TO_EXEC_MAX_MS
        record = LatencyRecord(
            timestamp=time.time(),
            label="signal_to_exec",
            duration_ms=round(duration_ms, 2),
            breached=breached,
        )
        self._signal_to_exec.append(record)
        if breached:
            self._on_breach("signal_to_exec", duration_ms, SIGNAL_TO_EXEC_MAX_MS)

    def record_exec_to_confirm(self, duration_ms: float):
        """Record execution-to-broker-confirmation latency."""
        breached = duration_ms > EXEC_TO_CONFIRM_MAX_MS
        record = LatencyRecord(
            timestamp=time.time(),
            label="exec_to_confirm",
            duration_ms=round(duration_ms, 2),
            breached=breached,
        )
        self._exec_to_confirm.append(record)
        if breached:
            self._on_breach("exec_to_confirm", duration_ms, EXEC_TO_CONFIRM_MAX_MS)

    def record_mt5_response(self, duration_ms: float):
        """Record MT5 response latency."""
        breached = duration_ms > MT5_RESPONSE_MAX_MS
        record = LatencyRecord(
            timestamp=time.time(),
            label="mt5_response",
            duration_ms=round(duration_ms, 2),
            breached=breached,
        )
        self._mt5_response.append(record)
        if breached:
            self._on_breach("mt5_response", duration_ms, MT5_RESPONSE_MAX_MS)

    def _on_breach(self, label: str, actual_ms: float, max_ms: float):
        """Handle a latency breach."""
        self._total_breaches += 1
        self._consecutive_spikes += 1

        self._sec.warning(
            SecurityEventCategory.LATENCY_BREACH,
            f"Latency spike: {label}={actual_ms:.0f}ms (max {max_ms:.0f}ms)",
            details={
                "label": label,
                "actual_ms": actual_ms,
                "threshold_ms": max_ms,
                "consecutive_spikes": self._consecutive_spikes,
            },
            source="LATENCY_MONITOR",
        )

        if self._consecutive_spikes >= SPIKE_CONSECUTIVE_THRESHOLD:
            self._activate_throttle()

    def _activate_throttle(self):
        """Activate execution frequency throttle due to latency spikes."""
        if self._throttle_active:
            return

        self._throttle_active = True

        self._sec.critical(
            SecurityEventCategory.LATENCY_BREACH,
            f"Latency throttle activated: {self._consecutive_spikes} consecutive spikes",
            details={"consecutive_spikes": self._consecutive_spikes},
            source="LATENCY_MONITOR",
        )
        logger.warning("LATENCY THROTTLE ACTIVATED — Reducing execution frequency")

        # Send Telegram warning
        self._notify_latency_spike()

    def _notify_latency_spike(self):
        """Send latency spike alert via Telegram."""
        if self._alert_sent:
            return

        try:
            from app.services.telegram_bot import get_telegram_service
            import asyncio

            telegram = get_telegram_service()
            avg_sig = self._avg(self._signal_to_exec)
            avg_mt5 = self._avg(self._mt5_response)

            message = (
                "LATENCY ALERT\n\n"
                f"Consecutive spikes: {self._consecutive_spikes}\n"
                f"Avg signal-to-exec: {avg_sig:.0f}ms\n"
                f"Avg MT5 response: {avg_mt5:.0f}ms\n\n"
                "Execution frequency reduced."
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(telegram.send_message(message))
                self._alert_sent = True
            except RuntimeError:
                pass
        except ImportError:
            pass

    def record_clean_execution(self):
        """Record a clean execution — resets consecutive spike counter."""
        self._consecutive_spikes = 0
        if self._throttle_active:
            self._throttle_active = False
            self._alert_sent = False
            logger.info("Latency throttle deactivated — Normal latencies restored")

    @property
    def is_throttled(self) -> bool:
        return self._throttle_active

    def _avg(self, records: deque) -> float:
        if not records:
            return 0.0
        vals = [r.duration_ms for r in records]
        return sum(vals) / len(vals)

    def _p95(self, records: deque) -> float:
        if not records:
            return 0.0
        vals = sorted(r.duration_ms for r in records)
        idx = int(len(vals) * 0.95)
        return vals[min(idx, len(vals) - 1)]

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "signal_to_exec": {
                "avg_ms": round(self._avg(self._signal_to_exec), 1),
                "p95_ms": round(self._p95(self._signal_to_exec), 1),
                "count": len(self._signal_to_exec),
            },
            "exec_to_confirm": {
                "avg_ms": round(self._avg(self._exec_to_confirm), 1),
                "p95_ms": round(self._p95(self._exec_to_confirm), 1),
                "count": len(self._exec_to_confirm),
            },
            "mt5_response": {
                "avg_ms": round(self._avg(self._mt5_response), 1),
                "p95_ms": round(self._p95(self._mt5_response), 1),
                "count": len(self._mt5_response),
            },
            "throttle_active": self._throttle_active,
            "consecutive_spikes": self._consecutive_spikes,
            "total_breaches": self._total_breaches,
        }


def get_latency_monitor() -> LatencyMonitor:
    return LatencyMonitor.get_instance()
