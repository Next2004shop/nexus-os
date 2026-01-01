"""
NEXUS Live Data Service - Real-Time Market Data Ingestion
==========================================================

Backend-only live data connectors for:
- Crypto: Binance WebSocket + REST
- FX: OANDA / MetaTrader feed
- Stocks: Polygon.io

ABSOLUTE LAW: No API keys on frontend - EVER.
All data normalized before frontend delivery.
"""

import logging
import asyncio
import json
import aiohttp
import websockets
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from abc import ABC, abstractmethod
import hmac
import hashlib
import time

logger = logging.getLogger("nexus.live_data")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class DataSource(Enum):
    """Supported data sources."""
    BINANCE = "binance"
    OANDA = "oanda"
    POLYGON = "polygon"
    METATRADER = "metatrader"


@dataclass
class LiveTick:
    """Normalized live market tick."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime
    source: DataSource
    
    def to_frontend(self) -> Dict[str, Any]:
        """Safe data for frontend - NO SECRETS."""
        return {
            "symbol": self.symbol,
            "price": self.last,
            "bid": self.bid,
            "ask": self.ask,
            "spread": round((self.ask - self.bid) / self.bid * 10000, 2),  # pips
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class LiveCandle:
    """Normalized OHLCV candle."""
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    source: DataSource


# =============================================================================
# BASE CONNECTOR
# =============================================================================

class BaseConnector(ABC):
    """Abstract base for live data connectors."""
    
    def __init__(self, source: DataSource):
        self.source = source
        self.is_connected = False
        self.last_heartbeat = None
        self.reconnect_count = 0
        self.max_reconnects = 10
        self.callbacks: List[Callable] = []
    
    @abstractmethod
    async def connect(self):
        """Establish connection."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection."""
        pass
    
    @abstractmethod
    async def subscribe(self, symbols: List[str]):
        """Subscribe to symbols."""
        pass
    
    def add_callback(self, callback: Callable):
        """Add tick callback."""
        self.callbacks.append(callback)
    
    async def _notify_callbacks(self, tick: LiveTick):
        """Notify all callbacks of new tick."""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(tick)
                else:
                    callback(tick)
            except Exception as e:
                logger.error(f"Callback error: {e}")


# =============================================================================
# BINANCE CONNECTOR (CRYPTO)
# =============================================================================

