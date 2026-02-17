"""
NEXUS Breakout Strategy
=======================
Standard Volatility Breakout Strategy.

Logic:
1. Calculate Bollinger Bands (20, 2).
2. Check for Close > Upper (Buy) or Close < Lower (Sell).
3. Confirm with Volume > 1.5x Moving Average Volume.
4. Filter by Regime (only TRENDING regimes allowed, via Strategic Engine check downstream).
"""

from typing import List, Any, Optional
import pandas as pd
from datetime import datetime, timezone

from strategies.base_strategy import BaseStrategy, Signal
from app.services.market_data import AssetClass, Timeframe

class BreakoutStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="BreakoutAlpha",
            version="1.0.0",
            parameters={
                "symbol": "BTCUSD", 
                "timeframe": Timeframe.H1,
                "period": 20,
                "dev": 2.0,
                "volume_mult": 1.2
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
                asset_class=AssetClass.CRYPTO, # TODO: Dynamic from symbol
                timeframe=tf,
                bars=50
            )

            if df.empty or len(df) < self.parameters["period"]:
                return []

            # 2. Indicators
            period = self.parameters["period"]
            df['sma'] = df['close'].rolling(period).mean()
            df['std'] = df['close'].rolling(period).std()
            df['upper'] = df['sma'] + (self.parameters["dev"] * df['std'])
            df['lower'] = df['sma'] - (self.parameters["dev"] * df['std'])
            df['vol_ma'] = df['volume'].rolling(period).mean()

            curr = df.iloc[-1]
            prev = df.iloc[-2]

            # 3. Logic
            # BUY: Crossover Upper + Volume Pulse
            if curr['close'] > curr['upper'] and prev['close'] <= prev['upper']:
                if curr['volume'] > (curr['vol_ma'] * self.parameters["volume_mult"]):
                    signals.append(Signal(
                        symbol=symbol,
                        side="BUY",
                        strategy_name=self.name,
                        timestamp=datetime.now(timezone.utc),
                        confidence=0.85,
                        reason=f"Bollinger Breakout (Vol x{curr['volume']/curr['vol_ma']:.1f})",
                        metadata={"close": curr['close'], "upper": curr['upper']}
                    ))

            # SELL: Crossunder Lower + Volume Pulse
            elif curr['close'] < curr['lower'] and prev['close'] >= prev['lower']:
                 if curr['volume'] > (curr['vol_ma'] * self.parameters["volume_mult"]):
                    signals.append(Signal(
                        symbol=symbol,
                        side="SELL",
                        strategy_name=self.name,
                        timestamp=datetime.now(timezone.utc),
                        confidence=0.85,
                        reason=f"Bollinger Breakdown (Vol x{curr['volume']/curr['vol_ma']:.1f})",
                        metadata={"close": curr['close'], "lower": curr['lower']}
                    ))
                    
        except Exception as e:
            self.logger.error(f"Analysis Failed: {e}")

        return signals

    async def on_tick(self, tick: Any) -> Optional[Signal]:
        return None

    async def on_candle(self, candle: Any) -> Optional[Signal]:
        return None
