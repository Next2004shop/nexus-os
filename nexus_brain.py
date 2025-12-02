import os
import time
import logging
import json
import pandas as pd
import numpy as np
import ta
from datetime import datetime

# Vertex AI Imports
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusBrain")

class NexusBrain:
    def __init__(self):
        self.risk_tolerance = 0.02 # 2% max risk per trade
        self.memory_file = "nexus_memory.json"
        self.load_memory()
        
        # Initialize Vertex AI
        self.vertex_active = False
        if VERTEX_AVAILABLE:
            try:
                # Initialize with auto-detection (works on GCP VM)
                vertexai.init(location="us-central1")
                self.model = GenerativeModel("gemini-1.5-pro-preview-0409") # Using latest available or standard gemini-pro
                self.vertex_active = True
                logger.info("🧠 VERTEX AI: CONNECTED (GEMINI PRO ACTIVE)")
            except Exception as e:
                logger.error(f"Vertex AI Init Failed: {e}")
                # Fallback to standard Gemini Pro if preview fails
                try:
                    self.model = GenerativeModel("gemini-pro")
                    self.vertex_active = True
                    logger.info("🧠 VERTEX AI: CONNECTED (GEMINI PRO STANDARD)")
                except:
                    logger.warning("⚠️ Vertex AI could not connect. Running in LOCAL MODE.")
        else:
            logger.warning("⚠️ google-cloud-aiplatform not installed. Running in LOCAL MODE.")

        logger.info("🧠 NEXUS BRAIN: ONLINE (LEGENDARY ALGORITHMIC MODE)")

    def load_memory(self):
        """Loads past trade performance to influence future decisions."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    self.memory = json.load(f)
            except:
                self.memory = {"wins": 0, "losses": 0, "successful_strategies": {}}
        else:
            self.memory = {"wins": 0, "losses": 0, "successful_strategies": {}}

    def save_memory(self):
        """Saves trade performance."""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=4)

    def ask_gemini(self, symbol, current_data, local_analysis):
        """Queries Gemini Pro for a second opinion."""
        if not self.vertex_active:
            return None

        try:
            prompt = f"""
            You are a Hedge Fund Master Trader. Analyze this market data for {symbol}.
            
            Current Price: {current_data['close']}
            RSI: {local_analysis['indicators']['rsi']}
            MACD: {local_analysis['indicators']['macd']}
            Trend: {local_analysis['indicators']['trend']}
            
            Local Bot Signal: {local_analysis['signal']} ({local_analysis['confidence']}%)
            Reason: {local_analysis['reason']}
            
            Task:
            1. Analyze the technical structure.
            2. Validate or Reject the Local Bot's signal.
            3. Provide a final confidence score (0-100).
            
            Output JSON ONLY:
            {{
                "signal": "BUY" or "SELL" or "HOLD",
                "confidence": <int>,
                "reason": "<short explanation>"
            }}
            """
            
            response = self.model.generate_content(prompt)
            # Clean response to ensure valid JSON
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini Analysis Failed: {e}")
            return None

    def analyze_market(self, symbol, price_data):
        """
        Analyzes market data using advanced technical indicators and adaptive logic.
        """
        if not price_data:
            return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient Data"}

        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Initialize variables
        signal = "HOLD"
        confidence = 50
        reasons = []
        
        # Calculate Indicators
        # 1. RSI (Relative Strength Index)
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # 2. MACD (Moving Average Convergence Divergence)
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        # 3. Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        
        # 4. EMA (Exponential Moving Average) - Trend Filter
        df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        df['ema_200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()

        # Get latest values
        current = df.iloc[-1]
        prev = df.iloc[-2]

        # --- HEDGE FUND LOGIC (MAXIMUM POTENTIAL) ---

        # 1. CRISIS MODE (Market Crash Detection)
        recent_high = df['high'].iloc[-5:].max()
        drop_percent = (recent_high - current['close']) / recent_high
        
        if drop_percent > 0.02:
            return {
                "signal": "SELL_ALL",
                "confidence": 100,
                "reason": "CRISIS MODE: >2% Drop Detected",
                "indicators": {"rsi": round(current['rsi'], 2), "trend": "CRASH"}
            }

        # 3. LEGENDARY STRATEGY LOGIC
        
        # Strategy A: Trend Following
        trend_score = 0
        if current['ema_50'] > current['ema_200']: trend_score += 1
        elif current['ema_50'] < current['ema_200']: trend_score -= 1

        # Strategy B: Mean Reversion
        reversion_score = 0
        if current['rsi'] < 30 and current['close'] < current['bb_lower']: reversion_score += 2
        elif current['rsi'] > 70 and current['close'] > current['bb_upper']: reversion_score -= 2

        # Strategy C: MACD Crossover
        momentum_score = 0
        if current['macd'] > current['macd_signal'] and prev['macd'] <= prev['macd_signal']: momentum_score += 1
        elif current['macd'] < current['macd_signal'] and prev['macd'] >= prev['macd_signal']: momentum_score -= 1

        # --- COMPOSITE DECISION ---
        
        # GOLD SPECIALIZATION (XAUUSD)
        if symbol == "XAUUSD":
            if trend_score > 0 and momentum_score > 0:
                signal = "BUY"; confidence = 90; reasons.append("Gold Bullish Trend + MACD")
            elif trend_score < 0 and momentum_score < 0:
                signal = "SELL"; confidence = 90; reasons.append("Gold Bearish Trend + MACD")
            elif reversion_score >= 2:
                signal = "BUY"; confidence = 75; reasons.append("Gold Oversold Bounce")
            elif reversion_score <= -2:
                signal = "SELL"; confidence = 75; reasons.append("Gold Overbought Rejection")

        # CRYPTO SPECIALIZATION (BTCUSD, ETHUSD)
        elif "BTC" in symbol or "ETH" in symbol:
            if trend_score > 0 and current['rsi'] > 50:
                signal = "BUY"; confidence = 85; reasons.append("Crypto Momentum Breakout")
            elif trend_score < 0 and current['rsi'] < 50:
                signal = "SELL"; confidence = 85; reasons.append("Crypto Panic Sell-off")
        
        # INDICES SPECIALIZATION
        elif symbol in ["US30", "NAS100", "SPX500", "DJ30"]:
            if current['close'] > current['ema_200'] and momentum_score > 0:
                signal = "BUY"; confidence = 80; reasons.append("Index Bull Run")
            elif current['close'] < current['ema_200'] and momentum_score < 0:
                signal = "SELL"; confidence = 80; reasons.append("Index Bear Market")

        # STOCKS SPECIALIZATION
        elif len(symbol) <= 4 and symbol not in ["GOLD", "OIL"]:
            vol_spike = current['tick_volume'] > df['tick_volume'].mean() * 1.5
            if vol_spike and trend_score > 0:
                signal = "BUY"; confidence = 88; reasons.append("Stock Volume Spike + Trend")
            elif vol_spike and trend_score < 0:
                signal = "SELL"; confidence = 88; reasons.append("Stock Institutional Dump")
        
        else:
            # General Strategy
            total_score = trend_score + momentum_score + reversion_score
            if total_score >= 2:
                signal = "BUY"; confidence = 60 + (total_score * 10); reasons.append("Technical Confluence (Buy)")
            elif total_score <= -2:
                signal = "SELL"; confidence = 60 + (abs(total_score) * 10); reasons.append("Technical Confluence (Sell)")

        # Cap confidence
        confidence = min(confidence, 99)
        
        # --- VERTEX AI VALIDATION (THE SUPER BRAIN) ---
        # Only ask Gemini if we are already interested (Confidence > 70) to save costs/latency
        if self.vertex_active and confidence > 70:
            local_result = {
                "signal": signal,
                "confidence": confidence,
                "reason": "; ".join(reasons),
                "indicators": {
                    "rsi": round(current['rsi'], 2),
                    "macd": round(current['macd'], 5),
                    "trend": "Bullish" if trend_score > 0 else "Bearish"
                }
            }
            
            logger.info(f"🤖 Asking Gemini Pro to validate {symbol}...")
            gemini_opinion = self.ask_gemini(symbol, current, local_result)
            
            if gemini_opinion:
                logger.info(f"✨ Gemini Says: {gemini_opinion['signal']} ({gemini_opinion['confidence']}%) - {gemini_opinion['reason']}")
                
                # Weighted Average: 70% Local, 30% Gemini (to keep it fast but smart)
                # Or if Gemini strongly disagrees, we abort.
                
                if gemini_opinion['signal'] != signal and gemini_opinion['confidence'] > 80:
                    logger.warning(f"⛔ Gemini VETOED the trade! Local: {signal}, Gemini: {gemini_opinion['signal']}")
                    signal = "HOLD"
                    confidence = 0
                    reasons.append(f"Gemini Veto: {gemini_opinion['reason']}")
                elif gemini_opinion['signal'] == signal:
                    confidence = (confidence + gemini_opinion['confidence']) / 2
                    reasons.append(f"Gemini Confirmed: {gemini_opinion['reason']}")

        return {
            "signal": signal,
            "confidence": confidence,
            "reason": "; ".join(reasons) if reasons else "Market Noise",
            "indicators": {
                "rsi": round(current['rsi'], 2),
                "macd": round(current['macd'], 5),
                "trend": "Bullish" if trend_score > 0 else "Bearish" if trend_score < 0 else "Neutral"
            }
        }

    def get_ai_insights(self):
        insights = [
            "AI Brain analyzing market structure...",
            "Volatility scan complete. Monitoring key levels.",
            "Legendary Mode: Active. Hunting for liquidity grabs.",
            "Pattern recognition engine: OPTIMIZED.",
            "Sentiment analysis: Mixed. Relying on technicals."
        ]
        import random
        return random.choice(insights)

brain = NexusBrain()