class BinanceConnector(BaseConnector):
    """
    Binance WebSocket connector for real-time crypto data.
    
    NO API KEYS REQUIRED for public market data.
    API keys stored in Secret Manager for trading only.
    """
    
    WS_URL = "wss://stream.binance.com:9443/ws"
    REST_URL = "https://api.binance.com/api/v3"
    
    def __init__(self):
        super().__init__(DataSource.BINANCE)
        self._ws = None
        self._subscriptions: List[str] = []
        self._running = False
    
    async def connect(self):
        """Connect to Binance WebSocket."""
        try:
            self._ws = await websockets.connect(self.WS_URL)
            self.is_connected = True
            self.last_heartbeat = datetime.now(timezone.utc)
            self._running = True
            logger.info("Binance WebSocket connected")
            
            # Start message handler
            asyncio.create_task(self._message_handler())
            
        except Exception as e:
            logger.error(f"Binance connection failed: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from Binance."""
        self._running = False
        if self._ws:
            await self._ws.close()
        self.is_connected = False
        logger.info("Binance WebSocket disconnected")
    
    async def subscribe(self, symbols: List[str]):
        """Subscribe to symbols (e.g., ['BTCUSDT', 'ETHUSDT'])."""
        if not self._ws:
            raise ConnectionError("WebSocket not connected")
        
        streams = [f"{s.lower()}@ticker" for s in symbols]
        
        msg = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": int(time.time())
        }
        
        await self._ws.send(json.dumps(msg))
        self._subscriptions.extend(symbols)
        logger.info(f"Subscribed to: {symbols}")
    
    async def _message_handler(self):
        """Handle incoming WebSocket messages."""
        while self._running:
            try:
                msg = await asyncio.wait_for(self._ws.recv(), timeout=30)
                data = json.loads(msg)
                
                if "e" in data and data["e"] == "24hrTicker":
                    tick = LiveTick(
                        symbol=data["s"],
                        bid=float(data["b"]),
                        ask=float(data["a"]),
                        last=float(data["c"]),
                        volume=float(data["v"]),
                        timestamp=datetime.now(timezone.utc),
                        source=self.source
                    )
                    await self._notify_callbacks(tick)
                    self.last_heartbeat = datetime.now(timezone.utc)
                    
            except asyncio.TimeoutError:
                # Send ping
                await self._ws.ping()
            except websockets.ConnectionClosed:
                logger.warning("Binance connection closed, reconnecting...")
                await self._reconnect()
            except Exception as e:
                logger.error(f"Binance message error: {e}")
    
    async def _reconnect(self):
        """Auto-reconnect on failure."""
        if self.reconnect_count >= self.max_reconnects:
            logger.critical("Max reconnects exceeded, halting Binance feed")
            self._running = False
            return
        
        self.reconnect_count += 1
        await asyncio.sleep(2 ** self.reconnect_count)  # Exponential backoff
        
        try:
            await self.connect()
            if self._subscriptions:
                await self.subscribe(self._subscriptions)
            self.reconnect_count = 0
        except Exception as e:
            logger.error(f"Reconnect failed: {e}")
    
    async def get_ticker(self, symbol: str) -> Optional[LiveTick]:
        """REST fallback for single ticker."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.REST_URL}/ticker/24hr?symbol={symbol}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return LiveTick(
                            symbol=data["symbol"],
                            bid=float(data["bidPrice"]),
                            ask=float(data["askPrice"]),
                            last=float(data["lastPrice"]),
                            volume=float(data["volume"]),
                            timestamp=datetime.now(timezone.utc),
                            source=self.source
                        )
        except Exception as e:
            logger.error(f"REST ticker error: {e}")
        return None


# =============================================================================
# POLYGON CONNECTOR (STOCKS)
# =============================================================================

class PolygonConnector(BaseConnector):
    """
    Polygon.io connector for real-time stock data.
    
    API key stored in Secret Manager - fetched at runtime.
    """
    
    WS_URL = "wss://socket.polygon.io/stocks"
    REST_URL = "https://api.polygon.io/v2"
    
    def __init__(self):
        super().__init__(DataSource.POLYGON)
        self._ws = None
        self._api_key = None
        self._subscriptions: List[str] = []
        self._running = False
    
    async def _get_api_key(self) -> str:
        """Fetch API key from Secret Manager."""
        if self._api_key:
            return self._api_key
        
        try:
            from app.services.vault import get_secret
            self._api_key = get_secret("POLYGON_API_KEY")
            return self._api_key
        except Exception as e:
            logger.error(f"Failed to get Polygon API key: {e}")
            raise
    
    async def connect(self):
        """Connect to Polygon WebSocket."""
        try:
            api_key = await asyncio.to_thread(self._get_api_key_sync)
            self._ws = await websockets.connect(self.WS_URL)
            
            # Authenticate
            auth_msg = {"action": "auth", "params": api_key}
            await self._ws.send(json.dumps(auth_msg))
            
            self.is_connected = True
            self.last_heartbeat = datetime.now(timezone.utc)
            self._running = True
            
            logger.info("Polygon WebSocket connected")
            asyncio.create_task(self._message_handler())
            
        except Exception as e:
            logger.error(f"Polygon connection failed: {e}")
            self.is_connected = False
            raise
    
    def _get_api_key_sync(self) -> str:
        """Synchronous API key fetch."""
        from app.services.vault import get_secret
        return get_secret("POLYGON_API_KEY")
    
    async def disconnect(self):
        """Disconnect from Polygon."""
        self._running = False
        if self._ws:
            await self._ws.close()
        self.is_connected = False
    
    async def subscribe(self, symbols: List[str]):
        """Subscribe to stock symbols."""
        if not self._ws:
            raise ConnectionError("WebSocket not connected")
        
        # Polygon uses T.AAPL format for trades
        streams = [f"T.{s}" for s in symbols]
        
        msg = {"action": "subscribe", "params": ",".join(streams)}
        await self._ws.send(json.dumps(msg))
        self._subscriptions.extend(symbols)
        logger.info(f"Polygon subscribed to: {symbols}")
    
    async def _message_handler(self):
        """Handle incoming messages."""
        while self._running:
            try:
                msg = await asyncio.wait_for(self._ws.recv(), timeout=30)
                data = json.loads(msg)
                
                for item in data if isinstance(data, list) else [data]:
                    if item.get("ev") == "T":  # Trade event
                        tick = LiveTick(
                            symbol=item["sym"],
                            bid=float(item["p"]),
                            ask=float(item["p"]),
                            last=float(item["p"]),
                            volume=float(item["s"]),
                            timestamp=datetime.fromtimestamp(item["t"] / 1000, tz=timezone.utc),
                            source=self.source
                        )
                        await self._notify_callbacks(tick)
                        
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.error(f"Polygon message error: {e}")


# =============================================================================
# METATRADER BRIDGE CONNECTOR
# =============================================================================

class MetaTraderConnector(BaseConnector):
    """
    MetaTrader data connector via VM bridge.
    
    Connects to local bridge running on Google Cloud VM.
    All credentials stored in Secret Manager.
    """
    
    def __init__(self, bridge_url: str = "http://localhost:5000"):
        super().__init__(DataSource.METATRADER)
        self.bridge_url = bridge_url
        self._session = None
        self._polling_task = None
        self._running = False
    
    async def connect(self):
        """Connect to MT bridge."""
        try:
            self._session = aiohttp.ClientSession()
            
            # Health check
            async with self._session.get(f"{self.bridge_url}/health") as resp:
                if resp.status == 200:
                    self.is_connected = True
                    self._running = True
                    logger.info("MetaTrader bridge connected")
                    
                    # Start polling
                    self._polling_task = asyncio.create_task(self._poll_quotes())
                else:
                    raise ConnectionError(f"Bridge health check failed: {resp.status}")
                    
        except Exception as e:
            logger.error(f"MT bridge connection failed: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from bridge."""
        self._running = False
        if self._polling_task:
            self._polling_task.cancel()
        if self._session:
            await self._session.close()
        self.is_connected = False
    
    async def subscribe(self, symbols: List[str]):
        """Subscribe to MT symbols."""
        try:
            async with self._session.post(
                f"{self.bridge_url}/subscribe",
                json={"symbols": symbols}
            ) as resp:
                if resp.status == 200:
                    logger.info(f"MT subscribed to: {symbols}")
                else:
                    logger.error(f"MT subscribe failed: {resp.status}")
        except Exception as e:
            logger.error(f"MT subscribe error: {e}")
    
    async def _poll_quotes(self):
        """Poll bridge for quotes."""
        while self._running:
            try:
                async with self._session.get(f"{self.bridge_url}/quotes") as resp:
                    if resp.status == 200:
                        quotes = await resp.json()
                        for q in quotes.get("quotes", []):
                            tick = LiveTick(
                                symbol=q["symbol"],
                                bid=float(q["bid"]),
                                ask=float(q["ask"]),
                                last=float(q["bid"] + q["ask"]) / 2,
                                volume=float(q.get("volume", 0)),
                                timestamp=datetime.now(timezone.utc),
                                source=self.source
                            )
                            await self._notify_callbacks(tick)
                            
            except Exception as e:
                logger.error(f"MT poll error: {e}")
            
            await asyncio.sleep(0.5)  # 500ms polling


