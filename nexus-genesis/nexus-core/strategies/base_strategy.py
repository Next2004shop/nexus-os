"""
NEXUS Base Strategy Interface
=============================
Abstract Base Class for all trading strategies.
Enforces standard interface for signal generation, state management, and parameters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

@dataclass
class Signal:
    symbol: str
    side: str # "BUY" or "SELL"
    strategy_name: str
    timestamp: datetime
    confidence: float # 0.0 to 1.0
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseStrategy(ABC):
    def __init__(self, name: str, version: str, parameters: Dict[str, Any]):
        self.name = name
        self.version = version
        self.parameters = parameters
        self.logger = logging.getLogger(f"nexus.strategy.{name}")
        self._active = False

    @abstractmethod
    async def analyze(self, market_data: Any) -> List[Signal]:
        """
        Analyze provided market data and generate signals.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def on_tick(self, tick: Any) -> Optional[Signal]:
        """
        Process a single tick (for HFT/Scalping logic).
        Optional implementation.
        """
        return None

    @abstractmethod
    async def on_candle(self, candle: Any) -> Optional[Signal]:
        """
        Process a closed candle.
        Optional implementation.
        """
        return None

    def start(self):
        self._active = True
        self.logger.info(f"Strategy {self.name} v{self.version} STARTED")

    def stop(self):
        self._active = False
        self.logger.info(f"Strategy {self.name} STOPPED")

    def update_parameters(self, new_params: Dict[str, Any]):
        self.parameters.update(new_params)
        self.logger.info(f"Parameters updated: {new_params}")
