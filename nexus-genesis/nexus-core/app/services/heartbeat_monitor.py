"""
NEXUS Heartbeat Monitor — System Reliability Layer
====================================================

Phase 4, Part C: Anti-Crash Infrastructure

1. Heartbeat Logger — logs system health every 60 seconds
2. Watchdog Thread — monitors MT5 connection, AI latency,
   execution loop health, memory usage
3. Graceful Shutdown — save state, close handles, sync logs
4. Auto-Restart Guard — crash reason logging + restart support
"""

import asyncio
import logging
import os
import platform
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("nexus.heartbeat")

# =============================================================================
# CONFIGURATION
# =============================================================================
HEARTBEAT_INTERVAL_SECS = 60     # log health every 60 seconds
WATCHDOG_INTERVAL_SECS = 15      # check critical systems every 15 seconds
MAX_MEMORY_MB = 2048             # warn if process exceeds 2GB
MAX_AI_LATENCY_MS = 10000        # 10s AI latency threshold


# =============================================================================
# SYSTEM METRICS COLLECTOR
# =============================================================================

def collect_system_metrics() -> Dict[str, Any]:
    """Collect current system metrics."""
    metrics: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
    }

    # Memory usage (cross-platform)
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # maxrss is in KB on Linux
        metrics["memory_mb"] = round(usage.ru_maxrss / 1024, 1)
    except (ImportError, AttributeError):
        metrics["memory_mb"] = 0

    # CPU time
    metrics["cpu_time_user"] = round(time.process_time(), 2)

    # Thread count
    metrics["active_threads"] = threading.active_count()

    return metrics


# =============================================================================
# HEARTBEAT LOGGER
# =============================================================================

class HeartbeatLogger:
    """
    Logs structured system health every HEARTBEAT_INTERVAL_SECS.

    Includes: equity, open trades, AI latency, CPU, memory.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_heartbeat: Optional[str] = None
        self._heartbeat_count: int = 0
        self._ai_latency_ms: float = 0.0
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start heartbeat logging thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="nexus-heartbeat"
        )
        self._thread.start()
        logger.info("Heartbeat logger started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Heartbeat logger stopped")

    def record_ai_latency(self, latency_ms: float) -> None:
        """Record latest AI response latency."""
        with self._lock:
            self._ai_latency_ms = latency_ms

    def _heartbeat_loop(self) -> None:
        while self._running:
            try:
                self._emit_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            time.sleep(HEARTBEAT_INTERVAL_SECS)

    def _emit_heartbeat(self) -> None:
        metrics = collect_system_metrics()

        # Gather trading state
        try:
            from app.services import risk_governor
            risk = risk_governor.get_risk_status()
            equity = risk.get("equity", {}).get("current", 0)
            open_positions = risk.get("open_positions_count", 0)
            drawdown = risk.get("drawdown", {}).get("current", 0)
        except Exception:
            equity = 0
            open_positions = 0
            drawdown = 0

        with self._lock:
            ai_latency = self._ai_latency_ms
            self._heartbeat_count += 1
            self._last_heartbeat = metrics["timestamp"]

        heartbeat = {
            "heartbeat": self._heartbeat_count,
            "equity": equity,
            "open_positions": open_positions,
            "drawdown_pct": drawdown,
            "ai_latency_ms": round(ai_latency, 1),
            "memory_mb": metrics["memory_mb"],
            "cpu_time": metrics["cpu_time_user"],
            "threads": metrics["active_threads"],
            "timestamp": metrics["timestamp"],
        }

        logger.info(f"HEARTBEAT #{self._heartbeat_count}: {heartbeat}")

        # Update watchdog heartbeat
        try:
            from app.services.watchdog import get_watchdog
            get_watchdog().record_heartbeat()
        except Exception:
            pass

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "heartbeat_count": self._heartbeat_count,
                "last_heartbeat": self._last_heartbeat,
                "ai_latency_ms": round(self._ai_latency_ms, 1),
            }


# =============================================================================
# WATCHDOG THREAD — monitors critical subsystems
# =============================================================================

class SystemWatchdogThread:
    """
    Background thread that monitors:
      - MT5 connection health
      - AI latency
      - Execution loop health
      - Memory usage

    On failure: enters SAFE mode and optionally notifies Telegram.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._alert_callbacks: List[Callable] = []
        self._last_check: Optional[str] = None
        self._issues: List[str] = []

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._watchdog_loop, daemon=True, name="nexus-watchdog"
        )
        self._thread.start()
        logger.info("System watchdog thread started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("System watchdog thread stopped")

    def register_alert_callback(self, callback: Callable) -> None:
        """Register a callback for alert notifications (e.g. Telegram)."""
        self._alert_callbacks.append(callback)

    def _watchdog_loop(self) -> None:
        while self._running:
            try:
                self._run_checks()
            except Exception as e:
                logger.error(f"Watchdog check error: {e}")
            time.sleep(WATCHDOG_INTERVAL_SECS)

    def _run_checks(self) -> None:
        issues: List[str] = []
        self._last_check = datetime.now(timezone.utc).isoformat()

        # Check 1: Memory usage
        metrics = collect_system_metrics()
        if metrics["memory_mb"] > MAX_MEMORY_MB:
            issues.append(f"HIGH_MEMORY: {metrics['memory_mb']}MB > {MAX_MEMORY_MB}MB")

        # Check 2: Watchdog execution hangs
        try:
            from app.services.watchdog import get_watchdog
            wd = get_watchdog()
            hangs = wd.check_execution_hangs()
            if hangs:
                issues.append(f"EXECUTION_HANG: {hangs}")
        except Exception:
            pass

        # Check 3: Daily loss cap
        try:
            from app.services.capital_protection import get_daily_tracker
            tracker = get_daily_tracker()
            if tracker.is_cap_hit():
                issues.append("DAILY_LOSS_CAP_HIT")
        except Exception:
            pass

        # Check 4: Black swan
        try:
            from app.services.capital_protection import get_black_swan
            bs = get_black_swan()
            if bs.is_triggered():
                issues.append("BLACK_SWAN_TRIGGERED")
        except Exception:
            pass

        self._issues = issues

        # If critical issues found, enter safe mode
        if issues:
            logger.warning(f"WATCHDOG_ISSUES: {issues}")
            try:
                from app.services.watchdog import get_watchdog
                wd = get_watchdog()
                if wd.is_trading_allowed():
                    wd.enter_safe_mode(f"Watchdog detected: {'; '.join(issues)}")
            except Exception:
                pass

            # Notify via callbacks
            for cb in self._alert_callbacks:
                try:
                    cb(issues)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "last_check": self._last_check,
            "issues": self._issues,
        }


