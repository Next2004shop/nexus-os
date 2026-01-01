"""
NEXUS Strategy Engine - Ancient Laws Module
============================================

Implements 5 ancient market principles:
1. TrendFollower - EMA crossovers (9/21/50)
2. MeanReversion - Bollinger Bands with RSI confirmation
3. LiquiditySweep - Volume spike detection at key levels
4. TimeCycles - Session alignment (London/NY/Asia)
5. FearGreed - Market sentiment oscillator

All strategies return advisory signals only.
AI never places trades directly.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import pytz

logger = logging.getLogger("nexus.strategy_engine")


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


class MarketRegime(Enum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"


@dataclass
class StrategyResult:
    """Unified result from any strategy module."""
    signal: Signal
    confidence: float  # 0.0 to 1.0
    strategy_name: str
    reasoning: str
    metadata: Dict[str, Any]


# =============================================================================
# STRATEGY 1: TREND FOLLOWER (EMA Crossovers)
# =============================================================================
class TrendFollower:
    """
    Ancient Law #1: The Trend is Your Friend
    
    Uses 3 EMAs (9, 21, 50) to detect trend direction and momentum.
    Entry signals generated on crossovers with momentum confirmation.
    """
    
    def __init__(self, fast_period: int = 9, mid_period: int = 21, slow_period: int = 50):
        self.fast_period = fast_period
        self.mid_period = mid_period
        self.slow_period = slow_period
        
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA using pandas for efficiency."""
        series = pd.Series(prices)
        return series.ewm(span=period, adjust=False).mean().values
    
    def analyze(self, ohlcv: pd.DataFrame) -> StrategyResult:
        """
        Analyze price data for trend signals.
        
        Args:
            ohlcv: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        
        Returns:
            StrategyResult with signal, confidence, and metadata
        """
        if len(ohlcv) < self.slow_period + 5:
            return StrategyResult(
                signal=Signal.WAIT,
                confidence=0.0,
                strategy_name="TrendFollower",
                reasoning="Insufficient data for EMA calculation",
                metadata={}
            )
        
        close = ohlcv['close'].values
        
        # Calculate EMAs
        ema_fast = self._calculate_ema(close, self.fast_period)
        ema_mid = self._calculate_ema(close, self.mid_period)
        ema_slow = self._calculate_ema(close, self.slow_period)
        
        # Current values
        curr_fast = ema_fast[-1]
        curr_mid = ema_mid[-1]
        curr_slow = ema_slow[-1]
        
        # Previous values for crossover detection
        prev_fast = ema_fast[-2]
        prev_mid = ema_mid[-2]
        
        # Trend alignment check
        bullish_alignment = curr_fast > curr_mid > curr_slow
        bearish_alignment = curr_fast < curr_mid < curr_slow
        
        # Golden cross: fast crosses above mid
        golden_cross = prev_fast <= prev_mid and curr_fast > curr_mid
        
        # Death cross: fast crosses below mid
        death_cross = prev_fast >= prev_mid and curr_fast < curr_mid
        
        # Calculate momentum (price distance from slow EMA)
        momentum = (close[-1] - curr_slow) / curr_slow * 100
        
        signal = Signal.WAIT
        confidence = 0.0
        reasoning = "No clear trend signal"
        
        if golden_cross and bullish_alignment:
            signal = Signal.BUY
            confidence = min(0.5 + abs(momentum) / 10, 0.95)
            reasoning = f"Golden cross with bullish alignment. Momentum: {momentum:.2f}%"
            
        elif death_cross and bearish_alignment:
            signal = Signal.SELL
            confidence = min(0.5 + abs(momentum) / 10, 0.95)
            reasoning = f"Death cross with bearish alignment. Momentum: {momentum:.2f}%"
            
        elif bullish_alignment:
            signal = Signal.BUY
            confidence = 0.3 + min(abs(momentum) / 20, 0.4)
            reasoning = f"Bullish trend alignment. Momentum: {momentum:.2f}%"
            
        elif bearish_alignment:
            signal = Signal.SELL
            confidence = 0.3 + min(abs(momentum) / 20, 0.4)
            reasoning = f"Bearish trend alignment. Momentum: {momentum:.2f}%"
        
        return StrategyResult(
            signal=signal,
            confidence=confidence,
            strategy_name="TrendFollower",
            reasoning=reasoning,
            metadata={
                "ema_fast": round(curr_fast, 4),
                "ema_mid": round(curr_mid, 4),
                "ema_slow": round(curr_slow, 4),
                "momentum_pct": round(momentum, 2),
                "bullish_alignment": bullish_alignment,
                "bearish_alignment": bearish_alignment
            }
        )


