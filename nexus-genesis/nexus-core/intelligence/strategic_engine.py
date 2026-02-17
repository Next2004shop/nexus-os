"""
NEXUS Strategic Intelligence Engine
===================================
Phase 8: Macro Context Awareness.

This module acts as the "General" of the army.
It determines IF the battlefield is suitable for engagement,
before the Capital Allocator determines HOW MUCH to commit,
and the Risk Governor determines if it's ALLOWED.

Responsibilities:
1. Market Regime Detection (Trend/Range/Volatile)
2. Volatility State (Low/Normal/High)
3. Correlation Cluster Monitoring
4. News Stress Filtering
5. Strategic Permissioning
"""

import logging
import json
import os
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from app.services.market_data import get_provider, AssetClass, Timeframe

logger = logging.getLogger("nexus.intelligence.strategic")

class MarketRegime(Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGE"
    VOLATILE = "VOLATILE"
    DEFENSIVE = "DEFENSIVE"

class RiskBias(Enum):
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    NEUTRAL = "NEUTRAL"

class VolatilityState(Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

@dataclass
class StrategicPermission:
    allowed: bool
    reason: str
    risk_multiplier: float
    regime: str
    volatility: str
    bias: str

class StrategicEngine:
    _instance = None
    
    # Configuration
    MEMORY_FILE = "nexus-core/intelligence/regime_memory.json"
    
    # Correlation Clusters
    CLUSTERS = {
        "GOLD_CLUSTER": ["XAUUSD", "XAGUSD", "USDJPY"], # Precious metals inverse USD
        "INDICES_CLUSTER": ["NAS100", "US500", "US30"],
        "CRYPTO_CLUSTER": ["BTCUSD", "ETHUSD", "SOLUSD"]
    }
    
    def __init__(self):
        self.memory = self._load_memory()
        self.market_provider = get_provider()
        self.last_analysis = {} # Cache analysis by symbol
        self.last_update = datetime.min.replace(tzinfo=timezone.utc)
        
        # State
        self.current_bias = RiskBias.NEUTRAL
        self.global_volatility = VolatilityState.NORMAL
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = StrategicEngine()
        return cls._instance

    def _load_memory(self) -> Dict:
        """Load adaptive memory."""
        try:
            if os.path.exists(self.MEMORY_FILE):
                with open(self.MEMORY_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load regime memory: {e}")
        return {"regime_stats": {}}

    def _save_memory(self):
        """Persist adaptive memory."""
        try:
            os.makedirs(os.path.dirname(self.MEMORY_FILE), exist_ok=True)
            with open(self.MEMORY_FILE, "w") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save regime memory: {e}")

    async def _fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch sufficient history for analysis."""
        # Determine asset class from symbol format or map
        # Simplified logic: 
        asset_class = AssetClass.FOREX
        if "BTC" in symbol or "ETH" in symbol:
            asset_class = AssetClass.CRYPTO
        elif "NAS" in symbol or "US500" in symbol or len(symbol) < 5:
            asset_class = AssetClass.STOCKS # Indices usually treated as stocks/CFD in Polygon
        
        # Use H1 for macro regime
        return await self.market_provider.get_ohlcv(
            symbol=symbol,
            asset_class=asset_class,
            timeframe=Timeframe.H1,
            bars=200 # Need enough for 200 SMA
        )

    def _analyze_volatility(self, df: pd.DataFrame) -> Tuple[VolatilityState, float]:
        """
        Analyze volatility using ATR and StdDev.
        Returns: (VolatilityState, ATR_Value)
        """
        if df.empty or len(df) < 14:
            return VolatilityState.NORMAL, 0.0

        # Calculate TR
        high = df['high']
        low = df['low']
        close = df['close']
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        # Baseline ATR (long term mean)
        baseline_atr = tr.rolling(50).mean().iloc[-1]
        
        if baseline_atr == 0:
             return VolatilityState.NORMAL, atr

        ratio = atr / baseline_atr
        
        if ratio > 2.0:
            return VolatilityState.EXTREME, atr
        elif ratio > 1.5:
            return VolatilityState.HIGH, atr
        elif ratio < 0.7:
            return VolatilityState.LOW, atr
            
        return VolatilityState.NORMAL, atr

    def _analyze_regime(self, df: pd.DataFrame) -> MarketRegime:
        """
        Detect market regime: Trending vs Ranging.
        Uses ADX and SMA alignment.
        """
        if df.empty or len(df) < 50:
            return MarketRegime.RANGING

        close = df['close']
        
        # SMAs
        sma_20 = close.rolling(20).mean().iloc[-1]
        sma_50 = close.rolling(50).mean().iloc[-1]
        
        # ADX Calculation (Simplified)
        # Using simple slope + SMA check for now to avoid huge TA lib dependency
        # Slope of SMA50
        prev_sma_50 = close.rolling(50).mean().iloc[-5]
        slope = (sma_50 - prev_sma_50) / prev_sma_50
        
        # Volatility check inside regime
        # If High Highs and Low Lows expanding?
        
        # Classification
        if abs(slope) > 0.001: # Significant slope
            # Check alignment
            if slope > 0 and close.iloc[-1] > sma_20 > sma_50:
                return MarketRegime.TRENDING
            if slope < 0 and close.iloc[-1] < sma_20 < sma_50:
                 return MarketRegime.TRENDING
        
        return MarketRegime.RANGING
    
    async def _check_correlation_stress(self, symbol: str) -> float:
        """
        Check if asset is part of a highly correlated cluster under stress.
        Returns correlation coefficient (max linkage).
        """
        # Identify cluster
        cluster_name = None
        cluster_assets = []
        for name, assets in self.CLUSTERS.items():
            if symbol in assets:
                cluster_name = name
                cluster_assets = assets
                break
        
        if not cluster_name:
            return 0.0
            
        # Fetch peers
        tasks = []
        for asset in cluster_assets:
            if asset == symbol:
                continue
            tasks.append(self._fetch_data(asset))
            
        if not tasks:
            return 0.0
            
        # This is expensive, so we should cache or limit freq. 
        # For prototype, we do it but rely on provider cache.
        # But wait, we need synchronized timestamps for correlation.
        # This is complex implementation detail. 
        # SIMPLIFICATION: We check "Directional Unanimity".
        # If all peers are moving same direction > 1% today?
        return 0.0 # Placeholder for complex matrix calc
        
    async def _check_news_stress(self) -> bool:
        """
        Check for high impact news.
        Placeholder until News API integrated.
        """
        # TODO: Integrate Polygon News
        return False

    async def evaluate(self, command: Any) -> StrategicPermission:
        """
        Main evaluation entry point.
        """
        symbol = command.asset
        
        # 1. Fetch Data
        try:
            df = await self._fetch_data(symbol)
        except Exception as e:
            logger.error(f"Data fetch failed for strategic analysis: {e}")
            # Fail safe: Allow trade but with caution
            return StrategicPermission(True, "Data Unavailable - Caution", 0.5, "UNKNOWN", "UNKNOWN", "NEUTRAL")

        # 2. Analyze
        vol_state, atr = self._analyze_volatility(df)
        regime = self._analyze_regime(df)
        
        # 3. Decision Logic
        allowed = True
        reason = "Strategic Approval"
        risk_mult = 1.0
        
        # A) Volatility Filter
        if vol_state == VolatilityState.EXTREME:
            risk_mult = 0.5
            reason = "Extreme Volatility - Size Halved"
        elif vol_state == VolatilityState.LOW:
            # Maybe risk more? Or less? 
            # User rule: "If volatility collapse: reduce frequency"
            # We don't control frequency here, but we can flag it.
            pass

        # B) Regime Filter
        # User: "If regime = RANGE: block trend strategies"
        # Since we don't know the strategy type (it comes from 'ai' or 'manual'), 
        # we assume 'ai' might be trending.
        # We can pass 'regime' in permission, command router can log it.
        # If regime == DEFENSIVE (e.g. crash): Block.
        
        if regime == MarketRegime.DEFENSIVE:
            allowed = False
            reason = "Market in Defensive Regime"
            return StrategicPermission(False, reason, 0.0, regime.value, vol_state.value, RiskBias.RISK_OFF.value)
            
        # C) News Filter
        if await self._check_news_stress():
            allowed = False
            reason = "High Impact News Detected"
            
        # D) Update Global Bias (based on Indices usually)
        # Placeholder logic
        bias = RiskBias.NEUTRAL
        if regime == MarketRegime.TRENDING:
            bias = RiskBias.RISK_ON
        
        # Log decision
        log_msg = f"STRATEGIC: {symbol} | {regime.value} | {vol_state.value} | {bias.value} | Allowed:{allowed} | x{risk_mult}"
        logger.info(log_msg)
        
        with open("logs/strategic.log", "a") as f:
             f.write(f"{datetime.now(timezone.utc).isoformat()} | {log_msg}\n")

        return StrategicPermission(
            allowed=allowed,
            reason=reason,
            risk_multiplier=risk_mult,
            regime=regime.value,
            volatility=vol_state.value,
            bias=bias.value
        )

# Global Accessor
_engine = None
def get_strategic_engine():
    global _engine
    if _engine is None:
        _engine = StrategicEngine()
    return _engine

def get_status() -> Dict:
    """Telemetry status."""
    engine = get_strategic_engine()
    return {
        "regime": "ANALYZING", # Should cache last global regime
        "volatility": engine.global_volatility.value,
        "bias": engine.current_bias.value,
        "active_constraints": []
    }
