"""
NEXUS Resource Monitor — Phase 12 (I)
========================================

Track:
    - CPU usage
    - RAM usage
    - Disk space
    - Network latency

If thresholds exceeded:
    - Alert via Telegram
    - Enter SAFE_MODE if critical
"""

import asyncio
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.resource_monitor")

# Thresholds
CPU_WARNING_PCT = 80.0
CPU_CRITICAL_PCT = 95.0
RAM_WARNING_PCT = 80.0
RAM_CRITICAL_PCT = 95.0
DISK_WARNING_MB = 500
DISK_CRITICAL_MB = 100
NETWORK_WARNING_MS = 2000
NETWORK_CRITICAL_MS = 5000

CHECK_INTERVAL_SECONDS = 60  # Check every 60 seconds


def _get_cpu_percent() -> float:
    """Get CPU usage percentage."""
    try:
        # Read from /proc/stat (Linux)
        with open("/proc/stat", "r") as f:
            line = f.readline()
        parts = line.split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:])

        # Need two samples for delta
        time.sleep(0.1)

        with open("/proc/stat", "r") as f:
            line = f.readline()
        parts2 = line.split()
        idle2 = int(parts2[4])
        total2 = sum(int(p) for p in parts2[1:])

        d_idle = idle2 - idle
        d_total = total2 - total
        if d_total == 0:
            return 0.0
        return round((1.0 - d_idle / d_total) * 100, 1)
    except Exception:
        return -1.0


def _get_ram_usage() -> Dict[str, Any]:
    """Get RAM usage info."""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()

        mem = {}
        for line in lines:
            parts = line.split()
            key = parts[0].rstrip(":")
            val = int(parts[1])  # in kB
            mem[key] = val

        total_mb = mem.get("MemTotal", 0) / 1024
        available_mb = mem.get("MemAvailable", mem.get("MemFree", 0)) / 1024
        used_mb = total_mb - available_mb
        pct = (used_mb / total_mb * 100) if total_mb > 0 else 0

        return {
            "total_mb": round(total_mb, 1),
            "used_mb": round(used_mb, 1),
            "available_mb": round(available_mb, 1),
            "percent": round(pct, 1),
        }
    except Exception:
        return {"total_mb": -1, "used_mb": -1, "available_mb": -1, "percent": -1}


def _get_disk_usage() -> Dict[str, Any]:
    """Get disk usage info."""
    try:
        usage = shutil.disk_usage("/")
        total_mb = usage.total / (1024 * 1024)
        used_mb = usage.used / (1024 * 1024)
        free_mb = usage.free / (1024 * 1024)
        pct = (used_mb / total_mb * 100) if total_mb > 0 else 0

        return {
            "total_mb": round(total_mb, 1),
            "used_mb": round(used_mb, 1),
            "free_mb": round(free_mb, 1),
            "percent": round(pct, 1),
        }
    except Exception:
        return {"total_mb": -1, "used_mb": -1, "free_mb": -1, "percent": -1}


def _get_network_latency() -> float:
    """Measure network latency (DNS resolve time as proxy)."""
    try:
        import socket
        start = time.time()
        socket.getaddrinfo("api.telegram.org", 443)
        elapsed_ms = (time.time() - start) * 1000
        return round(elapsed_ms, 1)
    except Exception:
        return -1.0


