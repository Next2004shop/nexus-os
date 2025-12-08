import os
import logging
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusBrain")

# Initialize OpenAI Client
API_KEY = os.getenv("OPENAI_API_KEY")
client = None

if API_KEY:
    try:
        client = OpenAI(api_key=API_KEY)
        logger.info("🧠 OPENAI (GPT-4): CONNECTED")
    except Exception as e:
        logger.error(f"❌ OPENAI CONNECTION FAILED: {e}")
else:
    logger.warning("⚠️ OPENAI_API_KEY not found in environment. AI features will be disabled.")

class NexusBrain:
    def __init__(self):
        pass

    def ask_gemini_chat(self, message: str, history: list = []) -> str:
        """
        Sends a message to OpenAI and returns the response.
        (Kept method name for compatibility with existing calls, or refactor caller)
        """
        if not client:
            return "⚠️ Nexus Brain Disconnected. Please set OPENAI_API_KEY."

        try:
            # Construct messages from history
            messages = [{"role": "system", "content": "You are Nexus AI, an advanced trading assistant."}]

            # Simple history reconstruction (can be improved)
            for msg in history:
                role = "user" if msg.get('sender') == 'user' else "assistant"
                messages.append({"role": role, "content": msg.get('text', '')})

            messages.append({"role": "user", "content": message})

            response = client.chat.completions.create(
                model="gpt-4o", # Using latest flagship
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI Chat Error: {e}")
            return "⚠️ I'm having trouble thinking right now. Please check my connection."

    def analyze_market(self, symbol: str, price_data: list) -> dict:
        """
        Analyzes market data using OpenAI to generate trading signals.
        """
        if not client:
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reasoning": "AI Brain Disconnected (Missing API Key)",
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
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise trading algorithm. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            text = response.choices[0].message.content
            return json.loads(text)

        except Exception as e:
            logger.error(f"AI Analysis Error: {e}")
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reasoning": f"Analysis Failed: {str(e)}",
                "direction": "NEUTRAL"
            }

# Singleton Instance
brain = NexusBrain()
