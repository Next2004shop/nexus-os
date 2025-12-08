import os
import logging
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env.local")

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusBrain")

# Initialize OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = None

if api_key:
    try:
        client = openai.OpenAI(api_key=api_key)
        logger.info("🧠 NEXUS BRAIN (OPENAI GPT-4o): CONNECTED")
    except Exception as e:
        logger.error(f"❌ OPENAI CONNECTION FAILED: {e}")
else:
    logger.error("❌ OPENAI_API_KEY not found in .env.local")

class NexusBrain:
    def __init__(self):
        self.client = client

    def ask_gemini_chat(self, message: str, history: list = []) -> dict:
        """
        Sends a message to OpenAI GPT-4o and returns the response logic.
        Now supports TOOL CALLING for trade execution.
        """
        if not self.client:
            return {"type": "text", "content": "⚠️ Nexus Brain Disconnected. Please check OpenAI API Key."}

        try:
            # Define Tools
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "execute_trade",
                        "description": "Execute a trade (Buy or Sell) for a specific financial asset.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "The ticker symbol (e.g., EURUSD, BTCUSD, AAPL)"
                                },
                                "action": {
                                    "type": "string",
                                    "enum": ["BUY", "SELL"],
                                    "description": "The action to take"
                                },
                                "volume": {
                                    "type": "number",
                                    "description": "The volume/lot size (e.g., 0.01 for currency, 1.0 for stocks)"
                                }
                            },
                            "required": ["symbol", "action", "volume"]
                        }
                    }
                }
            ]

            # Construct Messages
            messages = [
                {"role": "system", "content": """
                You are Nexus AI. 
                
                DIRECTIVE:
                1. If the user says "Buy" or "Sell", you MUST use the 'execute_trade' function. 
                2. DO NOT respond with just text for trade commands. Use the tool.
                3. If parameters (Symbol, Volume) are missing, ask for them.
                4. Be concise.
                """}
            ]
            
            for msg in history[-5:]: 
                role = "user" if msg.get('sender') == 'user' else "assistant"
                messages.append({"role": role, "content": msg.get('text', '')})
                
            messages.append({"role": "user", "content": message})

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message

            # Check for generic response content
            content = response_message.content

            # Check for tool calls
            tool_calls = response_message.tool_calls
            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call.function.name == "execute_trade":
                        import json
                        args = json.loads(tool_call.function.arguments)
                        return {
                            "type": "trade_command",
                            "symbol": args.get("symbol"),
                            "action": args.get("action"),
                            "volume": args.get("volume"),
                            "text": f"Initializing {args.get('action')} order for {args.get('symbol')}..."
                        }
            
            return {"type": "text", "content": content}

        except Exception as e:
            logger.error(f"AI Chat Error: {e}")
            return {"type": "text", "content": "⚠️ I'm having trouble thinking right now. Please check my connection."}

    def analyze_market(self, symbol: str, price_data: list) -> dict:
        """
        Analyzes market data using OpenAI GPT-4o to generate trading signals.
        """
        if not self.client:
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reasoning": "AI Brain Disconnected",
                "direction": "NEUTRAL"
            }

        try:
            # Construct Prompt
            prompt = f"""
            You are Nexus AI, an elite hedge fund trading algorithm with a 90% win rate target.
            Your job is to analyze the market structure, trend, and volatility for {symbol}.
            
            DATA (Last 20 candles):
            {json.dumps(price_data[-20:])} 
            
            INSTRUCTIONS:
            1. Analyze the Trend (Uptrend, Downtrend, Ranging).
            2. Identify Key Support & Resistance Levels.
            3. Determine a Trade Signal (BUY, SELL, or HOLD).
            4. STRICT RISK MANAGEMENT:
               - Stop Loss (SL) must be tight (max 5-10% risk).
               - Take Profit (TP) must offer at least 1:2 Risk/Reward.
            
            OUTPUT FORMAT (JSON ONLY):
            {{
                "signal": "BUY" or "SELL" or "HOLD",
                "confidence": <number 0-100>,
                "reasoning": "<concise technical explanation>",
                "entry": <suggested entry price>,
                "tp": <suggested take profit>,
                "sl": <suggested stop loss>
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a high-frequency trading AI. Output valid JSON only."},
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
