"""
NEXUS Command Layer — Validator
=================================

Validates TradeCommand against strict rules.
If validation fails, execution is BLOCKED.
"""

from typing import Dict, Any, List

from command.schema import TradeCommand


# Allowed assets — single source of truth for command layer
ALLOWED_ASSETS = ["XAUUSD", "EURUSD", "NAS100", "BTCUSD"]

# Maximum lot size
MAX_LOT_SIZE = 0.5


def validate_command(command: TradeCommand) -> Dict[str, Any]:
    """
    Validate a TradeCommand against all rules.
    
    Rules:
    1. lot_size > 0
    2. lot_size <= 0.5
    3. asset in allowed list
    4. stop_loss > 0 if provided
    5. take_profit > 0 if provided
    
    Returns:
        {"valid": bool, "errors": [str]}
    """
    errors: List[str] = []
    
    # Rule 1 & 2: Lot size
    if command.lot_size <= 0:
        errors.append(f"lot_size must be positive. Got: {command.lot_size}")
    elif command.lot_size > MAX_LOT_SIZE:
        errors.append(f"lot_size {command.lot_size} exceeds maximum {MAX_LOT_SIZE}")
    
    # Rule 3: Asset whitelist
    if command.asset not in ALLOWED_ASSETS:
        errors.append(
            f"Asset '{command.asset}' not allowed. "
            f"Permitted: {', '.join(ALLOWED_ASSETS)}"
        )
    
    # Rule 4: Stop loss
    if command.stop_loss is not None and command.stop_loss <= 0:
        errors.append(f"stop_loss must be positive. Got: {command.stop_loss}")
    
    # Rule 5: Take profit
    if command.take_profit is not None and command.take_profit <= 0:
        errors.append(f"take_profit must be positive. Got: {command.take_profit}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