# =============================================================================
# LIVE DATA MANAGER
# =============================================================================

class LiveDataManager:
    """
    Central manager for all live data feeds.
    
    Aggregates data from multiple sources.
    Ensures data integrity before trading.
    """
    
    def __init__(self):
        self.connectors: Dict[DataSource, BaseConnector] = {}
        self.ticks: Dict[str, LiveTick] = {}  # Latest tick per symbol
        self.is_healthy = False
        self.callbacks: List[Callable] = []
        
        # Data integrity tracking
        self.last_update: Dict[str, datetime] = {}
        self.stale_threshold_seconds = 30
    
    def add_connector(self, connector: BaseConnector):
        """Add a data connector."""
        self.connectors[connector.source] = connector
        connector.add_callback(self._on_tick)
    
    async def start(self):
        """Start all connectors."""
        for source, connector in self.connectors.items():
            try:
                await connector.connect()
                logger.info(f"Started {source.value} connector")
            except Exception as e:
                logger.error(f"Failed to start {source.value}: {e}")
        
        self.is_healthy = any(c.is_connected for c in self.connectors.values())
    
    async def stop(self):
        """Stop all connectors."""
        for connector in self.connectors.values():
            await connector.disconnect()
        self.is_healthy = False
    
    async def _on_tick(self, tick: LiveTick):
        """Handle incoming tick."""
        self.ticks[tick.symbol] = tick
        self.last_update[tick.symbol] = datetime.now(timezone.utc)
        
        # Notify subscribers
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(tick)
                else:
                    callback(tick)
            except Exception as e:
                logger.error(f"Tick callback error: {e}")
    
    def get_tick(self, symbol: str) -> Optional[LiveTick]:
        """Get latest tick for symbol."""
        return self.ticks.get(symbol)
    
    def get_frontend_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get safe data for frontend - NO SECRETS."""
        tick = self.ticks.get(symbol)
        if tick:
            return tick.to_frontend()
        return None
    
    def is_data_fresh(self, symbol: str) -> bool:
        """Check if data is fresh enough for trading."""
        last = self.last_update.get(symbol)
        if not last:
            return False
        
        age = (datetime.now(timezone.utc) - last).total_seconds()
        return age < self.stale_threshold_seconds
    
    def check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity for trading decisions."""
        now = datetime.now(timezone.utc)
        stale_symbols = []
        fresh_symbols = []
        
        for symbol, last_update in self.last_update.items():
            age = (now - last_update).total_seconds()
            if age > self.stale_threshold_seconds:
                stale_symbols.append(symbol)
            else:
                fresh_symbols.append(symbol)
        
        healthy_connectors = sum(1 for c in self.connectors.values() if c.is_connected)
        
        return {
            "healthy": len(stale_symbols) == 0 and healthy_connectors > 0,
            "connectors_online": healthy_connectors,
            "connectors_total": len(self.connectors),
            "fresh_symbols": len(fresh_symbols),
            "stale_symbols": stale_symbols,
            "trading_allowed": len(stale_symbols) == 0 and healthy_connectors > 0
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_live_data: Optional[LiveDataManager] = None


def get_live_data() -> LiveDataManager:
    """Get or create live data manager."""
    global _live_data
    if _live_data is None:
        _live_data = LiveDataManager()
    return _live_data


async def initialize_live_data():
    """Initialize all live data feeds."""
    manager = get_live_data()
    
    # Add connectors
    manager.add_connector(BinanceConnector())
    manager.add_connector(MetaTraderConnector())
    
    # Polygon requires API key - add only if available
    try:
        from app.services.vault import get_secret
        if get_secret("POLYGON_API_KEY"):
            manager.add_connector(PolygonConnector())
    except Exception:
        logger.warning("Polygon connector not available")
    
    await manager.start()
    return manager