class ResourceMonitor:
    """
    Monitors system resources and triggers alerts/mode changes on breach.
    """

    _instance = None

    def __init__(self):
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._last_check: Optional[str] = None
        self._alerts_sent: int = 0
        self._safe_mode_triggered: bool = False
        self._history: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> "ResourceMonitor":
        if cls._instance is None:
            cls._instance = ResourceMonitor()
        return cls._instance

    def check_now(self) -> Dict[str, Any]:
        """Run a resource check immediately."""
        cpu_pct = _get_cpu_percent()
        ram = _get_ram_usage()
        disk = _get_disk_usage()
        network_ms = _get_network_latency()

        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_percent": cpu_pct,
            "ram": ram,
            "disk": disk,
            "network_latency_ms": network_ms,
            "alerts": [],
        }

        alerts = []

        # CPU alerts
        if cpu_pct >= CPU_CRITICAL_PCT:
            alerts.append({"resource": "CPU", "level": "CRITICAL", "value": cpu_pct, "threshold": CPU_CRITICAL_PCT})
        elif cpu_pct >= CPU_WARNING_PCT:
            alerts.append({"resource": "CPU", "level": "WARNING", "value": cpu_pct, "threshold": CPU_WARNING_PCT})

        # RAM alerts
        ram_pct = ram.get("percent", 0)
        if ram_pct >= RAM_CRITICAL_PCT:
            alerts.append({"resource": "RAM", "level": "CRITICAL", "value": ram_pct, "threshold": RAM_CRITICAL_PCT})
        elif ram_pct >= RAM_WARNING_PCT:
            alerts.append({"resource": "RAM", "level": "WARNING", "value": ram_pct, "threshold": RAM_WARNING_PCT})

        # Disk alerts
        disk_free = disk.get("free_mb", 9999)
        if 0 <= disk_free <= DISK_CRITICAL_MB:
            alerts.append({"resource": "DISK", "level": "CRITICAL", "value": disk_free, "threshold": DISK_CRITICAL_MB})
        elif 0 <= disk_free <= DISK_WARNING_MB:
            alerts.append({"resource": "DISK", "level": "WARNING", "value": disk_free, "threshold": DISK_WARNING_MB})

        # Network alerts
        if network_ms >= NETWORK_CRITICAL_MS:
            alerts.append({"resource": "NETWORK", "level": "CRITICAL", "value": network_ms, "threshold": NETWORK_CRITICAL_MS})
        elif network_ms >= NETWORK_WARNING_MS:
            alerts.append({"resource": "NETWORK", "level": "WARNING", "value": network_ms, "threshold": NETWORK_WARNING_MS})

        snapshot["alerts"] = alerts
        self._last_check = snapshot["timestamp"]

        # Keep history (last 60 entries = ~1 hour)
        self._history.append(snapshot)
        if len(self._history) > 60:
            self._history = self._history[-60:]

        # Handle alerts
        if alerts:
            self._handle_alerts(alerts)

        return snapshot

    def _handle_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle resource alerts — notify and potentially enter safe mode."""
        critical_alerts = [a for a in alerts if a["level"] == "CRITICAL"]

        if critical_alerts:
            logger.critical(f"RESOURCE CRITICAL: {critical_alerts}")
            self._send_resource_alert(alerts)

            # Enter SAFE_MODE on critical resource issues
            if not self._safe_mode_triggered:
                try:
                    from security.failsafe import get_failsafe
                    failsafe = get_failsafe()
                    resource_names = ", ".join(a["resource"] for a in critical_alerts)
                    failsafe.enter_safe_mode(
                        f"Critical resource threshold breached: {resource_names}",
                        source="RESOURCE_MONITOR",
                    )
                    self._safe_mode_triggered = True
                    logger.critical(f"SAFE_MODE entered due to resource breach: {resource_names}")
                except Exception as e:
                    logger.error(f"Failed to enter SAFE_MODE: {e}")
        else:
            # Warning-level alerts
            warning_alerts = [a for a in alerts if a["level"] == "WARNING"]
            if warning_alerts:
                logger.warning(f"Resource warnings: {warning_alerts}")
                self._send_resource_alert(alerts)

    def _send_resource_alert(self, alerts: List[Dict[str, Any]]):
        """Send resource alert via Telegram."""
        try:
            from app.services.telegram_bot import get_telegram_service
            import asyncio

            telegram = get_telegram_service()

            lines = ["RESOURCE ALERT\n"]
            for a in alerts:
                lines.append(f"  [{a['level']}] {a['resource']}: {a['value']} (threshold: {a['threshold']})")

            message = "\n".join(lines)

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(telegram.send_message(message))
                self._alerts_sent += 1
            except RuntimeError:
                pass
        except ImportError:
            pass

    async def start(self):
        """Start the resource monitoring loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitor started")

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
        """Periodic resource check loop."""
        while self._running:
            try:
                self.check_now()
            except Exception as e:
                logger.error(f"Resource monitor error: {e}")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "last_check": self._last_check,
            "alerts_sent": self._alerts_sent,
            "safe_mode_triggered": self._safe_mode_triggered,
            "latest_snapshot": self._history[-1] if self._history else None,
            "thresholds": {
                "cpu_warning": CPU_WARNING_PCT,
                "cpu_critical": CPU_CRITICAL_PCT,
                "ram_warning": RAM_WARNING_PCT,
                "ram_critical": RAM_CRITICAL_PCT,
                "disk_warning_mb": DISK_WARNING_MB,
                "disk_critical_mb": DISK_CRITICAL_MB,
                "network_warning_ms": NETWORK_WARNING_MS,
                "network_critical_ms": NETWORK_CRITICAL_MS,
            },
        }


def get_resource_monitor() -> ResourceMonitor:
    return ResourceMonitor.get_instance()
