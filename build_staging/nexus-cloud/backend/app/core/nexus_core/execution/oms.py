import logging

logger = logging.getLogger("NexusOMS")

class OrderManagementSystem:
    """
    Central Execution Handler.
    Routes orders to the correct exchange/bridge.
    """
    
    def __init__(self):
        self.routes = {
            "FOREX": "MT5_BRIDGE",
            "CRYPTO": "BINANCE_API", # Placeholder
            "STOCKS": "MT5_BRIDGE"
        }
        
    def execute(self, decision: dict, symbol: str):
        """
        Executes a trade based on the AI decision.
        """
        if decision['signal'] == "HOLD":
            return
            
        logger.info(f"⚡ OMS RECEIVED ORDER: {decision['signal']} {symbol} (Confidence: {decision['confidence']}%)")
        
        # Determine Route
        route = self.get_route(symbol)
        
        if route == "MT5_BRIDGE":
            self.execute_mt5(decision, symbol)
        elif route == "BINANCE_API":
            self.execute_crypto(decision, symbol)
            
    def get_route(self, symbol: str):
        if "USD" in symbol or "JPY" in symbol:
            return "FOREX"
        if "BTC" in symbol or "ETH" in symbol:
            return "CRYPTO"
        return "STOCKS"

    def execute_mt5(self, decision, symbol):
        # This will be hooked up to the Flask bridge
        logger.info(f"➡️ Routing to MT5 Bridge: {symbol}")
        # In the real system, this would call the internal MT5 function or API
        
    def execute_crypto(self, decision, symbol):
        logger.info(f"➡️ Routing to Crypto Exchange: {symbol}")
