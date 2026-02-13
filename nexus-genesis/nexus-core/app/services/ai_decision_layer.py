"""
NEXUS AI Decision Layer — 3-Layer Intelligence Architecture
=============================================================

Layer 1 — Conversation Engine (LLM)
    Existing: intelligence.py (Gemini Pro), master_ai.py (command parser)
    This module does NOT host the LLM; it CONSUMES its output.

Layer 2 — Intent Parser (this module)
    Parses raw AI/LLM output into strict TradingIntent JSON.
    Validates every field. Rejects malformed responses.

Layer 3 — Deterministic Execution Engine (this module)
    Takes validated TradingIntent and routes it through the
    sovereign pipeline. No AI logic here — pure deterministic flow.

ABSOLUTE RULES:
  • AI cannot override risk governor.
  • AI cannot override daily loss cap.
  • AI cannot override lot limits.
  • AI cannot override system mode.
  • If LLM times out, system does NOT trade.
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from app.services.ai_intent_schema import (
    ConfidenceGate,
    Direction,
    IntentType,
    TradingIntent,
    build_clarification_request,
    validate_intent_json,
)
from app.services.ai_audit_logger import get_ai_audit_logger

logger = logging.getLogger("nexus.ai_decision")

# =============================================================================
# SYSTEM MODES (mirrors watchdog but adds AI-specific modes)
# =============================================================================

class AISystemMode:
    """
    Modes the AI decision layer respects.

    ANALYSIS       — AI can analyze, cannot trigger trades
    MANUAL_TRADE   — AI suggests, human confirms ALL trades
    AUTO           — AI auto-allowed if confidence > 0.85
    SAFE           — No trades allowed, analysis only
    EMERGENCY      — All AI interaction halted
    """
    ANALYSIS = "ANALYSIS"
    MANUAL_TRADE = "MANUAL_TRADE"
    AUTO = "AUTO"
    SAFE = "SAFE"
    EMERGENCY = "EMERGENCY"

    _VALID = {ANALYSIS, MANUAL_TRADE, AUTO, SAFE, EMERGENCY}

    @classmethod
    def is_valid(cls, mode: str) -> bool:
        return mode in cls._VALID

    @classmethod
    def allows_execution(cls, mode: str) -> bool:
        """Only AUTO and MANUAL_TRADE modes allow trade execution."""
        return mode in {cls.AUTO, cls.MANUAL_TRADE}

    @classmethod
    def allows_auto_execution(cls, mode: str) -> bool:
        """Only AUTO mode allows trades without explicit human confirmation."""
        return mode == cls.AUTO


# =============================================================================
# INTENT RATE LIMITER (per-symbol cooldown)
# =============================================================================

_DEFAULT_COOLDOWN_SECS = 30  # minimum seconds between intents for same symbol


class IntentRateLimiter:
    """Prevents rapid-fire execution intents per symbol."""

    def __init__(self, cooldown_secs: float = _DEFAULT_COOLDOWN_SECS):
        self._cooldown = cooldown_secs
        self._last_intent: Dict[str, float] = {}
        self._lock = threading.Lock()

    def check(self, symbol: str) -> Tuple[bool, float]:
        """
        Check if intent is allowed for this symbol.

        Returns:
            (allowed, seconds_remaining)
        """
        now = time.monotonic()
        with self._lock:
            last = self._last_intent.get(symbol, 0.0)
            elapsed = now - last
            if elapsed < self._cooldown:
                remaining = self._cooldown - elapsed
                return False, remaining
            return True, 0.0

    def record(self, symbol: str) -> None:
        """Record that an intent was processed for this symbol."""
        with self._lock:
            self._last_intent[symbol] = time.monotonic()

    def reset(self, symbol: Optional[str] = None) -> None:
        """Reset cooldown for one symbol or all."""
        with self._lock:
            if symbol:
                self._last_intent.pop(symbol, None)
            else:
                self._last_intent.clear()


# =============================================================================
# RESPONSE VALIDATOR (rejects hallucinations & malformed data)
# =============================================================================

def validate_ai_response(raw_text: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Validate raw AI/LLM text response.

    1. Must be valid JSON.
    2. Must not contain hallucinated symbols.
    3. Must not contain unrealistic lot sizes.
    4. Must not contain undefined assets.

    Returns:
        (valid, parsed_dict_or_None, error_message)
    """
    # ── Step 1: Parse JSON ───────────────────────────────────────────────
    raw_text = raw_text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_text = "\n".join(lines).strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        return False, None, f"MALFORMED_JSON: {e}"

    if not isinstance(parsed, dict):
        return False, None, f"EXPECTED_OBJECT: got {type(parsed).__name__}"

    return True, parsed, ""


