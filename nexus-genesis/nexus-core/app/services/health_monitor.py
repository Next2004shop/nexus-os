"""
NEXUS Health Monitor — Phase 7, Part 1
========================================

Institutional-grade system health monitoring.

Monitors:
  - MT5 connection status
  - Broker login state
  - API latency
  - Execution time per order
  - Memory / CPU usage
  - Disk availability
  - Open position count consistency
  - StateRegistry sync integrity

Behaviour:
  - Background thread reports every 60 seconds
  - Escalates to SAFE mode if 3 consecutive failures occur
  - Sends Telegram alert on anomaly detection
"""

import logging
import os
import platform
import shutil
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.health_monitor")

# =============================================================================
# CONFIGURATION
# =============================================================================
MONITOR_INTERVAL_SECS = 60           # report every 60 seconds
MAX_EXECUTION_LATENCY_MS = 5000      # 5s max per order
MAX_API_LATENCY_MS = 10000           # 10s max for AI API
MAX_MEMORY_MB = 2048                 # 2GB
MIN_DISK_FREE_MB = 500               # 500MB minimum free disk
CONSECUTIVE_FAILURE_THRESHOLD = 3    # safe mode after 3 consecutive failures
LATENCY_WINDOW = 100                 # rolling window size


# =============================================================================
# HEALTH REPORT
# =============================================================================

@dataclass
class HealthCheckResult:
    """Result of a single health check cycle."""
    timestamp: str = ""
    mt5_connected: bool = True
    broker_login_ok: bool = True
    api_latency_avg_ms: float = 0.0
    api_latency_p95_ms: float = 0.0
    execution_latency_avg_ms: float = 0.0
    execution_latency_p95_ms: float = 0.0
    memory_mb: float = 0.0
    cpu_time_secs: float = 0.0
    disk_free_mb: float = 0.0
    position_count_mt5: int = 0
    position_count_registry: int = 0
    position_sync_ok: bool = True
    state_registry_ok: bool = True
    issues: List[str] = field(default_factory=list)
    overall_status: str = "HEALTHY"  # HEALTHY, DEGRADED, CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "mt5_connected": self.mt5_connected,
            "broker_login_ok": self.broker_login_ok,
            "api_latency_avg_ms": round(self.api_latency_avg_ms, 1),
            "api_latency_p95_ms": round(self.api_latency_p95_ms, 1),
            "execution_latency_avg_ms": round(self.execution_latency_avg_ms, 1),
            "execution_latency_p95_ms": round(self.execution_latency_p95_ms, 1),
            "memory_mb": round(self.memory_mb, 1),
            "cpu_time_secs": round(self.cpu_time_secs, 2),
            "disk_free_mb": round(self.disk_free_mb, 1),
            "position_count_mt5": self.position_count_mt5,
            "position_count_registry": self.position_count_registry,
            "position_sync_ok": self.position_sync_ok,
            "state_registry_ok": self.state_registry_ok,
            "issues": self.issues,
        }


# =============================================================================
# HEALTH MONITOR
# =============================================================================

