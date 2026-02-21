"""
NEXUS Backtest Runner
=====================
Script to execute backtests on strategies.

Usage:
    python scripts/run_backtest.py [symbol] [timeframe]
"""

import sys
import os
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "nexus-core")))

# Mocking config/env
os.environ["NEXUS_ENV"] = "simulation"

from unittest.mock import MagicMock
sys.modules["ccxt"] = MagicMock()
sys.modules["aiohttp"] = MagicMock()
sys.modules["aiohttp.ClientError"] = MagicMock()
sys.modules["aiohttp.ClientTimeout"] = MagicMock()

# Mock dependencies that might be triggered by imports
sys.modules["risk.risk_governor"] = MagicMock()
sys.modules["risk.capital_allocator"] = MagicMock()
sys.modules["command.router"] = MagicMock()
sys.modules["app.services.risk_governor"] = MagicMock()
sys.modules["app.services.execution"] = MagicMock()

from simulation.backtest_engine import BacktestRunner, DataLoader, BacktestResult
from strategies.breakout import BreakoutStrategy
from strategies.mean_reversion import MeanReversionStrategy
from app.services.market_data import Timeframe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.runner")

def generate_dummy_data(days=30) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=days*24, freq='H')
    
    # Random Walk
    np.random.seed(42)
    returns = np.random.normal(0, 0.002, len(dates))
    price_path = 100 * np.cumprod(1 + returns)
    
    data = []
    for i, date in enumerate(dates):
        close = price_path[i]
        open_p = close * (1 + np.random.normal(0, 0.001))
        high = max(open_p, close) * (1 + abs(np.random.normal(0, 0.001)))
        low = min(open_p, close) * (1 - abs(np.random.normal(0, 0.001)))
        vol = np.random.randint(100, 1000)
        
        data.append({
            "date": date,
            "open": open_p,
            "high": high,
            "low": low,
            "close": close,
            "volume": vol
        })
        
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    return df

async def main():
    logger.info("Initializing Backtest Runner...")
    
    # 1. Load Data
    # For MVP, we generate synthetic data if file doesn't exist
    data_file = "data/BTCUSD_H1.csv"
    if os.path.exists(data_file):
        logger.info(f"Loading data from {data_file}")
        data = DataLoader.load_csv(data_file, "BTCUSD", Timeframe.H1)
    else:
        logger.warning(f"Data file {data_file} not found. Generating SYNTHETIC data.")
        data = generate_dummy_data(days=60)
        
    if data.empty:
        logger.error("No data available.")
        return

    runner = BacktestRunner(initial_capital=10000.0)
    
    # 2. Run Breakout Strategy
    logger.info("--- Running BreakoutStrategy ---")
    strategy_bo = BreakoutStrategy()
    # Inject params if needed
    result_bo = await runner.run(strategy_bo, data)
    print_report(result_bo)
    
    # 3. Run Mean Reversion Strategy
    logger.info("--- Running MeanReversionStrategy ---")
    strategy_mr = MeanReversionStrategy()
    result_mr = await runner.run(strategy_mr, data)
    print_report(result_mr)

def print_report(res: BacktestResult):
    print("\n" + "="*40)
    print(f"REPORT: {res.strategy_name}")
    print("="*40)
    print(f"Period: {res.start_date} to {res.end_date}")
    print(f"Total Trades: {res.total_trades}")
    print(f"Win Rate:     {res.win_rate*100:.2f}%")
    print(f"Total PnL:    ${res.total_pnl:.2f}")
    print(f"Max Drawdown: {res.max_drawdown*100:.2f}%")
    print(f"Sharpe Ratio: {res.sharpe_ratio:.2f}")
    print("="*40 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
