import sys
import os
import asyncio
import logging

# Add nexus-core to path
core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../nexus-core"))
sys.path.append(core_path)
print(f"DEBUG: Added path: {core_path}")
print(f"DEBUG: Path exists: {os.path.exists(core_path)}")
print(f"DEBUG: strategies exists: {os.path.exists(os.path.join(core_path, 'strategies'))}")
print(f"DEBUG: strategies/__init__.py exists: {os.path.exists(os.path.join(core_path, 'strategies', '__init__.py'))}")

# Mocking config/env for standalone test
os.environ["NEXUS_ENV"] = "development"

# Mock app.services.market_data to avoid ccxt dependency
import sys
from unittest.mock import MagicMock

# Create mock module for app.services.market_data
mock_market_data = MagicMock()
mock_provider = MagicMock()
mock_market_data.get_provider.return_value = mock_provider
mock_market_data.AssetClass = MagicMock()
mock_market_data.Timeframe = MagicMock()

# Inject into sys.modules
sys.modules["app.services.market_data"] = mock_market_data
sys.modules["ccxt"] = MagicMock()
sys.modules["command.router"] = MagicMock()
sys.modules["command.schema"] = MagicMock()
sys.modules["risk.capital_allocator"] = MagicMock()
sys.modules["risk.risk_governor"] = MagicMock()
# StrategyEngine imports route_command and TradeCommand.
# We might need to mock them too if they have complex dependencies.

from strategies.strategy_engine import StrategyEngine
from strategies.breakout import BreakoutStrategy
from strategies.mean_reversion import MeanReversionStrategy

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_strategy")

async def test_loading():
    logger.info("Initializing Strategy Engine...")
    engine = StrategyEngine.get_instance()
    
    logger.info("Loading BreakoutStrategy...")
    s1 = BreakoutStrategy()
    engine.load_strategy(s1)
    
    logger.info("Loading MeanReversionStrategy...")
    s2 = MeanReversionStrategy()
    engine.load_strategy(s2)
    
    if len(engine.strategies) == 2:
        logger.info("SUCCESS: All strategies loaded.")
    else:
        logger.error(f"FAILURE: Expected 2 strategies, found {len(engine.strategies)}")
        
    # Verify parameters
    logger.info(f"Breakout Params: {s1.parameters}")
    logger.info(f"MeanReversion Params: {s2.parameters}")

if __name__ == "__main__":
    asyncio.run(test_loading())
