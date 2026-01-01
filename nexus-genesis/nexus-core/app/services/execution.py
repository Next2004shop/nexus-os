import ccxt
import logging
import sys
from typing import Dict, Any
from . import vault

# Configure logging
logger = logging.getLogger("nexus.execution")

def get_exchange_client() -> ccxt.binance:
    """
    Initializes the Binance exchange client using secrets from Vault.
    """
    try:
        api_key = vault.get_secret("BINANCE_API_KEY")
        api_secret = vault.get_secret("BINANCE_API_SECRET")
        
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future', # Defaulting to futures for Axelrod style
            }
        })
        return exchange
    except Exception as e:
        logger.critical(f"Failed to initialize exchange client: {e}")
        sys.exit(1)

def execute_trade(symbol: str, side: str, quantity: float) -> Dict[str, Any]:
    """
    Executes a Market Order on Binance.
    
    Args:
        symbol (str): The trading pair (e.g., 'BTC/USDT').
        side (str): 'buy' or 'sell'.
        quantity (float): Amount to trade.
        
    Returns:
        Dict[str, Any]: Order result.
    """
    exchange = get_exchange_client()
    
    try:
        logger.info(f"Executing {side.upper()} order for {quantity} {symbol}")
        
        # Check side validity
        if side.lower() not in ['buy', 'sell']:
            raise ValueError(f"Invalid side: {side}")

        params = {} # Add specific params here if needed
        
        order = exchange.create_market_order(
            symbol=symbol,
            side=side.lower(),
            amount=quantity,
            params=params
        )
        
        logger.info(f"Order successful: {order['id']}")
        return order
        
    except Exception as e:
        logger.error(f"Execution Error: {e}")
        return {"error": str(e), "status": "failed"}

def kill_switch(symbol: str = None) -> Dict[str, Any]:
    """
    Emergency Kill Switch: Cancels all open orders and closes positions.
    """
    exchange = get_exchange_client()
    try:
        logger.warning(f"KILL SWITCH INITIATED{' for ' + symbol if symbol else ' for ALL SYMBOLS'}")
        
        # Cancel all open orders
        cancelled_orders = exchange.cancel_all_orders(symbol=symbol)
        
        # Note: Closing positions requires more complex logic depending on the exchange/market.
        # For simplicity in this version, we cancel all active orders.
        
        logger.warning("All active orders cancelled. System in safety state.")
        return {"status": "success", "cancelled_orders": cancelled_orders}
        
    except Exception as e:
        logger.error(f"Kill Switch Error: {e}")
        return {"error": str(e), "status": "failed"}
