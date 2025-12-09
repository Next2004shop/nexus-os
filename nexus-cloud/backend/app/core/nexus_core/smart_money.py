import pandas as pd
import logging

logger = logging.getLogger("NexusSmartMoney")

class SmartMoneyEngine:
    """
    MODULE C: SMART MONEY SCANNER
    Responsibility: Detecting Manipulation, Whales, and Liquidity Zones.
    """
    
    def analyze(self, df):
        """
        Detects anomalies in Volume and Price Action.
        """
        if df.empty: return None
        
        # 1. Volume Spikes (Whale Activity)
        # 3x standard deviation of volume
        vol_mean = df['tick_volume'].rolling(20).mean()
        vol_std = df['tick_volume'].rolling(20).std()
        df['whale_activity'] = df['tick_volume'] > (vol_mean + (3 * vol_std))
        
        # 2. Stop Hunts (Wicks)
        # Long wicks relative to body
        df['body_size'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        
        # Logic: Wick is 2x larger than body = Rejection/Stop Hunt
        df['stop_hunt_high'] = df['upper_wick'] > (2 * df['body_size'])
        df['stop_hunt_low'] = df['lower_wick'] > (2 * df['body_size'])
        
        return df

    def get_smc_summary(self, df):
        if df is None or df.empty: return {"status": "NO_DATA"}
        
        latest = df.iloc[-1]
        
        smc_status = "NORMAL"
        if latest['whale_activity']:
            smc_status = "WHALE_DETECTED"
        elif latest['stop_hunt_high']:
            smc_status = "LIQUIDITY_GRAB_HIGH"
        elif latest['stop_hunt_low']:
            smc_status = "LIQUIDITY_GRAB_LOW"
            
        return {
            "status": smc_status,
            "whale_volume": bool(latest['whale_activity'])
        }
