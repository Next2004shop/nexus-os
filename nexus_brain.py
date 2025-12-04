import os
import logging
import json
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusBrain")

# Initialize Vertex AI
# PROJECT_ID = "nexus-ai-god-mode" # REMOVED: Rely on ADC
LOCATION = "us-central1"

try:
    # Initialize without project_id to use Application Default Credentials (ADC)
    vertexai.init(location=LOCATION)
    model = GenerativeModel("gemini-pro")
    logger.info("🧠 VERTEX AI (GEMINI PRO): CONNECTED")
except Exception as e:
    logger.error(f"❌ VERTEX AI CONNECTION FAILED: {e}")
    model = None

class NexusBrain:
    def __init__(self):
        self.chat_session = None
        if model:
            self.chat_session = model.start_chat()

    def ask_gemini_chat(self, message: str, history: list = []) -> str:
        """
        Sends a message to Gemini Pro and returns the response.
        """
        if not model:
            return "⚠️ Nexus Brain Disconnected. Please check Google Cloud credentials."

        try:
            # Reconstruct history if needed, but for now we just send the message
            # Gemini SDK manages history in chat_session, but if we want stateless:
            response = self.chat_session.send_message(message)
            return response.text
        except Exception as e:
            logger.error(f"AI Chat Error: {e}")
            return "⚠️ I'm having trouble thinking right now. Please check my connection."

    def analyze_market(self, symbol: str, price_data: list) -> dict:
        """
        Analyzes market data using Gemini Pro to generate trading signals.
        """
        if not model:
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reasoning": "AI Brain Disconnected",
                "direction": "NEUTRAL"
            }

        try:
            # Construct Prompt
            prompt = f"""
            You are Nexus AI, an elite hedge fund trading algorithm.
            Analyze the following OHLC data for {symbol}:
            {json.dumps(price_data[-20:])} 
            
            Identify the trend, key levels, and provide a trade signal.
            Return ONLY a JSON object with this format:
            {{
                "signal": "BUY" or "SELL" or "HOLD",
                "confidence": <number 0-100>,
                "reasoning": "<short explanation>",
                "entry": <suggested entry price>,
                "tp": <suggested take profit>,
                "sl": <suggested stop loss>
            }}
            """
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up response if it contains markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            return json.loads(text)

        except Exception as e:
            logger.error(f"AI Analysis Error: {e}")
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reasoning": "Analysis Failed",
                "direction": "NEUTRAL"
            }

# Singleton Instance
brain = NexusBrain()
