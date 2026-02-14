"""
NEXUS Market Regime Classifier — Phase 5, Part A
==================================================

Classifies each asset into one of 5 regimes:
  TRENDING, RANGE_BOUND, HIGH_VOLATILITY, LOW_LIQUIDITY, NEWS_DRIVEN

Uses:
  - ATR expansion/contraction (volatility state)
  - Volatility percentile (relative to 20-period lookback)
  - Momentum persistence (consecutive directional bars)
  - Volume anomalies (vs 20-period average)

NO REGIME → NO TRADE SUGGESTION.
This module is advisory only — it feeds context to the AI layer.
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.market_regime")


# =============================================================================
# REGIME DEFINITIONS
# =============================================================================

class Regime(Enum):
    TRENDING = "TRENDING"
    RANGE_BOUND = "RANGE_BOUND"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    NEWS_DRIVEN = "NEWS_DRIVEN"
    UNKNOWN = "UNKNOWN"


class TrendDirection(Enum):
    UP = "UP"
    DOWN = "DOWN"
    FLAT = "FLAT"


@dataclass
class RegimeState:
    """Current regime classification for a single asset."""
    symbol: str
    regime: Regime = Regime.UNKNOWN
    trend_direction: TrendDirection = TrendDirection.FLAT
    confidence: float = 0.0            # 0.0–1.0 classification confidence
    atr_percentile: float = 50.0       # current ATR vs lookback (0–100)
    volatility_state: str = "NORMAL"   # EXPANDING, CONTRACTING, NORMAL
    momentum_persistence: int = 0      # consecutive directional bars
    volume_ratio: float = 1.0          # current volume / avg volume
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "regime": self.regime.value,
            "trend_direction": self.trend_direction.value,
            "confidence": round(self.confidence, 3),
            "atr_percentile": round(self.atr_percentile, 1),
            "volatility_state": self.volatility_state,
            "momentum_persistence": self.momentum_persistence,
            "volume_ratio": round(self.volume_ratio, 2),
            "updated_at": self.updated_at,
        }

    def summary(self) -> str:
        """One-line regime summary for AI context injection."""
        return (
            f"{self.symbol}: {self.regime.value} "
            f"(trend={self.trend_direction.value}, "
            f"vol_pct={self.atr_percentile:.0f}, "
            f"momentum={self.momentum_persistence}, "
            f"vol_ratio={self.volume_ratio:.1f})"
        )


# =============================================================================
# REGIME CLASSIFIER
# =============================================================================

# Thresholds (calibrated for forex/crypto)
ATR_HIGH_PERCENTILE = 75           # above = high volatility
ATR_LOW_PERCENTILE = 25            # below = low volatility / range
MOMENTUM_PERSISTENCE_MIN = 3       # bars in same direction = trending
VOLUME_ANOMALY_RATIO = 2.0         # volume > 2x average = anomaly
VOLUME_LOW_RATIO = 0.4             # volume < 0.4x average = low liquidity
ATR_EXPANSION_RATIO = 1.3          # current ATR / prev ATR > 1.3 = expanding
ATR_CONTRACTION_RATIO = 0.7        # current ATR / prev ATR < 0.7 = contracting


def classify_regime(
    closes: List[float],
    highs: List[float],
    lows: List[float],
    volumes: Optional[List[float]] = None,
    is_news_window: bool = False,
) -> RegimeState:
    """
    Classify the current market regime for a symbol.

    Args:
        closes: List of close prices (most recent last), min 20
        highs: List of high prices (same length as closes)
        lows: List of low prices (same length as closes)
        volumes: Optional list of volumes
        is_news_window: True if within high-impact news window

    Returns:
        RegimeState with classification
    """
    if len(closes) < 20 or len(highs) < 20 or len(lows) < 20:
        return RegimeState(symbol="", regime=Regime.UNKNOWN, confidence=0.0)

    # ── 1. Calculate ATR series ──────────────────────────────────
    atr_values = _calculate_atr_series(highs, lows, closes, period=14)
    current_atr = atr_values[-1] if atr_values else 0
    atr_percentile = _percentile_rank(atr_values, current_atr) if atr_values else 50

    # Volatility state
    if len(atr_values) >= 2 and atr_values[-2] > 0:
        atr_ratio = atr_values[-1] / atr_values[-2]
        if atr_ratio > ATR_EXPANSION_RATIO:
            volatility_state = "EXPANDING"
        elif atr_ratio < ATR_CONTRACTION_RATIO:
            volatility_state = "CONTRACTING"
        else:
            volatility_state = "NORMAL"
    else:
        volatility_state = "NORMAL"

    # ── 2. Momentum persistence ──────────────────────────────────
    momentum = _calculate_momentum_persistence(closes)

    # ── 3. Volume analysis ───────────────────────────────────────
    volume_ratio = 1.0
    if volumes and len(volumes) >= 20:
        avg_vol = sum(volumes[-20:]) / 20
        if avg_vol > 0:
            volume_ratio = volumes[-1] / avg_vol

    # ── 4. Trend direction ───────────────────────────────────────
    trend_dir = _detect_trend_direction(closes)

    # ── 5. Classify regime ───────────────────────────────────────
    regime, confidence = _determine_regime(
        atr_percentile=atr_percentile,
        volatility_state=volatility_state,
        momentum_persistence=momentum,
        volume_ratio=volume_ratio,
        is_news_window=is_news_window,
    )

    state = RegimeState(
        symbol="",
        regime=regime,
        trend_direction=trend_dir,
        confidence=confidence,
        atr_percentile=atr_percentile,
        volatility_state=volatility_state,
        momentum_persistence=momentum,
        volume_ratio=volume_ratio,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    return state


def _calculate_atr_series(
    highs: List[float], lows: List[float], closes: List[float], period: int = 14
) -> List[float]:
    """Calculate ATR series using Wilder's smoothing."""
    if len(highs) < period + 1:
        return []

    true_ranges = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return []

    # First ATR is simple average
    atr = sum(true_ranges[:period]) / period
    atr_series = [atr]

    # Wilder's smoothing
    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period
        atr_series.append(atr)

    return atr_series


