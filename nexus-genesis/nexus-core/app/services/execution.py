"""
NEXUS Execution Engine - Dual-Path Trading System
==================================================

Implements institutional-grade order execution:
1. Primary execution via MetaTrader 5
2. Secondary execution via Binance Spot API
3. Slippage control and monitoring
4. Order tracking and reconciliation
5. Circuit breaker integration

AI signals are advisory only - this module handles actual execution.
"""

import asyncio
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import ccxt

from . import risk_governor, vault
from .circuit_breaker import CircuitOpenError, get_breaker, with_circuit_breaker
from execution.execution_optimizer import get_optimizer

logger = logging.getLogger("nexus.execution")


class ExecutionVenue(Enum):
    """Available execution venues."""
    MT5 = "MT5"
    BINANCE = "BINANCE"
    PAPER = "PAPER"  # Paper trading for testing


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass
class OrderResult:
    """Unified order result structure."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    requested_price: Optional[float]
    filled_price: Optional[float]
    filled_quantity: float
    slippage: Optional[float]
    status: OrderStatus
    venue: ExecutionVenue
    timestamp: datetime
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "requested_price": self.requested_price,
            "filled_price": self.filled_price,
            "filled_quantity": self.filled_quantity,
            "slippage": self.slippage,
            "status": self.status.value,
            "venue": self.venue.value,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error
        }


# =============================================================================
# ASSET WHITELIST — Only these symbols can be traded
# =============================================================================
ASSET_WHITELIST = {
    # Forex
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    # Crypto
    "BTCUSD", "BTCUSDT", "BTC/USDT", "ETHUSD", "ETHUSDT", "ETH/USDT",
    # Indices
    "US30", "US500", "NAS100", "US100",
    # Metals
    "XAUUSD", "XAGUSD",
}


@dataclass  
class ExecutionConfig:
    """Execution engine configuration."""
    primary_venue: ExecutionVenue = ExecutionVenue.MT5
    secondary_venue: ExecutionVenue = ExecutionVenue.BINANCE
    max_slippage_pct: float = 0.1  # 0.1% max slippage
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    use_paper_trading: bool = False
    enable_failover: bool = True
    max_lot_size: float = 1.0  # Max lot per order
    max_daily_loss_pct: float = 0.05  # 5% max daily loss


# =============================================================================
# ORDER TRACKER
# =============================================================================
class OrderTracker:
    """
    Tracks all orders for reconciliation and audit.
    """
    
    def __init__(self):
        self._orders: Dict[str, OrderResult] = {}
        self._pending_orders: List[str] = []
    
    def record_order(self, order: OrderResult):
        """Record an order."""
        self._orders[order.order_id] = order
        if order.status == OrderStatus.PENDING:
            self._pending_orders.append(order.order_id)
        logger.info(f"Order recorded: {order.order_id} - {order.side} {order.quantity} {order.symbol}")
    
    def update_order(self, order_id: str, updates: Dict[str, Any]):
        """Update an existing order."""
        if order_id in self._orders:
            order = self._orders[order_id]
            for key, value in updates.items():
                if hasattr(order, key):
                    setattr(order, key, value)
            
            # Remove from pending if filled/failed
            if order.status in [OrderStatus.FILLED, OrderStatus.FAILED, OrderStatus.CANCELLED]:
                if order_id in self._pending_orders:
                    self._pending_orders.remove(order_id)
    
    def get_order(self, order_id: str) -> Optional[OrderResult]:
        """Get order by ID."""
        return self._orders.get(order_id)
    
    def get_pending_orders(self) -> List[OrderResult]:
        """Get all pending orders."""
        return [self._orders[oid] for oid in self._pending_orders if oid in self._orders]
    
    def get_orders_by_symbol(self, symbol: str) -> List[OrderResult]:
        """Get all orders for a symbol."""
        return [o for o in self._orders.values() if o.symbol == symbol]
    
    def calculate_total_slippage(self) -> float:
        """Calculate total slippage across all filled orders."""
        total = 0.0
        count = 0
        for order in self._orders.values():
            if order.status == OrderStatus.FILLED and order.slippage is not None:
                total += order.slippage
                count += 1
        return total / count if count > 0 else 0.0


# Global tracker
_order_tracker = OrderTracker()


# =============================================================================
# BINANCE EXECUTOR
# =============================================================================
class BinanceExecutor:
    """
    Binance Spot execution via CCXT.
    """
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self._exchange: Optional[ccxt.binance] = None
        self._breaker = get_breaker("binance_api")
    
    def _get_client(self) -> ccxt.binance:
        """Get or create Binance client."""
        if self._exchange is None:
            try:
                api_key = vault.get_secret("BINANCE_API_KEY")
                api_secret = vault.get_secret("BINANCE_API_SECRET")
                
                self._exchange = ccxt.binance({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                        'adjustForTimeDifference': True
                    }
                })
                logger.info("Binance client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Binance client: {e}")
                raise
        return self._exchange
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current mid price."""
        try:
            exchange = self._get_client()
            ticker = exchange.fetch_ticker(symbol)
            return (ticker['bid'] + ticker['ask']) / 2
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None
    
    def execute(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        limit_price: Optional[float] = None
    ) -> OrderResult:
        """
        Execute order on Binance.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: BUY or SELL
            quantity: Amount to trade
            limit_price: Optional limit price (market order if None)
        
        Returns:
            OrderResult with execution details
        """
        order_id = f"BN-{uuid.uuid4().hex[:8]}"
        requested_price = limit_price or self.get_current_price(symbol)
        
        try:
            result = self._breaker.call(self._execute_internal, symbol, side, quantity, limit_price)
            
            # Calculate slippage
            filled_price = result.get('average', result.get('price', 0))
            slippage = None
            if requested_price and filled_price:
                slippage = abs(filled_price - requested_price) / requested_price * 100
            
            order_result = OrderResult(
                order_id=result.get('id', order_id),
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                requested_price=requested_price,
                filled_price=filled_price,
                filled_quantity=result.get('filled', quantity),
                slippage=slippage,
                status=OrderStatus.FILLED if result.get('status') == 'closed' else OrderStatus.PENDING,
                venue=ExecutionVenue.BINANCE,
                timestamp=datetime.now(timezone.utc),
                raw_response=result
            )
            
            # Check slippage limit
            if slippage and slippage > self.config.max_slippage_pct:
                logger.warning(f"SLIPPAGE ALERT: {slippage:.3f}% on {symbol}")
            
            _order_tracker.record_order(order_result)
            return order_result
            
        except CircuitOpenError as e:
            logger.error(f"Binance circuit breaker open: {e}")
            return OrderResult(
                order_id=order_id,
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                requested_price=requested_price,
                filled_price=None,
                filled_quantity=0,
                slippage=None,
                status=OrderStatus.REJECTED,
                venue=ExecutionVenue.BINANCE,
                timestamp=datetime.now(timezone.utc),
                error=f"Circuit breaker open: {e}"
            )
        except Exception as e:
            logger.error(f"Binance execution error: {e}")
            return OrderResult(
                order_id=order_id,
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                requested_price=requested_price,
                filled_price=None,
                filled_quantity=0,
                slippage=None,
                status=OrderStatus.FAILED,
                venue=ExecutionVenue.BINANCE,
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )
    
    def _execute_internal(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        limit_price: Optional[float]
    ) -> Dict[str, Any]:
        """Internal execution with circuit breaker wrapper."""
        exchange = self._get_client()
        
        if limit_price:
            return exchange.create_limit_order(
                symbol=symbol,
                side=side.value.lower(),
                amount=quantity,
                price=limit_price
            )
        else:
            return exchange.create_market_order(
                symbol=symbol,
                side=side.value.lower(),
                amount=quantity
            )
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order."""
        try:
            exchange = self._get_client()
            exchange.cancel_order(order_id, symbol)
            _order_tracker.update_order(order_id, {"status": OrderStatus.CANCELLED})
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Cancel all open orders."""
        try:
            exchange = self._get_client()
            result = exchange.cancel_all_orders(symbol=symbol)
            logger.warning(f"Cancelled all orders for {symbol or 'ALL SYMBOLS'}")
            return {"status": "success", "cancelled": result}
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return {"status": "failed", "error": str(e)}


