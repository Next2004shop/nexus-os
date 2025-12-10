from .base_strategy import BaseStrategy

class ScalpingStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Scalping (Sniper)")

    def analyze(self, symbol: str, data: dict) -> dict:
        current = data['current']
        
        # Logic: RSI Extreme + Bollinger Band Breakout
        signal = "HOLD"
        confidence = 0
        reason = ""

        # Buy Condition
        if current['rsi'] < 30 and current['close'] < current['bb_lower']:
            signal = "BUY"
            confidence = 85
            reason = f"Oversold (RSI {current['rsi']:.1f}) + BB Lower Break"
        
        # Sell Condition
        elif current['rsi'] > 70 and current['close'] > current['bb_upper']:
            signal = "SELL"
            confidence = 85
            reason = f"Overbought (RSI {current['rsi']:.1f}) + BB Upper Break"

        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "strategy_name": self.name
        }
