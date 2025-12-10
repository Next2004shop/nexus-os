import pandas as pd
import ta

class TechnicalAnalysis:
    """
    Centralized Technical Analysis Library for Nexus.
    Wraps 'ta' library and provides custom indicators.
    """
    
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies all core indicators to the DataFrame.
        Expects columns: 'open', 'high', 'low', 'close', 'volume'.
        """
        if df.empty:
            return df

        # 1. Momentum
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['stoch_k'] = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close']).stoch()
        
        # 2. Trend
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        
        df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        df['ema_200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()
        
        # 3. Volatility
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
        
        # 4. Volume
        df['obv'] = ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
        
        return df
