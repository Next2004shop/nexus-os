import pandas as pd
import numpy as np
import logging
import logging

logger = logging.getLogger("NexusTA")

class TechnicalAnalysisEngine:
    """
    MODULE B: TECHNICAL ANALYSIS ENGINE
    Responsibility: Math, Structure, and Trend Identification
    """
    
    def analyze(self, df):
        """
        Applies Full Suite of Indicators to the DataFrame.
        Expects: timestamp, open, high, low, close, volume
        """
        if df.empty:
            return None

        # Helper for EMA
        def calculate_ema(series, span):
            return series.ewm(span=span, adjust=False).mean()

        # Helper for RSI
        def calculate_rsi(series, period=14):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        # 1. Trend Indicators
        df['ema_50'] = calculate_ema(df['close'], 50)
        df['ema_200'] = calculate_ema(df['close'], 200)
        
        # 2. Momentum
        df['rsi'] = calculate_rsi(df['close'], 14)
        
        # 3. Volatility (Bollinger Bands)
        sma = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['bb_upper'] = sma + (std * 2)
        df['bb_lower'] = sma - (std * 2)
        
        # 4. Market Structure (Simple Pivot High/Low)
        # Identify local mins/maxes for support/resistance (simplified)
        df['is_high'] = df['high'] == df['high'].rolling(10, center=True).max()
        df['is_low'] = df['low'] == df['low'].rolling(10, center=True).min()
        
        return df

    def get_signal_summary(self, df):
        """
        Returns a human-readable summary of the LATEST candle analysis.
        """
        if df is None or df.empty:
            return {"status": "NO_DATA"}
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Trend Detection
        trend = "NEUTRAL"
        if latest['close'] > latest['ema_200']:
            trend = "BULLISH" if latest['close'] > latest['ema_50'] else "WEAK_BULLISH"
        else:
            trend = "BEARISH" if latest['close'] < latest['ema_50'] else "WEAK_BEARISH"
            
        # RSI Condition
        rsi_status = "NEUTRAL"
        if latest['rsi'] > 70: rsi_status = "OVERBOUGHT"
        if latest['rsi'] < 30: rsi_status = "OVERSOLD"
        
        return {
            "trend": trend,
            "rsi": round(latest['rsi'], 2),
            "rsi_status": rsi_status,
            "close": latest['close']
        }
