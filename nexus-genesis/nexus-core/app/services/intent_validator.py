"""
NEXUS Intent Validator — Strict Pre-Execution Validation
==========================================================

Validates parsed TradeIntent against system constraints:
- Asset whitelist (from execution.py)
- Direction validity
- Lot size limits
- SL/TP logical consistency
- Required fields for trade_request

Returns structured ValidationResult. Invalid = reject before routing.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger("nexus.intent_validator")

# Import whitelist and config from execution layer (read-only)
from app.services.execution import ASSET_WHITELIST, ExecutionConfig

# Valid intent types
VALID_INTENTS = {"trade_request", "trade_suggestion", "analysis", "system_query", "clarification_needed"}
VALID_DIRECTIONS = {"buy", "sell", "none"}

# Default config for limit checks
_default_config = ExecutionConfig()


@dataclass
class ValidationResult:
    """Result of intent validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings
        }

    @classmethod
    def ok(cls, warnings: Optional[List[str]] = None) -> "ValidationResult":
        return cls(valid=True, warnings=warnings or [])

    @classmethod
    def reject(cls, errors: List[str], warnings: Optional[List[str]] = None) -> "ValidationResult":
        return cls(valid=False, errors=errors, warnings=warnings or [])


def validate_intent(intent_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a parsed TradeIntent dict.
    
    Checks:
    1. Intent type is valid
    2. Asset is in whitelist (for trade intents)
    3. Direction is valid
    4. Lot size within limits
    5. SL/TP logical consistency
    6. Required fields present for trade_request
    
    Args:
        intent_data: Dict from TradeIntent.to_dict()
    
    Returns:
        ValidationResult with valid flag and error list
    """
    errors = []
    warnings = []
    
    intent_type = intent_data.get("intent", "")
    
    # =========================================================================
    # 1. INTENT TYPE
    # =========================================================================
    if intent_type not in VALID_INTENTS and intent_type != "error":
        errors.append(f"Invalid intent type: '{intent_type}'. Must be one of: {', '.join(VALID_INTENTS)}")
    
    # Non-trade intents need minimal validation
    if intent_type in ("analysis", "system_query", "clarification_needed", "error"):
        if errors:
            return ValidationResult.reject(errors, warnings)
        return ValidationResult.ok(warnings)
    
    # =========================================================================
    # 2. ASSET WHITELIST (for trade_request and trade_suggestion)
    # =========================================================================
    asset = intent_data.get("asset")
    if intent_type == "trade_request":
        if not asset:
            errors.append("Missing asset for trade_request. Specify a trading symbol.")
        elif asset.upper() not in ASSET_WHITELIST and asset not in ASSET_WHITELIST:
            errors.append(f"Asset '{asset}' not in approved whitelist. Allowed: {', '.join(sorted(ASSET_WHITELIST))}")
    elif intent_type == "trade_suggestion" and asset:
        if asset.upper() not in ASSET_WHITELIST and asset not in ASSET_WHITELIST:
            warnings.append(f"Suggested asset '{asset}' not in whitelist — may be rejected at execution.")
    
    # =========================================================================
    # 3. DIRECTION
    # =========================================================================
    direction = intent_data.get("direction", "none")
    if direction and direction.lower() not in VALID_DIRECTIONS:
        errors.append(f"Invalid direction: '{direction}'. Must be: buy, sell, or none.")
    
    if intent_type == "trade_request" and (not direction or direction.lower() == "none"):
        errors.append("trade_request requires explicit direction (buy or sell).")
    
    # =========================================================================
    # 4. LOT SIZE LIMITS
    # =========================================================================
    lot_size = intent_data.get("lot_size")
    if lot_size is not None:
        try:
            lot_size = float(lot_size)
            if lot_size <= 0:
                errors.append(f"Lot size must be positive. Got: {lot_size}")
            elif lot_size > _default_config.max_lot_size:
                errors.append(
                    f"Lot size {lot_size} exceeds maximum allowed {_default_config.max_lot_size}."
                )
            elif lot_size < 0.01:
                warnings.append(f"Lot size {lot_size} is very small. Minimum is typically 0.01.")
        except (ValueError, TypeError):
            errors.append(f"Invalid lot_size value: {lot_size}")
    elif intent_type == "trade_request":
        warnings.append("No lot_size specified — will need confirmation before execution.")
    
    # =========================================================================
    # 5. SL/TP LOGICAL CONSISTENCY
    # =========================================================================
    stop_loss = intent_data.get("stop_loss")
    take_profit = intent_data.get("take_profit")
    
    if stop_loss is not None and take_profit is not None:
        try:
            sl = float(stop_loss)
            tp = float(take_profit)
            dir_lower = direction.lower() if direction else "none"
            
            if dir_lower == "buy":
                # For BUY: SL should be below TP
                if sl >= tp:
                    errors.append(
                        f"For BUY: stop_loss ({sl}) must be below take_profit ({tp})."
                    )
            elif dir_lower == "sell":
                # For SELL: SL should be above TP
                if sl <= tp:
                    errors.append(
                        f"For SELL: stop_loss ({sl}) must be above take_profit ({tp})."
                    )
        except (ValueError, TypeError):
            if stop_loss is not None:
                errors.append(f"Invalid stop_loss value: {stop_loss}")
            if take_profit is not None:
                errors.append(f"Invalid take_profit value: {take_profit}")
    
    if stop_loss is not None:
        try:
            sl = float(stop_loss)
            if sl <= 0:
                errors.append(f"stop_loss must be positive. Got: {sl}")
        except (ValueError, TypeError):
            pass
    
    if take_profit is not None:
        try:
            tp = float(take_profit)
            if tp <= 0:
                errors.append(f"take_profit must be positive. Got: {tp}")
        except (ValueError, TypeError):
            pass
    
    # =========================================================================
    # 6. CONFIDENCE
    # =========================================================================
    confidence = intent_data.get("confidence", 0.0)
    try:
        conf = float(confidence)
        if conf < 0 or conf > 1:
            warnings.append(f"Confidence {conf} out of [0,1] range — clamped.")
    except (ValueError, TypeError):
        warnings.append(f"Invalid confidence value: {confidence}")
    
    # =========================================================================
    # RESULT
    # =========================================================================
    if errors:
        logger.warning(f"Intent validation FAILED: {errors}")
        return ValidationResult.reject(errors, warnings)
    
    if warnings:
        logger.info(f"Intent validation OK with warnings: {warnings}")
    
    return ValidationResult.ok(warnings)
