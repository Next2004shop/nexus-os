"""
NEXUS Backtest Engine
=====================
Historical simulation harness for trading strategies.

Components:
1. DataLoader: Reads OHLCV data from CSV/Parquet.
2. BacktestRunner: Replays history, triggers strategy analysis, matches orders.
3. PerformanceAnalyzer: Calculates metrics (Sharpe, Drawdown, etc.).
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
import asyncio

from strategies.base_strategy import BaseStrategy, Signal
from app.services.market_data import Timeframe, AssetClass

logger = logging.getLogger("nexus.backtest")

@dataclass
class BacktestResult:
    """Result of a single backtest run."""
    strategy_name: str
    symbol: str
    timeframe: Timeframe
    start_date: datetime
    end_date: datetime
    total_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]

class DataLoader:
    """Loads historical data."""
    
    @staticmethod
    def load_csv(filepath: str, symbol: str, timeframe: Timeframe) -> pd.DataFrame:
        """
        Load CSV data. 
        Expected format: Date, Open, High, Low, Close, Volume
        """
        try:
            df = pd.read_csv(filepath)
            # Standardize columns
            df.columns = [c.lower() for c in df.columns]
            
            # Ensure required columns exist
            required = {'date', 'open', 'high', 'low', 'close', 'volume'}
            if not required.issubset(df.columns):
                raise ValueError(f"CSV missing columns. Required: {required}")
                
            # Parse dates
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV {filepath}: {e}")
            raise

class BacktestRunner:
    """Running engine for simulations."""
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.equity = initial_capital
        self.trades = []
        self.equity_curve = []
        
        # Position state
        self.position = None # Dict with 'side', 'entry_price', 'size', 'entry_time'
        
    async def run(self, strategy: BaseStrategy, data: pd.DataFrame) -> BacktestResult:
        """Run the backtest."""
        logger.info(f"Starting backtest for {strategy.name} on {len(data)} bars.")
        
        self.equity = self.initial_capital
        self.trades = []
        self.equity_curve = []
        self.position = None
        
        # Warmup period for indicators
        warmup = 50 
        
        for i in range(warmup, len(data)):
            # Slice mechanism to simulate strictly past data
            # In a real heavy simulation, we might optimize this to not copy data every step
            # For MVP, we pass the full dataframe up to index i
            
            # OPTIMIZATION: Strategy mostly needs latest data. 
            # We can rely on strategy.analyze() handling the logic.
            # But BaseStrategy.analyze takes a "Provider". 
            # We need to mock the Provider to return the sliced data.
            
            # Mock Provider
            window = data.iloc[:i+1]
            current_bar = window.iloc[-1]
            timestamp = current_bar.name
            
            # We need a way to inject this window into the strategy.
            # The strategy calls `provider.get_ohlcv`. 
            # We will handle this by creating a MockProvider that returns the window.
            
            mock_provider = MockProvider(window)
            
            signals = await strategy.analyze(mock_provider)
            
            # Process Signals
            self._process_signals(signals, current_bar, timestamp)
            
            # Mark to Market
            self._update_equity(current_bar, timestamp)
            
        # Close any open position at end
        if self.position:
            last_bar = data.iloc[-1]
            self._close_position(last_bar['close'], last_bar.name, "End of Data")
            
        return self._calculate_metrics(strategy, data)
        
    def _process_signals(self, signals: List[Signal], bar: pd.Series, timestamp: datetime):
        """Execute trade logic based on signals."""
        if not signals:
            return
            
        # Simple Logic: 1 active position at a time
        signal = signals[0] # Take high confidence one? Assuming list is sorted or we take first.
        
        # Entry
        if not self.position:
            if signal.side in ["BUY", "SELL"]:
                # Execute Entry
                price = bar['close'] # Assuming market order at close
                size = (self.equity * 0.1) / price # Fixed 10% equity sizing for test
                
                self.position = {
                    "side": signal.side,
                    "entry_price": price,
                    "size": size,
                    "entry_time": timestamp,
                    "symbol": signal.symbol
                }
                
                # Deduct Commission
                cost = price * size * self.commission
                self.equity -= cost
                
                logger.debug(f"ENTRY: {signal.side} {size:.4f} @ {price:.2f} at {timestamp}")
                
        # Exit (Reverse or specific exit signal if we had one)
        # Detailed strategy logic might allow "CLOSE" signals.
        # But BaseStrategy only has BUY/SELL/WAIT effectively (Signal side).
        # We assume if we are LONG and get SELL, we close and potentially flip.
        
        elif self.position:
            if (self.position['side'] == "BUY" and signal.side == "SELL") or \
               (self.position['side'] == "SELL" and signal.side == "BUY"):
                   
                self._close_position(bar['close'], timestamp, "Signal Reversal")
                
                # Flip? For now, just close.
                # If we want to flip, we'd proceed to open new position in next tick logic or here.
                # Keeping it simple: Close Only.

    def _close_position(self, price: float, timestamp: datetime, reason: str):
        """Close current position."""
        if not self.position:
            return
            
        entry_price = self.position['entry_price']
        size = self.position['size']
        side = self.position['side']
        
        if side == "BUY":
            pnl = (price - entry_price) * size
        else:
            pnl = (entry_price - price) * size
            
        # Deduct Commission
        pnl -= (price * size * self.commission)
        
        self.equity += pnl
        self.trades.append({
            "entry_time": self.position['entry_time'],
            "exit_time": timestamp,
            "side": side,
            "entry_price": entry_price,
            "exit_price": price,
            "size": size,
            "pnl": pnl,
            "reason": reason
        })
        
        logger.debug(f"EXIT: {side} @ {price:.2f}. PnL: {pnl:.2f}. Reason: {reason}")
        self.position = None

    def _update_equity(self, bar: pd.Series, timestamp: datetime):
        """Update floating equity curve."""
        current_equity = self.equity
        
        if self.position:
            price = bar['close']
            entry = self.position['entry_price']
            size = self.position['size']
            
            if self.position['side'] == "BUY":
                unrealized = (price - entry) * size
            else:
                unrealized = (entry - price) * size
                
            current_equity += unrealized
            
        self.equity_curve.append({
            "timestamp": timestamp,
            "equity": current_equity
        })

    def _calculate_metrics(self, strategy: BaseStrategy, data: pd.DataFrame) -> BacktestResult:
        """Calculate performance metrics."""
        if not self.trades:
            return BacktestResult(
                strategy_name=strategy.name,
                symbol=strategy.parameters.get("symbol", "UNKNOWN"),
                timeframe=strategy.parameters.get("timeframe", Timeframe.H1),
                start_date=data.index[0],
                end_date=data.index[-1],
                total_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                equity_curve=self.equity_curve,
                trades=[]
            )
            
        df_trades = pd.DataFrame(self.trades)
        wins = len(df_trades[df_trades['pnl'] > 0])
        win_rate = wins / len(df_trades) if len(df_trades) > 0 else 0.0
        total_pnl = df_trades['pnl'].sum()
        
        # Drawdown
        equity_series = pd.DataFrame(self.equity_curve).set_index("timestamp")['equity']
        peak = equity_series.expanding(min_periods=1).max()
        drawdown = (equity_series - peak) / peak
        max_drawdown = drawdown.min()
        
        # Sharpe (Daily approximation)
        # Resample to daily returns
        daily_equity = equity_series.resample('D').last().ffill()
        daily_returns = daily_equity.pct_change().dropna()
        if len(daily_returns) > 1 and daily_returns.std() != 0:
            sharpe = (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5)
        else:
            sharpe = 0.0
            
        return BacktestResult(
            strategy_name=strategy.name,
            symbol=strategy.parameters.get("symbol", "UNKNOWN"),
            timeframe=strategy.parameters.get("timeframe", Timeframe.H1),
            start_date=data.index[0],
            end_date=data.index[-1],
            total_trades=len(self.trades),
            win_rate=win_rate,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            equity_curve=self.equity_curve,
            trades=self.trades
        )


class MockProvider:
    """Mocks MarketProvider for Strategy Analysis."""
    def __init__(self, data_window: pd.DataFrame):
        self.data = data_window
        
    async def get_ohlcv(self, symbol, asset_class, timeframe, bars):
        """Returns the stored window."""
        return self.data.tail(bars) 
