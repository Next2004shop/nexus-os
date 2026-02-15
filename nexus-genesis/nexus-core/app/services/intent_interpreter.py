"""
NEXUS Intent Interpreter — LLM-Powered Command Intelligence
=============================================================

Converts natural language commands into strict structured trade intent.

Uses Vertex AI (Gemini) with deterministic system prompt.
Never guesses. Never fabricates. Clarifies ambiguity.

Output schema:
{
    "intent": "trade_request | trade_suggestion | analysis | system_query",
    "asset": str | null,
    "direction": "buy | sell | none",
    "lot_size": float | null,
    "stop_loss": float | null,
    "take_profit": float | null,
    "confidence": float (0-1),
    "requires_confirmation": bool,
    "reasoning": str
}
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

logger = logging.getLogger("nexus.intent")

# Vertex AI config (same as intelligence.py)
PROJECT_ID = "nexus-dyron-777"
REGION = "us-central1"
GEMINI_MODEL = "gemini-1.5-pro"

_vertex_initialized = False


def _ensure_vertex_init():
    """Lazy init Vertex AI — same pattern as intelligence.py."""
    global _vertex_initialized
    if not _vertex_initialized:
        try:
            import vertexai
            vertexai.init(project=PROJECT_ID, location=REGION)
            _vertex_initialized = True
            logger.info(f"IntentInterpreter: Vertex AI initialized ({PROJECT_ID})")
        except Exception as e:
            logger.error(f"IntentInterpreter: Vertex AI init failed: {e}")
            raise


# =============================================================================
# INTENT DATA STRUCTURE
# =============================================================================

@dataclass
class TradeIntent:
    """Structured trade intent — the ONLY output of the interpreter."""
    intent: str          # trade_request | trade_suggestion | analysis | system_query
    asset: Optional[str] = None
    direction: Optional[str] = None  # buy | sell | none
    lot_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float = 0.0
    requires_confirmation: bool = True
    reasoning: str = ""
    raw_input: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeIntent":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)

    @classmethod
    def error_intent(cls, raw_input: str, error_msg: str) -> "TradeIntent":
        return cls(
            intent="error",
            confidence=0.0,
            requires_confirmation=True,
            reasoning=error_msg,
            raw_input=raw_input,
            error=error_msg
        )

    @classmethod
    def clarification_needed(cls, raw_input: str, question: str) -> "TradeIntent":
        return cls(
            intent="clarification_needed",
            confidence=0.0,
            requires_confirmation=True,
            reasoning=question,
            raw_input=raw_input
        )


# =============================================================================
# SYSTEM PROMPT — ABSOLUTE RULES
# =============================================================================

SYSTEM_PROMPT = """You are NEXUS Command Intelligence — a deterministic intent parser for an institutional trading system.

YOUR SOLE PURPOSE: Convert human text into a strict JSON trade intent.

OUTPUT FORMAT (always valid JSON, no markdown):
{
    "intent": "trade_request" | "trade_suggestion" | "analysis" | "system_query",
    "asset": "XAUUSD" | "BTCUSD" | "EURUSD" | ... | null,
    "direction": "buy" | "sell" | "none",
    "lot_size": <float> | null,
    "stop_loss": <float> | null,
    "take_profit": <float> | null,
    "confidence": <float 0.0 to 1.0>,
    "requires_confirmation": true | false,
    "reasoning": "<short explanation>"
}

ABSOLUTE RULES:
1. NEVER guess values. If lot_size is not stated, return null.
2. NEVER fabricate market data. If price is not given, do not invent one.
3. If the command is vague (e.g., "Do something"), set intent to "clarification_needed" and ask in reasoning.
4. If the command is ambiguous (e.g., "Buy" with no asset), set requires_confirmation to true and ask which asset.
5. Map common names to symbols:
   - "gold" = "XAUUSD"
   - "silver" = "XAGUSD"
   - "nasdaq", "nas", "NAS100" = "NAS100"
   - "bitcoin", "btc" = "BTCUSD"
   - "ethereum", "eth" = "ETHUSD"
   - "euro" = "EURUSD"
   - "pound" = "GBPUSD"
   - "yen" = "USDJPY"
   - "dow" = "US30"
6. For system queries (status, health, risk, help), set intent="system_query", direction="none".
7. For analysis questions ("Why is BTC dropping?"), set intent="analysis".
8. Trade requests need explicit direction. "Buy gold" = trade_request. "What about gold?" = analysis.
9. For follow-up commands like "Close it", "Increase lot", "Move SL":
   - Check the conversation context for the last trade
   - Resolve "it" / "that" to the last traded asset
   - If no context exists, set intent="clarification_needed"
10. confidence reflects how clear the user's intent is (not market prediction).
    - "Buy XAUUSD 0.1 lots SL 2300 TP 2400" = high confidence (0.95)
    - "Buy gold" = medium confidence (0.7)
    - "Maybe gold?" = low confidence (0.3)