def _percentile_rank(values: List[float], current: float) -> float:
    """Calculate percentile rank of current value within the series."""
    if not values:
        return 50.0
    count_below = sum(1 for v in values if v < current)
    return (count_below / len(values)) * 100


def _calculate_momentum_persistence(closes: List[float]) -> int:
    """Count consecutive bars in the same direction (from most recent)."""
    if len(closes) < 2:
        return 0

    count = 0
    direction = None

    for i in range(len(closes) - 1, 0, -1):
        diff = closes[i] - closes[i - 1]
        if diff == 0:
            break
        current_dir = "UP" if diff > 0 else "DOWN"
        if direction is None:
            direction = current_dir
            count = 1
        elif current_dir == direction:
            count += 1
        else:
            break

    return count


def _detect_trend_direction(closes: List[float]) -> TrendDirection:
    """Detect trend using 10-period vs 20-period SMA."""
    if len(closes) < 20:
        return TrendDirection.FLAT

    sma10 = sum(closes[-10:]) / 10
    sma20 = sum(closes[-20:]) / 20
    price = closes[-1]

    if price > sma10 > sma20:
        return TrendDirection.UP
    elif price < sma10 < sma20:
        return TrendDirection.DOWN
    else:
        return TrendDirection.FLAT


def _determine_regime(
    atr_percentile: float,
    volatility_state: str,
    momentum_persistence: int,
    volume_ratio: float,
    is_news_window: bool,
) -> Tuple[Regime, float]:
    """
    Determine regime from indicators. Returns (Regime, confidence).
    Priority: NEWS_DRIVEN > HIGH_VOLATILITY > LOW_LIQUIDITY > TRENDING > RANGE_BOUND
    """
    # News override
    if is_news_window:
        return Regime.NEWS_DRIVEN, 0.9

    # High volatility
    if atr_percentile >= ATR_HIGH_PERCENTILE and volatility_state == "EXPANDING":
        confidence = min(1.0, 0.7 + (atr_percentile - ATR_HIGH_PERCENTILE) / 100)
        return Regime.HIGH_VOLATILITY, confidence

    # Low liquidity
    if volume_ratio < VOLUME_LOW_RATIO:
        return Regime.LOW_LIQUIDITY, 0.7

    # Trending
    if momentum_persistence >= MOMENTUM_PERSISTENCE_MIN and atr_percentile >= 40:
        confidence = min(1.0, 0.6 + momentum_persistence * 0.05)
        return Regime.TRENDING, confidence

    # Range-bound (default when nothing else stands out)
    if atr_percentile < ATR_LOW_PERCENTILE and volatility_state != "EXPANDING":
        return Regime.RANGE_BOUND, 0.75

    # Mild trending
    if momentum_persistence >= 2:
        return Regime.TRENDING, 0.55

    return Regime.RANGE_BOUND, 0.5


