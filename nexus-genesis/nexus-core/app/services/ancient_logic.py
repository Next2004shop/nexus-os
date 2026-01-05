"""
NEXUS Ancient Logic - Market Cycle Filter
==========================================

The Ancient Filters: Overrides AI based on Market Cycle Theory.

Market cycles:
- ACCUMULATION: Stealth entry only (blocked for this protocol)
- EXPANSION: BUY allowed
- DISTRIBUTION: 100% Cash (stay out)
- DECAY: SELL allowed

IMMUTABLE LAW: Cycle alignment required for trade execution.
"""

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger("nexus.ancient_logic")


# =============================================================================
# MARKET CYCLE DEFINITIONS
# =============================================================================

class MarketCycle:
    """Market cycle phases."""
    ACCUMULATION = "ACCUMULATION"
    EXPANSION = "EXPANSION"
    DISTRIBUTION = "DISTRIBUTION"
    DECAY = "DECAY"


# =============================================================================
# CYCLE VALIDATION
# =============================================================================

def check_cycle(market_context: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate trade signal against market cycle.
    
    Logic:
    - BUY only allowed during EXPANSION
    - SELL only allowed during DECAY
    - DISTRIBUTION = 100% Cash (Stay out)
    - ACCUMULATION = Stealth Entry only (Blocked for this protocol)
    
    Args:
        market_context: Dict containing cycle and signal
        
    Returns:
        Tuple of (is_allowed, reason_message)
    """
    cycle = market_context.get("cycle", MarketCycle.ACCUMULATION).upper()
    signal = market_context.get("signal", "WAIT").upper()

    logger.info(f"ANCIENT_LOGIC: Detected Cycle={cycle}, Signal={signal}")

    if cycle == MarketCycle.DISTRIBUTION:
        return False, "CYCLE_RESTRICTION: DISTRIBUTION DETECTED. EXIT TO CASH."

    if signal == "BUY":
        if cycle == MarketCycle.EXPANSION:
            return True, "CYCLE_ALIGNED: BUY ALLOWED IN EXPANSION."
        return False, f"CYCLE_RESTRICTION: BUY REJECTED IN {cycle}."

    if signal == "SELL":
        if cycle == MarketCycle.DECAY:
            return True, "CYCLE_ALIGNED: SELL ALLOWED IN DECAY."
        return False, f"CYCLE_RESTRICTION: SELL REJECTED IN {cycle}."

    return False, "NO_ACTION_REQUIRED"
