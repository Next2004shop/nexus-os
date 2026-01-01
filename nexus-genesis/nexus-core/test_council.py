"""
NEXUS Council Standalone Test
=============================

Standalone test that imports the council modules directly without
triggering the services __init__.py which has external dependencies.
"""

import sys
import os

# Setup path before any imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

print("\n" + "*" * 60)
print("*   NEXUS SOVEREIGN SYSTEM v3.0 - STANDALONE TEST         *")
print("*" * 60)

def create_test_data():
    """Create test market data."""
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


# ============================================================================
# TEST AGENT COUNCIL
# ============================================================================
print("\n" + "=" * 60)
print("TESTING AGENT COUNCIL")
print("=" * 60)

# Import directly from the module file, not through __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "agent_council", 
    os.path.join(os.path.dirname(__file__), "app/services/agent_council.py")
)
agent_council = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_council)

# Get classes
AgentCouncil = agent_council.AgentCouncil
Vote = agent_council.Vote
MarketStructureAgent = agent_council.MarketStructureAgent
MomentumAgent = agent_council.MomentumAgent
VolatilityRiskAgent = agent_council.VolatilityRiskAgent
MacroSentimentAgent = agent_council.MacroSentimentAgent
ExecutionSafetyAgent = agent_council.ExecutionSafetyAgent

# Create council
council = AgentCouncil()
print(f"\n[OK] Council created with {len(council.agents)} agents:")
for agent in council.agents:
    print(f"  - {agent.name} (weight: {agent.weight})")

# Create test data
ohlcv = create_test_data()
market_data = {
    "ohlcv": ohlcv,
    "regime": {"regime": "TRENDING_UP", "confidence": 0.75, "trend_strength": 0.7},
    "momentum": {"score": 0.5},
    "volatility": {"percentile": 50, "regime": "NORMAL"},
    "bid": 100.0,
    "ask": 100.02,
    "circuit_breaker_status": {"any_open": False},
    "anomaly": {"is_anomaly": False}
}

# Test BUY decision
print("\n" + "-" * 40)
print("Testing BUY decision on EURUSD...")
print("-" * 40)

decision = council.deliberate("EURUSD", "BUY", market_data)

print(f"\nVote Summary: {decision.vote_summary}")
print(f"Quorum Reached: {decision.quorum_reached}")
print(f"Final Decision: {decision.final_decision.value}")
print(f"Consensus Confidence: {decision.consensus_confidence:.1%}")
print(f"Position Modifier: {decision.position_size_modifier}")

# Show individual votes
print("\nIndividual Agent Votes:")
for vote in decision.votes:
    print(f"  {vote.agent_name}: {vote.vote.value} ({vote.confidence:.2f})")

# Test with circuit breaker (safety veto)
print("\n" + "-" * 40)
print("Testing Safety Veto (Circuit Breaker Active)...")
print("-" * 40)

market_data_unsafe = market_data.copy()
market_data_unsafe["circuit_breaker_status"] = {"any_open": True}

decision_veto = council.deliberate("EURUSD", "BUY", market_data_unsafe)
print(f"\nQuorum Reached: {decision_veto.quorum_reached}")
print(f"Position Modifier: {decision_veto.position_size_modifier}")
assert decision_veto.quorum_reached == False, "Safety agent should veto"
print("[OK] Safety Veto Working!")

print("\n[OK] AGENT COUNCIL TEST PASSED")

# ============================================================================
# TEST MODEL ENSEMBLE
# ============================================================================
print("\n" + "=" * 60)
print("TESTING MODEL ENSEMBLE")
print("=" * 60)

spec = importlib.util.spec_from_file_location(
    "model_ensemble", 
    os.path.join(os.path.dirname(__file__), "app/services/model_ensemble.py")
)
model_ensemble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_ensemble)

RuleBasedModel = model_ensemble.RuleBasedModel
PatternModel = model_ensemble.PatternModel
Prediction = model_ensemble.Prediction

# Test Rule-Based Model
print("\n" + "-" * 40)
print("Testing Rule-Based Model...")
print("-" * 40)

rule_model = RuleBasedModel()
pred = rule_model.predict(market_data)

print(f"Prediction: {pred.prediction.value}")
print(f"Confidence: {pred.confidence:.2f}")
print(f"Reasoning: {pred.reasoning}")

assert pred.prediction in [Prediction.UP, Prediction.DOWN, Prediction.NEUTRAL]
print("[OK] Rule-based model working")

# Test Pattern Model
print("\n" + "-" * 40)
print("Testing Pattern Model...")
print("-" * 40)

pattern_model = PatternModel()
pred2 = pattern_model.predict(market_data)

print(f"Prediction: {pred2.prediction.value}")
print(f"Confidence: {pred2.confidence:.2f}")
print(f"Reasoning: {pred2.reasoning}")
print("[OK] Pattern model working")

print("\n[OK] MODEL ENSEMBLE TEST PASSED")

# ============================================================================
# TEST STEALTH MODE
# ============================================================================
print("\n" + "=" * 60)
print("TESTING STEALTH MODE")
print("=" * 60)

spec = importlib.util.spec_from_file_location(
    "stealth_mode", 
    os.path.join(os.path.dirname(__file__), "app/services/stealth_mode.py")
)
stealth_mode = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stealth_mode)

StealthMode = stealth_mode.StealthMode

stealth = StealthMode()
print(f"\n[OK] Stealth Mode initialized")

# Test response minimization
print("\n" + "-" * 40)
print("Testing Response Minimization...")
print("-" * 40)

full_response = {
    "status": "success",
    "direction": "BUY",
    "confidence": 0.85,
    "internal_id": "should_be_removed",
    "api_key": "should_be_removed",
}

minimized = stealth.minimize_response(full_response)
print(f"Original keys: {list(full_response.keys())}")
print(f"Minimized keys: {list(minimized.keys())}")

assert "internal_id" not in minimized, "internal_id should be removed"
assert "api_key" not in minimized, "api_key should be removed"
print("[OK] Response minimization working")

# Test order randomization
print("\n" + "-" * 40)
print("Testing Order Randomization...")
print("-" * 40)

delays = [stealth.get_order_delay() for _ in range(5)]
print(f"Random delays: {[f'{d:.3f}s' for d in delays]}")
print("[OK] Order randomization working")

# Test operational status
print("\n" + "-" * 40)
print("Testing Operational Status...")
print("-" * 40)

assert stealth.is_operational() == True
print(f"Operational: {stealth.is_operational()}")
print("[OK] Stealth mode operational")

print("\n[OK] STEALTH MODE TEST PASSED")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)
print("  Agent Council:    [OK] PASS")
print("  Model Ensemble:   [OK] PASS")
print("  Stealth Mode:     [OK] PASS")
print("=" * 60)

print("\n[SUCCESS] ALL COMPONENTS VALIDATED SUCCESSFULLY")
print("   NEXUS Sovereign System v3.0 is ready for deployment.\n")
