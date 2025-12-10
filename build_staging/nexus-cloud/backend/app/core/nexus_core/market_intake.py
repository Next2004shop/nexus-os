import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger("NexusIntake")

class MarketIntake:
    """
    MODULE A: MARKET INTAKE LAYER
    Responsibility: Reliable High-Frequency Data Aggregation
    """
    def __init__(self):
        self.connected = False
        self._connect()

    def _connect(self):
        if not mt5.initialize():
            logger.critical("Nexus Market Intake: MT5 Initialization FAILED")
            self.connected = False
        else:
            logger.info("Nexus Market Intake: Connected to MT5 Feed")
            self.connected = True

    def get_latest_price(self, symbol):
        """Fetches the absolute latest Tick data."""
        if not self.connected: self._connect()
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            return {
                "bid": tick.bid,
                "ask": tick.ask,
                "time": datetime.fromtimestamp(tick.time),
                "volume": tick.volume_real
            }
        return None

    def get_candles(self, symbol, timeframe, n=100):
        """
        Fetches OHLCV Data.
        Timeframe map: 'M1', 'M5', 'H1', 'H4', 'D1'
        """
        if not self.connected: self._connect()
        
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        
        mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, n)
        
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to fetch candles for {symbol} {timeframe}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
