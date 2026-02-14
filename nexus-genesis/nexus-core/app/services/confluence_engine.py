"""
NEXUS Multi-Timeframe Confluence Engine — Phase 5, Part B
==========================================================

Requires alignment across three timeframes:
  1. Higher TF (bias) — sets directional filter
  2. Execution TF (entry) — triggers the trade
  3. Lower TF (confirmation) — validates timing

Confluence score reflects:
  - Timeframe alignment (all agree = high, conflict = low)
  - Trend strength across frames
  - Volatility suitability

If higher TF bias conflicts with execution TF → downgrade or reject.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.confluence")


# =============================================================================
# TIMEFRAME DEFINITIONS
# =============================================================================

class TimeframeRole(Enum):
    HIGHER = "HIGHER"        # e.g. H4 or D1 — directional bias
    EXECUTION = "EXECUTION"  # e.g. H1 or M15 — entry signal
    LOWER = "LOWER"          # e.g. M5 or M1 — confirmation


class Bias(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class TimeframeAnalysis:
    """Analysis result for a single timeframe."""
    role: TimeframeRole
    timeframe: str          # e.g. "H4", "H1", "M15"
    bias: Bias
    trend_strength: float   # 0.0–1.0
    volatility_ok: bool     # True if volatility is suitable for entry
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "timeframe": self.timeframe,
            "bias": self.bias.value,
            "trend_strength": round(self.trend_strength, 3),
            "volatility_ok": self.volatility_ok,
            "reasoning": self.reasoning,
        }


@dataclass
class ConfluenceResult:
    """Final confluence assessment across all timeframes."""
    symbol: str
    confluence_score: float       # 0.0–1.0 overall alignment
    is_aligned: bool              # True if all TFs agree
    recommended_action: str       # "PROCEED", "DOWNGRADE", "REJECT"
    confidence_modifier: float    # multiplier for trade confidence (0.0–1.0)
    higher_bias: Bias
    execution_bias: Bias
    lower_bias: Bias
    analyses: List[TimeframeAnalysis]
    reasoning: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "confluence_score": round(self.confluence_score, 3),
            "is_aligned": self.is_aligned,
            "recommended_action": self.recommended_action,
            "confidence_modifier": round(self.confidence_modifier, 3),
            "higher_bias": self.higher_bias.value,
            "execution_bias": self.execution_bias.value,
            "lower_bias": self.lower_bias.value,
            "analyses": [a.to_dict() for a in self.analyses],
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
        }


# =============================================================================
# TIMEFRAME ANALYSIS HELPERS
# =============================================================================

def analyze_timeframe(
    role: TimeframeRole,
    timeframe_label: str,
    closes: List[float],
    highs: List[float],
    lows: List[float],
) -> TimeframeAnalysis:
    """
    Analyze a single timeframe for directional bias and trend strength.

    Uses SMA crossover + price position for bias detection.
    """
    if len(closes) < 20:
        return TimeframeAnalysis(
            role=role,
            timeframe=timeframe_label,
            bias=Bias.NEUTRAL,
            trend_strength=0.0,
            volatility_ok=True,
            reasoning="Insufficient data",
        )

    # SMA10 vs SMA20 for bias
    sma10 = sum(closes[-10:]) / 10
    sma20 = sum(closes[-20:]) / 20
    price = closes[-1]

    # Trend strength = distance between SMAs relative to price
    sma_spread = (sma10 - sma20) / price if price > 0 else 0

    if price > sma10 > sma20:
        bias = Bias.BULLISH
        trend_strength = min(1.0, abs(sma_spread) * 100)
    elif price < sma10 < sma20:
        bias = Bias.BEARISH
        trend_strength = min(1.0, abs(sma_spread) * 100)
    else:
        bias = Bias.NEUTRAL
        trend_strength = max(0.0, 0.3 - abs(sma_spread) * 50)

    # Volatility check: recent range vs average
    recent_ranges = [highs[i] - lows[i] for i in range(-5, 0)]
    avg_ranges = [highs[i] - lows[i] for i in range(-20, -5)]
    avg_recent = sum(recent_ranges) / len(recent_ranges) if recent_ranges else 0
    avg_older = sum(avg_ranges) / len(avg_ranges) if avg_ranges else 1
    vol_ratio = avg_recent / avg_older if avg_older > 0 else 1.0
    volatility_ok = vol_ratio < 2.5  # not excessively volatile

    reasoning = (
        f"{timeframe_label}: bias={bias.value}, "
        f"SMA10={sma10:.5f}, SMA20={sma20:.5f}, "
        f"strength={trend_strength:.2f}, vol_ok={volatility_ok}"
    )

    return TimeframeAnalysis(
        role=role,
        timeframe=timeframe_label,
        bias=bias,
        trend_strength=trend_strength,
        volatility_ok=volatility_ok,
        reasoning=reasoning,
    )


# =============================================================================
# CONFLUENCE CALCULATOR
# =============================================================================

def calculate_confluence(
    symbol: str,
    higher_tf: TimeframeAnalysis,
    execution_tf: TimeframeAnalysis,
    lower_tf: TimeframeAnalysis,
) -> ConfluenceResult:
    """
    Calculate multi-timeframe confluence score.

    Rules:
      - All 3 aligned → score >= 0.8, PROCEED
      - Higher + Execution aligned, lower neutral → score ~0.6, PROCEED
      - Higher conflicts with execution → DOWNGRADE or REJECT
      - Low volatility suitability → reduce score
    """
    h_bias = higher_tf.bias
    e_bias = execution_tf.bias
    l_bias = lower_tf.bias

    # Check alignment
    all_biases = [h_bias, e_bias, l_bias]
    non_neutral = [b for b in all_biases if b != Bias.NEUTRAL]

    # Full alignment
    if len(non_neutral) >= 2 and len(set(non_neutral)) == 1:
        alignment_score = 0.8 + (0.2 if len(non_neutral) == 3 else 0.0)
        is_aligned = True
    # Higher + execution agree, lower neutral
    elif h_bias == e_bias and h_bias != Bias.NEUTRAL:
        alignment_score = 0.65
        is_aligned = True
    # Higher conflicts with execution — critical
    elif h_bias != Bias.NEUTRAL and e_bias != Bias.NEUTRAL and h_bias != e_bias:
        alignment_score = 0.2
        is_aligned = False
    # Everything neutral
    elif all(b == Bias.NEUTRAL for b in all_biases):
        alignment_score = 0.3
        is_aligned = False
    else:
        alignment_score = 0.45
        is_aligned = False

    # Trend strength bonus
    avg_strength = (
        higher_tf.trend_strength * 0.4 +
        execution_tf.trend_strength * 0.4 +
        lower_tf.trend_strength * 0.2
    )
    strength_bonus = avg_strength * 0.15

    # Volatility penalty
    vol_penalty = 0.0
    if not higher_tf.volatility_ok:
        vol_penalty += 0.1
    if not execution_tf.volatility_ok:
        vol_penalty += 0.15

    # Final score
    confluence_score = max(0.0, min(1.0, alignment_score + strength_bonus - vol_penalty))

    # Determine action
    if is_aligned and confluence_score >= 0.6:
        action = "PROCEED"
        confidence_modifier = min(1.0, confluence_score)
    elif confluence_score >= 0.4:
        action = "DOWNGRADE"
        confidence_modifier = confluence_score * 0.7
    else:
        action = "REJECT"
        confidence_modifier = 0.0

    # Build reasoning
    reasoning_parts = []
    if is_aligned:
        reasoning_parts.append(f"Timeframes aligned ({', '.join(b.value for b in non_neutral)})")
    else:
        reasoning_parts.append("Timeframe conflict detected")
        if h_bias != Bias.NEUTRAL and e_bias != Bias.NEUTRAL and h_bias != e_bias:
            reasoning_parts.append(
                f"Higher TF ({h_bias.value}) conflicts with "
                f"Execution TF ({e_bias.value})"
            )

    if vol_penalty > 0:
        reasoning_parts.append(f"Volatility concern (penalty: {vol_penalty:.2f})")

    reasoning_parts.append(f"Avg trend strength: {avg_strength:.2f}")

    return ConfluenceResult(
        symbol=symbol,
        confluence_score=confluence_score,
        is_aligned=is_aligned,
        recommended_action=action,
        confidence_modifier=confidence_modifier,
        higher_bias=h_bias,
        execution_bias=e_bias,
        lower_bias=l_bias,
        analyses=[higher_tf, execution_tf, lower_tf],
        reasoning="; ".join(reasoning_parts),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def get_confluence_context_for_ai(result: ConfluenceResult) -> str:
    """Format confluence result for AI prompt injection."""
    lines = [
        f"MULTI-TIMEFRAME CONFLUENCE FOR {result.symbol}:",
        f"  Score: {result.confluence_score:.0%}",
        f"  Aligned: {result.is_aligned}",
        f"  Action: {result.recommended_action}",
        f"  Higher TF Bias: {result.higher_bias.value}",
        f"  Execution TF Bias: {result.execution_bias.value}",
        f"  Lower TF Bias: {result.lower_bias.value}",
        f"  Confidence Modifier: {result.confidence_modifier:.2f}",
        f"  Reasoning: {result.reasoning}",
    ]
    return "\n".join(lines)