11. requires_confirmation = true for any trade_request without explicit lot size and SL/TP.
12. NEVER return anything other than valid JSON.
"""


# =============================================================================
# INTERPRETER ENGINE
# =============================================================================

class IntentInterpreter:
    """
    LLM-powered intent interpreter.
    
    Accepts raw text, returns structured TradeIntent.
    Uses conversation context for follow-up resolution.
    """

    def __init__(self):
        self._model = None

    def _get_model(self):
        """Lazy-load Gemini model."""
        if self._model is None:
            _ensure_vertex_init()
            from vertexai.generative_models import GenerativeModel
            self._model = GenerativeModel(GEMINI_MODEL)
            logger.info("IntentInterpreter: Gemini model loaded")
        return self._model

    def interpret(
        self,
        text: str,
        conversation_context: Optional[Dict[str, Any]] = None,
        user_id: str = "unknown"
    ) -> TradeIntent:
        """
        Interpret natural language command into structured intent.
        
        Args:
            text: Raw user input
            conversation_context: Output from ConversationMemory.get_context()
            user_id: For logging
        
        Returns:
            TradeIntent with parsed fields
        """
        if not text or not text.strip():
            return TradeIntent.error_intent("", "Empty command received")

        text = text.strip()
        logger.info(f"Interpreting command from {user_id[:8]}...: {text[:80]}")

        try:
            model = self._get_model()

            # Build prompt with conversation context
            prompt_parts = [SYSTEM_PROMPT]

            if conversation_context:
                recent = conversation_context.get("recent_messages", [])
                if recent:
                    prompt_parts.append("\nCONVERSATION HISTORY (last messages):")
                    for msg in recent[-6:]:  # Last 6 messages max
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        prompt_parts.append(f"  {role}: {content}")

                trade_ctx = conversation_context.get("last_trade_context")
                if trade_ctx:
                    prompt_parts.append(f"\nLAST TRADE CONTEXT: {json.dumps(trade_ctx)}")

            prompt_parts.append(f"\nUSER COMMAND: {text}")
            prompt_parts.append("\nRespond with ONLY the JSON object:")

            full_prompt = "\n".join(prompt_parts)

            # Call LLM
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1,  # Near-deterministic
                    "max_output_tokens": 500
                }
            )

            result_text = response.text
            logger.info("Intent parsed successfully")

            # Parse JSON
            result_json = json.loads(result_text)

            # Normalize fields
            result_json["raw_input"] = text
            if result_json.get("direction"):
                result_json["direction"] = result_json["direction"].lower()
            if result_json.get("asset"):
                result_json["asset"] = result_json["asset"].upper()

            # Ensure confidence is bounded
            conf = result_json.get("confidence", 0.0)
            result_json["confidence"] = max(0.0, min(1.0, float(conf)))

            return TradeIntent.from_dict(result_json)

        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            return TradeIntent.error_intent(text, f"Failed to parse LLM response: {e}")

        except Exception as e:
            logger.error(f"Intent interpretation failed: {e}")
            return TradeIntent.error_intent(text, f"Interpretation error: {e}")

    def interpret_offline(self, text: str) -> TradeIntent:
        """
        Fallback interpreter when LLM is unavailable.
        Uses simple keyword matching (not a replacement for LLM).
        """
        text_lower = text.lower().strip()

        # System queries
        system_keywords = ["status", "health", "help", "risk", "how are you"]
        if any(kw in text_lower for kw in system_keywords):
            return TradeIntent(
                intent="system_query",
                direction="none",
                confidence=0.8,
                requires_confirmation=False,
                reasoning=f"Offline parse: system query detected",
                raw_input=text
            )

        # Simple trade detection
        asset_map = {
            "gold": "XAUUSD", "silver": "XAGUSD", "bitcoin": "BTCUSD",
            "btc": "BTCUSD", "eth": "ETHUSD", "ethereum": "ETHUSD",
            "nasdaq": "NAS100", "nas100": "NAS100", "euro": "EURUSD",
            "pound": "GBPUSD", "dow": "US30",
            "xauusd": "XAUUSD", "xagusd": "XAGUSD", "btcusd": "BTCUSD",
            "eurusd": "EURUSD", "gbpusd": "GBPUSD", "usdjpy": "USDJPY",
            "nas100": "NAS100", "us30": "US30",
        }

        direction = None
        if text_lower.startswith("buy") or " buy " in text_lower:
            direction = "buy"
        elif text_lower.startswith("sell") or " sell " in text_lower:
            direction = "sell"

        asset = None
        for keyword, symbol in asset_map.items():
            if keyword in text_lower:
                asset = symbol
                break

        if direction and asset:
            return TradeIntent(
                intent="trade_request",
                asset=asset,
                direction=direction,
                confidence=0.6,
                requires_confirmation=True,
                reasoning="Offline parse: basic trade intent detected (LLM unavailable)",
                raw_input=text
            )

        if asset and not direction:
            return TradeIntent(
                intent="analysis",
                asset=asset,
                direction="none",
                confidence=0.5,
                requires_confirmation=False,
                reasoning="Offline parse: asset mentioned without direction — treating as analysis",
                raw_input=text
            )

        return TradeIntent.clarification_needed(text, "Could not parse command (LLM offline). Please be more specific.")


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================
_interpreter: Optional[IntentInterpreter] = None


def get_interpreter() -> IntentInterpreter:
    """Get or create global IntentInterpreter instance."""
    global _interpreter
    if _interpreter is None:
        _interpreter = IntentInterpreter()
    return _interpreter
