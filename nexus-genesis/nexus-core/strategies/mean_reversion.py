"""
NEXUS Mean Reversion Strategy
=============================
Ranging Market Strategy.

Logic:
1. Only active if Market Regime is 'RANGING' (checked via Strategic Engine or internal check).
2. Buy: Price <= Lower BB AND RSI < 30.
3. Sell: Price >= Upper BB AND RSI > 70.
4. Exit: Price touches SMA (Middle Band).
"""

from typing import List, Any, Optional
import pandas as pd
from datetime import datetime, timezone

from strategies.base_strategy import BaseStrategy, Signal
from app.services.market_data import AssetClass, Timeframe

class MeanReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="MeanReversionAlpha",
            version="1.0.0",
            parameters={
                "symbol": "BTCUSD", 
                "timeframe": Timeframe.H1,
                "period": 20,
                "dev": 2.0,
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30
            }
        )

    async def analyze(self, provider: Any) -> List[Signal]:
        signals = []
        symbol = self.parameters["symbol"]
        tf = self.parameters["timeframe"]
        
        try:
            # 1. Fetch Data
            df = await provider.get_ohlcv(
                symbol=symbol,
                asset_class=AssetClass.CRYPTO,
                timeframe=tf,
                bars=50
            )

            if df.empty or len(df) < max(self.parameters["period"], self.parameters["rsi_period"]):
                return []

            # 2. Indicators
            period = self.parameters["period"]
            df['sma'] = df['close'].rolling(period).mean()
            df['std'] = df['close'].rolling(period).std()
            df['upper'] = df['sma'] + (self.parameters["dev"] * df['std'])
            df['lower'] = df['sma'] - (self.parameters["dev"] * df['std'])
            
            # RSI Calculation
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.parameters["rsi_period"]).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.parameters["rsi_period"]).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            curr = df.iloc[-1]
            
            # 3. Logic
            # BUY: Price <= Lower Band AND RSI < 30
            if curr['close'] <= curr['lower'] and curr['rsi'] < self.parameters["rsi_oversold"]:
                 signals.append(Signal(
                    symbol=symbol,
                    side="BUY",
                    strategy_name=self.name,
                    timestamp=datetime.now(timezone.utc),
                    confidence=0.75,
                    reason=f"Mean Reversion Buy (RSI {curr['rsi']:.1f} < {self.parameters['rsi_oversold']})",
                    metadata={"close": curr['close'], "lower": curr['lower'], "rsi": curr['rsi']}
                ))

            # SELL: Price >= Upper Band AND RSI > 70
            elif curr['close'] >= curr['upper'] and curr['rsi'] > self.parameters["rsi_overbought"]:
                 signals.append(Signal(
                    symbol=symbol,
                    side="SELL",
                    strategy_name=self.name,
                    timestamp=datetime.now(timezone.utc),
                    confidence=0.75,
                    reason=f"Mean Reversion Sell (RSI {curr['rsi']:.1f} > {self.parameters['rsi_overbought']})",
                    metadata={"close": curr['close'], "upper": curr['upper'], "rsi": curr['rsi']}
                ))
                    
        except Exception as e:
            self.logger.error(f"Analysis Failed: {e}")

        return signals

    async def on_tick(self, tick: Any) -> Optional[Signal]:
        return None

    async def on_candle(self, candle: Any) -> Optional[Signal]:
        return None