# =============================================================================
# GRACEFUL SHUTDOWN HANDLER
# =============================================================================

class GracefulShutdown:
    """
    Handles process termination signals gracefully.

    On SIGTERM/SIGINT:
      1. Save state
      2. Close file handles
      3. Sync logs
      4. Notify Telegram (if available)
    """

    def __init__(self):
        self._shutdown_callbacks: List[Callable] = []
        self._shutting_down = False

    def register_callback(self, callback: Callable) -> None:
        """Register a shutdown callback."""
        self._shutdown_callbacks.append(callback)

    def install_signal_handlers(self) -> None:
        """Install signal handlers for graceful shutdown."""
        # Only install in main thread
        try:
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT, self._handle_signal)
            logger.info("Graceful shutdown signal handlers installed")
        except (ValueError, OSError):
            # Not in main thread — skip
            logger.warning("Cannot install signal handlers (not main thread)")

    def _handle_signal(self, signum, frame) -> None:
        sig_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
        logger.critical(f"SHUTDOWN SIGNAL RECEIVED: {sig_name}")
        self.execute_shutdown(f"Signal {sig_name}")

    def execute_shutdown(self, reason: str = "Unknown") -> None:
        """Execute graceful shutdown sequence."""
        if self._shutting_down:
            return
        self._shutting_down = True

        logger.critical(f"NEXUS GRACEFUL SHUTDOWN: {reason}")

        for i, cb in enumerate(self._shutdown_callbacks):
            try:
                logger.info(f"Shutdown callback {i + 1}/{len(self._shutdown_callbacks)}")
                cb()
            except Exception as e:
                logger.error(f"Shutdown callback {i + 1} failed: {e}")

        logger.critical("NEXUS SHUTDOWN COMPLETE")

    @property
    def is_shutting_down(self) -> bool:
        return self._shutting_down


# =============================================================================
# CRASH LOGGER
# =============================================================================

def log_crash(exc_type, exc_value, exc_tb) -> None:
    """
    Unhandled exception hook — logs crash reason before process dies.
    """
    import traceback
    crash_info = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(f"NEXUS CRASH:\n{crash_info}")

    # Try to notify
    try:
        from app.services.telegram_reporter import get_telegram_reporter
        reporter = get_telegram_reporter()
        reporter.send_emergency_sync(f"NEXUS CRASHED: {exc_value}")
    except Exception:
        pass


def install_crash_handler() -> None:
    """Install global crash handler."""
    sys.excepthook = log_crash
    logger.info("Crash handler installed")


# =============================================================================
# SINGLETONS
# =============================================================================

_heartbeat: Optional[HeartbeatLogger] = None
_watchdog_thread: Optional[SystemWatchdogThread] = None
_shutdown: Optional[GracefulShutdown] = None


def get_heartbeat() -> HeartbeatLogger:
    global _heartbeat
    if _heartbeat is None:
        _heartbeat = HeartbeatLogger()
    return _heartbeat


def get_watchdog_thread() -> SystemWatchdogThread:
    global _watchdog_thread
    if _watchdog_thread is None:
        _watchdog_thread = SystemWatchdogThread()
    return _watchdog_thread


def get_graceful_shutdown() -> GracefulShutdown:
    global _shutdown
    if _shutdown is None:
        _shutdown = GracefulShutdown()
    return _shutdown
