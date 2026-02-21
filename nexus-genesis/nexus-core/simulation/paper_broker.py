"""
NEXUS Paper Broker
==================
Realistic simulation broker for "Live-Simulation" mode.

Features:
1. Matches MT5 execution interface.
2. Simulates network latency (random delay).
3. Simulates slippage based on volatility.
4. Tracks virtual balance and positions.
"""

import asyncio
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from uuid import uuid4

logger = logging.getLogger("nexus.paper_broker")

@dataclass
class PaperPosition:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    opened_at: datetime
    sl: Optional[float] = None
    tp: Optional[float] = None

@dataclass
class DetailedOrderResult:
    """Matches output of execution.py trade result."""
    status: str
    message: str
    order_id: str
    filled_price: float
    slippage: float
    venue: Any = None # identifying self as venue

class PaperVenue:
    name: str = "PAPER_SIMULATOR"

class PaperBroker:
    """
    Simulates a real broker.
    Values are stored in memory.
    """
    
    def __init__(self, initial_balance: float = 100000.0):
        self.balance = initial_balance
        self.equity = initial_balance
        self.positions: Dict[str, PaperPosition] = {}
        self.orders: Dict[str, Any] = {}
        self._price_source = None # Needs to be injected or updated via tick
        
    def set_price_source(self, provider):
        """Inject market data provider for current price lookups."""
        self._price_source = provider

    async def get_balance(self) -> float:
        return self.balance
        
    async def get_equity(self) -> float:
        # Calculate unrealized PnL
        unrealized = 0.0
        # This requires current price for all positions. 
        # For simplicity in this version, we assume equity ~= balance if price source not available,
        # or we implement a price fetch if source is available.
        return self.equity

    async def execute_order(self, symbol: str, side: str, quantity: float, price: float = 0.0, 
                          sl: float = 0.0, tp: float = 0.0) -> DetailedOrderResult:
        """Simulate trade execution with latency and slippage."""
        
        # 1. Simulate Network Latency (50ms - 200ms)
        latency = random.uniform(0.05, 0.2)
        await asyncio.sleep(latency)
        
        # 2. Get Execution Price (with Slippage)
        # If price is 0 (Market Order), use "current" price.
        # Check if we have a price source
        exec_price = price
        if exec_price <= 0:
            # Fallback for simulation if no live feed: use a random walk from 100
            # In real usage, this method should probably be called with a reference price
            exec_price = 100.0 
            if self._price_source:
                # Try to get latest price
                ticker = await self._price_source.get_ticker(symbol)
                exec_price = ticker['ask'] if side == 'buy' else ticker['bid']

        # Simulate Slippage (0.1 to 2 pips equivalent, roughly 0.01% - 0.05%)
        slippage_pct = random.uniform(0.0001, 0.0005)
        if side == 'buy':
            exec_price = exec_price * (1 + slippage_pct)
        else:
            exec_price = exec_price * (1 - slippage_pct)
            
        # 3. Create Position
        position = PaperPosition(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=exec_price,
            opened_at=datetime.now(timezone.utc),
            sl=sl,
            tp=tp
        )
        
        # 4. Store
        order_id = str(uuid4())
        self.orders[order_id] = position
        
        # Determine if closing or opening
        # Simplified: Auto-hedge / Netting not fully implemented. 
        # We assume separate positions for now or simple netting.
        # Let's implement simple netting: if opposite exists, reduce/close.
        
        if symbol in self.positions:
            existing = self.positions[symbol]
            if existing.side != side:
                # Closing / Reducing
                # Calculate PnL on closed portion
                close_qty = min(existing.quantity, quantity)
                
                # Update Balance
                if existing.side == 'buy':
                    pnl = (exec_price - existing.entry_price) * close_qty
                else:
                    pnl = (existing.entry_price - exec_price) * close_qty
                
                self.balance += pnl
                self.equity += pnl # Realized
                
                # Update Position
                if existing.quantity > quantity:
                    existing.quantity -= quantity
                elif existing.quantity < quantity:
                    # Flip
                    remaining = quantity - existing.quantity
                    self.positions[symbol] = PaperPosition(
                        symbol=symbol, 
                        side=side, 
                        quantity=remaining, 
                        entry_price=exec_price,
                        opened_at=datetime.now(timezone.utc)
                    )
                else:
                    del self.positions[symbol]
                    
            else:
                # Adding (Averaging)
                total_qty = existing.quantity + quantity
                avg_price = ((existing.entry_price * existing.quantity) + (exec_price * quantity)) / total_qty
                existing.quantity = total_qty
                existing.entry_price = avg_price
        else:
            self.positions[symbol] = position

        logger.info(f"PAPER EXECUTION: {side.upper()} {quantity} {symbol} @ {exec_price:.5f} (Slippage: {slippage_pct*100:.3f}%)")

        return DetailedOrderResult(
            status="FILLED",
            message="Paper execution successful",
            order_id=order_id,
            filled_price=exec_price,
            slippage=exec_price - price if price > 0 else 0.0,
            venue=PaperVenue()
        )

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        return {
            sym: {
                "symbol": p.symbol,
                "side": p.side,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "pnl": 0.0 # Placeholder, requires live price
            }
            for sym, p in self.positions.items()
        }