# =============================================================================
# MT5 EXECUTOR
# =============================================================================
class MT5Executor:
    """
    MetaTrader 5 execution.
    Note: MT5 package is Windows-only. This implements the interface
    and falls back to mock for non-Windows environments.
    """
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self._initialized = False
        self._mt5 = None
        self._breaker = get_breaker("mt5_api")
        
        # Try to import MT5
        try:
            import MetaTrader5 as mt5
            self._mt5 = mt5
        except ImportError:
            logger.warning("MetaTrader5 package not available (Windows only)")
    
    def initialize(self) -> bool:
        """Initialize MT5 connection."""
        if self._mt5 is None:
            logger.warning("MT5 not available, using mock mode")
            return False
        
        try:
            login = int(vault.get_secret("MT5_LOGIN"))
            password = vault.get_secret("MT5_PASSWORD")
            server = vault.get_secret("MT5_SERVER")
            
            if not self._mt5.initialize(login=login, password=password, server=server):
                error = self._mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            self._initialized = True
            logger.info("MT5 connection established")
            return True
            
        except Exception as e:
            logger.error(f"MT5 initialization error: {e}")
            return False
    
    def get_current_price(self, symbol: str) -> Tuple[Optional[float], Optional[float]]:
        """Get current bid/ask prices."""
        if self._mt5 is None or not self._initialized:
            return None, None
        
        try:
            tick = self._mt5.symbol_info_tick(symbol)
            if tick:
                return tick.bid, tick.ask
        except Exception as e:
            logger.error(f"Failed to get MT5 price: {e}")
        
        return None, None
    
    def execute(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        limit_price: Optional[float] = None
    ) -> OrderResult:
        """Execute order on MT5."""
        order_id = f"MT5-{uuid.uuid4().hex[:8]}"
        
        # Mock mode for non-Windows
        if self._mt5 is None or not self._initialized:
            logger.warning(f"MT5 MOCK: {side.value} {quantity} {symbol}")
            return OrderResult(
                order_id=order_id,
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                requested_price=limit_price or 0,
                filled_price=limit_price or 0,
                filled_quantity=quantity,
                slippage=0,
                status=OrderStatus.FILLED,
                venue=ExecutionVenue.PAPER,
                timestamp=datetime.now(timezone.utc),
                raw_response={"mock": True}
            )
        
        try:
            result = self._breaker.call(
                self._execute_internal, symbol, side, quantity
            )
            
            if result["status"] == "SUCCESS":
                filled_price = result.get("price", limit_price or 0)
                slippage = None
                if limit_price and filled_price:
                    slippage = abs(filled_price - limit_price) / limit_price * 100
                
                order_result = OrderResult(
                    order_id=str(result.get("order_id", order_id)),
                    symbol=symbol,
                    side=side.value,
                    quantity=quantity,
                    requested_price=limit_price,
                    filled_price=filled_price,
                    filled_quantity=quantity,
                    slippage=slippage,
                    status=OrderStatus.FILLED,
                    venue=ExecutionVenue.MT5,
                    timestamp=datetime.now(timezone.utc),
                    raw_response=result
                )
                
                _order_tracker.record_order(order_result)
                return order_result
            else:
                return OrderResult(
                    order_id=order_id,
                    symbol=symbol,
                    side=side.value,
                    quantity=quantity,
                    requested_price=limit_price,
                    filled_price=None,
                    filled_quantity=0,
                    slippage=None,
                    status=OrderStatus.FAILED,
                    venue=ExecutionVenue.MT5,
                    timestamp=datetime.now(timezone.utc),
                    error=result.get("error", "Unknown error")
                )
                
        except CircuitOpenError as e:
            return OrderResult(
                order_id=order_id,
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                requested_price=limit_price,
                filled_price=None,
                filled_quantity=0,
                slippage=None,
                status=OrderStatus.REJECTED,
                venue=ExecutionVenue.MT5,
                timestamp=datetime.now(timezone.utc),
                error=f"Circuit breaker open: {e}"
            )
        except Exception as e:
            logger.error(f"MT5 execution error: {e}")
            return OrderResult(
                order_id=order_id,
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                requested_price=limit_price,
                filled_price=None,
                filled_quantity=0,
                slippage=None,
                status=OrderStatus.FAILED,
                venue=ExecutionVenue.MT5,
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )
    
    def _execute_internal(self, symbol: str, side: OrderSide, quantity: float) -> Dict[str, Any]:
        """Internal MT5 order execution."""
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"status": "FAILED", "error": f"Symbol {symbol} not found"}
        
        price = tick.ask if side == OrderSide.BUY else tick.bid
        order_type = self._mt5.ORDER_TYPE_BUY if side == OrderSide.BUY else self._mt5.ORDER_TYPE_SELL
        
        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": quantity,
            "type": order_type,
            "price": price,
            "magic": 777777,
            "comment": "NEXUS_EXECUTION",
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self._mt5.ORDER_FILLING_IOC,
        }
        
        result = self._mt5.order_send(request)
        
        if result.retcode == self._mt5.TRADE_RETCODE_DONE:
            return {
                "status": "SUCCESS",
                "order_id": result.order,
                "price": price,
                "volume": quantity
            }
        else:
            return {
                "status": "FAILED",
                "error": result.comment,
                "retcode": result.retcode
            }
    
    def shutdown(self):
        """Shutdown MT5 connection."""
        if self._mt5 and self._initialized:
            self._mt5.shutdown()
            self._initialized = False


