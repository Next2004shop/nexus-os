import logging
from typing import Dict, Any, Tuple

# Configure logging
logger = logging.getLogger("nexus.risk_governor")

# State (In production, these would be in Firestore/BigQuery)
STATE = {
    "peak_equity": 10000.0,
    "current_equity": 10000.0,
    "max_drawdown_limit": 0.02, # 2%
    "max_position_size_pct": 0.05, # 5%
    "trading_enabled": True
}

def calculate_drawdown() -> float:
    """
    DD = (PeakValue - CurrentValue) / PeakValue
    """
    if STATE["peak_equity"] <= 0:
        return 0.0
    return (STATE["peak_equity"] - STATE["current_equity"]) / STATE["peak_equity"]

def validate_trade(symbol: str, quantity: float, price: float, atr_data: Dict[str, float]) -> Tuple[bool, str]:
    """
    The Survival Filter: Validates trade parameters against risk limits.
    """
    if not STATE["trading_enabled"]:
        return False, "TRADING_DISABLED_BY_GOVERNOR"

    # 1. Drawdown Check
    current_dd = calculate_drawdown()
    if current_dd > STATE["max_drawdown_limit"]:
        STATE["trading_enabled"] = False
        logger.critical(f"MAX DRAWDOWN EXCEEDED: {current_dd:.2%}. SYSTEM SHUTDOWN.")
        return False, "MAX_DRAWDOWN_EXCEEDED"

    # 2. Position Size Check
    notional_value = quantity * price
    max_position_value = STATE["current_equity"] * STATE["max_position_size_pct"]
    if notional_value > max_position_value:
        logger.warning(f"POSITION SIZE EXPOSURE: {notional_value} > {max_position_value}. REDUCING SIZE REQUIRED.")
        return False, "MAX_POSITION_SIZE_EXCEEDED"

    # 3. Volatility Check (ATR)
    if atr_data:
        current_atr = atr_data.get("current_atr", 0)
        normal_atr = atr_data.get("normal_atr", 0)
        if current_atr > (3 * normal_atr):
            logger.critical("EXCESSIVE VOLATILITY (3x ATR). KILL SWITCH ARMED.")
            return False, "VOLATILITY_ANOMALY_DETECTED"

    return True, "RISK_VALIDATED"

def update_equity(new_equity: float):
    """
    Updates the governor state with new equity values.
    """
    STATE["current_equity"] = new_equity
    if new_equity > STATE["peak_equity"]:
        STATE["peak_equity"] = new_equity
        logger.info(f"NEW PEAK EQUITY: {new_equity}")
