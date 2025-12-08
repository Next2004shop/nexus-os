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

        # Default values if keys missing (safety)
        rsi = current.get('rsi', 50)
        close = current.get('close', 0)
        bb_lower = current.get('bb_lower', 0)
        bb_upper = current.get('bb_upper', 999999)

        # Buy Condition
        if rsi < 30 and close < bb_lower:
            signal = "BUY"
            confidence = 85
            reason = f"Oversold (RSI {rsi:.1f}) + BB Lower Break"
        
        # Sell Condition
        elif rsi > 70 and close > bb_upper:
            signal = "SELL"
            confidence = 85
            reason = f"Overbought (RSI {rsi:.1f}) + BB Upper Break"

        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "strategy_name": self.name
        }