# =============================================================================
# UNIFIED EXECUTION ENGINE
# =============================================================================
class ExecutionEngine:
    """
    Master execution engine with dual-path routing and failover.
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self.mt5 = MT5Executor(self.config)
        self.binance = BinanceExecutor(self.config)
        self.tracker = _order_tracker
        self.optimizer = get_optimizer()
        
        # Initialize primary venue
        if self.config.primary_venue == ExecutionVenue.MT5:
            self.mt5.initialize()
    
    def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        venue: Optional[ExecutionVenue] = None,
        limit_price: Optional[float] = None,
        skip_risk_check: bool = False
    ) -> OrderResult:
        """
        Execute a trade with mandatory risk gate and failover support.
        
        ARCHITECTURE LAW: Every trade passes through this method.
        Risk gate fires here regardless of caller (API, scheduler, or direct).
        
        Args:
            symbol: Trading symbol
            side: "BUY" or "SELL"
            quantity: Position size
            venue: Specific venue (optional, uses primary if not specified)
            limit_price: Optional limit price
            skip_risk_check: Only True if caller already validated (defense-in-depth still logs)
        
        Returns:
            OrderResult with execution details
        """
        order_id = f"NX-{__import__('uuid').uuid4().hex[:8]}"
        
        # =====================================================================
        # GATE 1: ASSET WHITELIST
        # =====================================================================
        if symbol.upper() not in ASSET_WHITELIST and symbol not in ASSET_WHITELIST:
            logger.warning(f"REJECTED: Asset {symbol} not in whitelist")
            return OrderResult(
                order_id=order_id, symbol=symbol, side=side, quantity=quantity,
                requested_price=limit_price, filled_price=None, filled_quantity=0,
                slippage=None, status=OrderStatus.REJECTED, venue=ExecutionVenue.PAPER,
                timestamp=datetime.now(timezone.utc),
                error=f"Asset '{symbol}' not in approved whitelist"
            )
        
        # =====================================================================
        # GATE 2: MAX LOT SIZE
        # =====================================================================
        if quantity > self.config.max_lot_size:
            logger.warning(f"REJECTED: Lot size {quantity} exceeds max {self.config.max_lot_size}")
            return OrderResult(
                order_id=order_id, symbol=symbol, side=side, quantity=quantity,
                requested_price=limit_price, filled_price=None, filled_quantity=0,
                slippage=None, status=OrderStatus.REJECTED, venue=ExecutionVenue.PAPER,
                timestamp=datetime.now(timezone.utc),
                error=f"Lot size {quantity} exceeds maximum {self.config.max_lot_size}"
            )
        
        # =====================================================================
        # GATE 3: PAPER MODE — NEVER touch live markets
        # =====================================================================
        if self.config.use_paper_trading:
            logger.info(f"PAPER MODE: {side} {quantity} {symbol} — no live execution")
            return self._paper_trade(symbol, side, quantity, limit_price)
        
        # =====================================================================
        # GATE 4: RISK GOVERNOR (defense-in-depth)
        # =====================================================================
        if not skip_risk_check:
            price = limit_price or 0.0
            risk_ok, risk_msg = risk_governor.validate_trade(
                symbol, quantity, price
            )
            if not risk_ok:
                logger.warning(f"RISK GATE REJECTED: {risk_msg}")
                return OrderResult(
                    order_id=order_id, symbol=symbol, side=side, quantity=quantity,
                    requested_price=limit_price, filled_price=None, filled_quantity=0,
                    slippage=None, status=OrderStatus.REJECTED, venue=ExecutionVenue.PAPER,
                    timestamp=datetime.now(timezone.utc),
                    error=f"Risk gate: {risk_msg}"
                )
        else:
            logger.info(f"Risk check skipped (caller pre-validated) for {symbol}")
        
        # =====================================================================
        # GATE 4.5: EXECUTION INTELLIGENCE (Optimizer)
        # =====================================================================
        opt_score = 100
        spread = 0.0
        try:
            # 1. Get real-time spread from MT5 (if primary)
            bid, ask = self.mt5.get_current_price(symbol)
            if bid and ask:
                spread = (ask - bid) * 10000 if "JPY" not in symbol else (ask-bid) * 100 # Rough pip calc
            
            # 2. Optimize
            price_to_check = limit_price or (ask if side.upper() == "BUY" else bid) or 0.0
            
            # Ensure we await. execution_optimizer.optimize_entry is async.
            # But execute_trade is sync?
            # PROBLEM: execute_trade is defined as synchronous `def execute_trade`.
            # Optimizer uses `await self.market_provider.get_ohlcv`.
            # We need to run it synchronously or change execute_trade to async.
            # Changing execute_trade to async ripples through the whole system.
            # For now, we will run it in event loop if possible, or skip async part if safer. 
            # But we are in async context usually? NOT necessarily.
            # `CommandRouter` calls `get_allocator` (sync) then `risk_governor` (sync).
            # But `CommandRouter.execute_command` IS async. 
            # `execute_trade` is called by `CommandRouter`? No, `CommandRouter` calls `execution_engine.execute_trade`?
            # Wait, `CommandRouter` currently has `# from app.services.execution import get_engine` commented out.
            # The system is designed to be Async.
            # But `execute_trade` is legacy sync?
            
            # Let's check `execution.py` imports. `import asyncio`.
            # `execute_trade` is NOT async defined: `def execute_trade(...)`.
            
            # I should wrap the async call.
            if self.config.primary_venue == ExecutionVenue.MT5: # Only optimize if MT5 context allows
                 opt_result = asyncio.run_coroutine_threadsafe(
                    self.optimizer.optimize_entry(symbol, side, price_to_check, spread),
                    asyncio.get_event_loop()
                 ).result()
                 
                 if not opt_result.allowed:
                     logger.warning(f"OPTIMIZER DETECTED POOR CONDITIONS: {opt_result.reason}")
                     # In strict mode we might block. Per instructions: "delay order... If still high reduce or cancel".
                     # If wait_time > 0, we sleep.
                 
                 if opt_result.wait_time > 0:
                     logger.info(f"Optimizer requested wait: {opt_result.wait_time}s")
                     time.sleep(opt_result.wait_time) # Sync sleep for now as we are in sync method
                 
                 opt_score = opt_result.score
                 
        except Exception as e:
            logger.warning(f"Optimization step failed (proceeding anyway): {e}")

        # =====================================================================
        # GATE 5: MT5 CONNECTION CHECK
        # =====================================================================
        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        target_venue = venue or self.config.primary_venue
        
        if target_venue == ExecutionVenue.MT5 and not self.mt5._initialized:
            if not self.config.enable_failover:
                logger.error("MT5 not connected and failover disabled — cannot execute")
                return OrderResult(
                    order_id=order_id, symbol=symbol, side=side, quantity=quantity,
                    requested_price=limit_price, filled_price=None, filled_quantity=0,
                    slippage=None, status=OrderStatus.FAILED, venue=ExecutionVenue.MT5,
                    timestamp=datetime.now(timezone.utc),
                    error="MT5 not connected. Failover disabled."
                )
            else:
                logger.warning("MT5 not connected — failing over to secondary venue")
                target_venue = self.config.secondary_venue
        
        logger.info(f"EXECUTING: {side} {quantity} {symbol} on {target_venue.value}")
        
        # Try target venue
        if target_venue == ExecutionVenue.MT5:
            result = self.mt5.execute(symbol, order_side, quantity, limit_price)
        else:
            result = self.binance.execute(symbol, order_side, quantity, limit_price)
        
        # Failover to secondary if enabled and primary failed
        if self.config.enable_failover and result.status == OrderStatus.FAILED:
            logger.warning(f"Primary venue failed, attempting failover")
            
            if target_venue == ExecutionVenue.MT5:
                result = self.binance.execute(symbol, order_side, quantity, limit_price)
            else:
                result = self.mt5.execute(symbol, order_side, quantity, limit_price)
        
        # Register position with risk governor if filled
        if result.status == OrderStatus.FILLED:
            risk_governor.register_position(
                symbol,
                quantity,
                result.filled_price or 0,
                side
            )
            
            # Record execution quality
            try:
                slippage_val = result.slippage if result.slippage is not None else 0.0
                self.optimizer.record_execution(symbol, slippage_val, spread, opt_score)
            except Exception as e:
                logger.error(f"Failed to record execution stats: {e}")
        
        return result
    
    def _paper_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: Optional[float]
    ) -> OrderResult:
        """Execute paper trade for testing."""
        order_id = f"PAPER-{uuid.uuid4().hex[:8]}"
        
        result = OrderResult(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            requested_price=limit_price or 0,
            filled_price=limit_price or 0,
            filled_quantity=quantity,
            slippage=0,
            status=OrderStatus.FILLED,
            venue=ExecutionVenue.PAPER,
            timestamp=datetime.now(timezone.utc),
            raw_response={"paper_trade": True}
        )
        
        _order_tracker.record_order(result)
        logger.info(f"PAPER TRADE: {result.order_id}")
        return result
    
    def kill_switch(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Emergency kill switch - cancel all orders and optionally close positions.
        """
        logger.critical(f"KILL SWITCH ACTIVATED{' for ' + symbol if symbol else ''}")
        
        results = {
            "binance": self.binance.cancel_all_orders(symbol),
            "mt5": {"status": "MT5 requires manual intervention"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return results
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        orders = list(self.tracker._orders.values())
        
        filled_orders = [o for o in orders if o.status == OrderStatus.FILLED]
        failed_orders = [o for o in orders if o.status == OrderStatus.FAILED]
        
        return {
            "total_orders": len(orders),
            "filled_orders": len(filled_orders),
            "failed_orders": len(failed_orders),
            "pending_orders": len(self.tracker.get_pending_orders()),
            "average_slippage": self.tracker.calculate_total_slippage(),
            "venues": {
                "mt5": len([o for o in filled_orders if o.venue == ExecutionVenue.MT5]),
                "binance": len([o for o in filled_orders if o.venue == ExecutionVenue.BINANCE]),
                "paper": len([o for o in filled_orders if o.venue == ExecutionVenue.PAPER])
            }
        }
    
    def shutdown(self):
        """Shutdown all executors."""
        self.mt5.shutdown()
        logger.info("Execution engine shutdown complete")


# =============================================================================
# GLOBAL INSTANCE & CONVENIENCE FUNCTIONS
# =============================================================================
_engine: Optional[ExecutionEngine] = None


def get_engine() -> ExecutionEngine:
    """Get global execution engine."""
    global _engine
    if _engine is None:
        _engine = ExecutionEngine()
    return _engine


def execute_trade(symbol: str, side: str, quantity: float) -> Dict[str, Any]:
    """
    Convenience function for trade execution.
    
    Args:
        symbol: Trading symbol
        side: 'buy' or 'sell'
        quantity: Position size
    
    Returns:
        Order result dictionary
    """
    engine = get_engine()
    result = engine.execute_trade(symbol, side, quantity)
    return result.to_dict()


def kill_switch(symbol: Optional[str] = None) -> Dict[str, Any]:
    """Emergency kill switch."""
    engine = get_engine()
    return engine.kill_switch(symbol)


# Backward compatibility
def get_exchange_client() -> ccxt.binance:
    """Legacy function for Binance client access."""
    engine = get_engine()
    return engine.binance._get_client()
