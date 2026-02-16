"""
NEXUS Runtime Guard - Self-Healing Supervisor
============================================

Monitors system health and stability.
Implements the "Resilience Layer" (Phase 6).

Responsibilities:
1. Detect crashes and stalls
2. Monitor resources (memory)
3. Track error rates
4. Manage System Mode (RUNNING -> RECOVERING -> SAFE_MODE)
5. Execute auto-recovery procedures

Safe, isolated, and authoritative over system state.
"""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional

# Try to import psutil for memory monitoring
try:
    import psutil
except ImportError:
    psutil = None

from app.services import execution, risk_governor, circuit_breaker
from telemetry import telemetry_engine

# Setup specialized logger for recovery events
recovery_logger = logging.getLogger("nexus.recovery")
file_handler = logging.FileHandler("logs/recovery.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
recovery_logger.addHandler(file_handler)
recovery_logger.setLevel(logging.INFO)

logger = logging.getLogger("nexus.system.guard")

class RuntimeMode(Enum):
    RUNNING = "RUNNING"
    RECOVERING = "RECOVERING"
    SAFE_MODE = "SAFE_MODE"
    HALTED = "HALTED"

@dataclass
class SystemStatus:
    mode: RuntimeMode
    uptime_seconds: float
    memory_usage_mb: float
    loop_latency_ms: float
    active_warnings: int
    last_recovery_action: Optional[str]

class RuntimeGuard:
    _instance = None

    def __init__(self):
        self._mode = RuntimeMode.RUNNING
        self._start_time = time.time()
        self._last_tick = time.time()
        self._loop_latency = 0.0
        self._check_interval = 3.0  # Seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Thresholds
        self.MAX_LOOP_LATENCY = 15.0  # Seconds (Stall detection)
        self.MAX_MEMORY_MB = 1024.0   # 1GB Limit
        self.MAX_ERROR_RATE = 10.0    # Errors per minute
        self.BROKER_TIMEOUT = 10.0    # Seconds
        
        # State
        self._crash_count = 0
        self._last_recovery_time = 0
        self._consecutive_failures = 0

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RuntimeGuard()
        return cls._instance

    async def start(self):
        """Start the guard loop."""
        if self._running:
            return
        self._running = True
        logger.info("RuntimeGuard STARTED - Monitoring Active")
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop the guard loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("RuntimeGuard STOPPED")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                start_check = time.time()
                
                # 1. Update Monitor Stats (Self-Monitoring)
                self._update_loop_stats()
                
                # 2. Perform System Checks
                if self._mode != RuntimeMode.SAFE_MODE:
                    await self._check_health()
                
                # 3. Sleep for remainder of interval
                elapsed = time.time() - start_check
                sleep_time = max(0.1, self._check_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Critical Guard Error: {e}")
                traceback.print_exc()
                # Don't crash the guard itself
                await asyncio.sleep(5)

    def _update_loop_stats(self):
        """Calculate loop latency (stall detection)."""
        now = time.time()
        # Time since last tick is the actual loop duration including sleep
        # If this exceeds interval significantly, the loop is stalling
        delta = now - self._last_tick
        self._loop_latency = delta
        self._last_tick = now

        # Warning only, effectively detected by check below
        if delta > self.MAX_LOOP_LATENCY:
            logger.warning(f"HIGH LOOP LATENCY DETECTED: {delta:.2f}s")

    async def _check_health(self):
        """Execute health checks."""
        failures = []

        # CHECK 1: Broker Heartbeat
        # Use Circuit Breaker's connectivity monitor or check MT5/Binance directly via engine
        # Assuming ConnectivityMonitor tracks this, otherwise we check provider
        # For now, we'll check if RiskGovernor has recent data update?
        # Let's rely on telemetry's latency metric or Engine's heartbeat logic if it existed.
        # Implementation: Check Circuit Breaker Connectivity
        manager = circuit_breaker.get_manager()
        # Assuming 'MT5' service is registered in connectivity monitor
        if not manager.connectivity.is_connected('MT5') and execution.get_engine().config.primary_venue.value == "MT5":
             # Only a failure if we expect it to be connected
             # We can check engine.mt5._initialized
             pass 

        # CHECK 2: Execution Loop Stalled
        # Checked via self._loop_latency (which proxies the event loop health)
        if self._loop_latency > self.MAX_LOOP_LATENCY:
            failures.append(f"Execution loop stalled ({self._loop_latency:.1f}s)")

        # CHECK 3: Memory Usage
        if psutil:
            mem = psutil.Process().memory_info().rss / (1024 * 1024)
            if mem > self.MAX_MEMORY_MB:
                failures.append(f"Memory critical: {mem:.1f}MB")

        # CHECK 4: Error Rate
        tel = telemetry_engine.get_telemetry()
        if tel.error_rate > self.MAX_ERROR_RATE:
            failures.append(f"High error rate: {tel.error_rate:.1f}/min")

        # DECISION
        if failures:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3: # 3 consecutive failing checks triggers recovery
                await self._trigger_recovery(failures)
        else:
            self._consecutive_failures = 0
            if self._mode == RuntimeMode.RECOVERING:
                self._transition_to(RuntimeMode.RUNNING, "Health checks passed")

    async def _trigger_recovery(self, reasons: list):
        """Initiate Recovery Protocol."""
        reason_str = "; ".join(reasons)
        recovery_logger.warning(f"FAILURE DETAILS | {reason_str}")
        
        self._transition_to(RuntimeMode.RECOVERING, f"Detected: {reason_str}")
        
        try:
            # STEP 1: Freeze Trade Requests
            # We trip the 'system_guard' circuit breaker
            circuit_breaker.get_breaker("system_guard").force_open("RuntimeGuard Recovery Initiated")
            recovery_logger.info("ACTION | Trade requests frozen")

            # STEP 2: Sync Positions (Read-only check)
            # We trigger a force refresh on RiskGovernor
            await risk_governor.get_risk_status(force_update=True)
            recovery_logger.info("ACTION | Positions Synced")

            # STEP 3: Clear Stale Requests
            # Assuming execution engine has a way to flush, or just log
            # execution.get_engine().tracker? 
            # For now we just log
            recovery_logger.info("ACTION | Stale requests cleared (Simulated)")

            # STEP 4: Reconnect Broker
            # If MT5 is disconnected, try to init
            engine = execution.get_engine()
            if engine.config.primary_venue.value == "MT5" and not engine.mt5._initialized:
                recovery_logger.info("ACTION | Attempting MT5 Reconnect...")
                engine.mt5.initialize()

            # STEP 5: Resume if Safe
            # Verify healthy immediate
            # If we don't crash here, we assume partial success.
            # Real success is confirmed by subsequent health checks moving mode back to RUNNING
            
            # Reset Circuit Breaker if immediate checks pass?
            # No, let the half-open logic handle it or 'resume_trading'
            # circuit_breaker.get_breaker("system_guard").force_close() 
            # We will leave it OPEN so 'RECOVERING' mode persists until next health check proves stability
            
            recovery_logger.info("RESULT | Recovery sequence completed. Monitoring...")

        except Exception as e:
            recovery_logger.error(f"RECOVERY FAILED | {e}")
            self._transition_to(RuntimeMode.SAFE_MODE, f"Recovery failed: {e}")

    def _transition_to(self, mode: RuntimeMode, reason: str):
        """Handle state transitions."""
        if self._mode == mode:
            return
        
        old_mode = self._mode
        self._mode = mode
        
        log_msg = f"TRANSITION | {old_mode.name} -> {mode.name} | {reason}"
        logger.warning(log_msg)
        recovery_logger.info(log_msg)
        
        if mode == RuntimeMode.SAFE_MODE:
            # Final Safety Net
            circuit_breaker.get_manager().global_halt(f"SAFE MODE: {reason}")
        
        elif mode == RuntimeMode.RUNNING:
            if old_mode == RuntimeMode.RECOVERING:
                 circuit_breaker.get_breaker("system_guard").force_close()
                 recovery_logger.info("ACTION | System Restored to Normal Operation")

    def get_status(self) -> Dict:
        """Public status accessor."""
        mem_usage = 0.0
        if psutil:
            mem_usage = psutil.Process().memory_info().rss / (1024 * 1024)
            
        return {
            "mode": self._mode.value,
            "uptime": time.time() - self._start_time,
            "memory_mb": round(mem_usage, 1),
            "loop_latency_ms": round(self._loop_latency * 1000, 1),
            "warnings": self._consecutive_failures
        }

# Global Monitor
_guard = RuntimeGuard()

def get_guard():
    return _guard
