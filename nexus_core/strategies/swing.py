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

        macd = current.get('macd', 0)
        macd_signal = current.get('macd_signal', 0)
        prev_macd = prev.get('macd', 0)
        prev_macd_signal = prev.get('macd_signal', 0)

        # Bullish Reversal
        if macd > macd_signal and prev_macd <= prev_macd_signal:
            # Check if near zero line for better quality
            if -0.001 < macd < 0.001:
                signal = "BUY"
                confidence = 75
                reason = "MACD Zero-Line Crossover (Bullish)"
            else:
                signal = "BUY"
                confidence = 60
                reason = "MACD Crossover (Bullish)"

        # Bearish Reversal
        elif macd < macd_signal and prev_macd >= prev_macd_signal:
            if -0.001 < macd < 0.001:
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