class HealthMonitor:
    """
    Comprehensive system health monitor.

    Runs as a background thread, checking all subsystems every 60 seconds.
    Escalates to SAFE mode after CONSECUTIVE_FAILURE_THRESHOLD failures.
    Sends Telegram alerts on anomaly detection.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Latency tracking
        self._execution_latencies: deque = deque(maxlen=LATENCY_WINDOW)
        self._api_latencies: deque = deque(maxlen=LATENCY_WINDOW)

        # State
        self._consecutive_failures: int = 0
        self._total_checks: int = 0
        self._total_failures: int = 0
        self._last_result: Optional[HealthCheckResult] = None
        self._alert_callbacks: List[Callable] = []

    # ── Metric Recording ─────────────────────────────────────────

    def record_execution_latency(self, latency_ms: float) -> None:
        """Record a trade execution latency sample."""
        with self._lock:
            self._execution_latencies.append(latency_ms)

    def record_api_latency(self, latency_ms: float) -> None:
        """Record an AI API latency sample."""
        with self._lock:
            self._api_latencies.append(latency_ms)

    def register_alert_callback(self, callback: Callable) -> None:
        """Register callback for anomaly alerts (e.g. Telegram)."""
        self._alert_callbacks.append(callback)

    # ── Health Check ─────────────────────────────────────────────

    def run_check(self) -> HealthCheckResult:
        """Execute a comprehensive health check across all subsystems."""
        result = HealthCheckResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 1. MT5 connection + broker login
        self._check_mt5(result)

        # 2. API latency
        self._check_api_latency(result)

        # 3. Execution latency
        self._check_execution_latency(result)

        # 4. Memory usage
        self._check_memory(result)

        # 5. CPU usage
        result.cpu_time_secs = time.process_time()

        # 6. Disk availability
        self._check_disk(result)

        # 7. Position count consistency
        self._check_position_sync(result)

        # 8. StateRegistry integrity
        self._check_state_registry(result)

        # Determine overall status
        if len(result.issues) >= 3 or any(
            i.startswith("MT5_DISCONNECTED") or i.startswith("STATE_REGISTRY_CORRUPT")
            for i in result.issues
        ):
            result.overall_status = "CRITICAL"
        elif result.issues:
            result.overall_status = "DEGRADED"
        else:
            result.overall_status = "HEALTHY"

        # Track consecutive failures
        with self._lock:
            self._total_checks += 1
            self._last_result = result

            if result.overall_status == "CRITICAL":
                self._consecutive_failures += 1
                self._total_failures += 1
            elif result.overall_status == "DEGRADED":
                # Degraded counts as half-failure for consecutive tracking
                self._consecutive_failures += 1
                self._total_failures += 1
            else:
                self._consecutive_failures = 0

        # Log
        if result.overall_status == "CRITICAL":
            logger.critical(f"HEALTH_CRITICAL: {result.issues}")
        elif result.overall_status == "DEGRADED":
            logger.warning(f"HEALTH_DEGRADED: {result.issues}")
        else:
            logger.info(
                f"HEALTH_OK: mem={result.memory_mb:.0f}MB, "
                f"disk={result.disk_free_mb:.0f}MB, "
                f"positions={result.position_count_registry}"
            )

        # Escalation: 3 consecutive failures → SAFE mode
        if self._consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
            self._escalate_to_safe_mode(result)

        # Alert on any issue
        if result.issues:
            self._send_alerts(result)

        return result

    # ── Individual Checks ────────────────────────────────────────

    def _check_mt5(self, result: HealthCheckResult) -> None:
        """Check MT5 connection and broker login state."""
        try:
            import MetaTrader5 as mt5
            info = mt5.terminal_info()
            if info is None:
                result.mt5_connected = False
                result.broker_login_ok = False
                result.issues.append("MT5_DISCONNECTED: terminal_info returned None")
                return

            result.mt5_connected = info.connected
            if not info.connected:
                result.issues.append("MT5_DISCONNECTED: terminal not connected")

            account = mt5.account_info()
            if account is None:
                result.broker_login_ok = False
                result.issues.append("BROKER_LOGIN_FAILED: account_info returned None")
            else:
                result.broker_login_ok = True
                result.position_count_mt5 = mt5.positions_total()

        except ImportError:
            # Non-Windows — MT5 not available, not an error
            result.mt5_connected = True
            result.broker_login_ok = True
        except Exception as e:
            result.mt5_connected = False
            result.issues.append(f"MT5_CHECK_ERROR: {e}")

    def _check_api_latency(self, result: HealthCheckResult) -> None:
        """Check AI API latency from recorded samples."""
        with self._lock:
            samples = list(self._api_latencies)

        if not samples:
            return

        result.api_latency_avg_ms = sum(samples) / len(samples)
        if len(samples) >= 5:
            sorted_s = sorted(samples)
            result.api_latency_p95_ms = sorted_s[int(len(sorted_s) * 0.95)]
        else:
            result.api_latency_p95_ms = result.api_latency_avg_ms

        if result.api_latency_avg_ms > MAX_API_LATENCY_MS:
            result.issues.append(
                f"API_LATENCY_HIGH: avg={result.api_latency_avg_ms:.0f}ms > {MAX_API_LATENCY_MS}ms"
            )

    def _check_execution_latency(self, result: HealthCheckResult) -> None:
        """Check trade execution latency."""
        with self._lock:
            samples = list(self._execution_latencies)

        if not samples:
            return

        result.execution_latency_avg_ms = sum(samples) / len(samples)
        if len(samples) >= 5:
            sorted_s = sorted(samples)
            result.execution_latency_p95_ms = sorted_s[int(len(sorted_s) * 0.95)]
        else:
            result.execution_latency_p95_ms = result.execution_latency_avg_ms

        if result.execution_latency_avg_ms > MAX_EXECUTION_LATENCY_MS:
            result.issues.append(
                f"EXECUTION_LATENCY_HIGH: avg={result.execution_latency_avg_ms:.0f}ms > {MAX_EXECUTION_LATENCY_MS}ms"
            )

    def _check_memory(self, result: HealthCheckResult) -> None:
        """Check process memory usage."""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            result.memory_mb = usage.ru_maxrss / 1024  # KB → MB on Linux
        except (ImportError, AttributeError):
            result.memory_mb = 0.0

        if result.memory_mb > MAX_MEMORY_MB:
            result.issues.append(
                f"MEMORY_HIGH: {result.memory_mb:.0f}MB > {MAX_MEMORY_MB}MB"
            )

    def _check_disk(self, result: HealthCheckResult) -> None:
        """Check available disk space."""
        try:
            usage = shutil.disk_usage("/")
            result.disk_free_mb = usage.free / (1024 * 1024)
        except Exception:
            result.disk_free_mb = 0.0

        if 0 < result.disk_free_mb < MIN_DISK_FREE_MB:
            result.issues.append(
                f"DISK_LOW: {result.disk_free_mb:.0f}MB free < {MIN_DISK_FREE_MB}MB"
            )

    def _check_position_sync(self, result: HealthCheckResult) -> None:
        """Check that open position count matches between MT5 and registry."""
        try:
            from app.services import risk_governor
            state = risk_governor._get_state()
            result.position_count_registry = len(state.open_positions)
        except Exception:
            result.position_count_registry = 0

        # Only compare if MT5 is available and connected
        if result.mt5_connected and result.position_count_mt5 >= 0:
            if result.position_count_mt5 != result.position_count_registry:
                result.position_sync_ok = False
                result.issues.append(
                    f"POSITION_DESYNC: MT5={result.position_count_mt5}, "
                    f"registry={result.position_count_registry}"
                )

    def _check_state_registry(self, result: HealthCheckResult) -> None:
        """Check StateRegistry file integrity."""
        try:
            from app.services import risk_governor
            state = risk_governor._get_state()
            # Basic integrity: equity should be positive if trading
            if state.trading_enabled and state.current_equity <= 0:
                result.state_registry_ok = False
                result.issues.append("STATE_REGISTRY_CORRUPT: equity=0 while trading_enabled=True")
        except Exception as e:
            result.state_registry_ok = False
            result.issues.append(f"STATE_REGISTRY_ERROR: {e}")

    # ── Escalation ───────────────────────────────────────────────

    def _escalate_to_safe_mode(self, result: HealthCheckResult) -> None:
        """Enter SAFE mode after consecutive failures."""
        logger.critical(
            f"HEALTH_ESCALATION: {self._consecutive_failures} consecutive failures "
            f"→ entering SAFE mode"
        )
        try:
            from app.services.watchdog import get_watchdog
            wd = get_watchdog()
            if wd.is_trading_allowed():
                wd.enter_safe_mode(
                    f"Health monitor: {self._consecutive_failures} consecutive failures — "
                    f"{'; '.join(result.issues)}"
                )
        except Exception as e:
            logger.error(f"Failed to enter safe mode: {e}")

    def _send_alerts(self, result: HealthCheckResult) -> None:
        """Send alerts via registered callbacks."""
        for cb in self._alert_callbacks:
            try:
                cb(result)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    # ── Background Monitor ───────────────────────────────────────

    def start(self) -> None:
        """Start background health monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="nexus-health-monitor"
        )
        self._thread.start()
        logger.info("Health monitor started (interval: 60s)")

    def stop(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Health monitor stopped")

    def _monitor_loop(self) -> None:
        while self._running:
            try:
                self.run_check()
            except Exception as e:
                logger.error(f"Health monitor loop error: {e}")
            time.sleep(MONITOR_INTERVAL_SECS)

    # ── Status ───────────────────────────────────────────────────

    def get_latest_result(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._last_result.to_dict() if self._last_result else None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "total_checks": self._total_checks,
                "total_failures": self._total_failures,
                "consecutive_failures": self._consecutive_failures,
                "escalation_threshold": CONSECUTIVE_FAILURE_THRESHOLD,
                "latest_status": self._last_result.overall_status if self._last_result else "UNKNOWN",
            }

    def get_full_diagnostic(self) -> Dict[str, Any]:
        """Full diagnostic report for /health command."""
        with self._lock:
            return {
                "monitor_status": {
                    "running": self._running,
                    "total_checks": self._total_checks,
                    "total_failures": self._total_failures,
                    "consecutive_failures": self._consecutive_failures,
                    "uptime_checks": self._total_checks - self._total_failures,
                },
                "latest_check": self._last_result.to_dict() if self._last_result else None,
                "thresholds": {
                    "max_execution_latency_ms": MAX_EXECUTION_LATENCY_MS,
                    "max_api_latency_ms": MAX_API_LATENCY_MS,
                    "max_memory_mb": MAX_MEMORY_MB,
                    "min_disk_free_mb": MIN_DISK_FREE_MB,
                    "consecutive_failure_threshold": CONSECUTIVE_FAILURE_THRESHOLD,
                },
            }


# =============================================================================
# SINGLETON
# =============================================================================

_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    global _monitor
    if _monitor is None:
        _monitor = HealthMonitor()
    return _monitor
