from .base_strategy import BaseStrategy

class SwingStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Swing (Reversal)")

    def analyze(self, symbol: str, data: dict) -> dict:
        current = data['current']
        prev = data['prev']
        
        # Logic: MACD Reversal on Zero Line or Divergence (Simplified)
        signal = "HOLD"
        confidence = 0
        reason = ""

        # Bullish Reversal
        if current['macd'] > current['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            # Check if near zero line for better quality
            if -0.001 < current['macd'] < 0.001: 
                signal = "BUY"
                confidence = 75
                reason = "MACD Zero-Line Crossover (Bullish)"
            else:
                signal = "BUY"
                confidence = 60
                reason = "MACD Crossover (Bullish)"

        # Bearish Reversal
        elif current['macd'] < current['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            if -0.001 < current['macd'] < 0.001:
                signal = "SELL"
                confidence = 75
                reason = "MACD Zero-Line Crossover (Bearish)"
            else:
                signal = "SELL"
                confidence = 60
                reason = "MACD Crossover (Bearish)"

        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "strategy_name": self.name
        }
