"""
NEXUS Conversation Memory — Lightweight Session Context
=========================================================

Stores last 5 commands + 5 responses per user session.
Enables follow-up resolution: "Close it", "Move SL", "Increase lot".

RULES:
- No secrets stored
- No long-term persistence
- Auto-expires after 30 minutes of inactivity
- Session-keyed by user_id
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger("nexus.memory")

SESSION_EXPIRY_MINUTES = 30
MAX_HISTORY = 5


@dataclass
class MemoryEntry:
    """Single command or response entry."""
    role: str  # "user" or "assistant"
    content: str
    intent_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Session:
    """Per-user conversation session."""
    user_id: str
    history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY * 2))
    last_trade_context: Optional[Dict[str, Any]] = None
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self) -> bool:
        elapsed = datetime.now(timezone.utc) - self.last_active
        return elapsed > timedelta(minutes=SESSION_EXPIRY_MINUTES)

    def touch(self):
        self.last_active = datetime.now(timezone.utc)


class ConversationMemory:
    """
    Manages lightweight conversation memory across user sessions.
    
    Usage:
        memory = get_memory()
        memory.add_command("user_123", "Buy gold 0.1 lots")
        memory.add_response("user_123", {...intent_data...}, "Trade submitted")
        context = memory.get_context("user_123")
    """

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def _get_session(self, user_id: str) -> Session:
        """Get or create session, pruning expired ones."""
        session = self._sessions.get(user_id)
        if session is None or session.is_expired():
            if session and session.is_expired():
                logger.info(f"Session expired for {user_id[:8]}..., creating new")
            session = Session(user_id=user_id)
            self._sessions[user_id] = session
        session.touch()
        return session

    def add_command(self, user_id: str, text: str):
        """Record a user command."""
        session = self._get_session(user_id)
        session.history.append(MemoryEntry(role="user", content=text))

    def add_response(
        self,
        user_id: str,
        intent_data: Dict[str, Any],
        response_text: str
    ):
        """Record system response with parsed intent data."""
        session = self._get_session(user_id)
        session.history.append(MemoryEntry(
            role="assistant",
            content=response_text,
            intent_data=intent_data
        ))

        # Update trade context if this was a trade-related intent
        intent_type = intent_data.get("intent", "")
        if intent_type in ("trade_request", "trade_suggestion"):
            session.last_trade_context = {
                "asset": intent_data.get("asset"),
                "direction": intent_data.get("direction"),
                "lot_size": intent_data.get("lot_size"),
                "stop_loss": intent_data.get("stop_loss"),
                "take_profit": intent_data.get("take_profit"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def get_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation context for LLM prompt injection.
        
        Returns dict with:
        - recent_messages: last 5 messages (user + assistant combined)
        - last_trade_context: last trade asset/direction/params or None
        """
        session = self._get_session(user_id)

        messages = []
        for entry in session.history:
            msg = {"role": entry.role, "content": entry.content}
            if entry.intent_data:
                msg["parsed_intent"] = entry.intent_data
            messages.append(msg)

        return {
            "recent_messages": list(messages),
            "last_trade_context": session.last_trade_context
        }

    def get_last_trade_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get last trade context for follow-up resolution."""
        session = self._get_session(user_id)
        return session.last_trade_context

    def clear_session(self, user_id: str):
        """Clear a user's session."""
        if user_id in self._sessions:
            del self._sessions[user_id]

    def cleanup_expired(self):
        """Remove all expired sessions. Call periodically."""
        expired = [uid for uid, s in self._sessions.items() if s.is_expired()]
        for uid in expired:
            del self._sessions[uid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================
_memory: Optional[ConversationMemory] = None


def get_memory() -> ConversationMemory:
    """Get or create global ConversationMemory instance."""
    global _memory
    if _memory is None:
        _memory = ConversationMemory()
    return _memory
