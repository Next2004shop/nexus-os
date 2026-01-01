import logging
import sys
# Note: MetaTrader5 package is Windows-only. In a Linux Cloud Run environment, 
# this would typically connect to a MT5-Gateway or a dedicated bridge.
# For this architecture, we implement the logic assuming an MT5-compatible interface.
try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

from . import vault

# Configure logging
logger = logging.getLogger("nexus.broker_mt5")

def initialize_mt5():
    """ Initializes connection to MT5 using secrets from Vault. """
    if mt5 is None:
        logger.error("MetaTrader5 package not installed or not supported on this OS.")
        return False
        
    login = int(vault.get_secret("MT5_LOGIN"))
    password = vault.get_secret("MT5_PASSWORD")
    server = vault.get_secret("MT5_SERVER")
    
    if not mt5.initialize(login=login, password=password, server=server):
        logger.critical(f"MT5 Initialization Failed: {mt5.last_error()}")
        return False
        
    logger.info("MT5 BRIDGE ACTIVE.")
    return True

def get_account_info():
    """ Pulls live balance and equity for the Risk Governor. """
    if mt5 is None or not mt5.terminal_info():
        # Fallback/Mock for non-Windows environments
        return {"balance": 10000.0, "equity": 10000.0}
        
    account_info = mt5.account_info()
    if account_info is None:
        logger.error("Failed to get account info")
        return None
        
    return {
        "balance": account_info.balance,
        "equity": account_info.equity,
        "margin_free": account_info.margin_free
    }

def send_order(symbol: str, volume: float, order_type: str):
    """
    Sends a request to the MT5 terminal.
    order_type: 'BUY' or 'SELL'
    """
    if mt5 is None:
        logger.warning(f"MT5 NOT ACTIVE. MOCK ORDER: {order_type} {volume} {symbol}")
        return {"result": "MOCK_SUCCESS"}

    price = mt5.symbol_info_tick(symbol).ask if order_type == 'BUY' else mt5.symbol_info_tick(symbol).bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL,
        "price": price,
        "magic": 777777,
        "comment": "NEXUS_SOVEREIGN_EXECUTION",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"MT5 Order Failed: {result.comment}")
        return {"status": "FAILED", "error": result.comment}
        
    logger.info(f"MT5 Order Successful: {result.order}")
    return {"status": "SUCCESS", "order_id": result.order}

def shutdown_mt5():
    if mt5:
        mt5.shutdown()
