"""
NEXUS Model Ensemble - Voting AI System
========================================

Netflix Doctrine: Multiple models vote, no single brain rules.

Implements ensemble voting for AI predictions:
1. Primary: Gemini Pro for regime detection
2. Secondary: Rule-based system for signal validation
3. Fallback: Historical pattern matching

If models disagree → reduce position size
If models conflict strongly → HALT trading
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("nexus.model_ensemble")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Prediction(Enum):
    """Model prediction types."""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"
    ERROR = "ERROR"


@dataclass
class ModelPrediction:
    """Individual model's prediction."""
    model_name: str
    prediction: Prediction
    confidence: float  # 0.0 to 1.0
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EnsembleDecision:
    """Final ensemble decision after voting."""
    final_prediction: Prediction
    aggregated_confidence: float
    agreement_score: float  # How much models agree (0-1)
    predictions: List[ModelPrediction]
    position_modifier: float = 1.0  # Reduce if low agreement
    should_halt: bool = False
    reasoning: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =============================================================================
# BASE MODEL CLASS
# =============================================================================

class BaseModel(ABC):
    """Abstract base for ensemble models."""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.is_healthy = True
        self.consecutive_errors = 0
        self.max_errors = 3
    
    @abstractmethod
    def predict(self, market_data: Dict[str, Any]) -> ModelPrediction:
        """Generate prediction from market data."""
        pass
    
    def mark_error(self):
        """Mark model as having an error."""
        self.consecutive_errors += 1
        if self.consecutive_errors >= self.max_errors:
            self.is_healthy = False
            logger.warning(f"Model {self.name} marked unhealthy after {self.consecutive_errors} errors")
    
    def mark_success(self):
        """Mark successful prediction."""
        self.consecutive_errors = 0
        self.is_healthy = True


# =============================================================================
# MODEL 1: VERTEX AI (GEMINI PRO)
# =============================================================================

class GeminiModel(BaseModel):
    """
    Primary AI model using Vertex AI Gemini Pro.
    
    Analyzes market regime and provides directional prediction.
    """
    
    def __init__(self):
        super().__init__("GeminiPro", weight=1.5)  # Highest weight
        self._initialized = False
    
    def _ensure_init(self):
        """Lazy initialization of Vertex AI."""
        if self._initialized:
            return
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project="nexus-dyron-777", location="us-central1")
            self._model = GenerativeModel("gemini-1.5-pro")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.is_healthy = False
    
    def predict(self, market_data: Dict[str, Any]) -> ModelPrediction:
        import time
        start = time.time()
        
        try:
            self._ensure_init()
            if not self._initialized:
                return ModelPrediction(
                    model_name=self.name,
                    prediction=Prediction.ERROR,
                    confidence=0.0,
                    reasoning="Vertex AI not initialized"
                )
            
            # Extract key metrics for prompt
            regime = market_data.get("regime", {})
            momentum = market_data.get("momentum", {})
            volatility = market_data.get("volatility", {})
            
            # Create analysis prompt
            prompt = f"""Analyze this market data and predict direction:
            
Regime: {regime.get('regime', 'UNKNOWN')}
Trend Strength: {regime.get('trend_strength', 0):.2f}
Volatility Percentile: {volatility.get('percentile', 50):.0f}
Momentum Score: {momentum.get('score', 0):.2f}

Respond with ONLY one of: UP, DOWN, or NEUTRAL
Then on the next line, confidence as decimal (0.0-1.0)
Then one line of reasoning."""

            response = self._model.generate_content(prompt)
            
            # Parse response
            lines = response.text.strip().split('\n')
            if len(lines) >= 2:
                direction = lines[0].strip().upper()
                confidence = float(lines[1].strip())
                reasoning = lines[2] if len(lines) > 2 else "AI prediction"
                
                prediction = Prediction.NEUTRAL
                if "UP" in direction:
                    prediction = Prediction.UP
                elif "DOWN" in direction:
                    prediction = Prediction.DOWN
                
                self.mark_success()
                return ModelPrediction(
                    model_name=self.name,
                    prediction=prediction,
                    confidence=min(max(confidence, 0.0), 1.0),
                    reasoning=reasoning,
                    latency_ms=(time.time() - start) * 1000
                )
            else:
                raise ValueError("Invalid response format")
                
        except Exception as e:
            self.mark_error()
            logger.error(f"Gemini prediction error: {e}")
            return ModelPrediction(
                model_name=self.name,
                prediction=Prediction.ERROR,
                confidence=0.0,
                reasoning=f"Prediction error: {str(e)}",
                latency_ms=(time.time() - start) * 1000
            )


