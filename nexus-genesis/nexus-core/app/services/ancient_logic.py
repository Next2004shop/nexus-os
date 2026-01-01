import logging
from typing import Dict, Any, Tuple

# Configure logging
logger = logging.getLogger("nexus.ancient_logic")

class MarketCycle:
    ACCUMULATION = "ACCUMULATION"
    EXPANSION = "EXPANSION"
    DISTRIBUTION = "DISTRIBUTION"
    DECAY = "DECAY"

def check_cycle(market_context: Dict[str, Any]) -> Tuple[bool, str]:
    """
    The Ancient Filters: Overrides AI based on Market Cycle Theory.
    
    Logic:
    - BUY only allowed during EXPANSION.
    - SELL only allowed during DECAY.
    - DISTRIBUTION = 100% Cash (Stay out).
    - ACCUMULATION = Stealth Entry only (Blocked for this protocol).
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
