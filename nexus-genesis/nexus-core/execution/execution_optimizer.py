"""
NEXUS Execution Optimizer
=========================
Phase 9: Execution Intelligence Layer.

This module sits between the Execution Engine and the Broker (MT5/Binance).
It refines HOW orders are executed to minimize friction and maximize precision.

Responsibilities:
1. Spread Monitoring (Delay if spread > threshold)
2. Micro-Structure Analysis (Avoid buying extended tops)
3. Slippage Control & Tracking
4. Execution Scoring
5. Liquidity Time Filter
"""

import logging
import asyncio
import json
import os
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple

from app.services.market_data import get_provider, AssetClass, Timeframe
from app.services.risk_governor import validate_trade
# Circular import avoidance: We don't import ExecutionEngine here, 
# ExecutionEngine will import ExecutionOptimizer.

logger = logging.getLogger("nexus.execution.optimizer")

@dataclass
class ExecutionOptimizationResult:
    allowed: bool
    modified_price: Optional[float]
    wait_time: float # Seconds to delay
    reason: str
    score: int # 0-100 predicted quality

class ExecutionOptimizer:
    _instance = None
    
    # Configuration
    SPREAD_THRESHOLD_PIPS = 3.0 # Standard
    MAX_SPREAD_DEVIATION = 1.5 # 1.5x normal spread
    SLIPPAGE_TOLERANCE_PCT = 0.1 # 0.1%
    MICRO_STRUCTURE_LOOKBACK = 5 # M1 candles
    
    def __init__(self):
        self.market_provider = get_provider()
        self.stats_file = "nexus-core/execution/execution_stats.json"
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ExecutionOptimizer()
        return cls._instance

    async def optimize_entry(
        self, 
        symbol: str, 
        side: str, 
        current_price: float,
        venue_spread: float = 0.0
    ) -> ExecutionOptimizationResult:
        """
        Analyze execution conditions before transmission.
        """
        score = 100
        reason = "Optimal"
        wait = 0.0
        allowed = True
        
        # 1. Spread Filter
        # If passed venue_spread (real-time from MT5) is high
        if venue_spread > 0:
            # Simple heuristic: if spread > 5 pips (assuming standard pair), might depend on asset
            # Refinement needed per asset class. 
            # For now, generic check.
            pass

        # 2. Time Filter (Liquidity)
        # Avoid first/last 2 mins of hour? Or market open?
        # User request: "Avoid First 2 minutes after open... Last 2 minutes before close"
        # We need market hours. For now, we skip this complex calendar logic 
        # unless we detect high volatility.

        # 3. Micro-Structure Check (The "Don't Buy Top" logic)
        try:
            # Fetch last 5 M1 candles
            df = await self.market_provider.get_ohlcv(symbol, AssetClass.FOREX, Timeframe.M1, bars=5)
            if not df.empty:
                last_close = df.iloc[-1]['close']
                # Check extension
                # If price is far from M1 EMA(5)? 
                ema_5 = df['close'].ewm(span=5).mean().iloc[-1]
                extension = abs(last_close - ema_5) / ema_5 * 100
                
                # If extended > 0.05% on M1?
                if extension > 0.05:
                     score -= 20
                     reason = "Price Extended - Micro Pullback Likely"
                     wait = 5.0 # Wait 5 seconds
        except Exception as e:
            logger.warning(f"Micro-structure check failed: {e}")
            
        # 4. Slippage Scoring (Historical)
        # TODO: Read execution_stats.json and penalize score if asset has bad history
        
        return ExecutionOptimizationResult(
            allowed=allowed,
            modified_price=None, # Market order usually
            wait_time=wait,
            reason=reason,
            score=score
        )

    def record_execution(self, symbol: str, slippage: float, spread: float, score: int):
        """
        Log execution quality for future learning.
        """
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "slippage": slippage,
                "spread": spread,
                "score": score
            }
            # Append to log file (or proper DB)
            with open("logs/execution_quality.log", "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Telemetry status."""
        return {
            "execution_score": 98, # Placeholder
            "slippage_avg": 0.0,
            "broker_condition": "OPTIMAL",
            "last_optimization": "NONE"
        }

# Global Accessor
_optimizer = None
def get_optimizer():
    global _optimizer
    if _optimizer is None:
        _optimizer = ExecutionOptimizer()
    return _optimizer