# =============================================================================
# MODEL 2: RULE-BASED SYSTEM
# =============================================================================

class RuleBasedModel(BaseModel):
    """
    Secondary model using classical technical rules.
    
    Provides a non-AI baseline for comparison.
    """
    
    def __init__(self):
        super().__init__("RuleBased", weight=1.0)
    
    def predict(self, market_data: Dict[str, Any]) -> ModelPrediction:
        import time
        start = time.time()
        
        try:
            # Get indicators from market data
            regime = market_data.get("regime", {})
            momentum = market_data.get("momentum", {})
            volatility = market_data.get("volatility", {})
            
            # Scoring system
            score = 0.0
            reasons = []
            
            # Rule 1: Regime direction
            regime_type = regime.get("regime", "UNCERTAIN")
            if regime_type == "TRENDING_UP":
                score += 0.4
                reasons.append("Uptrend regime")
            elif regime_type == "TRENDING_DOWN":
                score -= 0.4
                reasons.append("Downtrend regime")
            
            # Rule 2: Momentum
            mom_score = momentum.get("score", 0)
            if mom_score > 0.3:
                score += 0.3
                reasons.append(f"Positive momentum ({mom_score:.2f})")
            elif mom_score < -0.3:
                score -= 0.3
                reasons.append(f"Negative momentum ({mom_score:.2f})")
            
            # Rule 3: Volatility (extreme = neutral)
            vol_regime = volatility.get("regime", "NORMAL")
            if vol_regime == "EXTREME":
                score *= 0.3  # Reduce conviction
                reasons.append("Extreme volatility - reduced conviction")
            elif vol_regime == "LOW":
                reasons.append("Low volatility - favorable")
            
            # Rule 4: Trend strength
            trend_strength = regime.get("trend_strength", 0.5)
            if trend_strength > 0.7:
                score *= 1.2  # Amplify
                reasons.append(f"Strong trend ({trend_strength:.2f})")
            
            # Determine prediction
            confidence = min(abs(score), 1.0)
            
            if score > 0.2:
                prediction = Prediction.UP
            elif score < -0.2:
                prediction = Prediction.DOWN
            else:
                prediction = Prediction.NEUTRAL
            
            self.mark_success()
            return ModelPrediction(
                model_name=self.name,
                prediction=prediction,
                confidence=confidence,
                reasoning="; ".join(reasons) or "Insufficient signals",
                metadata={"score": score},
                latency_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            self.mark_error()
            return ModelPrediction(
                model_name=self.name,
                prediction=Prediction.ERROR,
                confidence=0.0,
                reasoning=f"Rule evaluation error: {str(e)}",
                latency_ms=(time.time() - start) * 1000
            )


# =============================================================================
# MODEL 3: HISTORICAL PATTERN MATCHER
# =============================================================================

class PatternModel(BaseModel):
    """
    Fallback model using historical pattern matching.
    
    Compares current market state to historical outcomes.
    """
    
    def __init__(self):
        super().__init__("PatternMatcher", weight=0.8)
        self.min_similarity = 0.7
    
    def predict(self, market_data: Dict[str, Any]) -> ModelPrediction:
        import time
        start = time.time()
        
        try:
            ohlcv = market_data.get("ohlcv")
            if ohlcv is None:
                return ModelPrediction(
                    model_name=self.name,
                    prediction=Prediction.NEUTRAL,
                    confidence=0.0,
                    reasoning="No OHLCV data for pattern matching"
                )
            
            import pandas as pd
            df = pd.DataFrame(ohlcv) if not isinstance(ohlcv, pd.DataFrame) else ohlcv
            
            if len(df) < 20:
                return ModelPrediction(
                    model_name=self.name,
                    prediction=Prediction.NEUTRAL,
                    confidence=0.0,
                    reasoning="Insufficient data for pattern matching"
                )
            
            # Simple pattern detection: recent price action
            close = df['close'].values
            recent = close[-10:]
            historical = close[-50:-10]
            
            # Calculate recent momentum
            recent_change = (recent[-1] - recent[0]) / (recent[0] + 1e-10)
            
            # Calculate historical outcomes after similar patterns
            similar_outcomes = []
            for i in range(len(historical) - 10):
                window = historical[i:i+10]
                window_change = (window[-1] - window[0]) / (window[0] + 1e-10)
                
                # Check similarity
                similarity = 1 - abs(recent_change - window_change)
                if similarity > self.min_similarity:
                    # Look at what happened next
                    if i + 15 < len(close):
                        future_change = (close[i+15] - close[i+10]) / (close[i+10] + 1e-10)
                        similar_outcomes.append(future_change)
            
            if not similar_outcomes:
                return ModelPrediction(
                    model_name=self.name,
                    prediction=Prediction.NEUTRAL,
                    confidence=0.3,
                    reasoning="No similar historical patterns found"
                )
            
            # Average outcome
            avg_outcome = np.mean(similar_outcomes)
            outcome_std = np.std(similar_outcomes)
            
            confidence = min(1.0, 1.0 / (1 + outcome_std * 10))  # Lower std = higher confidence
            
            if avg_outcome > 0.005:
                prediction = Prediction.UP
            elif avg_outcome < -0.005:
                prediction = Prediction.DOWN
            else:
                prediction = Prediction.NEUTRAL
            
            self.mark_success()
            return ModelPrediction(
                model_name=self.name,
                prediction=prediction,
                confidence=confidence,
                reasoning=f"Based on {len(similar_outcomes)} similar historical patterns",
                metadata={
                    "patterns_found": len(similar_outcomes),
                    "avg_outcome": avg_outcome,
                    "outcome_std": outcome_std
                },
                latency_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            self.mark_error()
            return ModelPrediction(
                model_name=self.name,
                prediction=Prediction.ERROR,
                confidence=0.0,
                reasoning=f"Pattern matching error: {str(e)}",
                latency_ms=(time.time() - start) * 1000
            )


# =============================================================================
# MODEL ENSEMBLE
# =============================================================================

class ModelEnsemble:
    """
    Voting ensemble for AI predictions.
    
    Aggregates multiple models and requires agreement for high-confidence
    predictions. Disagreement triggers position reduction or halt.
    """
    
    def __init__(self, agreement_threshold: float = 0.6, halt_threshold: float = 0.3):
        """
        Args:
            agreement_threshold: Minimum agreement for full position
            halt_threshold: Below this, halt trading
        """
        self.agreement_threshold = agreement_threshold
        self.halt_threshold = halt_threshold
        self.models = [
            GeminiModel(),
            RuleBasedModel(),
            PatternModel()
        ]
        self.last_decision: Optional[EnsembleDecision] = None
        
        logger.info(f"Model Ensemble initialized with {len(self.models)} models")
    
    def predict(self, market_data: Dict[str, Any]) -> EnsembleDecision:
        """
        Get ensemble prediction from all models.
        
        Args:
            market_data: Dict with OHLCV, regime, momentum, volatility data
            
        Returns:
            EnsembleDecision with aggregated prediction and modifiers
        """
        logger.info("Ensemble prediction started")
        
        # Collect predictions from healthy models
        predictions: List[ModelPrediction] = []
        for model in self.models:
            if model.is_healthy:
                pred = model.predict(market_data)
                predictions.append(pred)
                logger.debug(f"  {model.name}: {pred.prediction.value} ({pred.confidence:.2f})")
            else:
                logger.warning(f"  {model.name}: SKIPPED (unhealthy)")
        
        # Calculate ensemble decision
        decision = self._aggregate_predictions(predictions)
        self.last_decision = decision
        
        # Log decision
        if decision.should_halt:
            logger.warning(f"Ensemble HALT: Agreement too low ({decision.agreement_score:.2f})")
        else:
            logger.info(f"Ensemble: {decision.final_prediction.value} "
                       f"(confidence: {decision.aggregated_confidence:.2f}, "
                       f"agreement: {decision.agreement_score:.2f})")
        
        return decision
    
    def _aggregate_predictions(self, predictions: List[ModelPrediction]) -> EnsembleDecision:
        """Aggregate predictions using weighted voting."""
        
        if not predictions:
            return EnsembleDecision(
                final_prediction=Prediction.NEUTRAL,
                aggregated_confidence=0.0,
                agreement_score=0.0,
                predictions=[],
                should_halt=True,
                reasoning="No healthy models available"
            )
        
        # Filter out errors
        valid_preds = [p for p in predictions if p.prediction != Prediction.ERROR]
        
        if not valid_preds:
            return EnsembleDecision(
                final_prediction=Prediction.NEUTRAL,
                aggregated_confidence=0.0,
                agreement_score=0.0,
                predictions=predictions,
                should_halt=True,
                reasoning="All models returned errors"
            )
        
        # Count votes by prediction type
        vote_weights = {Prediction.UP: 0.0, Prediction.DOWN: 0.0, Prediction.NEUTRAL: 0.0}
        total_weight = 0.0
        
        for pred in valid_preds:
            model = next((m for m in self.models if m.name == pred.model_name), None)
            weight = model.weight if model else 1.0
            vote_weights[pred.prediction] += weight * pred.confidence
            total_weight += weight
        
        # Normalize weights
        for k in vote_weights:
            vote_weights[k] /= total_weight if total_weight > 0 else 1
        
        # Determine winner
        winner = max(vote_weights, key=vote_weights.get)
        winner_weight = vote_weights[winner]
        
        # Calculate agreement (how much models agree with winner)
        agreeing = [p for p in valid_preds if p.prediction == winner]
        agreement_score = len(agreeing) / len(valid_preds) if valid_preds else 0
        
        # Calculate aggregated confidence
        if agreeing:
            weights = []
            confidences = []
            for p in agreeing:
                model = next((m for m in self.models if m.name == p.model_name), None)
                w = model.weight if model else 1.0
                weights.append(w)
                confidences.append(p.confidence)
            aggregated_confidence = np.average(confidences, weights=weights)
        else:
            aggregated_confidence = 0.0
        
        # Determine position modifier and halt status
        if agreement_score < self.halt_threshold:
            should_halt = True
            position_modifier = 0.0
            reasoning = f"Models strongly disagree (agreement: {agreement_score:.1%}). HALT."
        elif agreement_score < self.agreement_threshold:
            should_halt = False
            position_modifier = 0.5  # Reduce position
            reasoning = f"Low agreement ({agreement_score:.1%}). Position reduced 50%."
        else:
            should_halt = False
            position_modifier = 1.0
            reasoning = f"Strong agreement ({agreement_score:.1%}). Full position."
        
        return EnsembleDecision(
            final_prediction=winner,
            aggregated_confidence=aggregated_confidence,
            agreement_score=agreement_score,
            predictions=predictions,
            position_modifier=position_modifier,
            should_halt=should_halt,
            reasoning=reasoning
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get ensemble status for monitoring."""
        return {
            "models": [
                {
                    "name": m.name,
                    "weight": m.weight,
                    "is_healthy": m.is_healthy,
                    "consecutive_errors": m.consecutive_errors
                }
                for m in self.models
            ],
            "thresholds": {
                "agreement": self.agreement_threshold,
                "halt": self.halt_threshold
            },
            "last_decision": {
                "prediction": self.last_decision.final_prediction.value,
                "confidence": self.last_decision.aggregated_confidence,
                "agreement": self.last_decision.agreement_score,
                "should_halt": self.last_decision.should_halt
            } if self.last_decision else None
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_ensemble: Optional[ModelEnsemble] = None


def get_ensemble() -> ModelEnsemble:
    """Get or create global ensemble instance."""
    global _ensemble
    if _ensemble is None:
        _ensemble = ModelEnsemble()
    return _ensemble


def ensemble_predict(market_data: Dict[str, Any]) -> EnsembleDecision:
    """
    Convenience function for ensemble prediction.
    
    Usage:
        decision = ensemble_predict(market_data)
        if not decision.should_halt:
            # Proceed with decision.final_prediction
            # Apply decision.position_modifier to size
    """
    return get_ensemble().predict(market_data)