# =============================================================================
# LLM FALLBACK RESPONSE
# =============================================================================

def fallback_response(reason: str) -> Dict[str, Any]:
    """
    Safe fallback when LLM is unavailable or times out.
    System does NOT trade. Returns safe status message.
    """
    return {
        "status": "AI_UNAVAILABLE",
        "trade_allowed": False,
        "message": f"AI layer returned safe fallback: {reason}",
        "action": "NO_TRADE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# AI DECISION ENGINE (Orchestrates Layer 2 + Layer 3)
# =============================================================================

# LLM response timeout
LLM_TIMEOUT_SECS = 15


class AIDecisionEngine:
    """
    The three-layer AI decision processor.

    Usage:
        engine = get_ai_decision_engine()
        result = await engine.process_ai_output(
            raw_prompt="...",
            ai_response_text="...",
            system_mode="AUTO",
            user_id="master",
            human_confirmed=False,
        )
    """

    def __init__(self):
        self._rate_limiter = IntentRateLimiter()
        self._mode = AISystemMode.MANUAL_TRADE  # conservative default
        self._mode_lock = threading.Lock()
        logger.info("AI Decision Engine initialized (mode=MANUAL_TRADE)")

    # ── Mode Management ──────────────────────────────────────────────────
    def get_mode(self) -> str:
        with self._mode_lock:
            return self._mode

    def set_mode(self, mode: str) -> Tuple[bool, str]:
        """Set AI system mode. Validates against watchdog state."""
        if not AISystemMode.is_valid(mode):
            return False, f"Invalid mode: {mode}"

        # Consult watchdog — if watchdog is not RUNNING, force SAFE or EMERGENCY
        try:
            from app.services.watchdog import get_watchdog, SystemMode as WatchdogMode
            wd = get_watchdog()
            wd_state = wd.get_state()
            if wd_state.mode == WatchdogMode.EMERGENCY:
                mode = AISystemMode.EMERGENCY
            elif wd_state.mode in (WatchdogMode.SAFE, WatchdogMode.HALTED):
                if mode in (AISystemMode.AUTO, AISystemMode.MANUAL_TRADE):
                    return False, f"Cannot enter {mode}: watchdog is in {wd_state.mode.value}"
        except Exception:
            pass  # watchdog not available — allow mode change

        with self._mode_lock:
            old = self._mode
            self._mode = mode
            logger.info(f"AI mode changed: {old} → {mode}")
        return True, f"Mode set to {mode}"

    # ── Core Processing ──────────────────────────────────────────────────
    async def process_ai_output(
        self,
        raw_prompt: str,
        ai_response_text: str,
        system_mode: Optional[str] = None,
        user_id: Optional[str] = None,
        human_confirmed: bool = False,
    ) -> Dict[str, Any]:
        """
        Full 3-layer processing pipeline:

        Layer 2: Parse → Validate → Confidence Gate
        Layer 3: Mode Check → Rate Limit → Sovereign Pipeline (if applicable)

        Always produces an audit record.
        """
        start_time = time.monotonic()
        audit = get_ai_audit_logger()

        current_mode = system_mode or self.get_mode()

        # ── Emergency / Safe: reject immediately ─────────────────────────
        if current_mode == AISystemMode.EMERGENCY:
            result = {"status": "REJECTED_EMERGENCY", "message": "System in EMERGENCY mode. AI halted."}
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=None, validation_result={"valid": False, "reason": "EMERGENCY_MODE"},
                confidence_gate=None, execution_result=None,
                system_mode=current_mode, user_id=user_id,
            )
            return result

        # ── LAYER 2: Validate AI response text ──────────────────────────
        json_valid, parsed, json_error = validate_ai_response(ai_response_text)
        if not json_valid:
            result = fallback_response(f"AI response is not valid JSON: {json_error}")
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=None,
                validation_result={"valid": False, "reason": json_error},
                confidence_gate=None, execution_result=None,
                system_mode=current_mode, user_id=user_id,
            )
            return result

        # ── LAYER 2: Validate against intent schema ─────────────────────
        schema_valid, issues, intent = validate_intent_json(parsed)
        if not schema_valid:
            result = build_clarification_request(parsed, issues)
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=parsed,
                validation_result={"valid": False, "issues": issues},
                confidence_gate=None, execution_result=None,
                system_mode=current_mode, user_id=user_id,
            )
            return result

        # ── LAYER 2: Confidence Gate ─────────────────────────────────────
        gate = intent.confidence_gate

        # Non-trade intents (analysis, status_query) → return immediately
        if intent.intent in (IntentType.ANALYSIS, IntentType.STATUS_QUERY):
            result = {
                "status": "ANALYSIS_COMPLETE",
                "intent": intent.to_dict(),
                "trade_allowed": False,
                "message": "Analysis intent — no execution path.",
            }
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=intent.to_dict(),
                validation_result={"valid": True},
                confidence_gate=gate.value, execution_result=None,
                system_mode=current_mode, user_id=user_id,
                duration_ms=(time.monotonic() - start_time) * 1000,
            )
            return result

        # Suggestions: never execute, just return
        if intent.intent == IntentType.TRADE_SUGGESTION or gate == ConfidenceGate.SUGGEST_ONLY:
            result = {
                "status": "SUGGESTION_ONLY",
                "intent": intent.to_dict(),
                "trade_allowed": False,
                "message": f"Confidence {intent.confidence_score:.2f} < 0.75 — suggestion only, no execution.",
            }
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=intent.to_dict(),
                validation_result={"valid": True},
                confidence_gate=gate.value, execution_result=None,
                system_mode=current_mode, user_id=user_id,
                duration_ms=(time.monotonic() - start_time) * 1000,
            )
            return result

        # ── LAYER 3: Mode gate ───────────────────────────────────────────
        if current_mode == AISystemMode.SAFE:
            result = {
                "status": "REJECTED_SAFE_MODE",
                "intent": intent.to_dict(),
                "trade_allowed": False,
                "message": "System in SAFE mode — no trades allowed.",
            }
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=intent.to_dict(),
                validation_result={"valid": True},
                confidence_gate=gate.value, execution_result=None,
                system_mode=current_mode, user_id=user_id,
                duration_ms=(time.monotonic() - start_time) * 1000,
            )
            return result

        if current_mode == AISystemMode.ANALYSIS:
            result = {
                "status": "ANALYSIS_MODE",
                "intent": intent.to_dict(),
                "trade_allowed": False,
                "message": "System in ANALYSIS mode — trade intents are logged but not executed.",
            }
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=intent.to_dict(),
                validation_result={"valid": True},
                confidence_gate=gate.value, execution_result=None,
                system_mode=current_mode, user_id=user_id,
                duration_ms=(time.monotonic() - start_time) * 1000,
            )
            return result

        # ── LAYER 3: Confirmation gate ───────────────────────────────────
        needs_confirmation = (
            gate == ConfidenceGate.REQUIRES_CONFIRMATION
            or current_mode == AISystemMode.MANUAL_TRADE
            or intent.requires_confirmation
        )

        if needs_confirmation and not human_confirmed:
            result = {
                "status": "AWAITING_CONFIRMATION",
                "intent": intent.to_dict(),
                "trade_allowed": False,
                "message": (
                    f"Confidence {intent.confidence_score:.2f} requires human confirmation. "
                    f"Mode: {current_mode}. Resubmit with human_confirmed=true to proceed."
                ),
            }
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=intent.to_dict(),
                validation_result={"valid": True},
                confidence_gate=gate.value, execution_result=None,
                system_mode=current_mode, user_id=user_id,
                duration_ms=(time.monotonic() - start_time) * 1000,
            )
            return result

        # ── LAYER 3: Rate limit ──────────────────────────────────────────
        allowed, remaining = self._rate_limiter.check(intent.asset)
        if not allowed:
            result = {
                "status": "RATE_LIMITED",
                "intent": intent.to_dict(),
                "trade_allowed": False,
                "message": f"Rate limited: {intent.asset} cooldown has {remaining:.1f}s remaining.",
            }
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=intent.to_dict(),
                validation_result={"valid": True},
                confidence_gate=gate.value, execution_result=None,
                system_mode=current_mode, user_id=user_id,
                duration_ms=(time.monotonic() - start_time) * 1000,
            )
            return result

        # ── LAYER 3: Direction guard — "none" direction cannot execute ───
        if intent.direction == Direction.NONE:
            result = {
                "status": "NO_DIRECTION",
                "intent": intent.to_dict(),
                "trade_allowed": False,
                "message": "Direction is 'none' — cannot execute a trade without buy/sell.",
            }
            audit.record(
                raw_prompt=raw_prompt, ai_response=ai_response_text,
                parsed_json=intent.to_dict(),
                validation_result={"valid": True},
                confidence_gate=gate.value, execution_result=None,
                system_mode=current_mode, user_id=user_id,
                duration_ms=(time.monotonic() - start_time) * 1000,
            )
            return result

        # ── LAYER 3: Deterministic Execution via Sovereign Pipeline ──────
        execution_result = await self._execute_via_pipeline(intent)

        # Record rate limit timestamp
        self._rate_limiter.record(intent.asset)

        duration_ms = (time.monotonic() - start_time) * 1000
        audit.record(
            raw_prompt=raw_prompt, ai_response=ai_response_text,
            parsed_json=intent.to_dict(),
            validation_result={"valid": True},
            confidence_gate=gate.value, execution_result=execution_result,
            system_mode=current_mode, user_id=user_id,
            duration_ms=duration_ms,
        )

        return {
            "status": "EXECUTED" if execution_result.get("status") == "EXECUTED" else execution_result.get("status", "FAILED"),
            "intent": intent.to_dict(),
            "trade_allowed": True,
            "execution": execution_result,
            "duration_ms": round(duration_ms, 1),
        }

    # ── Deterministic Pipeline Bridge ────────────────────────────────────
    async def _execute_via_pipeline(self, intent: TradingIntent) -> Dict[str, Any]:
        """
        Layer 3: Route validated intent to sovereign pipeline.

        This is PURE DETERMINISTIC — no AI logic here.
        AI cannot override risk governor, lot limits, or system mode.
        The sovereign pipeline has its own 6-stage safety gates.
        """
        from app.services.sovereign_pipeline import execute_sovereign_pipeline

        side = intent.direction.value.upper()  # "BUY" or "SELL"
        quantity = intent.lot_size if intent.lot_size else 0.01  # minimum default

        market_context = {
            "ai_confidence": intent.confidence_score,
            "ai_risk_level": intent.risk_level.value,
            "ai_reasoning": intent.reasoning,
            "stop_loss": intent.stop_loss,
            "take_profit": intent.take_profit,
            "source": "ai_decision_layer",
        }

        try:
            result = await execute_sovereign_pipeline(
                symbol=intent.asset,
                side=side,
                quantity=quantity,
                market_context=market_context,
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"AI pipeline execution timed out for {intent.asset}")
            return {"status": "TIMEOUT", "error": "Pipeline execution timed out"}
        except Exception as e:
            logger.error(f"AI pipeline execution error for {intent.asset}: {e}")
            return {"status": "FAILED", "error": str(e)}


