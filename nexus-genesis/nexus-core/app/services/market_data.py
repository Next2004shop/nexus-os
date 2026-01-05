"""
NEXUS Market Data Module - Polygon.io Integration
==================================================

Unified market data feed providing:
1. Historical OHLCV data
2. Real-time WebSocket streaming
3. Normalized market schema
4. Multiple asset class support

All data normalized to unified schema for strategy consumption.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import numpy as np
import pandas as pd

from .vault import get_secret

logger = logging.getLogger("nexus.market_data")


class AssetClass(Enum):
    """Supported asset classes."""
    FOREX = "forex"
    CRYPTO = "crypto"
    STOCKS = "stocks"
    INDICES = "indices"


class Timeframe(Enum):
    """Supported timeframes."""
    M1 = "1"
    M5 = "5"
    M15 = "15"
    M30 = "30"
    H1 = "60"
    H4 = "240"
    D1 = "D"
    W1 = "W"


@dataclass
class MarketBar:
    """Unified OHLCV bar structure."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    trades: Optional[int] = None
    spread: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "vwap": self.vwap,
            "trades": self.trades,
            "spread": self.spread
        }


@dataclass
class MarketTick:
    """Real-time tick data."""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: float
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2


@dataclass
class MarketDepth:
    """Order book depth data."""
    symbol: str
    timestamp: datetime
    bids: List[Dict[str, float]]  # [{"price": 100, "size": 10}, ...]
    asks: List[Dict[str, float]]
    
    @property
    def best_bid(self) -> float:
        return self.bids[0]["price"] if self.bids else 0
    
    @property
    def best_ask(self) -> float:
        return self.asks[0]["price"] if self.asks else 0
    
    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid


