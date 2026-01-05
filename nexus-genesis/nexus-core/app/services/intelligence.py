"""
NEXUS Intelligence Module - AI Brain
=====================================

Vertex AI integration for:
1. Market regime detection (TRENDING/RANGING/VOLATILE)
2. Volatility clustering analysis
3. Anomaly detection pipeline
4. Signal generation (advisory only)

AI is advisor only - never places trades directly.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logger = logging.getLogger("nexus.brain")

# Initialize Vertex AI
PROJECT_ID = "nexus-dyron-777"
REGION = "us-central1"

# Model options
GEMINI_MODEL = "gemini-1.5-pro"  # Primary for regime detection
CLAUDE_MODEL = "claude-3-5-haiku@20241022"  # Backup for signal analysis

_vertex_initialized = False

def _ensure_vertex_init():
    """Lazy initialization of Vertex AI."""
    global _vertex_initialized
    if not _vertex_initialized:
        try:
            import vertexai
            vertexai.init(project=PROJECT_ID, location=REGION)
            _vertex_initialized = True
            logger.info(f"Vertex AI initialized: project={PROJECT_ID}, region={REGION}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise


class MarketRegime(Enum):
    """Market regime classifications."""
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class RegimeAnalysis:
    """Result of regime detection."""
    regime: MarketRegime
    confidence: float
    volatility_score: float
    trend_strength: float
    reasoning: str
    metadata: Dict[str, Any]


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    is_anomaly: bool
    anomaly_type: Optional[str]
    severity: float  # 0-1
    details: str
    recommendations: List[str]


# =============================================================================
# REGIME DETECTION
# =============================================================================
class RegimeDetector:
    """
    Detects current market regime using statistical methods + AI validation.
    
    Regimes:
    - TRENDING_UP: Strong upward direction, high ADX
    - TRENDING_DOWN: Strong downward direction, high ADX  
    - RANGING: Low ADX, price oscillating in bands
    - VOLATILE: High ATR expansion, uncertain direction
    """
    
    def __init__(self, adx_period: int = 14, atr_period: int = 14):
        self.adx_period = adx_period
        self.atr_period = atr_period
    
    def _calculate_adx(self, ohlcv: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Calculate ADX and Directional Indicators.
        Returns: (ADX, +DI, -DI)
        """
        high = ohlcv['high'].values
        low = ohlcv['low'].values
        close = ohlcv['close'].values
        
        # True Range
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        
        # +DM and -DM
        up_move = high[1:] - high[:-1]
        down_move = low[:-1] - low[1:]
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed averages
        atr = pd.Series(tr).rolling(window=self.adx_period).mean().values
        plus_di = 100 * pd.Series(plus_dm).rolling(window=self.adx_period).mean().values / (atr + 1e-10)
        minus_di = 100 * pd.Series(minus_dm).rolling(window=self.adx_period).mean().values / (atr + 1e-10)
        
        # DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = pd.Series(dx).rolling(window=self.adx_period).mean().values
        
        return adx[-1] if len(adx) > 0 else 0, plus_di[-1] if len(plus_di) > 0 else 0, minus_di[-1] if len(minus_di) > 0 else 0
    
    def _calculate_atr(self, ohlcv: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate current ATR and its Z-score vs historical.
        Returns: (current_atr, atr_zscore)
        """
        high = ohlcv['high'].values
        low = ohlcv['low'].values
        close = ohlcv['close'].values
        
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        
        atr_series = pd.Series(tr).rolling(window=self.atr_period).mean()
        current_atr = atr_series.iloc[-1] if len(atr_series) > 0 else 0
        
        # Z-score: how many std devs from mean
        atr_mean = atr_series.mean()
        atr_std = atr_series.std()
        
        if atr_std > 0:
            atr_zscore = (current_atr - atr_mean) / atr_std
        else:
            atr_zscore = 0
        
        return current_atr, atr_zscore
    
    def _calculate_trend_strength(self, ohlcv: pd.DataFrame, lookback: int = 20) -> float:
        """
        Calculate trend strength using linear regression R-squared.
        Returns: R-squared value (0 to 1)
        """
        close = ohlcv['close'].tail(lookback).values
        x = np.arange(len(close))
        
        # Linear regression
        n = len(close)
        sum_x = np.sum(x)
        sum_y = np.sum(close)
        sum_xy = np.sum(x * close)
        sum_x2 = np.sum(x ** 2)
        sum_y2 = np.sum(close ** 2)
        
        # Slope and intercept
        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            return 0
        
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n
        
        # Predicted values
        y_pred = slope * x + intercept
        
        # R-squared
        ss_res = np.sum((close - y_pred) ** 2)
        ss_tot = np.sum((close - np.mean(close)) ** 2)
        
        if ss_tot == 0:
            return 0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0, r_squared)
    
    def detect(self, ohlcv: pd.DataFrame) -> RegimeAnalysis:
        """
        Detect current market regime.
        
        Args:
            ohlcv: DataFrame with OHLCV data (minimum 50 bars recommended)
        
        Returns:
            RegimeAnalysis with regime classification and metadata
        """
        if len(ohlcv) < 30:
            return RegimeAnalysis(
                regime=MarketRegime.UNCERTAIN,
                confidence=0.0,
                volatility_score=0.0,
                trend_strength=0.0,
                reasoning="Insufficient data for regime detection",
                metadata={}
            )
        
        # Calculate indicators
        adx, plus_di, minus_di = self._calculate_adx(ohlcv)
        current_atr, atr_zscore = self._calculate_atr(ohlcv)
        trend_strength = self._calculate_trend_strength(ohlcv)
        
        # Volatility score (0-1 based on ATR z-score)
        volatility_score = min(1.0, max(0.0, (atr_zscore + 2) / 4))
        
        # Determine regime
        regime = MarketRegime.UNCERTAIN
        confidence = 0.0
        reasoning = ""
        
        # High volatility regime (ATR z-score > 1.5)
        if atr_zscore > 1.5:
            regime = MarketRegime.VOLATILE
            confidence = min(0.9, 0.5 + atr_zscore / 5)
            reasoning = f"Extreme volatility detected. ATR z-score: {atr_zscore:.2f}"
        
        # Trending regime (ADX > 25)
        elif adx > 25:
            if plus_di > minus_di:
                regime = MarketRegime.TRENDING_UP
                confidence = min(0.9, adx / 50)
                reasoning = f"Uptrend. ADX: {adx:.1f}, +DI > -DI"
            else:
                regime = MarketRegime.TRENDING_DOWN
                confidence = min(0.9, adx / 50)
                reasoning = f"Downtrend. ADX: {adx:.1f}, -DI > +DI"
        
        # Ranging regime (ADX < 25, trend strength < 0.5)
        elif adx < 25 and trend_strength < 0.5:
            regime = MarketRegime.RANGING
            confidence = min(0.85, (25 - adx) / 25)
            reasoning = f"Range-bound. ADX: {adx:.1f}, R²: {trend_strength:.2f}"
        
        # Weak trend / transitional
        else:
            regime = MarketRegime.UNCERTAIN
            confidence = 0.4
            reasoning = f"Transitional phase. ADX: {adx:.1f}, R²: {trend_strength:.2f}"
        
        return RegimeAnalysis(
            regime=regime,
            confidence=round(confidence, 3),
            volatility_score=round(volatility_score, 3),
            trend_strength=round(trend_strength, 3),
            reasoning=reasoning,
            metadata={
                "adx": round(adx, 2),
                "plus_di": round(plus_di, 2),
                "minus_di": round(minus_di, 2),
                "atr": round(current_atr, 4),
                "atr_zscore": round(atr_zscore, 2)
            }
        )


# =============================================================================
# VOLATILITY CLUSTERING
# =============================================================================
class VolatilityClustering:
    """
    Analyzes volatility clustering patterns using GARCH-like concepts.
    
    Volatility clusters: High volatility tends to follow high volatility.
    """
    
    def __init__(self, lookback: int = 20, threshold_multiplier: float = 1.5):
        self.lookback = lookback
        self.threshold_multiplier = threshold_multiplier
    
    def analyze(self, ohlcv: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze volatility clustering.
        
        Returns:
            Dict with clustering analysis
        """
        if len(ohlcv) < self.lookback + 10:
            return {"error": "Insufficient data", "cluster_active": False}
        
        close = ohlcv['close'].values
        
        # Calculate returns
        returns = np.diff(np.log(close))
        squared_returns = returns ** 2
        
        # Rolling volatility
        vol_series = pd.Series(squared_returns).rolling(window=5).mean().values
        avg_vol = np.nanmean(vol_series)
        
        # Detect volatility regime
        current_vol = vol_series[-1] if len(vol_series) > 0 else 0
        vol_ratio = current_vol / (avg_vol + 1e-10)
        
        # Persistence check (autocorrelation of squared returns)
        if len(squared_returns) > 10:
            autocorr = np.corrcoef(squared_returns[:-1], squared_returns[1:])[0, 1]
        else:
            autocorr = 0
        
        cluster_active = vol_ratio > self.threshold_multiplier and autocorr > 0.3
        
        return {
            "cluster_active": cluster_active,
            "current_volatility": round(np.sqrt(current_vol) * 100, 4),  # % terms
            "average_volatility": round(np.sqrt(avg_vol) * 100, 4),
            "volatility_ratio": round(vol_ratio, 2),
            "persistence_autocorr": round(autocorr, 3),
            "regime": "HIGH_VOL_CLUSTER" if cluster_active else "NORMAL",
            "recommendation": "REDUCE_SIZE" if cluster_active else "NORMAL_SIZE"
        }


# =============================================================================
# ANOMALY DETECTION
# =============================================================================
class AnomalyDetector:
    """
    Detects market anomalies that should trigger caution or halts.
    
    Anomaly types:
    - FLASH_CRASH: Sudden price drop > 3 ATR
    - VOLUME_SPIKE: Volume > 5x average
    - GAP: Open significantly different from previous close
    - LIQUIDITY_VOID: No volume for sustained period
    """
    
    def __init__(self, atr_threshold: float = 3.0, volume_threshold: float = 5.0):
        self.atr_threshold = atr_threshold
        self.volume_threshold = volume_threshold
    
    def detect(self, ohlcv: pd.DataFrame) -> AnomalyResult:
        """
        Detect anomalies in recent price action.
        """
        if len(ohlcv) < 20:
            return AnomalyResult(
                is_anomaly=False,
                anomaly_type=None,
                severity=0.0,
                details="Insufficient data",
                recommendations=[]
            )
        
        # Calculate ATR
        high = ohlcv['high'].values
        low = ohlcv['low'].values
        close = ohlcv['close'].values
        volume = ohlcv['volume'].values
        
        tr = np.maximum(high[1:] - low[1:], 
                       np.maximum(np.abs(high[1:] - close[:-1]), 
                                 np.abs(low[1:] - close[:-1])))
        atr = np.mean(tr[-14:]) if len(tr) >= 14 else np.mean(tr)
        
        # Current bar metrics
        current_range = high[-1] - low[-1]
        price_change = close[-1] - close[-2]
        avg_volume = np.mean(volume[-20:])
        current_volume = volume[-1]
        
        anomalies = []
        severity = 0.0
        recommendations = []
        
        # Flash crash/surge detection
        if abs(price_change) > atr * self.atr_threshold:
            direction = "CRASH" if price_change < 0 else "SURGE"
            anomalies.append(f"FLASH_{direction}")
            severity = max(severity, min(1.0, abs(price_change) / (atr * 5)))
            recommendations.append("HALT_TRADING")
            recommendations.append("WAIT_FOR_STABILIZATION")
        
        # Volume spike
        if avg_volume > 0 and current_volume > avg_volume * self.volume_threshold:
            anomalies.append("VOLUME_SPIKE")
            severity = max(severity, min(0.8, current_volume / (avg_volume * 10)))
            recommendations.append("REDUCE_POSITION_SIZE")
        
        # Gap detection
        if len(close) >= 2:
            gap = abs(ohlcv['open'].iloc[-1] - close[-2])
            if gap > atr * 2:
                anomalies.append("GAP")
                severity = max(severity, min(0.7, gap / (atr * 4)))
                recommendations.append("AVOID_IMMEDIATE_ENTRY")
        
        # Liquidity void (near-zero volume)
        if avg_volume > 0 and current_volume < avg_volume * 0.1:
            anomalies.append("LIQUIDITY_VOID")
            severity = max(severity, 0.6)
            recommendations.append("AVOID_LARGE_ORDERS")
        
        is_anomaly = len(anomalies) > 0
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_type=anomalies[0] if anomalies else None,
            severity=round(severity, 3),
            details=f"Detected: {', '.join(anomalies)}" if anomalies else "No anomalies",
            recommendations=recommendations
        )