# =============================================================================
# STRATEGY 2: MEAN REVERSION (Bollinger Bands + RSI)
# =============================================================================
class MeanReversion:
    """
    Ancient Law #2: What Goes Up Must Come Down
    
    Uses Bollinger Bands for price extremes with RSI confirmation.
    Entries at band touches with divergence confirmation.
    """
    
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, rsi_period: int = 14):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate RSI indicator."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = pd.Series(gains).rolling(window=period).mean().values
        avg_loss = pd.Series(losses).rolling(window=period).mean().values
        
        rs = np.divide(avg_gain, avg_loss, where=avg_loss != 0)
        rsi = 100 - (100 / (1 + rs))
        
        # Prepend NaN to match original array length
        return np.append([np.nan], rsi)
    
    def _calculate_bollinger(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands."""
        series = pd.Series(prices)
        middle = series.rolling(window=self.bb_period).mean()
        std = series.rolling(window=self.bb_period).std()
        
        upper = middle + (std * self.bb_std)
        lower = middle - (std * self.bb_std)
        
        return upper.values, middle.values, lower.values
    
    def analyze(self, ohlcv: pd.DataFrame) -> StrategyResult:
        """
        Analyze price data for mean reversion opportunities.
        """
        if len(ohlcv) < max(self.bb_period, self.rsi_period) + 5:
            return StrategyResult(
                signal=Signal.WAIT,
                confidence=0.0,
                strategy_name="MeanReversion",
                reasoning="Insufficient data",
                metadata={}
            )
        
        close = ohlcv['close'].values
        
        # Calculate indicators
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger(close)
        rsi = self._calculate_rsi(close, self.rsi_period)
        
        curr_price = close[-1]
        curr_rsi = rsi[-1]
        curr_upper = bb_upper[-1]
        curr_lower = bb_lower[-1]
        curr_middle = bb_middle[-1]
        
        # Calculate %B (position within Bollinger Bands)
        band_width = curr_upper - curr_lower
        if band_width > 0:
            pct_b = (curr_price - curr_lower) / band_width
        else:
            pct_b = 0.5
        
        signal = Signal.WAIT
        confidence = 0.0
        reasoning = "No mean reversion opportunity"
        
        # Oversold: Price at/below lower band + RSI < 30
        if curr_price <= curr_lower and curr_rsi < 30:
            signal = Signal.BUY
            oversold_strength = (30 - curr_rsi) / 30
            confidence = min(0.6 + oversold_strength * 0.3, 0.95)
            reasoning = f"Oversold: Price at lower BB, RSI={curr_rsi:.1f}"
            
        # Overbought: Price at/above upper band + RSI > 70
        elif curr_price >= curr_upper and curr_rsi > 70:
            signal = Signal.SELL
            overbought_strength = (curr_rsi - 70) / 30
            confidence = min(0.6 + overbought_strength * 0.3, 0.95)
            reasoning = f"Overbought: Price at upper BB, RSI={curr_rsi:.1f}"
            
        # Near lower band with RSI suggesting reversal
        elif pct_b < 0.2 and curr_rsi < 40:
            signal = Signal.BUY
            confidence = 0.4 + (0.2 - pct_b) * 1.5
            reasoning = f"Approaching oversold: %B={pct_b:.2f}, RSI={curr_rsi:.1f}"
            
        # Near upper band with RSI suggesting reversal
        elif pct_b > 0.8 and curr_rsi > 60:
            signal = Signal.SELL
            confidence = 0.4 + (pct_b - 0.8) * 1.5
            reasoning = f"Approaching overbought: %B={pct_b:.2f}, RSI={curr_rsi:.1f}"
        
        return StrategyResult(
            signal=signal,
            confidence=confidence,
            strategy_name="MeanReversion",
            reasoning=reasoning,
            metadata={
                "bb_upper": round(curr_upper, 4),
                "bb_middle": round(curr_middle, 4),
                "bb_lower": round(curr_lower, 4),
                "rsi": round(curr_rsi, 2) if not np.isnan(curr_rsi) else None,
                "pct_b": round(pct_b, 3),
                "band_width": round(band_width, 4)
            }
        )


# =============================================================================
# STRATEGY 3: LIQUIDITY SWEEP DETECTION
# =============================================================================
class LiquiditySweep:
    """
    Ancient Law #3: Smart Money Hunts Stop Losses
    
    Detects liquidity sweeps at key levels where stops are typically clustered.
    Volume confirmation for genuine sweeps vs fake breakouts.
    """
    
    def __init__(self, lookback: int = 20, volume_threshold: float = 1.5):
        self.lookback = lookback
        self.volume_threshold = volume_threshold  # Multiplier of average volume
    
    def _find_swing_levels(self, ohlcv: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """Find swing highs and lows where liquidity pools exist."""
        highs = ohlcv['high'].values
        lows = ohlcv['low'].values
        
        swing_highs = []
        swing_lows = []
        
        # Simple swing detection (3-bar pattern)
        for i in range(2, len(highs) - 2):
            # Swing high: higher than 2 bars on each side
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])
            
            # Swing low: lower than 2 bars on each side
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])
        
        return swing_highs[-5:] if swing_highs else [], swing_lows[-5:] if swing_lows else []
    
    def analyze(self, ohlcv: pd.DataFrame) -> StrategyResult:
        """
        Detect liquidity sweep patterns.
        """
        if len(ohlcv) < self.lookback + 10:
            return StrategyResult(
                signal=Signal.WAIT,
                confidence=0.0,
                strategy_name="LiquiditySweep",
                reasoning="Insufficient data",
                metadata={}
            )
        
        # Use lookback window
        recent = ohlcv.tail(self.lookback + 5)
        
        swing_highs, swing_lows = self._find_swing_levels(ohlcv.tail(50))
        
        curr_high = ohlcv['high'].iloc[-1]
        curr_low = ohlcv['low'].iloc[-1]
        curr_close = ohlcv['close'].iloc[-1]
        curr_open = ohlcv['open'].iloc[-1]
        curr_volume = ohlcv['volume'].iloc[-1]
        
        avg_volume = ohlcv['volume'].tail(20).mean()
        volume_spike = curr_volume > avg_volume * self.volume_threshold
        
        signal = Signal.WAIT
        confidence = 0.0
        reasoning = "No liquidity sweep detected"
        sweep_type = None
        
        # Check for sweep of highs (potential short entry)
        for high in swing_highs:
            if curr_high > high and curr_close < high:
                # Swept the high but closed below = rejection
                if volume_spike:
                    signal = Signal.SELL
                    confidence = 0.7 + (curr_volume / avg_volume - 1) * 0.1
                    sweep_type = "HIGH_SWEEP"
                    reasoning = f"Liquidity sweep above {high:.2f} with rejection. Volume: {curr_volume/avg_volume:.1f}x avg"
                    break
        
        # Check for sweep of lows (potential long entry)
        if signal == Signal.WAIT:
            for low in swing_lows:
                if curr_low < low and curr_close > low:
                    # Swept the low but closed above = rejection
                    if volume_spike:
                        signal = Signal.BUY
                        confidence = 0.7 + (curr_volume / avg_volume - 1) * 0.1
                        sweep_type = "LOW_SWEEP"
                        reasoning = f"Liquidity sweep below {low:.2f} with rejection. Volume: {curr_volume/avg_volume:.1f}x avg"
                        break
        
        confidence = min(confidence, 0.95)
        
        return StrategyResult(
            signal=signal,
            confidence=confidence,
            strategy_name="LiquiditySweep",
            reasoning=reasoning,
            metadata={
                "swing_highs": [round(h, 4) for h in swing_highs],
                "swing_lows": [round(l, 4) for l in swing_lows],
                "volume_ratio": round(curr_volume / avg_volume, 2) if avg_volume > 0 else 0,
                "sweep_type": sweep_type,
                "volume_spike": volume_spike
            }
        )


# =============================================================================
# STRATEGY 4: TIME CYCLES (Session Alignment)
# =============================================================================
class TimeCycles:
    """
    Ancient Law #4: Time is the Ultimate Indicator
    
    Aligns entries with optimal trading sessions (London/NY overlap).
    Avoids low-liquidity periods and major news times.
    """
    
    # Session times in UTC
    SESSIONS = {
        "sydney": (21, 6),     # 21:00 - 06:00 UTC
        "tokyo": (0, 9),       # 00:00 - 09:00 UTC
        "london": (7, 16),     # 07:00 - 16:00 UTC
        "newyork": (12, 21),   # 12:00 - 21:00 UTC
    }
    
    # High volatility overlap periods
    OVERLAPS = {
        "london_newyork": (12, 16),  # Best trading period
        "tokyo_london": (7, 9),
    }
    
    def __init__(self, preferred_sessions: List[str] = None):
        self.preferred_sessions = preferred_sessions or ["london", "newyork"]
    
    def _get_active_sessions(self, utc_hour: int) -> List[str]:
        """Determine which sessions are active."""
        active = []
        for session, (start, end) in self.SESSIONS.items():
            if start <= end:
                if start <= utc_hour < end:
                    active.append(session)
            else:  # Wraps around midnight
                if utc_hour >= start or utc_hour < end:
                    active.append(session)
        return active
    
    def _is_overlap_period(self, utc_hour: int) -> Optional[str]:
        """Check if currently in overlap period."""
        for overlap, (start, end) in self.OVERLAPS.items():
            if start <= utc_hour < end:
                return overlap
        return None
    
    def analyze(self, utc_time: Optional[datetime] = None) -> StrategyResult:
        """
        Analyze current time for optimal trading conditions.
        """
        if utc_time is None:
            utc_time = datetime.now(timezone.utc)
        
        utc_hour = utc_time.hour
        day_of_week = utc_time.weekday()
        
        # Weekend check
        if day_of_week >= 5:  # Saturday or Sunday
            return StrategyResult(
                signal=Signal.WAIT,
                confidence=0.0,
                strategy_name="TimeCycles",
                reasoning="Weekend - markets closed",
                metadata={"day_of_week": day_of_week, "weekend": True}
            )
        
        active_sessions = self._get_active_sessions(utc_hour)
        overlap = self._is_overlap_period(utc_hour)
        
        # Calculate trading score
        score = 0.0
        reasoning_parts = []
        
        # Preferred session bonus
        for session in active_sessions:
            if session in self.preferred_sessions:
                score += 0.3
                reasoning_parts.append(f"{session.capitalize()} session active")
        
        # Overlap bonus (highest quality)
        if overlap:
            score += 0.4
            reasoning_parts.append(f"{overlap.replace('_', '/')} overlap")
        
        # Monday/Friday penalty (typically lower quality)
        if day_of_week == 0:
            score -= 0.1
            reasoning_parts.append("Monday (accumulation)")
        elif day_of_week == 4:
            score -= 0.1
            reasoning_parts.append("Friday (position squaring)")
        
        # Normalize score
        score = max(0.0, min(1.0, score))
        
        # Determine signal permission
        if score >= 0.5:
            signal = Signal.BUY  # Indicates trading is allowed
            reasoning = "Optimal trading time: " + ", ".join(reasoning_parts)
        elif score >= 0.3:
            signal = Signal.WAIT
            reasoning = "Suboptimal but acceptable: " + ", ".join(reasoning_parts)
        else:
            signal = Signal.WAIT
            reasoning = "Avoid trading: " + (", ".join(reasoning_parts) if reasoning_parts else "No active sessions")
        
        return StrategyResult(
            signal=signal,
            confidence=score,
            strategy_name="TimeCycles",
            reasoning=reasoning,
            metadata={
                "utc_hour": utc_hour,
                "day_of_week": day_of_week,
                "active_sessions": active_sessions,
                "overlap": overlap,
                "trading_score": round(score, 2)
            }
        )


# =============================================================================
# STRATEGY 5: FEAR/GREED IMBALANCE
# =============================================================================
class FearGreed:
    """
    Ancient Law #5: Be Greedy When Others Are Fearful
    
    Measures market sentiment through price action and volume patterns.
    Extreme readings suggest contrarian opportunities.
    """
    
    def __init__(self, lookback: int = 14, extreme_threshold: float = 0.25):
        self.lookback = lookback
        self.extreme_threshold = extreme_threshold
    
    def _calculate_williams_r(self, ohlcv: pd.DataFrame, period: int = 14) -> float:
        """Williams %R as fear/greed proxy."""
        high = ohlcv['high'].tail(period)
        low = ohlcv['low'].tail(period)
        close = ohlcv['close'].iloc[-1]
        
        highest = high.max()
        lowest = low.min()
        
        if highest == lowest:
            return -50  # Neutral
        
        return ((highest - close) / (highest - lowest)) * -100
    
    def _calculate_volume_sentiment(self, ohlcv: pd.DataFrame) -> float:
        """Calculate volume-weighted price momentum."""
        recent = ohlcv.tail(self.lookback)
        
        # Up volume vs down volume
        up_volume = 0.0
        down_volume = 0.0
        
        for i in range(len(recent)):
            if recent['close'].iloc[i] >= recent['open'].iloc[i]:
                up_volume += recent['volume'].iloc[i]
            else:
                down_volume += recent['volume'].iloc[i]
        
        total_volume = up_volume + down_volume
        if total_volume == 0:
            return 0.5
        
        return up_volume / total_volume  # 0-1 scale, higher = greed
    
    def _calculate_consecutive_candles(self, ohlcv: pd.DataFrame) -> Tuple[int, int]:
        """Count consecutive green/red candles."""
        recent = ohlcv.tail(10)
        
        green_streak = 0
        red_streak = 0
        
        for i in range(len(recent) - 1, -1, -1):
            if recent['close'].iloc[i] >= recent['open'].iloc[i]:
                if red_streak > 0:
                    break
                green_streak += 1
            else:
                if green_streak > 0:
                    break
                red_streak += 1
        
        return green_streak, red_streak
    
    def analyze(self, ohlcv: pd.DataFrame) -> StrategyResult:
        """
        Analyze market sentiment for extremes.
        """
        if len(ohlcv) < self.lookback + 5:
            return StrategyResult(
                signal=Signal.WAIT,
                confidence=0.0,
                strategy_name="FearGreed",
                reasoning="Insufficient data",
                metadata={}
            )
        
        williams_r = self._calculate_williams_r(ohlcv)
        volume_sentiment = self._calculate_volume_sentiment(ohlcv)
        green_streak, red_streak = self._calculate_consecutive_candles(ohlcv)
        
        # Composite fear/greed score (0 = extreme fear, 100 = extreme greed)
        # Williams %R: -100 to 0 -> 0 to 100
        williams_normalized = (williams_r + 100) / 100 * 100
        
        # Volume sentiment: 0-1 -> 0-100
        volume_normalized = volume_sentiment * 100
        
        # Streak factor
        streak_factor = 50  # Neutral
        if green_streak >= 5:
            streak_factor = 80 + min(green_streak - 5, 2) * 5
        elif red_streak >= 5:
            streak_factor = 20 - min(red_streak - 5, 2) * 5
        
        # Weighted composite
        fg_score = (williams_normalized * 0.4 + volume_normalized * 0.35 + streak_factor * 0.25)
        
        signal = Signal.WAIT
        confidence = 0.0
        reasoning = "Sentiment neutral"
        
        # Extreme fear (contrarian buy)
        if fg_score < 25:
            signal = Signal.BUY
            confidence = 0.5 + (25 - fg_score) / 50
            reasoning = f"Extreme FEAR detected (score: {fg_score:.0f}). Contrarian buy opportunity."
        
        # Extreme greed (contrarian sell)
        elif fg_score > 75:
            signal = Signal.SELL
            confidence = 0.5 + (fg_score - 75) / 50
            reasoning = f"Extreme GREED detected (score: {fg_score:.0f}). Contrarian sell opportunity."
        
        # Moderate zones
        elif fg_score < 40:
            signal = Signal.BUY
            confidence = 0.3
            reasoning = f"Moderate fear (score: {fg_score:.0f}). Accumulation zone."
        
        elif fg_score > 60:
            signal = Signal.SELL
            confidence = 0.3
            reasoning = f"Moderate greed (score: {fg_score:.0f}). Distribution zone."
        
        confidence = min(confidence, 0.95)
        
        return StrategyResult(
            signal=signal,
            confidence=confidence,
            strategy_name="FearGreed",
            reasoning=reasoning,
            metadata={
                "fear_greed_score": round(fg_score, 1),
                "williams_r": round(williams_r, 2),
                "volume_sentiment": round(volume_sentiment, 3),
                "green_streak": green_streak,
                "red_streak": red_streak,
                "interpretation": "FEAR" if fg_score < 40 else "GREED" if fg_score > 60 else "NEUTRAL"
            }
        )


# =============================================================================
# STRATEGY ORCHESTRATOR
# =============================================================================
class StrategyOrchestrator:
    """
    Master orchestrator that combines all 5 strategies into a unified signal.
    
    Implements weighted voting with confidence adjustment.
    """
    
    def __init__(self, strategy_weights: Optional[Dict[str, float]] = None):
        self.trend_follower = TrendFollower()
        self.mean_reversion = MeanReversion()
        self.liquidity_sweep = LiquiditySweep()
        self.time_cycles = TimeCycles()
        self.fear_greed = FearGreed()
        
        # Default weights
        self.weights = strategy_weights or {
            "TrendFollower": 0.25,
            "MeanReversion": 0.20,
            "LiquiditySweep": 0.25,
            "TimeCycles": 0.15,
            "FearGreed": 0.15
        }
    
    def analyze_all(self, ohlcv: pd.DataFrame, utc_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Run all strategies and produce a composite decision.
        
        Returns:
            Dict with:
                - composite_signal: Final BUY/SELL/WAIT
                - composite_confidence: Weighted confidence
                - individual_results: Each strategy's result
                - reasoning: Combined reasoning
        """
        results = {}
        
        # Run each strategy
        results["TrendFollower"] = self.trend_follower.analyze(ohlcv)
        results["MeanReversion"] = self.mean_reversion.analyze(ohlcv)
        results["LiquiditySweep"] = self.liquidity_sweep.analyze(ohlcv)
        results["TimeCycles"] = self.time_cycles.analyze(utc_time)
        results["FearGreed"] = self.fear_greed.analyze(ohlcv)
        
        # Calculate weighted vote
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        
        for name, result in results.items():
            weight = self.weights.get(name, 0.0)
            weighted_confidence = result.confidence * weight
            
            if result.signal == Signal.BUY:
                buy_score += weighted_confidence
            elif result.signal == Signal.SELL:
                sell_score += weighted_confidence
            
            total_weight += weight * result.confidence
        
        # Determine composite signal
        if total_weight == 0:
            composite_signal = Signal.WAIT
            composite_confidence = 0.0
        elif buy_score > sell_score and buy_score > 0.3:
            composite_signal = Signal.BUY
            composite_confidence = buy_score / sum(self.weights.values())
        elif sell_score > buy_score and sell_score > 0.3:
            composite_signal = Signal.SELL
            composite_confidence = sell_score / sum(self.weights.values())
        else:
            composite_signal = Signal.WAIT
            composite_confidence = 0.0
        
        # Time cycles acts as a gate
        time_result = results["TimeCycles"]
        if time_result.confidence < 0.3 and composite_signal != Signal.WAIT:
            logger.info("TimeCycles gate: Downgrading signal due to suboptimal timing")
            composite_confidence *= 0.5
        
        # Compile reasoning
        active_reasons = [
            r.reasoning for r in results.values() 
            if r.signal != Signal.WAIT or r.confidence > 0.3
        ]
        
        return {
            "composite_signal": composite_signal.value,
            "composite_confidence": round(composite_confidence, 3),
            "buy_score": round(buy_score, 3),
            "sell_score": round(sell_score, 3),
            "individual_results": {
                name: {
                    "signal": r.signal.value,
                    "confidence": round(r.confidence, 3),
                    "reasoning": r.reasoning,
                    "metadata": r.metadata
                }
                for name, r in results.items()
            },
            "combined_reasoning": " | ".join(active_reasons[:3])  # Top 3 reasons
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================
def create_orchestrator(weights: Optional[Dict[str, float]] = None) -> StrategyOrchestrator:
    """Factory function to create a strategy orchestrator."""
    return StrategyOrchestrator(weights)


def quick_analysis(ohlcv: pd.DataFrame) -> Dict[str, Any]:
    """Quick convenience function for single analysis."""
    orchestrator = StrategyOrchestrator()
    return orchestrator.analyze_all(ohlcv)
