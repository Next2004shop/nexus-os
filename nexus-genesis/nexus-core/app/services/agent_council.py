"""
NEXUS Agent Council - Multi-Agent Decision System
==================================================

Implements the "Council Over King" principle from Ancient × Axelrod × Netflix doctrine.

5 Independent Agents:
1. MarketStructureAgent - Wyckoff accumulation/distribution patterns
2. MomentumAgent - Price momentum + volume confirmation
3. VolatilityRiskAgent - ATR-based risk assessment
4. MacroSentimentAgent - Market sentiment and regime analysis
5. ExecutionSafetyAgent - Pre-trade safety validation

IMMUTABLE LAW: No trade executes without quorum (3/5 agents agreeing).
"""

"""
NEXUS Agent Council - Multi-Agent Decision System
==================================================

Implements the "Council Over King" principle from Ancient × Axelrod × Netflix doctrine.

5 Independent Agents:
1. MarketStructureAgent - Wyckoff accumulation/distribution patterns
2. MomentumAgent - Price momentum + volume confirmation
3. VolatilityRiskAgent - ATR-based risk assessment
4. MacroSentimentAgent - Market sentiment and regime analysis
5. ExecutionSafetyAgent - Pre-trade safety validation

IMMUTABLE LAW: No trade executes without quorum (3/5 agents agreeing).
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("nexus.agent_council")


# =============================================================================
# VOTE TYPES
# =============================================================================

class Vote(Enum):
    """Agent vote options."""
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    ABSTAIN = "ABSTAIN"  # Agent cannot make determination


@dataclass
class AgentVote:
    """Individual agent's vote with reasoning."""
    agent_name: str
    vote: Vote
    confidence: float  # 0.0 to 1.0
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CouncilDecision:
    """Final council decision after voting."""
    quorum_reached: bool
    final_decision: Vote
    consensus_confidence: float
    votes: List[AgentVote]
    vote_summary: Dict[str, int]
    reasoning: str
    position_size_modifier: float = 1.0  # Reduce if low consensus
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =============================================================================
# BASE AGENT CLASS
# =============================================================================

class BaseAgent(ABC):
    """
    Abstract base class for all council agents.
    
    Each agent must:
    1. Analyze independently (no knowledge of other agents' decisions)
    2. Return a vote with confidence level
    3. Provide reasoning for audit trail
    """
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight  # Voting weight (default equal)
        self.last_vote: Optional[AgentVote] = None
    
    @abstractmethod
    def analyze(self, symbol: str, side: str, market_data: Dict[str, Any]) -> AgentVote:
        """
        Analyze market conditions and return a vote.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            side: Proposed trade direction ("BUY" or "SELL")
            market_data: Dict containing OHLCV data, indicators, context
            
        Returns:
            AgentVote with decision and confidence
        """
        pass
    
    def _create_vote(self, vote: Vote, confidence: float, reasoning: str, 
                     metadata: Dict[str, Any] = None) -> AgentVote:
        """Helper to create consistent vote objects."""
        agent_vote = AgentVote(
            agent_name=self.name,
            vote=vote,
            confidence=min(max(confidence, 0.0), 1.0),  # Clamp to [0, 1]
            reasoning=reasoning,
            metadata=metadata or {}
        )
        self.last_vote = agent_vote
        return agent_vote


# =============================================================================
# AGENT 1: MARKET STRUCTURE AGENT (Wyckoff)
# =============================================================================