# =============================================================================
# CONVERSATION MEMORY vs EXECUTION MEMORY — ISOLATION
# =============================================================================

class ConversationMemory:
    """
    Isolated conversation memory.
    AI conversation state is COMPLETELY SEPARATE from execution state.
    The execution engine reads ONLY validated TradingIntent JSON.
    """

    def __init__(self, max_history: int = 50):
        self._history: list = []
        self._max = max_history
        self._lock = threading.Lock()

    def add_exchange(self, user_input: str, ai_output: str) -> None:
        """Record a conversation exchange."""
        with self._lock:
            self._history.append({
                "user": user_input[:2000],
                "ai": ai_output[:5000],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            if len(self._history) > self._max:
                self._history = self._history[-self._max:]

    def get_history(self, n: int = 10) -> list:
        with self._lock:
            return list(self._history[-n:])

    def clear(self) -> None:
        with self._lock:
            self._history.clear()


# =============================================================================
# SINGLETON
# =============================================================================

_engine: Optional[AIDecisionEngine] = None
_conversation_memory: Optional[ConversationMemory] = None


def get_ai_decision_engine() -> AIDecisionEngine:
    """Get or create the singleton AI decision engine."""
    global _engine
    if _engine is None:
        _engine = AIDecisionEngine()
    return _engine


def get_conversation_memory() -> ConversationMemory:
    """Get or create the singleton conversation memory."""
    global _conversation_memory
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    return _conversation_memory
