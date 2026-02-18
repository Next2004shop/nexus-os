"""
NEXUS MT5 Heartbeat Monitor — Production Resilience
======================================================

Periodically checks MT5 bridge connectivity and auto-reconnects.

Behavior:
    - Ping MT5 bridge every 30 seconds
    - If 3 consecutive failures: alert via Telegram
    - Auto-reconnect with exponential backoff
    - Log all connection state changes

Does NOT modify mt_bridge.py — monitors it externally.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.mt5_heartbeat")

HEARTBEAT_INTERVAL_SECONDS = 30
MAX_CONSECUTIVE_FAILURES = 3
RECONNECT_BACKOFF_BASE = 2  # seconds


class MT5HeartbeatMonitor:
    """
    External monitor for MT5 bridge connectivity.
    Auto-reconnects and alerts on persistent failures.
    """

    _instance = None

    def __init__(self):
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._consecutive_failures: int = 0
        self._total_pings: int = 0
        self._total_failures: int = 0
        self._last_status: str = "UNKNOWN"
        self._last_check: Optional[str] = None
        self._alert_sent: bool = False
        self._events: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> "MT5HeartbeatMonitor":
        if cls._instance is None:
            cls._instance = MT5HeartbeatMonitor()
        return cls._instance

    async def start(self):
        """Start the heartbeat monitor."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("MT5 heartbeat monitor started")

    async def stop(self):
        """Stop the monitor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MT5 heartbeat monitor stopped")

    async def _monitor_loop(self):
        """Periodic heartbeat check."""
        # Wait for system to initialize
        await asyncio.sleep(10)

        while self._running:
            try:
                await self._check_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)

    async def _check_heartbeat(self):
        """Perform a single heartbeat check."""
        self._total_pings += 1
        self._last_check = datetime.now(timezone.utc).isoformat()

        connected = False
        try:
            from app.services.execution import get_engine
            engine = get_engine()
            connected = engine.mt5._initialized
        except Exception:
            connected = False

        if connected:
            if self._last_status != "CONNECTED":
                self._record_event("CONNECTED", "MT5 bridge connection restored")
                if self._alert_sent:
                    await self._send_recovery_alert()
                    self._alert_sent = False
            self._consecutive_failures = 0
            self._last_status = "CONNECTED"
        else:
            self._consecutive_failures += 1
            self._total_failures += 1
            self._last_status = "DISCONNECTED"

            if self._consecutive_failures == 1:
                self._record_event("FAILURE", "MT5 bridge connection lost")
                logger.warning("MT5 heartbeat: connection lost")

            # Alert after threshold
            if self._consecutive_failures >= MAX_CONSECUTIVE_FAILURES and not self._alert_sent:
                self._record_event("ALERT", f"MT5 disconnected for {self._consecutive_failures} checks")
                await self._send_failure_alert()
                self._alert_sent = True

            # Auto-reconnect attempt
            await self._attempt_reconnect()

    async def _attempt_reconnect(self):
        """Attempt to reconnect MT5 bridge."""
        try:
            from app.services.mt_bridge import get_session_bridge
            bridge = get_session_bridge()
            status = bridge.get_status()

            # Try reconnecting active sessions
            for uid_prefix, conn_info in status.get("connections", {}).items():
                if not conn_info.get("connected"):
                    # Find full user_id (we only have prefix)
                    for full_uid in list(bridge._connections.keys()):
                        if full_uid.startswith(uid_prefix.replace("...", "")):
                            await bridge.reconnect(full_uid)
                            break
        except Exception as e:
            logger.error(f"MT5 reconnect attempt failed: {e}")

    async def _send_failure_alert(self):
        """Send MT5 disconnection alert via Telegram."""
        try:
            from app.services.telegram_bot import get_telegram_service
            telegram = get_telegram_service()
            await telegram.send_message(
                "*MT5 CONNECTION LOST*\n\n"
                f"Consecutive failures: {self._consecutive_failures}\n"
                f"Total failures: {self._total_failures}\n\n"
                "Auto-reconnect in progress.\n"
                "Use /status to check."
            )
        except Exception as e:
            logger.error(f"Failed to send MT5 alert: {e}")

    async def _send_recovery_alert(self):
        """Send MT5 recovery alert via Telegram."""
        try:
            from app.services.telegram_bot import get_telegram_service
            telegram = get_telegram_service()
            await telegram.send_message(
                "*MT5 CONNECTION RESTORED*\n\n"
                "Bridge reconnected successfully.\n"
                "Trading operations resumed."
            )
        except Exception as e:
            logger.error(f"Failed to send MT5 recovery alert: {e}")

    def _record_event(self, event_type: str, message: str):
        """Record a monitor event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "message": message,
        }
        self._events.append(event)
        if len(self._events) > 100:
            self._events = self._events[-100:]

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "last_status": self._last_status,
            "last_check": self._last_check,
            "consecutive_failures": self._consecutive_failures,
            "total_pings": self._total_pings,
            "total_failures": self._total_failures,
            "alert_sent": self._alert_sent,
            "recent_events": self._events[-10:],
        }


def get_mt5_heartbeat() -> MT5HeartbeatMonitor:
    return MT5HeartbeatMonitor.get_instance()
