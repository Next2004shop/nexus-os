"""
NEXUS Strategy Engine
=====================
Controller for loading and running trading strategies.
Polls market data, feeds it to strategies, and routes signals to the Command Layer.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from strategies.base_strategy import BaseStrategy, Signal
from app.services.market_data import get_provider, AssetClass, Timeframe
from command.router import route_command
from command.schema import TradeCommand

logger = logging.getLogger("nexus.strategies.engine")

class StrategyEngine:
    _instance = None
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.market_provider = get_provider()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = StrategyEngine()
        return cls._instance

    def load_strategy(self, strategy: BaseStrategy):
        """Register a strategy instance."""
        self.strategies[strategy.name] = strategy
        logger.info(f"Loaded strategy: {strategy.name} v{strategy.version}")

    def unload_strategy(self, name: str):
        if name in self.strategies:
            self.strategies[name].stop()
            del self.strategies[name]
            logger.info(f"Unloaded strategy: {name}")

    async def start(self):
        """Start the engine loop."""
        if self._running:
            return
            
        self._running = True
        # Start all strategies
        for s in self.strategies.values():
            s.start()
            
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Strategy Engine STARTED")

    async def stop(self):
        """Stop the engine loop."""
        self._running = False
        if self._task:
            await self._task
        
        for s in self.strategies.values():
            s.stop()
            
        logger.info("Strategy Engine STOPPED")

    async def _process_loop(self):
        """Main analysis loop."""
        while self._running:
            try:
                # In a real engine, we would subscribe to streams.
                # Here, we poll for demonstration/MVP.
                # Assuming strategies tell us what they want? 
                # For now, we iterate strategies and let them request data inside `analyze` 
                # OR we pre-fetch. 
                # Let's let `analyze` handle fetching via the provider usage if needed, 
                # OR we pass the provider to them. 
                # BaseStrategy.analyze signature is `analyze(self, market_data)`.
                # We can pass the provider itself or specific data.
                # Let's pass the provider reference or ensure they have access.
                # Actually, `BaseStrategy` methods are abstract. 
                # We will let the strategy use `get_provider()` internally or pass constraints.
                
                # However, to be efficient, the engine should control the clock.
                
                for name, strategy in self.strategies.items():
                    try:
                        # 1. ANALYZE
                        # We pass 'None' for data if strategy fetches its own, 
                        # or we could fetch the latest M1 candle for the strategy's target symbol.
                        # Since we don't know the target symbol here without metadata, 
                        # we assume strategy parameters define it.
                        
                        signals = await strategy.analyze(self.market_provider)
                        
                        # 2. PROCESS SIGNALS
                        for signal in signals:
                            await self._route_signal(signal)
                            
                    except Exception as e:
                        logger.error(f"Error in strategy {name}: {e}")
                        
                await asyncio.sleep(1) # 1Hz Tick
                
            except Exception as e:
                logger.error(f"Strategy Engine Loop Error: {e}")
                await asyncio.sleep(5)

    async def _route_signal(self, signal: Signal):
        """Convert Signal to Command and Route."""
        if signal.confidence < 0.7: # Minimum confidence gate
             return

        logger.info(f"SIGNAL ROUTING: {signal.side} {signal.symbol} ({signal.reason})")
        
        # Create Command
        # Quantity logic? Strategy should specify? Or Capital Allocator?
        # Strategy usually signals "Entry". Capital Allocator decides size.
        # But TradeCommand requires `lot_size`.
        # We can put a placeholder "0.0" (auto-calculate) or "0.01" min.
        # Let's use 0.01 as base, Capital Allocator receives it.
        # Does capital allocator override? Yes, if we implemented it right.
        # `router.py`: `command.lot_size = allocation.lot_size`.
        
        cmd = TradeCommand(
            direction=signal.side.lower(),
            asset=signal.symbol,
            lot_size=0.01, # Placeholder, will be resized by Capital Allocator
            source=f"STRATEGY_{signal.strategy_name.upper()}"
        )
        
        # Route
        result = await route_command(cmd)
        logger.info(f"Signal Execution Result: {result['status']}")

def get_strategy_engine():
    return StrategyEngine.get_instance()
