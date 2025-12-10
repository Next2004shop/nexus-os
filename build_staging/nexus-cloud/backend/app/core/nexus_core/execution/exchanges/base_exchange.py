from abc import ABC, abstractmethod

class BaseExchange(ABC):
    """
    Abstract Base Class for Crypto Exchanges.
    """
    
    def __init__(self, name: str, api_key: str = "", api_secret: str = ""):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: float, price: float = None):
        pass
