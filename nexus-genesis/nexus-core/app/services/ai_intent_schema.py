"""
NEXUS AI Intent Schema — Layer 2: Strict JSON Intent Parser
============================================================

Enforces strict JSON schema for ALL AI trading intents.
AI must NEVER guess. AI must NEVER execute directly.
All AI output passes through this schema before reaching
the deterministic execution engine.

Schema Fields:
  intent           — trade_request | trade_suggestion | analysis | status_query
  asset            — symbol string
  direction        — buy | sell | none
  confidence_score — 0.0–1.0
  risk_level       — low | medium | high
  lot_size         — positive float or null
  stop_loss        — positive float or null
  take_profit      — positive float or null
  reasoning        — clear macro + technical logic
  requires_confirmation — bool

Confidence Gate:
  < 0.75         → Suggestion only (no execution path)
  0.75 – 0.85   → Requires human confirmation
  > 0.85        → Auto-allowed (still passes risk engine)
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.ai_intent")


# =============================================================================
# ENUMS
# =============================================================================

class IntentType(Enum):
    TRADE_REQUEST = "trade_request"
    TRADE_SUGGESTION = "trade_suggestion"
    ANALYSIS = "analysis"
    STATUS_QUERY = "status_query"


class Direction(Enum):
    BUY = "buy"
    SELL = "sell"
    NONE = "none"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidenceGate(Enum):
    """Confidence threshold classification."""
    SUGGEST_ONLY = "suggest_only"          # < 0.75
    REQUIRES_CONFIRMATION = "requires_confirmation"  # 0.75–0.85
    AUTO_ALLOWED = "auto_allowed"          # > 0.85


# =============================================================================
# ALLOWED SYMBOLS (mirrors sovereign_pipeline whitelist)
# =============================================================================
ALLOWED_SYMBOLS = {
    "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "XAUUSD",
    "BTC/USDT", "ETH/USDT",
}


# =============================================================================
# TRADING INTENT DATACLASS
# =============================================================================

@dataclass
class TradingIntent:
    """Strict schema for all AI-generated trading intents."""
    intent: IntentType
    asset: str
    direction: Direction
    confidence_score: float
    risk_level: RiskLevel
    lot_size: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasoning: str
    requires_confirmation: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Derived at validation time
    confidence_gate: ConfidenceGate = field(init=False)

    def __post_init__(self):
        self.confidence_gate = classify_confidence(self.confidence_score)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "asset": self.asset,
            "direction": self.direction.value,
            "confidence_score": self.confidence_score,
            "risk_level": self.risk_level.value,
            "lot_size": self.lot_size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "reasoning": self.reasoning,
            "requires_confirmation": self.requires_confirmation,
            "confidence_gate": self.confidence_gate.value,
            "timestamp": self.timestamp,
        }


# =============================================================================
# CONFIDENCE GATE CLASSIFICATION
# =============================================================================

def classify_confidence(score: float) -> ConfidenceGate:
    """Classify confidence score into gate tier."""
    if score < 0.75:
        return ConfidenceGate.SUGGEST_ONLY
    elif score <= 0.85:
        return ConfidenceGate.REQUIRES_CONFIRMATION
    else:
        return ConfidenceGate.AUTO_ALLOWED


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

_REQUIRED_FIELDS = [
    "intent", "asset", "direction", "confidence_score",
    "risk_level", "reasoning", "requires_confirmation",
]


def validate_intent_json(raw: Dict[str, Any]) -> Tuple[bool, List[str], Optional[TradingIntent]]:
    """
    Validate raw JSON dict against the strict trading intent schema.

    Returns:
        (is_valid, list_of_issues, TradingIntent_or_None)
    """
    issues: List[str] = []

    # ── Check required fields ─────────────────────────────────────────────
    for f in _REQUIRED_FIELDS:
        if f not in raw:
            issues.append(f"MISSING_FIELD: '{f}' is required")

    if issues:
        return False, issues, None

    # ── Validate intent ──────────────────────────────────────────────────
    valid_intents = {e.value for e in IntentType}
    if raw["intent"] not in valid_intents:
        issues.append(f"INVALID_INTENT: '{raw['intent']}' — must be one of {valid_intents}")

    # ── Validate asset ───────────────────────────────────────────────────
    asset = raw.get("asset", "")
    if not asset or not isinstance(asset, str):
        issues.append("INVALID_ASSET: must be a non-empty string")
    elif asset.upper() not in ALLOWED_SYMBOLS:
        issues.append(f"UNKNOWN_ASSET: '{asset}' — not in allowed symbols {ALLOWED_SYMBOLS}")

    # ── Validate direction ───────────────────────────────────────────────
    valid_directions = {e.value for e in Direction}
    if raw["direction"] not in valid_directions:
        issues.append(f"INVALID_DIRECTION: '{raw['direction']}' — must be one of {valid_directions}")

    # ── Validate confidence_score ────────────────────────────────────────
    cs = raw["confidence_score"]
    if not isinstance(cs, (int, float)):
        issues.append(f"INVALID_CONFIDENCE: must be a number, got {type(cs).__name__}")
    elif math.isnan(cs) or math.isinf(cs):
        issues.append("INVALID_CONFIDENCE: NaN/Inf not allowed")
    elif not (0.0 <= cs <= 1.0):
        issues.append(f"INVALID_CONFIDENCE: {cs} — must be between 0.0 and 1.0")

    # ── Validate risk_level ──────────────────────────────────────────────
    valid_risks = {e.value for e in RiskLevel}
    if raw["risk_level"] not in valid_risks:
        issues.append(f"INVALID_RISK_LEVEL: '{raw['risk_level']}' — must be one of {valid_risks}")

    # ── Validate lot_size (optional) ─────────────────────────────────────
    lot = raw.get("lot_size")
    if lot is not None:
        if not isinstance(lot, (int, float)):
            issues.append(f"INVALID_LOT_SIZE: must be a number or null, got {type(lot).__name__}")
        elif math.isnan(lot) or math.isinf(lot):
            issues.append("INVALID_LOT_SIZE: NaN/Inf not allowed")
        elif lot <= 0:
            issues.append(f"INVALID_LOT_SIZE: {lot} — must be > 0")
        elif lot > 100:
            issues.append(f"UNREALISTIC_LOT_SIZE: {lot} — exceeds maximum 100 lots")

    # ── Validate stop_loss (optional) ────────────────────────────────────
    sl = raw.get("stop_loss")
    if sl is not None:
        if not isinstance(sl, (int, float)):
            issues.append(f"INVALID_STOP_LOSS: must be a number or null")
        elif math.isnan(sl) or math.isinf(sl) or sl <= 0:
            issues.append(f"INVALID_STOP_LOSS: {sl}")

    # ── Validate take_profit (optional) ──────────────────────────────────
    tp = raw.get("take_profit")
    if tp is not None:
        if not isinstance(tp, (int, float)):
            issues.append(f"INVALID_TAKE_PROFIT: must be a number or null")
        elif math.isnan(tp) or math.isinf(tp) or tp <= 0:
            issues.append(f"INVALID_TAKE_PROFIT: {tp}")

    # ── Validate reasoning ───────────────────────────────────────────────
    reasoning = raw.get("reasoning", "")
    if not reasoning or not isinstance(reasoning, str) or len(reasoning.strip()) < 10:
        issues.append("INVALID_REASONING: must be a string with at least 10 characters")

    # ── Validate requires_confirmation ───────────────────────────────────
    if not isinstance(raw["requires_confirmation"], bool):
        issues.append("INVALID_REQUIRES_CONFIRMATION: must be a boolean")

    # ── Build TradingIntent if valid ─────────────────────────────────────
    if issues:
        return False, issues, None

    try:
        intent = TradingIntent(
            intent=IntentType(raw["intent"]),
            asset=asset.upper(),
            direction=Direction(raw["direction"]),
            confidence_score=float(cs),
            risk_level=RiskLevel(raw["risk_level"]),
            lot_size=float(lot) if lot is not None else None,
            stop_loss=float(sl) if sl is not None else None,
            take_profit=float(tp) if tp is not None else None,
            reasoning=reasoning.strip(),
            requires_confirmation=bool(raw["requires_confirmation"]),
        )
        return True, [], intent
    except Exception as exc:
        issues.append(f"SCHEMA_ERROR: {exc}")
        return False, issues, None


def build_clarification_request(raw: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
    """Build a structured clarification request when intent is invalid."""
    return {
        "status": "CLARIFICATION_REQUIRED",
        "message": "AI intent failed schema validation. Please provide missing or corrected fields.",
        "issues": issues,
        "received_fields": list(raw.keys()),
        "required_fields": _REQUIRED_FIELDS,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
