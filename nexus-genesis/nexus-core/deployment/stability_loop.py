"""
NEXUS Production Stability Loop — Phase 12 (K)
=================================================

Main loop supervisor:
    If main engine crashes:
        - Restart engine
        - Log crash
        - Count crash frequency

    If crashes > 3 in 1 hour:
        - Enter LOCKDOWN
        - Alert operator
"""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger("nexus.stability_loop")

MAX_CRASHES_PER_HOUR = 3
CRASH_WINDOW_SECONDS = 3600  # 1 hour
RESTART_DELAY_SECONDS = 5  # Wait before restart


class StabilityLoop:
    """
    Supervises the main engine loop with crash detection and auto-restart.
    """

    _instance = None

    def __init__(self):
        self._running: bool = False
        self._crash_timestamps: deque = deque(maxlen=50)
        self._total_crashes: int = 0
        self._total_restarts: int = 0
        self._lockdown_triggered: bool = False
        self._current_task: Optional[asyncio.Task] = None
        self._supervised_tasks: Dict[str, asyncio.Task] = {}
        self._crash_log: List[Dict[str, Any]] = []
        self._started_at: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "StabilityLoop":
        if cls._instance is None:
            cls._instance = StabilityLoop()
        return cls._instance

    def supervise(
        self,
        name: str,
        coro_factory: Callable[[], Coroutine],
    ):
        """
        Register a coroutine to be supervised.

        If it crashes, it will be restarted automatically.

        Args:
            name: Identifier for this supervised task
            coro_factory: Callable that returns a new coroutine to run
        """
        if not self._running:
            logger.warning(f"Cannot supervise '{name}' — stability loop not running")
            return

        task = asyncio.create_task(
            self._supervised_runner(name, coro_factory)
        )
        self._supervised_tasks[name] = task
        logger.info(f"Supervising task: {name}")

    async def _supervised_runner(
        self,
        name: str,
        coro_factory: Callable[[], Coroutine],
    ):
        """Run a coroutine with crash detection and auto-restart."""
        while self._running and not self._lockdown_triggered:
            try:
                await coro_factory()
                # If the coroutine completes normally, don't restart
                logger.info(f"Supervised task '{name}' completed normally")
                break
            except asyncio.CancelledError:
                logger.info(f"Supervised task '{name}' cancelled")
                break
            except Exception as e:
                self._record_crash(name, e)

                # Check if too many crashes
                if self._check_crash_frequency():
                    await self._enter_lockdown(name)
                    break

                # Wait before restart
                logger.warning(
                    f"Supervised task '{name}' crashed: {e}. "
                    f"Restarting in {RESTART_DELAY_SECONDS}s..."
                )
                await asyncio.sleep(RESTART_DELAY_SECONDS)
                self._total_restarts += 1

    def _record_crash(self, task_name: str, error: Exception):
        """Record a crash event."""
        now = time.time()
        self._crash_timestamps.append(now)
        self._total_crashes += 1

        crash_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task": task_name,
            "error": str(error),
            "error_type": type(error).__name__,
        }
        self._crash_log.append(crash_record)
        if len(self._crash_log) > 100:
            self._crash_log = self._crash_log[-100:]

        logger.error(f"CRASH RECORDED: {task_name} — {type(error).__name__}: {error}")

    def _check_crash_frequency(self) -> bool:
        """Check if crashes exceed threshold."""
        now = time.time()
        window_start = now - CRASH_WINDOW_SECONDS
        recent_crashes = sum(1 for t in self._crash_timestamps if t >= window_start)
        return recent_crashes >= MAX_CRASHES_PER_HOUR

    async def _enter_lockdown(self, trigger_task: str):
        """Enter LOCKDOWN due to excessive crashes."""
        if self._lockdown_triggered:
            return

        self._lockdown_triggered = True
        logger.critical(
            f"STABILITY LOOP: LOCKDOWN — {MAX_CRASHES_PER_HOUR}+ crashes in 1 hour "
            f"(triggered by: {trigger_task})"
        )

        # Enter failsafe lockdown
        try:
            from security.failsafe import get_failsafe
            failsafe = get_failsafe()
            failsafe.enter_lockdown(
                f"Stability loop: >{MAX_CRASHES_PER_HOUR} crashes/hour (last: {trigger_task})",
                source="STABILITY_LOOP",
            )
        except Exception as e:
            logger.error(f"Failed to enter lockdown: {e}")

        # Alert operator via Telegram
        try:
            from app.services.telegram_bot import get_telegram_service
            telegram = get_telegram_service()

            recent = self._crash_log[-5:]
            crash_summary = "\n".join(
                f"  {c['task']}: {c['error_type']}" for c in recent
            )

            message = (
                "STABILITY LOCKDOWN\n"
                "=" * 25 + "\n\n"
                f"Crashes in last hour: {MAX_CRASHES_PER_HOUR}+\n"
                f"Trigger: {trigger_task}\n"
                f"Total crashes: {self._total_crashes}\n"
                f"Total restarts: {self._total_restarts}\n\n"
                f"Recent crashes:\n{crash_summary}\n\n"
                "System LOCKED DOWN. Manual intervention required."
            )
            await telegram.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send lockdown alert: {e}")

    async def start(self):
        """Start the stability loop supervisor."""
        if self._running:
            return
        self._running = True
        self._started_at = datetime.now(timezone.utc).isoformat()
        logger.info("Stability loop supervisor started")

    async def stop(self):
        """Stop all supervised tasks and the loop."""
        self._running = False

        # Cancel all supervised tasks
        for name, task in self._supervised_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            logger.info(f"Supervised task '{name}' stopped")

        self._supervised_tasks.clear()
        logger.info("Stability loop supervisor stopped")

    def get_status(self) -> Dict[str, Any]:
        now = time.time()
        window_start = now - CRASH_WINDOW_SECONDS
        recent_crashes = sum(1 for t in self._crash_timestamps if t >= window_start)

        return {
            "running": self._running,
            "started_at": self._started_at,
            "supervised_tasks": list(self._supervised_tasks.keys()),
            "total_crashes": self._total_crashes,
            "total_restarts": self._total_restarts,
            "crashes_last_hour": recent_crashes,
            "lockdown_triggered": self._lockdown_triggered,
            "max_crashes_per_hour": MAX_CRASHES_PER_HOUR,
            "recent_crashes": self._crash_log[-10:],
        }


def get_stability_loop() -> StabilityLoop:
    return StabilityLoop.get_instance()
