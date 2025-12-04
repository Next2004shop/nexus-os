from .base_strategy import BaseStrategy

class TrendStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Trend Following (Surfer)")

    def analyze(self, symbol: str, data: dict) -> dict:
        current = data['current']
        
        # Logic: EMA Crossover + MACD Confirmation
        signal = "HOLD"
        confidence = 0
        reason = ""

        # Bullish Trend
        if current['ema_50'] > current['ema_200']:
            if current['macd'] > current['macd_signal'] and current['macd'] > 0:
                signal = "BUY"
                confidence = 80
                reason = "Golden Cross + MACD Bullish"
        
        # Bearish Trend
        elif current['ema_50'] < current['ema_200']:
            if current['macd'] < current['macd_signal'] and current['macd'] < 0:
                signal = "SELL"
                confidence = 80
                reason = "Death Cross + MACD Bearish"

        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "strategy_name": self.name
        }