# =============================================================================
# REGIME STORE (per-symbol, in-memory)
# =============================================================================

class RegimeStore:
    """
    Thread-safe store for current regime classifications.
    One entry per symbol, updated on each analysis cycle.
    """

    def __init__(self):
        self._regimes: Dict[str, RegimeState] = {}
        self._lock = threading.Lock()

    def update(self, symbol: str, state: RegimeState) -> None:
        """Update regime for a symbol."""
        state.symbol = symbol
        with self._lock:
            self._regimes[symbol] = state
        logger.info(f"REGIME_UPDATE: {state.summary()}")

    def get(self, symbol: str) -> Optional[RegimeState]:
        """Get current regime for a symbol."""
        with self._lock:
            return self._regimes.get(symbol)

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all regimes as dict."""
        with self._lock:
            return {sym: state.to_dict() for sym, state in self._regimes.items()}

    def has_regime(self, symbol: str) -> bool:
        """Check if a regime exists for this symbol."""
        with self._lock:
            state = self._regimes.get(symbol)
            return state is not None and state.regime != Regime.UNKNOWN

    def get_regime_context_for_ai(self, symbol: str) -> str:
        """
        Get a formatted regime context string for injection into AI prompts.
        Returns empty string if no regime is classified.
        """
        with self._lock:
            state = self._regimes.get(symbol)
            if state is None or state.regime == Regime.UNKNOWN:
                return "REGIME: UNKNOWN — insufficient data for classification."

        lines = [
            f"CURRENT MARKET REGIME FOR {symbol}:",
            f"  Classification: {state.regime.value}",
            f"  Trend Direction: {state.trend_direction.value}",
            f"  Regime Confidence: {state.confidence:.0%}",
            f"  ATR Percentile: {state.atr_percentile:.0f}th",
            f"  Volatility State: {state.volatility_state}",
            f"  Momentum Persistence: {state.momentum_persistence} bars",
            f"  Volume Ratio: {state.volume_ratio:.1f}x average",
        ]

        # Strategy guidance per regime
        guidance = {
            Regime.TRENDING: "Favor trend-following entries. Avoid counter-trend.",
            Regime.RANGE_BOUND: "Favor mean-reversion at extremes. Tighten stops.",
            Regime.HIGH_VOLATILITY: "Reduce position size. Widen stops. Caution.",
            Regime.LOW_LIQUIDITY: "Avoid new entries. Spread risk elevated.",
            Regime.NEWS_DRIVEN: "No new trades. Event risk active.",
        }
        lines.append(f"  Guidance: {guidance.get(state.regime, 'Proceed with caution.')}")

        return "\n".join(lines)


# =============================================================================
# SINGLETON
# =============================================================================

_regime_store: Optional[RegimeStore] = None


def get_regime_store() -> RegimeStore:
    global _regime_store
    if _regime_store is None:
        _regime_store = RegimeStore()
    return _regime_store
