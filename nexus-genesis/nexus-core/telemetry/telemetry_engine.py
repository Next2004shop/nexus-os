"""
NEXUS Telemetry Engine
======================

Real-time system observability and performance tracking.
Polls state registries and computes live metrics without interfering with execution.

Responsibilities:
- Poll broker/risk state every 5s
- Aggregation of rolling limits
- Error rate tracking
- Latency monitoring
"""

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# Import internal state accessors
from risk.risk_governor import get_risk_status
from system.runtime_guard import get_guard

logger = logging.getLogger("nexus.telemetry")

@dataclass
class SystemMetrics:
    equity: float = 0.0
    balance: float = 0.0
    floating_pl: float = 0.0
    daily_return: float = 0.0
    win_rate: float = 0.0
    drawdown: float = 0.0
    open_positions: int = 0
    margin_usage: float = 0.0
    system_mode: str = "RUNNING"
    latency_ms: float = 0.0
    error_rate: float = 0.0
    runtime_status: str = "UNKNOWN"
    
    # Warning flags
    warning_drawdown: bool = False
    warning_latency: bool = False
    warning_errors: bool = False

class TelemetryEngine:
    _instance = None
    
    def __init__(self):
        self._metrics = SystemMetrics()
        self._history_equity = deque(maxlen=2000) # Store ~2-3 hours of 5s data or more
        self._history_pnl = deque(maxlen=2000)
        self._errors = deque(maxlen=100) # Rolling error log for rate calc
        self._start_time = datetime.now()
        self._running = False
        self._polling_task = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TelemetryEngine()
        return cls._instance
    
    async def start(self):
        """Start the background polling task."""
        if self._running:
            return
        
        self._running = True
        self._polling_task = asyncio.create_task(self._poll_loop())
        logger.info("Telemetry Engine started")
        
    async def stop(self):
        """Stop polling."""
        self._running = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        logger.info("Telemetry Engine stopped")

    def record_error(self, source: str):
        """Record an error event."""
        self._errors.append(datetime.now())

    def _calculate_error_rate(self) -> float:
        """Calculate errors per minute."""
        if not self._errors:
            return 0.0
        
        now = datetime.now()
        # Count errors in last 60 seconds
        recent_errors = [t for t in self._errors if (now - t).total_seconds() < 60]
        return len(recent_errors)

    async def _poll_loop(self):
        """Main polling loop."""
        while self._running:
            try:
                start_tick = datetime.now()
                await self._update_metrics()
                
                # Calculate latency of the update cycle itself as a proxy for system load
                latency = (datetime.now() - start_tick).total_seconds() * 1000
                self._metrics.latency_ms = round(latency, 2)
                
            except Exception as e:
                logger.error(f"Telemetry update failed: {e}")
                self.record_error("telemetry_poll")
            
            await asyncio.sleep(5) # 5 second interval

    async def _update_metrics(self):
        """Fetch and compute latest metrics."""
        # 1. Get Risk State
        risk_state = get_risk_status() # This is fast (in-memory)
        
        # 1.5. Get Runtime Guard Status
        try:
            from system.runtime_guard import get_guard
            guard_status = get_guard().get_status()
            self._metrics.runtime_status = guard_status["mode"]
        except ImportError:
            self._metrics.runtime_status = "UNKNOWN"
        except Exception as e:
            logger.error(f"Failed to get guard status: {e}")
            self._metrics.runtime_status = "ERROR"
        

        
        # 2. Update scalar metrics
        self._metrics.equity = risk_state["equity"]["current"]
        self._metrics.balance = risk_state["equity"]["initial"] # Using initial as balance proxy if balance not in status
        self._metrics.drawdown = risk_state["drawdown"]["current"]
        self._metrics.system_mode = risk_state["risk_level"]
        self._metrics.open_positions = risk_state["open_positions_count"]
        self._metrics.daily_return = risk_state["total_pnl_pct"] # "Total" for now acting as Daily in simple mode
        self._metrics.floating_pl = self._metrics.equity - self._metrics.balance
        
        # Win rate (placeholder - RiskGovernor tracks consecutive losses but not full win rate history in status)
        # We'll default to 0 or mock until StrategyEngine pushes trade history
        self._metrics.win_rate = 0.0 

        # Exposure/Margin
        if "exposure" in risk_state:
            self._metrics.margin_usage = risk_state["exposure"]["current_pct"]
        
        # Error Rate
        self._metrics.error_rate = self._calculate_error_rate()
        
        # 3. Update History (for charts)
        timestamp = datetime.now().isoformat()
        self._history_equity.append({
            "timestamp": timestamp,
            "value": self._metrics.equity
        })
        self._history_pnl.append({
            "timestamp": timestamp,
            "value": self._metrics.daily_return
        })
        
        # 4. Check Warnings
        self._metrics.warning_drawdown = self._metrics.drawdown > 5.0
        self._metrics.warning_latency = self._metrics.latency_ms > 500
        self._metrics.warning_errors = self._metrics.error_rate > 5

    def get_snapshot(self) -> Dict[str, Any]:
        """Return current snapshot for API."""
        return {
            "metrics": {
                "equity": self._metrics.equity,
                "balance": self._metrics.balance,
                "floating_pl": round(self._metrics.floating_pl, 2),
                "daily_return": self._metrics.daily_return,
                "win_rate": self._metrics.win_rate,
                "drawdown": self._metrics.drawdown,
                "open_positions": self._metrics.open_positions,
                "system_mode": self._metrics.system_mode,
                "runtime_status": self._metrics.runtime_status,
                "latency_ms": self._metrics.latency_ms,
                "error_rate": self._metrics.error_rate,
                "margin_usage": self._metrics.margin_usage
            },
            "history": {
                "equity": list(self._history_equity),
                "pnl": list(self._history_pnl)
            },
            "warnings": {
                "drawdown": self._metrics.warning_drawdown,
                "latency": self._metrics.warning_latency,
                "errors": self._metrics.warning_errors
            }
        }

# Global accessor
def get_telemetry():
    return TelemetryEngine.get_instance()
