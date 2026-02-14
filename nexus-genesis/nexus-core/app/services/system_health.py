"""
NEXUS System Health Guard — Phase 6, Part F
=============================================

Automated system diagnostics monitoring:
  - Execution latency
  - MT5 connection health
  - Telegram response time
  - Memory usage

On anomaly: SAFE MODE + alert.
"""

import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.system_health")


# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_EXECUTION_LATENCY_MS = 5000     # 5s max per trade execution
MAX_API_LATENCY_MS = 10000          # 10s max for AI API
MAX_MEMORY_MB = 2048                # 2GB
HEALTH_CHECK_INTERVAL_SECS = 30     # check every 30 seconds
LATENCY_WINDOW_SIZE = 50            # keep last 50 latency samples


# =============================================================================
# HEALTH METRICS
# =============================================================================

class HealthStatus:
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


@dataclass
class HealthReport:
    """System health snapshot."""
    overall_status: str
    execution_latency_avg_ms: float
    execution_latency_p95_ms: float
    api_latency_avg_ms: float
    memory_mb: float
    mt5_connected: bool
    telegram_operational: bool
    issues: List[str]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "execution_latency_avg_ms": round(self.execution_latency_avg_ms, 1),
            "execution_latency_p95_ms": round(self.execution_latency_p95_ms, 1),
            "api_latency_avg_ms": round(self.api_latency_avg_ms, 1),
            "memory_mb": round(self.memory_mb, 1),
            "mt5_connected": self.mt5_connected,
            "telegram_operational": self.telegram_operational,
            "issues": self.issues,
            "timestamp": self.timestamp,
        }


# =============================================================================
# SYSTEM HEALTH GUARD
# =============================================================================

class SystemHealthGuard:
    """
    Monitors system health metrics and triggers SAFE mode on anomaly.
    Thread-safe.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._execution_latencies: deque = deque(maxlen=LATENCY_WINDOW_SIZE)
        self._api_latencies: deque = deque(maxlen=LATENCY_WINDOW_SIZE)
        self._telegram_latencies: deque = deque(maxlen=LATENCY_WINDOW_SIZE)
        self._mt5_connected: bool = True
        self._telegram_ok: bool = True
        self._last_report: Optional[HealthReport] = None
        self._alert_callbacks: List[Callable] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ── Metric Recording ─────────────────────────────────────────

    def record_execution_latency(self, latency_ms: float) -> None:
        """Record a trade execution latency sample."""
        with self._lock:
            self._execution_latencies.append(latency_ms)
        if latency_ms > MAX_EXECUTION_LATENCY_MS:
            logger.warning(f"HEALTH: high execution latency: {latency_ms:.0f}ms")

    def record_api_latency(self, latency_ms: float) -> None:
        """Record an AI API latency sample."""
        with self._lock:
            self._api_latencies.append(latency_ms)
        if latency_ms > MAX_API_LATENCY_MS:
            logger.warning(f"HEALTH: high API latency: {latency_ms:.0f}ms")

    def record_telegram_latency(self, latency_ms: float) -> None:
        """Record a Telegram API latency sample."""
        with self._lock:
            self._telegram_latencies.append(latency_ms)

    def set_mt5_status(self, connected: bool) -> None:
        with self._lock:
            self._mt5_connected = connected

    def set_telegram_status(self, operational: bool) -> None:
        with self._lock:
            self._telegram_ok = operational

    def register_alert_callback(self, callback: Callable) -> None:
        self._alert_callbacks.append(callback)

    # ── Health Check ─────────────────────────────────────────────

    def run_health_check(self) -> HealthReport:
        """Run a comprehensive health check."""
        issues: List[str] = []

        with self._lock:
            # Execution latency
            exec_lats = list(self._execution_latencies)
            api_lats = list(self._api_latencies)
            mt5 = self._mt5_connected
            tg = self._telegram_ok

        # Execution latency analysis
        exec_avg = sum(exec_lats) / len(exec_lats) if exec_lats else 0
        exec_p95 = sorted(exec_lats)[int(len(exec_lats) * 0.95)] if len(exec_lats) >= 5 else exec_avg

        if exec_avg > MAX_EXECUTION_LATENCY_MS:
            issues.append(f"EXECUTION_LATENCY_HIGH: avg={exec_avg:.0f}ms")
        if exec_p95 > MAX_EXECUTION_LATENCY_MS * 1.5:
            issues.append(f"EXECUTION_LATENCY_P95_CRITICAL: p95={exec_p95:.0f}ms")

        # API latency
        api_avg = sum(api_lats) / len(api_lats) if api_lats else 0
        if api_avg > MAX_API_LATENCY_MS:
            issues.append(f"API_LATENCY_HIGH: avg={api_avg:.0f}ms")

        # Memory
        memory_mb = 0.0
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            memory_mb = usage.ru_maxrss / 1024
        except (ImportError, AttributeError):
            pass
        if memory_mb > MAX_MEMORY_MB:
            issues.append(f"MEMORY_HIGH: {memory_mb:.0f}MB > {MAX_MEMORY_MB}MB")

        # MT5
        if not mt5:
            issues.append("MT5_DISCONNECTED")

        # Telegram
        if not tg:
            issues.append("TELEGRAM_OFFLINE")

        # Overall status
        if len(issues) >= 3 or "MT5_DISCONNECTED" in str(issues):
            overall = HealthStatus.CRITICAL
        elif issues:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        report = HealthReport(
            overall_status=overall,
            execution_latency_avg_ms=exec_avg,
            execution_latency_p95_ms=exec_p95,
            api_latency_avg_ms=api_avg,
            memory_mb=memory_mb,
            mt5_connected=mt5,
            telegram_operational=tg,
            issues=issues,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._last_report = report

        # Trigger SAFE mode on CRITICAL
        if overall == HealthStatus.CRITICAL:
            logger.critical(f"HEALTH_CRITICAL: {issues}")
            try:
                from app.services.watchdog import get_watchdog
                wd = get_watchdog()
                if wd.is_trading_allowed():
                    wd.enter_safe_mode(f"System health critical: {'; '.join(issues)}")
            except Exception:
                pass

            for cb in self._alert_callbacks:
                try:
                    cb(issues)
                except Exception:
                    pass

        return report

    # ── Background Monitor ───────────────────────────────────────

    def start(self) -> None:
        """Start background health monitoring."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="nexus-health"
        )
        self._thread.start()
        logger.info("System health guard started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _monitor_loop(self) -> None:
        while self._running:
            try:
                self.run_health_check()
            except Exception as e:
                logger.error(f"Health check error: {e}")
            time.sleep(HEALTH_CHECK_INTERVAL_SECS)

    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._last_report.to_dict() if self._last_report else None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "execution_samples": len(self._execution_latencies),
                "api_samples": len(self._api_latencies),
                "latest_status": self._last_report.overall_status if self._last_report else "UNKNOWN",
            }


# =============================================================================
# SINGLETON
# =============================================================================

_guard: Optional[SystemHealthGuard] = None


def get_health_guard() -> SystemHealthGuard:
    global _guard
    if _guard is None:
        _guard = SystemHealthGuard()
    return _guard
