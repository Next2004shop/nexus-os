from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Abstract Base Class for all Nexus Strategies.
    Enforces a standard interface for the AI Engine.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.active = True

    @abstractmethod
    def analyze(self, symbol: str, data: dict) -> dict:
        """
        Analyze market data and return a trade decision.
        
        Args:
            symbol (str): The asset symbol (e.g., "EURUSD").
            data (dict): Standardized data packet containing OHLCV, indicators, etc.
            
        Returns:
            dict: {
                "signal": "BUY" | "SELL" | "HOLD",
                "confidence": float (0-100),
                "reason": str,
                "strategy_name": str
            }
        """
        pass

    def log(self, message: str):
        print(f"[{self.name}] {message}")