# =============================================================================
# POLYGON.IO CLIENT
# =============================================================================
class PolygonClient:
    """
    Polygon.io REST API client for market data.
    """
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def api_key(self) -> str:
        """Lazy load API key from vault."""
        if self._api_key is None:
            try:
                self._api_key = get_secret("POLYGON_API_KEY")
            except Exception as e:
                logger.error(f"Failed to get Polygon API key: {e}")
                raise ValueError("Polygon API key not available")
        return self._api_key
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request."""
        session = await self._get_session()
        
        params = params or {}
        params["apiKey"] = self.api_key
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Polygon API error {response.status}: {error_text}")
                    raise Exception(f"API error: {response.status}")
                
                return await response.json()
        except Exception as e:
            logger.error(f"Polygon request failed: {e}")
            raise
    
    # =========================================================================
    # FOREX
    # =========================================================================
    async def get_forex_aggregates(
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        from_date: str,
        to_date: str,
        limit: int = 5000
    ) -> List[MarketBar]:
        """
        Get forex OHLCV data.
        
        Args:
            ticker: Currency pair (e.g., "C:EURUSD")
            multiplier: Size of timespan multiplier
            timespan: minute, hour, day, week, month
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            limit: Max results
        
        Returns:
            List of MarketBar objects
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        
        data = await self._request(endpoint, {"limit": limit, "sort": "asc"})
        
        bars = []
        for result in data.get("results", []):
            bars.append(MarketBar(
                symbol=ticker.replace("C:", ""),
                timestamp=datetime.fromtimestamp(result["t"] / 1000, tz=timezone.utc),
                open=result["o"],
                high=result["h"],
                low=result["l"],
                close=result["c"],
                volume=result.get("v", 0),
                vwap=result.get("vw"),
                trades=result.get("n")
            ))
        
        return bars
    
    async def get_forex_quote(self, from_currency: str, to_currency: str) -> MarketTick:
        """Get real-time forex quote."""
        endpoint = f"/v1/last_quote/currencies/{from_currency}/{to_currency}"
        
        data = await self._request(endpoint)
        
        last = data.get("last", {})
        return MarketTick(
            symbol=f"{from_currency}{to_currency}",
            timestamp=datetime.fromtimestamp(last.get("timestamp", 0) / 1000, tz=timezone.utc),
            bid=last.get("bid", 0),
            ask=last.get("ask", 0),
            last=(last.get("bid", 0) + last.get("ask", 0)) / 2,
            volume=0
        )
    
    # =========================================================================
    # CRYPTO
    # =========================================================================
    async def get_crypto_aggregates(
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        from_date: str,
        to_date: str,
        limit: int = 5000
    ) -> List[MarketBar]:
        """
        Get crypto OHLCV data.
        
        Args:
            ticker: Crypto pair (e.g., "X:BTCUSD")
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        
        data = await self._request(endpoint, {"limit": limit, "sort": "asc"})
        
        bars = []
        for result in data.get("results", []):
            bars.append(MarketBar(
                symbol=ticker.replace("X:", ""),
                timestamp=datetime.fromtimestamp(result["t"] / 1000, tz=timezone.utc),
                open=result["o"],
                high=result["h"],
                low=result["l"],
                close=result["c"],
                volume=result.get("v", 0),
                vwap=result.get("vw"),
                trades=result.get("n")
            ))
        
        return bars
    
    # =========================================================================
    # STOCKS
    # =========================================================================
    async def get_stock_aggregates(
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        from_date: str,
        to_date: str,
        limit: int = 5000
    ) -> List[MarketBar]:
        """Get stock OHLCV data."""
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        
        data = await self._request(endpoint, {"limit": limit, "sort": "asc"})
        
        bars = []
        for result in data.get("results", []):
            bars.append(MarketBar(
                symbol=ticker,
                timestamp=datetime.fromtimestamp(result["t"] / 1000, tz=timezone.utc),
                open=result["o"],
                high=result["h"],
                low=result["l"],
                close=result["c"],
                volume=result.get("v", 0),
                vwap=result.get("vw"),
                trades=result.get("n")
            ))
        
        return bars


# =============================================================================
# DATA NORMALIZER
# =============================================================================
class DataNormalizer:
    """
    Normalizes market data from various sources into unified format.
    """
    
    @staticmethod
    def bars_to_dataframe(bars: List[MarketBar]) -> pd.DataFrame:
        """Convert list of MarketBar to pandas DataFrame."""
        if not bars:
            return pd.DataFrame()
        
        data = [bar.to_dict() for bar in bars]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df
    
    @staticmethod
    def normalize_symbol(symbol: str, asset_class: AssetClass) -> str:
        """
        Normalize symbol format.
        
        Converts various formats to standard:
        - EURUSD (forex)
        - BTCUSD (crypto)
        - AAPL (stocks)
        """
        symbol = symbol.upper().replace("/", "").replace("-", "")
        
        # Remove Polygon prefixes
        if symbol.startswith("C:"):
            symbol = symbol[2:]
        elif symbol.startswith("X:"):
            symbol = symbol[2:]
        
        return symbol
    
    @staticmethod
    def polygon_symbol(symbol: str, asset_class: AssetClass) -> str:
        """Convert standard symbol to Polygon format."""
        symbol = symbol.upper().replace("/", "")
        
        if asset_class == AssetClass.FOREX:
            return f"C:{symbol}"
        elif asset_class == AssetClass.CRYPTO:
            return f"X:{symbol}"
        
        return symbol
    
    @staticmethod
    def resample_bars(df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
        """
        Resample OHLCV data to different timeframe.
        
        Args:
            df: DataFrame with OHLCV columns
            target_timeframe: pandas-compatible timeframe (e.g., '15T', '1H', '1D')
        
        Returns:
            Resampled DataFrame
        """
        if df.empty:
            return df
        
        resampled = df.resample(target_timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return resampled


# =============================================================================
# UNIFIED MARKET DATA PROVIDER
# =============================================================================
class MarketDataProvider:
    """
    Unified interface for market data across all sources.
    """
    
    def __init__(self):
        self.polygon = PolygonClient()
        self.normalizer = DataNormalizer()
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)
    
    def _get_cache_key(self, symbol: str, timeframe: str) -> str:
        """Generate cache key."""
        return f"{symbol}_{timeframe}"
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache is still valid."""
        if key not in self._cache_expiry:
            return False
        return datetime.now(timezone.utc) < self._cache_expiry[key]
    
    async def get_ohlcv(
        self,
        symbol: str,
        asset_class: AssetClass,
        timeframe: Timeframe = Timeframe.M15,
        bars: int = 100
    ) -> pd.DataFrame:
        """
        Get OHLCV data for symbol.
        
        Args:
            symbol: Trading symbol
            asset_class: Type of asset
            timeframe: Bar timeframe
            bars: Number of bars to fetch
        
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = self._get_cache_key(symbol, timeframe.value)
        
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key].tail(bars)
        
        # Calculate date range
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Estimate from_date based on timeframe
        days_back = {
            Timeframe.M1: 2,
            Timeframe.M5: 5,
            Timeframe.M15: 10,
            Timeframe.M30: 20,
            Timeframe.H1: 30,
            Timeframe.H4: 60,
            Timeframe.D1: 365,
            Timeframe.W1: 730
        }.get(timeframe, 30)
        
        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        # Map timeframe to Polygon parameters
        timespan_map = {
            Timeframe.M1: ("minute", 1),
            Timeframe.M5: ("minute", 5),
            Timeframe.M15: ("minute", 15),
            Timeframe.M30: ("minute", 30),
            Timeframe.H1: ("hour", 1),
            Timeframe.H4: ("hour", 4),
            Timeframe.D1: ("day", 1),
            Timeframe.W1: ("week", 1)
        }
        
        timespan, multiplier = timespan_map.get(timeframe, ("minute", 15))
        
        # Fetch from Polygon
        polygon_symbol = self.normalizer.polygon_symbol(symbol, asset_class)
        
        try:
            if asset_class == AssetClass.FOREX:
                market_bars = await self.polygon.get_forex_aggregates(
                    polygon_symbol, multiplier, timespan, from_date, to_date
                )
            elif asset_class == AssetClass.CRYPTO:
                market_bars = await self.polygon.get_crypto_aggregates(
                    polygon_symbol, multiplier, timespan, from_date, to_date
                )
            else:
                market_bars = await self.polygon.get_stock_aggregates(
                    polygon_symbol, multiplier, timespan, from_date, to_date
                )
            
            df = self.normalizer.bars_to_dataframe(market_bars)
            
            # Cache the result
            self._cache[cache_key] = df
            self._cache_expiry[cache_key] = datetime.now(timezone.utc) + self._cache_ttl
            
            return df.tail(bars)
            
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            
            # Return cached data if available, even if expired
            if cache_key in self._cache:
                logger.warning(f"Returning stale cache for {symbol}")
                return self._cache[cache_key].tail(bars)
            
            return pd.DataFrame()
    
    async def get_current_price(self, symbol: str, asset_class: AssetClass) -> Optional[float]:
        """Get current mid price for symbol."""
        try:
            if asset_class == AssetClass.FOREX:
                # Parse forex pair
                from_curr = symbol[:3]
                to_curr = symbol[3:]
                tick = await self.polygon.get_forex_quote(from_curr, to_curr)
                return tick.mid
            else:
                # For other assets, get last bar close
                df = await self.get_ohlcv(symbol, asset_class, Timeframe.M1, 1)
                if not df.empty:
                    return float(df['close'].iloc[-1])
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
        
        return None
    
    async def close(self):
        """Cleanup resources."""
        await self.polygon.close()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================
_provider: Optional[MarketDataProvider] = None


def get_provider() -> MarketDataProvider:
    """Get global market data provider."""
    global _provider
    if _provider is None:
        _provider = MarketDataProvider()
    return _provider


async def fetch_ohlcv(
    symbol: str,
    asset_class: str = "forex",
    timeframe: str = "M15",
    bars: int = 100
) -> pd.DataFrame:
    """
    Quick convenience function to fetch OHLCV data.
    
    Args:
        symbol: Trading symbol (e.g., "EURUSD", "BTCUSD")
        asset_class: "forex", "crypto", or "stocks"
        timeframe: "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"
        bars: Number of bars
    
    Returns:
        DataFrame with OHLCV data
    """
    provider = get_provider()
    
    asset_map = {
        "forex": AssetClass.FOREX,
        "crypto": AssetClass.CRYPTO,
        "stocks": AssetClass.STOCKS
    }
    
    tf_map = {
        "M1": Timeframe.M1,
        "M5": Timeframe.M5,
        "M15": Timeframe.M15,
        "M30": Timeframe.M30,
        "H1": Timeframe.H1,
        "H4": Timeframe.H4,
        "D1": Timeframe.D1,
        "W1": Timeframe.W1
    }
    
    return await provider.get_ohlcv(
        symbol,
        asset_map.get(asset_class.lower(), AssetClass.FOREX),
        tf_map.get(timeframe.upper(), Timeframe.M15),
        bars
    )
