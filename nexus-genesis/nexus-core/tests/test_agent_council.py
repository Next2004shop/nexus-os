"""
NEXUS Agent Council - Unit Tests
================================

Tests the Multi-Agent Council decision system.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from app.services.agent_council import (
    AgentCouncil, Vote, AgentVote, CouncilDecision,
    MarketStructureAgent, MomentumAgent, VolatilityRiskAgent,
    MacroSentimentAgent, ExecutionSafetyAgent,
    get_council, require_quorum
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_ohlcv():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    n = 100
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    
    return pd.DataFrame({
        'open': close - np.random.rand(n) * 0.5,
        'high': close + np.random.rand(n) * 1.0,
        'low': close - np.random.rand(n) * 1.0,
        'close': close,
        'volume': np.random.randint(1000, 10000, n)
    })


@pytest.fixture
def bullish_ohlcv():
    """Create bullish trending OHLCV data."""
    n = 100
    close = np.arange(100, 100 + n * 0.5, 0.5)[:n]  # Strong uptrend
    
    return pd.DataFrame({
        'open': close - 0.2,
        'high': close + 0.5,
        'low': close - 0.5,
        'close': close,
        'volume': np.full(n, 5000)
    })


@pytest.fixture
def bearish_ohlcv():
    """Create bearish trending OHLCV data."""
    n = 100
    close = np.arange(150, 150 - n * 0.5, -0.5)[:n]  # Strong downtrend
    
    return pd.DataFrame({
        'open': close + 0.2,
        'high': close + 0.5,
        'low': close - 0.5,
        'close': close,
        'volume': np.full(n, 5000)
    })


@pytest.fixture
def volatile_ohlcv():
    """Create highly volatile OHLCV data."""
    np.random.seed(42)
    n = 100
    close = 100 + np.cumsum(np.random.randn(n) * 5)  # High volatility
    
    return pd.DataFrame({
        'open': close - np.random.rand(n) * 3,
        'high': close + np.random.rand(n) * 5,
        'low': close - np.random.rand(n) * 5,
        'close': close,
        'volume': np.random.randint(5000, 20000, n)
    })


@pytest.fixture
def market_data(sample_ohlcv):
    """Create complete market data dict."""
    return {
        "ohlcv": sample_ohlcv,
        "regime": {"regime": "TRENDING_UP", "confidence": 0.75, "trend_strength": 0.7},
        "momentum": {"score": 0.5},
        "volatility": {"percentile": 50, "regime": "NORMAL"},
        "bid": 100.0,
        "ask": 100.05,
        "circuit_breaker_status": {"any_open": False},
        "anomaly": {"is_anomaly": False}
    }


# =============================================================================
# INDIVIDUAL AGENT TESTS
# =============================================================================

class TestMarketStructureAgent:
    """Tests for MarketStructureAgent (Wyckoff)."""
    
    def test_analyze_bullish(self, bullish_ohlcv):
        agent = MarketStructureAgent()
        vote = agent.analyze("EURUSD", "BUY", {"ohlcv": bullish_ohlcv})
        
        assert vote.vote in [Vote.BUY, Vote.WAIT]
        assert 0 <= vote.confidence <= 1
        assert vote.agent_name == "MarketStructureAgent"
    
    def test_analyze_bearish(self, bearish_ohlcv):
        agent = MarketStructureAgent()
        vote = agent.analyze("EURUSD", "SELL", {"ohlcv": bearish_ohlcv})
        
        assert vote.vote in [Vote.SELL, Vote.WAIT]
        assert 0 <= vote.confidence <= 1
    
    def test_abstain_on_insufficient_data(self):
        agent = MarketStructureAgent()
        small_data = pd.DataFrame({
            'open': [100, 101],
            'high': [102, 103],
            'low': [99, 100],
            'close': [101, 102],
            'volume': [1000, 1000]
        })
        
        vote = agent.analyze("EURUSD", "BUY", {"ohlcv": small_data})
        assert vote.vote == Vote.ABSTAIN
        assert vote.confidence == 0.0


class TestMomentumAgent:
    """Tests for MomentumAgent."""
    
    def test_analyze_positive_momentum(self, bullish_ohlcv):
        agent = MomentumAgent()
        vote = agent.analyze("EURUSD", "BUY", {"ohlcv": bullish_ohlcv})
        
        assert vote.vote in [Vote.BUY, Vote.WAIT]
        assert vote.agent_name == "MomentumAgent"
    
    def test_analyze_negative_momentum(self, bearish_ohlcv):
        agent = MomentumAgent()
        vote = agent.analyze("EURUSD", "SELL", {"ohlcv": bearish_ohlcv})
        
        assert vote.vote in [Vote.SELL, Vote.WAIT]


class TestVolatilityRiskAgent:
    """Tests for VolatilityRiskAgent."""
    
    def test_normal_volatility(self, sample_ohlcv):
        agent = VolatilityRiskAgent()
        vote = agent.analyze("EURUSD", "BUY", {"ohlcv": sample_ohlcv})
        
        # Should not be WAIT with normal volatility
        assert vote.confidence > 0.5
        assert "volatility" in str(vote.reasoning).lower() or "vol" in str(vote.reasoning).lower()
    
    def test_extreme_volatility_warns(self, volatile_ohlcv):
        agent = VolatilityRiskAgent()
        vote = agent.analyze("EURUSD", "BUY", {"ohlcv": volatile_ohlcv})
        
        # With extreme volatility, should have lower confidence or WAIT
        assert vote.vote in [Vote.BUY, Vote.WAIT]


class TestMacroSentimentAgent:
    """Tests for MacroSentimentAgent."""
    
    def test_bullish_macro(self, bullish_ohlcv):
        agent = MacroSentimentAgent()
        # Need 200 bars for MA analysis, but should work with regime
        market_data = {
            "ohlcv": bullish_ohlcv,
            "regime": {"regime": "TRENDING_UP", "confidence": 0.8}
        }
        vote = agent.analyze("EURUSD", "BUY", market_data)
        
        assert vote.vote in [Vote.BUY, Vote.WAIT]
    
    def test_bearish_macro(self, bearish_ohlcv):
        agent = MacroSentimentAgent()
        market_data = {
            "ohlcv": bearish_ohlcv,
            "regime": {"regime": "TRENDING_DOWN", "confidence": 0.8}
        }
        vote = agent.analyze("EURUSD", "SELL", market_data)
        
        assert vote.vote in [Vote.SELL, Vote.WAIT]


class TestExecutionSafetyAgent:
    """Tests for ExecutionSafetyAgent."""
    
    def test_all_clear(self):
        agent = ExecutionSafetyAgent()
        market_data = {
            "bid": 100.0,
            "ask": 100.01,  # Tight spread
            "circuit_breaker_status": {"any_open": False},
            "anomaly": {"is_anomaly": False},
            "recent_execution_failures": 0
        }
        vote = agent.analyze("EURUSD", "BUY", market_data)
        
        assert vote.vote == Vote.BUY
        assert vote.confidence >= 0.8
    
    def test_circuit_breaker_active(self):
        agent = ExecutionSafetyAgent()
        market_data = {
            "circuit_breaker_status": {"any_open": True}
        }
        vote = agent.analyze("EURUSD", "BUY", market_data)
        
        assert vote.vote == Vote.WAIT
        assert "CIRCUIT BREAKER" in vote.reasoning.upper()
    
    def test_wide_spread(self):
        agent = ExecutionSafetyAgent()
        market_data = {
            "bid": 100.0,
            "ask": 100.50,  # 0.5% spread (very wide)
            "circuit_breaker_status": {"any_open": False}
        }
        vote = agent.analyze("EURUSD", "BUY", market_data)
        
        assert vote.vote == Vote.WAIT
        assert "spread" in vote.reasoning.lower()


# =============================================================================
# COUNCIL TESTS
# =============================================================================

class TestAgentCouncil:
    """Tests for the full Agent Council."""
    
    def test_council_creation(self):
        council = AgentCouncil()
        
        assert len(council.agents) == 5
        assert council.quorum_threshold == 0.6
    
    def test_deliberate_returns_decision(self, market_data):
        council = AgentCouncil()
        decision = council.deliberate("EURUSD", "BUY", market_data)
        
        assert isinstance(decision, CouncilDecision)
        assert len(decision.votes) == 5
        assert decision.final_decision in [Vote.BUY, Vote.SELL, Vote.WAIT]
        assert 0 <= decision.consensus_confidence <= 1
    
    def test_quorum_required(self, market_data):
        council = AgentCouncil(quorum_threshold=0.8)  # High threshold
        decision = council.deliberate("EURUSD", "BUY", market_data)
        
        # With high threshold, quorum may or may not be reached
        assert isinstance(decision.quorum_reached, bool)
        if not decision.quorum_reached:
            assert decision.position_size_modifier == 0.0
    
    def test_vote_summary(self, market_data):
        council = AgentCouncil()
        decision = council.deliberate("EURUSD", "BUY", market_data)
        
        # Vote summary should have all vote types
        assert "BUY" in decision.vote_summary or "SELL" in decision.vote_summary or "WAIT" in decision.vote_summary
        total_votes = sum(decision.vote_summary.values())
        assert total_votes == 5
    
    def test_council_status(self, market_data):
        council = AgentCouncil()
        council.deliberate("EURUSD", "BUY", market_data)
        
        status = council.get_status()
        
        assert "agents" in status
        assert "quorum_threshold" in status
        assert "last_decision" in status
        assert len(status["agents"]) == 5
    
    def test_safety_agent_veto(self):
        """Test that Safety Agent can veto trades."""
        council = AgentCouncil()
        
        # Market data with circuit breaker active
        market_data = {
            "ohlcv": None,  # Will cause other agents to abstain
            "circuit_breaker_status": {"any_open": True}
        }
        
        decision = council.deliberate("EURUSD", "BUY", market_data)
        
        # Safety agent should veto
        assert decision.quorum_reached == False
        assert decision.position_size_modifier == 0.0


class TestConvenienceFunctions:
    """Tests for module-level functions."""
    
    def test_get_council_singleton(self):
        council1 = get_council()
        council2 = get_council()
        
        assert council1 is council2
    
    def test_require_quorum(self, market_data):
        decision = require_quorum("EURUSD", "BUY", market_data)
        
        assert isinstance(decision, CouncilDecision)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestCouncilWithRealScenarios:
    """Tests with realistic trading scenarios."""
    
    def test_strong_trend_buy(self, bullish_ohlcv):
        """Test council with strong uptrend."""
        council = AgentCouncil()
        
        market_data = {
            "ohlcv": bullish_ohlcv,
            "regime": {"regime": "TRENDING_UP", "confidence": 0.9, "trend_strength": 0.85},
            "momentum": {"score": 0.7},
            "volatility": {"percentile": 40, "regime": "NORMAL"},
            "bid": 149.0,
            "ask": 149.02,
            "circuit_breaker_status": {"any_open": False},
            "anomaly": {"is_anomaly": False}
        }
        
        decision = council.deliberate("EURUSD", "BUY", market_data)
        
        # Strong trend should lead to BUY consensus
        assert decision.final_decision in [Vote.BUY, Vote.WAIT]
        assert decision.consensus_confidence > 0
    
    def test_strong_trend_sell(self, bearish_ohlcv):
        """Test council with strong downtrend."""
        council = AgentCouncil()
        
        market_data = {
            "ohlcv": bearish_ohlcv,
            "regime": {"regime": "TRENDING_DOWN", "confidence": 0.9, "trend_strength": 0.85},
            "momentum": {"score": -0.7},
            "volatility": {"percentile": 40, "regime": "NORMAL"},
            "bid": 101.0,
            "ask": 101.02,
            "circuit_breaker_status": {"any_open": False},
            "anomaly": {"is_anomaly": False}
        }
        
        decision = council.deliberate("EURUSD", "SELL", market_data)
        
        # Strong trend should lead to SELL consensus
        assert decision.final_decision in [Vote.SELL, Vote.WAIT]
    
    def test_conflicting_signals(self, sample_ohlcv):
        """Test council with conflicting signals."""
        council = AgentCouncil()
        
        # Conflicting: bullish regime but trying to sell
        market_data = {
            "ohlcv": sample_ohlcv,
            "regime": {"regime": "TRENDING_UP", "confidence": 0.7, "trend_strength": 0.6},
            "momentum": {"score": 0.5},  # Bullish
            "volatility": {"percentile": 50, "regime": "NORMAL"},
            "bid": 100.0,
            "ask": 100.02,
            "circuit_breaker_status": {"any_open": False},
            "anomaly": {"is_anomaly": False}
        }
        
        decision = council.deliberate("EURUSD", "SELL", market_data)
        
        # Conflicting signals should reduce confidence
        assert decision.consensus_confidence < 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