# =============================================================================
# AI MARKET ANALYSIS (Vertex AI Integration)
# =============================================================================
def analyze_market(data: Any) -> Dict[str, Any]:
    """
    Analyzes market data using Vertex AI (Gemini Pro).
    
    Args:
        data (Any): The OHLCV data or market context to analyze.
        
    Returns:
        Dict[str, Any]: JSON response containing signal and confidence.
    """
    _ensure_vertex_init()
    
    try:
        from vertexai.generative_models import GenerativeModel
        model = GenerativeModel(GEMINI_MODEL)
        
        system_instruction = """You are NEXUS, an institutional-grade execution algorithm.
        
Analyze the provided market data and output a JSON response with:
{
    "signal": "BUY" | "SELL" | "WAIT",
    "confidence": 0.0 to 1.0,
    "regime": "TRENDING_UP" | "TRENDING_DOWN" | "RANGING" | "VOLATILE",
    "reasoning": "Brief explanation",
    "risk_level": "LOW" | "MEDIUM" | "HIGH"
}

Rules:
- Only output valid JSON, no markdown
- Confidence must reflect certainty (>0.7 for actionable signals)
- WAIT is the default when uncertain
- Risk level should escalate in volatile conditions"""
        
        # Convert data to string if it's not already
        data_str = json.dumps(data) if isinstance(data, dict) else str(data)
        
        prompt = f"{system_instruction}\n\nMarket Data:\n{data_str}"
        
        logger.info(f"Sending analysis request to {GEMINI_MODEL}")
        
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.2,  # Low temperature for consistency
                "max_output_tokens": 500
            }
        )
        
        result_text = response.text
        logger.info("AI analysis complete.")
        
        # Parse JSON
        result_json = json.loads(result_text)
        
        # Ensure required fields
        result_json.setdefault("signal", "WAIT")
        result_json.setdefault("confidence", 0.0)
        result_json.setdefault("regime", "UNCERTAIN")
        result_json.setdefault("risk_level", "MEDIUM")
        
        return result_json

    except Exception as e:
        logger.error(f"Error during AI market analysis: {e}")
        return {
            "signal": "WAIT", 
            "confidence": 0.0, 
            "regime": "UNCERTAIN",
            "risk_level": "HIGH",
            "error": str(e)
        }