class MarketStructureAgent(BaseAgent):
    """
    Ancient Law: Read the footprints of smart money.
    
    Analyzes Wyckoff phases:
    - Accumulation: Smart money buying at lows
    - Distribution: Smart money selling at highs
    - Markup: Uptrend after accumulation
    - Markdown: Downtrend after distribution
    """
    
    def __init__(self):
        super().__init__("MarketStructureAgent", weight=1.2)  # Slightly higher weight
        self.lookback = 50
    
    def analyze(self, symbol: str, side: str, market_data: Dict[str, Any]) -> AgentVote:
        try:
            ohlcv = market_data.get("ohlcv")
            if ohlcv is None or len(ohlcv) < self.lookback:
                return self._create_vote(
                    Vote.ABSTAIN, 0.0, 
                    "Insufficient data for Wyckoff analysis"
                )
            
            df = pd.DataFrame(ohlcv) if not isinstance(ohlcv, pd.DataFrame) else ohlcv
            
            # Calculate Wyckoff indicators
            phase, phase_confidence = self._detect_wyckoff_phase(df)
            volume_analysis = self._analyze_volume_spread(df)
            
            # Determine vote based on phase and proposed side
            if phase == "ACCUMULATION":
                if side == "BUY":
                    return self._create_vote(
                        Vote.BUY, phase_confidence * 0.9,
                        f"Wyckoff accumulation detected. Volume confirms smart money buying.",
                        {"phase": phase, "volume_analysis": volume_analysis}
                    )
                else:
                    return self._create_vote(
                        Vote.WAIT, phase_confidence * 0.7,
                        f"Accumulation phase suggests caution on SELL entries.",
                        {"phase": phase}
                    )
            
            elif phase == "DISTRIBUTION":
                if side == "SELL":
                    return self._create_vote(
                        Vote.SELL, phase_confidence * 0.9,
                        f"Wyckoff distribution detected. Smart money exiting.",
                        {"phase": phase, "volume_analysis": volume_analysis}
                    )
                else:
                    return self._create_vote(
                        Vote.WAIT, phase_confidence * 0.7,
                        f"Distribution phase suggests caution on BUY entries.",
                        {"phase": phase}
                    )
            
            elif phase == "MARKUP":
                if side == "BUY":
                    return self._create_vote(
                        Vote.BUY, phase_confidence * 0.8,
                        f"Markup phase - trend continuation expected.",
                        {"phase": phase}
                    )
                else:
                    return self._create_vote(
                        Vote.WAIT, 0.5,
                        f"Markup phase active, SELL may be premature.",
                        {"phase": phase}
                    )
            
            elif phase == "MARKDOWN":
                if side == "SELL":
                    return self._create_vote(
                        Vote.SELL, phase_confidence * 0.8,
                        f"Markdown phase - downtrend continuation expected.",
                        {"phase": phase}
                    )
                else:
                    return self._create_vote(
                        Vote.WAIT, 0.5,
                        f"Markdown phase active, BUY may be premature.",
                        {"phase": phase}
                    )
            
            else:
                return self._create_vote(
                    Vote.WAIT, 0.4,
                    f"Unclear market structure. Phase: {phase}",
                    {"phase": phase}
                )
                
        except Exception as e:
            logger.error(f"MarketStructureAgent error: {e}")
            return self._create_vote(Vote.ABSTAIN, 0.0, f"Analysis error: {str(e)}")
    
    def _detect_wyckoff_phase(self, df: pd.DataFrame) -> Tuple[str, float]:
        """Detect current Wyckoff phase."""
        close = df['close'].values
        volume = df['volume'].values if 'volume' in df.columns else np.ones(len(close))
        
        # Price position relative to recent range
        recent_high = np.max(close[-self.lookback:])
        recent_low = np.min(close[-self.lookback:])
        current = close[-1]
        range_position = (current - recent_low) / (recent_high - recent_low + 1e-10)
        
        # Volume trend
        vol_ma = np.mean(volume[-20:])
        recent_vol = np.mean(volume[-5:])
        vol_increasing = recent_vol > vol_ma * 1.2
        
        # Price momentum
        momentum = (close[-1] - close[-20]) / (close[-20] + 1e-10)
        
        # Determine phase
        if range_position < 0.3 and vol_increasing and momentum > -0.02:
            return "ACCUMULATION", 0.75
        elif range_position > 0.7 and vol_increasing and momentum < 0.02:
            return "DISTRIBUTION", 0.75
        elif range_position > 0.5 and momentum > 0.02:
            return "MARKUP", 0.70
        elif range_position < 0.5 and momentum < -0.02:
            return "MARKDOWN", 0.70
        else:
            return "RANGING", 0.50
    
    def _analyze_volume_spread(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume-spread relationship."""
        if 'volume' not in df.columns:
            return {"available": False}
        
        close = df['close'].values
        volume = df['volume'].values
        
        # Calculate spread (high - low)
        spread = (df['high'] - df['low']).values if 'high' in df.columns else np.zeros(len(close))
        
        # Volume-spread analysis
        avg_vol = np.mean(volume[-20:])
        avg_spread = np.mean(spread[-20:])
        
        return {
            "available": True,
            "volume_trend": "increasing" if volume[-1] > avg_vol else "decreasing",
            "spread_trend": "widening" if spread[-1] > avg_spread else "narrowing"
        }


# =============================================================================
# AGENT 2: MOMENTUM AGENT
# =============================================================================

class MomentumAgent(BaseAgent):
    """
    Ancient Law: Follow the force, not the noise.
    
    Analyzes price momentum using:
    - Rate of Change (ROC)
    - RSI momentum
    - Volume confirmation
    """
    
    def __init__(self):
        super().__init__("MomentumAgent", weight=1.0)
        self.roc_period = 14
        self.rsi_period = 14
    
    def analyze(self, symbol: str, side: str, market_data: Dict[str, Any]) -> AgentVote:
        try:
            ohlcv = market_data.get("ohlcv")
            if ohlcv is None or len(ohlcv) < 30:
                return self._create_vote(
                    Vote.ABSTAIN, 0.0,
                    "Insufficient data for momentum analysis"
                )
            
            df = pd.DataFrame(ohlcv) if not isinstance(ohlcv, pd.DataFrame) else ohlcv
            close = df['close'].values
            
            # Calculate momentum indicators
            roc = self._calculate_roc(close)
            rsi = self._calculate_rsi(close)
            momentum_score = self._calculate_momentum_score(roc, rsi)
            
            proposed_vote = Vote.BUY if side == "BUY" else Vote.SELL
            
            # Strong bullish momentum
            if momentum_score > 0.6:
                if side == "BUY":
                    return self._create_vote(
                        Vote.BUY, momentum_score,
                        f"Strong bullish momentum. ROC: {roc:.2%}, RSI: {rsi:.1f}",
                        {"roc": roc, "rsi": rsi, "score": momentum_score}
                    )
                else:
                    return self._create_vote(
                        Vote.WAIT, 0.4,
                        f"Bullish momentum conflicts with SELL signal.",
                        {"roc": roc, "rsi": rsi}
                    )
            
            # Strong bearish momentum
            elif momentum_score < -0.6:
                if side == "SELL":
                    return self._create_vote(
                        Vote.SELL, abs(momentum_score),
                        f"Strong bearish momentum. ROC: {roc:.2%}, RSI: {rsi:.1f}",
                        {"roc": roc, "rsi": rsi, "score": momentum_score}
                    )
                else:
                    return self._create_vote(
                        Vote.WAIT, 0.4,
                        f"Bearish momentum conflicts with BUY signal.",
                        {"roc": roc, "rsi": rsi}
                    )
            
            # Neutral momentum
            else:
                return self._create_vote(
                    Vote.WAIT, 0.5,
                    f"Neutral momentum. Waiting for clearer signal.",
                    {"roc": roc, "rsi": rsi, "score": momentum_score}
                )
                
        except Exception as e:
            logger.error(f"MomentumAgent error: {e}")
            return self._create_vote(Vote.ABSTAIN, 0.0, f"Analysis error: {str(e)}")
    
    def _calculate_roc(self, close: np.ndarray) -> float:
        """Calculate Rate of Change."""
        if len(close) < self.roc_period + 1:
            return 0.0
        return (close[-1] - close[-self.roc_period - 1]) / (close[-self.roc_period - 1] + 1e-10)
    
    def _calculate_rsi(self, close: np.ndarray) -> float:
        """Calculate RSI."""
        if len(close) < self.rsi_period + 1:
            return 50.0
        
        deltas = np.diff(close[-self.rsi_period - 1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_momentum_score(self, roc: float, rsi: float) -> float:
        """Calculate combined momentum score (-1 to 1)."""
        # Normalize ROC to -1 to 1 range (assuming max 10% move)
        roc_normalized = np.clip(roc / 0.1, -1, 1)
        
        # Normalize RSI to -1 to 1 range (50 = neutral)
        rsi_normalized = (rsi - 50) / 50
        
        # Combined score
        return (roc_normalized * 0.6 + rsi_normalized * 0.4)


# =============================================================================
# AGENT 3: VOLATILITY & RISK AGENT
# =============================================================================

class VolatilityRiskAgent(BaseAgent):
    """
    Axelrod Discipline: Never fight in a storm.
    
    Analyzes market volatility and risk conditions:
    - ATR-based volatility assessment
    - Volatility regime detection
    - Risk-adjusted entry evaluation
    """
    
    def __init__(self):
        super().__init__("VolatilityRiskAgent", weight=1.3)  # Higher weight for safety
        self.atr_period = 14
        self.volatility_lookback = 50
    
    def analyze(self, symbol: str, side: str, market_data: Dict[str, Any]) -> AgentVote:
        try:
            ohlcv = market_data.get("ohlcv")
            if ohlcv is None or len(ohlcv) < self.volatility_lookback:
                return self._create_vote(
                    Vote.ABSTAIN, 0.0,
                    "Insufficient data for volatility analysis"
                )
            
            df = pd.DataFrame(ohlcv) if not isinstance(ohlcv, pd.DataFrame) else ohlcv
            
            # Calculate volatility metrics
            atr = self._calculate_atr(df)
            atr_percentile = self._calculate_atr_percentile(df)
            vol_regime = self._detect_volatility_regime(atr_percentile)
            
            proposed_vote = Vote.BUY if side == "BUY" else Vote.SELL
            
            # Extreme volatility - HALT ALL TRADING
            if vol_regime == "EXTREME":
                return self._create_vote(
                    Vote.WAIT, 0.95,
                    f"EXTREME VOLATILITY DETECTED. ATR at {atr_percentile:.0f}th percentile. Trading suspended.",
                    {"atr": atr, "percentile": atr_percentile, "regime": vol_regime}
                )
            
            # High volatility - proceed with caution
            elif vol_regime == "HIGH":
                return self._create_vote(
                    proposed_vote, 0.5,
                    f"High volatility ({atr_percentile:.0f}th percentile). Reduced position size recommended.",
                    {"atr": atr, "percentile": atr_percentile, "regime": vol_regime, 
                     "position_modifier": 0.5}
                )
            
            # Normal volatility - clear to proceed
            elif vol_regime == "NORMAL":
                return self._create_vote(
                    proposed_vote, 0.75,
                    f"Normal volatility conditions. Clear for standard position sizing.",
                    {"atr": atr, "percentile": atr_percentile, "regime": vol_regime}
                )
            
            # Low volatility - potentially good entries
            else:  # LOW
                return self._create_vote(
                    proposed_vote, 0.85,
                    f"Low volatility ({atr_percentile:.0f}th percentile). Favorable entry conditions.",
                    {"atr": atr, "percentile": atr_percentile, "regime": vol_regime}
                )
                
        except Exception as e:
            logger.error(f"VolatilityRiskAgent error: {e}")
            return self._create_vote(Vote.ABSTAIN, 0.0, f"Analysis error: {str(e)}")
    
    def _calculate_atr(self, df: pd.DataFrame) -> float:
        """Calculate Average True Range."""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        tr1 = high[-self.atr_period:] - low[-self.atr_period:]
        tr2 = np.abs(high[-self.atr_period:] - np.roll(close, 1)[-self.atr_period:])
        tr3 = np.abs(low[-self.atr_period:] - np.roll(close, 1)[-self.atr_period:])
        
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        return np.mean(tr)
    
    def _calculate_atr_percentile(self, df: pd.DataFrame) -> float:
        """Calculate current ATR percentile vs historical."""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calculate rolling ATR for all periods
        tr_all = []
        for i in range(self.atr_period, len(df)):
            h = high[i-self.atr_period:i]
            l = low[i-self.atr_period:i]
            c = close[i-self.atr_period:i]
            
            tr1 = h - l
            tr2 = np.abs(h - np.roll(c, 1))
            tr3 = np.abs(l - np.roll(c, 1))
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            tr_all.append(np.mean(tr))
        
        if not tr_all:
            return 50.0
        
        current_atr = tr_all[-1]
        percentile = (np.sum(np.array(tr_all) <= current_atr) / len(tr_all)) * 100
        return percentile
    
    def _detect_volatility_regime(self, percentile: float) -> str:
        """Classify volatility regime."""
        if percentile >= 95:
            return "EXTREME"
        elif percentile >= 75:
            return "HIGH"
        elif percentile >= 25:
            return "NORMAL"
        else:
            return "LOW"


# =============================================================================
# AGENT 4: MACRO SENTIMENT AGENT
# =============================================================================

class MacroSentimentAgent(BaseAgent):
    """
    Ancient Law: Know the tide before sailing.
    
    Analyzes broader market sentiment:
    - Market regime (from Intelligence module if available)
    - Price relative to moving averages
    - Overall market bias
    """
    
    def __init__(self):
        super().__init__("MacroSentimentAgent", weight=0.9)
        self.ma_periods = [50, 200]
    
    def analyze(self, symbol: str, side: str, market_data: Dict[str, Any]) -> AgentVote:
        try:
            ohlcv = market_data.get("ohlcv")
            regime = market_data.get("regime")  # From Intelligence module
            
            if ohlcv is None or len(ohlcv) < 200:
                # Use regime if available, otherwise abstain
                if regime:
                    return self._analyze_from_regime(regime, side)
                return self._create_vote(
                    Vote.ABSTAIN, 0.0,
                    "Insufficient data for macro analysis"
                )
            
            df = pd.DataFrame(ohlcv) if not isinstance(ohlcv, pd.DataFrame) else ohlcv
            close = df['close'].values
            
            # Calculate moving averages
            ma50 = np.mean(close[-50:])
            ma200 = np.mean(close[-200:])
            current = close[-1]
            
            # Determine macro trend
            above_ma50 = current > ma50
            above_ma200 = current > ma200
            ma50_above_ma200 = ma50 > ma200
            
            proposed_vote = Vote.BUY if side == "BUY" else Vote.SELL
            
            # Strong bullish macro
            if above_ma50 and above_ma200 and ma50_above_ma200:
                if side == "BUY":
                    return self._create_vote(
                        Vote.BUY, 0.85,
                        f"Bullish macro: Price above MA50/MA200, golden cross active.",
                        {"above_ma50": True, "above_ma200": True, "golden_cross": True}
                    )
                else:
                    return self._create_vote(
                        Vote.WAIT, 0.4,
                        f"Bullish macro environment conflicts with SELL signal.",
                        {"macro_bias": "BULLISH"}
                    )
            
            # Strong bearish macro
            elif not above_ma50 and not above_ma200 and not ma50_above_ma200:
                if side == "SELL":
                    return self._create_vote(
                        Vote.SELL, 0.85,
                        f"Bearish macro: Price below MA50/MA200, death cross active.",
                        {"above_ma50": False, "above_ma200": False, "death_cross": True}
                    )
                else:
                    return self._create_vote(
                        Vote.WAIT, 0.4,
                        f"Bearish macro environment conflicts with BUY signal.",
                        {"macro_bias": "BEARISH"}
                    )
            
            # Mixed signals
            else:
                return self._create_vote(
                    proposed_vote, 0.55,
                    f"Mixed macro signals. No clear directional bias.",
                    {"above_ma50": above_ma50, "above_ma200": above_ma200}
                )
                
        except Exception as e:
            logger.error(f"MacroSentimentAgent error: {e}")
            return self._create_vote(Vote.ABSTAIN, 0.0, f"Analysis error: {str(e)}")
    
    def _analyze_from_regime(self, regime: Dict[str, Any], side: str) -> AgentVote:
        """Analyze using regime data from Intelligence module."""
        regime_type = regime.get("regime", "UNCERTAIN")
        confidence = regime.get("confidence", 0.5)
        
        if regime_type == "TRENDING_UP":
            if side == "BUY":
                return self._create_vote(Vote.BUY, confidence, f"Uptrend regime detected.")
            else:
                return self._create_vote(Vote.WAIT, 0.4, f"Uptrend conflicts with SELL.")
        elif regime_type == "TRENDING_DOWN":
            if side == "SELL":
                return self._create_vote(Vote.SELL, confidence, f"Downtrend regime detected.")
            else:
                return self._create_vote(Vote.WAIT, 0.4, f"Downtrend conflicts with BUY.")
        else:
            return self._create_vote(Vote.WAIT, 0.5, f"Unclear regime: {regime_type}")


# =============================================================================
# AGENT 5: EXECUTION SAFETY AGENT
# =============================================================================

class ExecutionSafetyAgent(BaseAgent):
    """
    Netflix Doctrine: Assume everything will fail.
    
    Pre-trade safety validation:
    - Spread check
    - Liquidity assessment
    - Time-of-day validation
    - Circuit breaker status
    """
    
    def __init__(self):
        super().__init__("ExecutionSafetyAgent", weight=1.5)  # Highest weight - safety first
        self.max_spread_pct = 0.1  # 0.1% max spread
    
    def analyze(self, symbol: str, side: str, market_data: Dict[str, Any]) -> AgentVote:
        try:
            # Check circuit breaker status
            circuit_status = market_data.get("circuit_breaker_status", {})
            if circuit_status.get("any_open", False):
                return self._create_vote(
                    Vote.WAIT, 0.99,
                    f"CIRCUIT BREAKER ACTIVE. Trading halted for safety.",
                    {"circuit_breaker": True, "details": circuit_status}
                )
            
            # Check spread
            bid = market_data.get("bid")
            ask = market_data.get("ask")
            if bid and ask:
                spread_pct = (ask - bid) / bid * 100
                if spread_pct > self.max_spread_pct:
                    return self._create_vote(
                        Vote.WAIT, 0.85,
                        f"Spread too wide: {spread_pct:.3f}% (max: {self.max_spread_pct}%)",
                        {"spread_pct": spread_pct}
                    )
            
            # Check trading hours (if provided)
            trading_session = market_data.get("trading_session", {})
            if trading_session.get("is_closed", False):
                return self._create_vote(
                    Vote.WAIT, 0.90,
                    f"Market closed or low liquidity session.",
                    {"session": trading_session}
                )
            
            # Check for extreme market conditions
            anomaly = market_data.get("anomaly", {})
            if anomaly.get("is_anomaly", False):
                severity = anomaly.get("severity", 0)
                if severity > 0.7:
                    return self._create_vote(
                        Vote.WAIT, 0.95,
                        f"Market anomaly detected: {anomaly.get('anomaly_type')}",
                        {"anomaly": anomaly}
                    )
            
            # Check recent execution failures
            recent_failures = market_data.get("recent_execution_failures", 0)
            if recent_failures >= 3:
                return self._create_vote(
                    Vote.WAIT, 0.80,
                    f"Multiple recent execution failures ({recent_failures}). Pausing for stability.",
                    {"failures": recent_failures}
                )
            
            # All safety checks passed
            proposed_vote = Vote.BUY if side == "BUY" else Vote.SELL
            return self._create_vote(
                proposed_vote, 0.90,
                f"All safety checks passed. Clear for execution.",
                {"checks_passed": ["circuit_breaker", "spread", "session", "anomaly", "failures"]}
            )
            
        except Exception as e:
            logger.error(f"ExecutionSafetyAgent error: {e}")
            return self._create_vote(
                Vote.WAIT, 0.70,
                f"Safety check error - defaulting to WAIT: {str(e)}"
            )


# =============================================================================
# AGENT COUNCIL
# =============================================================================

class AgentCouncil:
    """
    The Council of Five: No trade without quorum.
    
    Orchestrates all agents and enforces consensus requirements.
    
    Quorum Rules:
    - 3/5 agents must agree on direction
    - Weighted voting based on agent expertise
    - Disagreement reduces position size
    - WAIT votes count against the trade
    """
    
    def __init__(self, quorum_threshold: float = 0.6):
        """
        Args:
            quorum_threshold: Minimum weighted agreement needed (default 60%)
        """
        self.quorum_threshold = quorum_threshold
        self.agents = [
            MarketStructureAgent(),
            MomentumAgent(),
            VolatilityRiskAgent(),
            MacroSentimentAgent(),
            ExecutionSafetyAgent()
        ]
        self.last_decision: Optional[CouncilDecision] = None
        
        logger.info(f"Agent Council initialized with {len(self.agents)} agents")
    
    def deliberate(self, symbol: str, side: str, market_data: Dict[str, Any]) -> CouncilDecision:
        """
        Gather votes from all agents and make council decision.
        
        Args:
            symbol: Trading symbol
            side: Proposed direction ("BUY" or "SELL")
            market_data: Market context for analysis
            
        Returns:
            CouncilDecision with quorum status and final vote
        """
        logger.info(f"Council deliberating: {symbol} {side}")
        
        # Collect votes from all agents
        votes: List[AgentVote] = []
        for agent in self.agents:
            vote = agent.analyze(symbol, side, market_data)
            votes.append(vote)
            logger.debug(f"  {agent.name}: {vote.vote.value} ({vote.confidence:.2f})")
        
        # Calculate weighted consensus
        proposed_vote = Vote.BUY if side == "BUY" else Vote.SELL
        decision = self._calculate_consensus(votes, proposed_vote)
        
        self.last_decision = decision
        
        # Log decision
        if decision.quorum_reached:
            logger.info(f"Council APPROVED: {decision.final_decision.value} "
                       f"(confidence: {decision.consensus_confidence:.2f})")
        else:
            logger.warning(f"Council REJECTED: Quorum not reached. "
                          f"Summary: {decision.vote_summary}")
        
        return decision
    
    def _calculate_consensus(self, votes: List[AgentVote], 
                            proposed_vote: Vote) -> CouncilDecision:
        """Calculate weighted consensus from agent votes."""
        
        # Count votes by type
        vote_counts = {Vote.BUY: 0, Vote.SELL: 0, Vote.WAIT: 0, Vote.ABSTAIN: 0}
        weighted_agreement = 0.0
        total_weight = 0.0
        
        for i, vote in enumerate(votes):
            vote_counts[vote.vote] += 1
            agent_weight = self.agents[i].weight
            total_weight += agent_weight
            
            # Agreement with proposed direction
            if vote.vote == proposed_vote:
                weighted_agreement += agent_weight * vote.confidence
        
        # Calculate consensus percentage
        consensus_pct = weighted_agreement / total_weight if total_weight > 0 else 0
        
        # Determine if quorum reached
        quorum_reached = consensus_pct >= self.quorum_threshold
        
        # Count agreeing agents (not just weighted)
        agreeing_count = vote_counts[proposed_vote]
        
        # Also require at least 3 agents to agree (not just weighted threshold)
        if agreeing_count < 3:
            quorum_reached = False
        
        # Position size modifier based on consensus strength
        if quorum_reached:
            if consensus_pct >= 0.8:
                position_modifier = 1.0  # Full position
            elif consensus_pct >= 0.7:
                position_modifier = 0.75  # 75% position
            else:
                position_modifier = 0.5  # 50% position (barely passed)
        else:
            position_modifier = 0.0  # No trade
        
        # Check for high-weight WAIT votes (safety override)
        safety_agent_wait = any(
            v.vote == Vote.WAIT and self.agents[i].name == "ExecutionSafetyAgent"
            for i, v in enumerate(votes)
        )
        if safety_agent_wait:
            # Safety agent has veto power
            quorum_reached = False
            position_modifier = 0.0
        
        # Build decision
        vote_summary = {k.value: v for k, v in vote_counts.items()}
        
        # Generate reasoning
        if quorum_reached:
            reasoning = f"Quorum achieved: {agreeing_count}/5 agents agree on {proposed_vote.value}. " \
                       f"Weighted consensus: {consensus_pct:.1%}"
        else:
            if safety_agent_wait:
                reasoning = "Safety Agent vetoed trade. Execution safety concerns."
            elif agreeing_count < 3:
                reasoning = f"Quorum failed: Only {agreeing_count}/5 agents agree. Minimum 3 required."
            else:
                reasoning = f"Weighted consensus too low: {consensus_pct:.1%} < {self.quorum_threshold:.1%}"
        
        return CouncilDecision(
            quorum_reached=quorum_reached,
            final_decision=proposed_vote if quorum_reached else Vote.WAIT,
            consensus_confidence=consensus_pct,
            votes=votes,
            vote_summary=vote_summary,
            reasoning=reasoning,
            position_size_modifier=position_modifier
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get council status for monitoring."""
        return {
            "agents": [
                {
                    "name": agent.name,
                    "weight": agent.weight,
                    "last_vote": agent.last_vote.vote.value if agent.last_vote else None,
                    "last_confidence": agent.last_vote.confidence if agent.last_vote else None
                }
                for agent in self.agents
            ],
            "quorum_threshold": self.quorum_threshold,
            "last_decision": {
                "quorum_reached": self.last_decision.quorum_reached,
                "decision": self.last_decision.final_decision.value,
                "confidence": self.last_decision.consensus_confidence,
                "summary": self.last_decision.vote_summary
            } if self.last_decision else None
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global council instance
_council: Optional[AgentCouncil] = None


def get_council() -> AgentCouncil:
    """Get or create global council instance."""
    global _council
    if _council is None:
        _council = AgentCouncil()
    return _council


def require_quorum(symbol: str, side: str, market_data: Dict[str, Any]) -> CouncilDecision:
    """
    Convenience function to get council decision.
    
    Usage:
        decision = require_quorum("EURUSD", "BUY", market_data)
        if decision.quorum_reached:
            # Execute trade with decision.position_size_modifier
        else:
            # Log rejection reason
    """
    return get_council().deliberate(symbol, side, market_data)