def detect_regime_ai(ohlcv_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use AI to validate and enhance statistical regime detection.
    """
    _ensure_vertex_init()
    
    try:
        from vertexai.generative_models import GenerativeModel
        model = GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""Analyze this market summary and determine the current regime:

{json.dumps(ohlcv_summary, indent=2)}

Output JSON:
{{
    "regime": "TRENDING_UP" | "TRENDING_DOWN" | "RANGING" | "VOLATILE",
    "confidence": 0.0-1.0,
    "key_observations": ["observation1", "observation2"],
    "expected_duration": "SHORT" | "MEDIUM" | "LONG"
}}"""

        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        )
        
        return json.loads(response.text)
        
    except Exception as e:
        logger.error(f"AI regime detection failed: {e}")
        return {"regime": "UNCERTAIN", "confidence": 0.0, "error": str(e)}


# =============================================================================
# UNIFIED INTELLIGENCE INTERFACE
# =============================================================================
class NexusIntelligence:
    """
    Master intelligence class combining all analysis capabilities.
    """
    
    def __init__(self):
        self.regime_detector = RegimeDetector()
        self.volatility_analyzer = VolatilityClustering()
        self.anomaly_detector = AnomalyDetector()
    
    def full_analysis(self, ohlcv: pd.DataFrame, use_ai: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive market analysis.
        
        Args:
            ohlcv: DataFrame with OHLCV data
            use_ai: Whether to include AI validation
        
        Returns:
            Complete analysis dictionary
        """
        # Statistical analysis
        regime = self.regime_detector.detect(ohlcv)
        volatility = self.volatility_analyzer.analyze(ohlcv)
        anomaly = self.anomaly_detector.detect(ohlcv)
        
        result = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "regime": {
                "classification": regime.regime.value,
                "confidence": regime.confidence,
                "volatility_score": regime.volatility_score,
                "trend_strength": regime.trend_strength,
                "reasoning": regime.reasoning,
                "indicators": regime.metadata
            },
            "volatility_clustering": volatility,
            "anomaly_detection": {
                "is_anomaly": anomaly.is_anomaly,
                "type": anomaly.anomaly_type,
                "severity": anomaly.severity,
                "details": anomaly.details,
                "recommendations": anomaly.recommendations
            }
        }
        
        # AI validation if enabled
        if use_ai:
            try:
                # Prepare summary for AI
                ohlcv_summary = {
                    "last_close": float(ohlcv['close'].iloc[-1]),
                    "price_change_pct": float((ohlcv['close'].iloc[-1] / ohlcv['close'].iloc[-10] - 1) * 100),
                    "statistical_regime": regime.regime.value,
                    "adx": regime.metadata.get("adx", 0),
                    "volatility_ratio": volatility.get("volatility_ratio", 1),
                    "anomaly_detected": anomaly.is_anomaly
                }
                
                ai_analysis = analyze_market(ohlcv_summary)
                result["ai_analysis"] = ai_analysis
                
            except Exception as e:
                logger.warning(f"AI analysis skipped: {e}")
                result["ai_analysis"] = {"status": "unavailable", "error": str(e)}
        
        # Composite recommendation
        if anomaly.is_anomaly and anomaly.severity > 0.7:
            result["composite_action"] = "HALT"
            result["composite_reason"] = f"Anomaly detected: {anomaly.details}"
        elif regime.regime == MarketRegime.VOLATILE and volatility.get("cluster_active"):
            result["composite_action"] = "REDUCE_EXPOSURE"
            result["composite_reason"] = "High volatility cluster active"
        else:
            result["composite_action"] = "NORMAL"
            result["composite_reason"] = regime.reasoning
        
        return result



def list_models() -> Dict[str, str]:
    """List available AI models."""
    return {
        "gemini": GEMINI_MODEL,
        "claude": CLAUDE_MODEL
    }


# Convenience function
def quick_intelligence(ohlcv: pd.DataFrame) -> Dict[str, Any]:
    """Quick intelligence analysis."""
    intel = NexusIntelligence()
    return intel.full_analysis(ohlcv, use_ai=False)  # Skip AI for speed
