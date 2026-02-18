"""
NEXUS Telegram Auth Hardening — Phase 11 (D)
================================================

Hardens Telegram command interface:
    - Whitelisted chat IDs only
    - Command signature validation
    - Rate limiting (max 5 commands/min)
    - Lock high-risk commands behind confirmation flow
    - Log all command attempts

This module provides a middleware wrapper around Telegram commands.
Does NOT modify the existing TelegramService — wraps it.
"""

import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)

logger = logging.getLogger("nexus.telegram_hardening")

# Rate limit
MAX_COMMANDS_PER_MINUTE = 5

# High-risk commands requiring confirmation
HIGH_RISK_COMMANDS = {
    "/kill",          # Kill switch
    "/halt",          # Emergency halt (alias)
    "/trade",         # Manual trade
    "/reset",         # Reset circuit breaker
    "/unlock",        # Capital unlock
    "/restore",       # Disaster recovery
    "/lockdown",      # Enter lockdown
    "/resume",        # Resume trading after halt
    "/close_all",     # Close all open positions
}

# Confirmation timeout
CONFIRMATION_TIMEOUT_SECONDS = 30


class TelegramHardening:
    """
    Security wrapper for Telegram bot commands.

    Enforces:
        - Whitelist-only access
        - Rate limiting
        - High-risk command confirmation
        - Full command audit logging
    """

    _instance = None

    def __init__(self):
        self._allowed_chat_ids: Set[str] = set()
        self._rate_tracker: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self._command_log: List[Dict[str, Any]] = []
        self._blocked_count: int = 0
        self._allowed_count: int = 0
        self._sec = get_security_logger()

        # Load whitelisted chat IDs
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if chat_id:
            self._allowed_chat_ids = {s.strip() for s in chat_id.split(",") if s.strip()}
            logger.info(f"Telegram hardening: {len(self._allowed_chat_ids)} whitelisted chat ID(s)")

    @classmethod
    def get_instance(cls) -> "TelegramHardening":
        if cls._instance is None:
            cls._instance = TelegramHardening()
        return cls._instance

    def validate_command(
        self,
        chat_id: str,
        user_id: str,
        command: str,
        username: str = "",
    ) -> Tuple[bool, str]:
        """
        Validate a Telegram command before execution.

        Returns:
            (allowed, reason)
        """
        now = time.time()

        # Log every command attempt
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "chat_id": chat_id,
            "user_id": user_id,
            "username": username,
            "command": command,
            "allowed": False,
            "reason": "",
        }

        # Gate 1: Whitelist check
        if self._allowed_chat_ids and chat_id not in self._allowed_chat_ids:
            log_entry["reason"] = "NOT_WHITELISTED"
            self._log_command(log_entry)
            self._blocked_count += 1

            self._sec.critical(
                SecurityEventCategory.TELEGRAM_AUTH,
                f"Unauthorized Telegram access: chat={chat_id} user={user_id} cmd={command}",
                details=log_entry,
                source="TELEGRAM_HARDENING",
            )

            return False, "Unauthorized. Access denied."

        # Gate 2: Rate limiting
        user_key = f"{chat_id}:{user_id}"
        rate_window = self._rate_tracker[user_key]
        rate_window.append(now)

        # Count commands in last 60 seconds
        recent_count = sum(1 for t in rate_window if now - t < 60)
        if recent_count > MAX_COMMANDS_PER_MINUTE:
            log_entry["reason"] = "RATE_LIMITED"
            self._log_command(log_entry)
            self._blocked_count += 1

            self._sec.warning(
                SecurityEventCategory.TELEGRAM_AUTH,
                f"Telegram rate limit: {user_id} ({recent_count} cmd/min)",
                details=log_entry,
                source="TELEGRAM_HARDENING",
            )

            return False, f"Rate limited. Max {MAX_COMMANDS_PER_MINUTE} commands/minute."

        # Gate 3: High-risk confirmation check
        cmd_base = command.split()[0].lower() if command else ""
        if cmd_base in HIGH_RISK_COMMANDS:
            confirmation = self._pending_confirmations.get(user_key)

            if confirmation and confirmation.get("command") == cmd_base:
                # This is the confirmation — clear and allow
                elapsed = now - confirmation.get("requested_at", 0)
                if elapsed <= CONFIRMATION_TIMEOUT_SECONDS:
                    del self._pending_confirmations[user_key]
                    log_entry["allowed"] = True
                    log_entry["reason"] = "HIGH_RISK_CONFIRMED"
                    self._log_command(log_entry)
                    self._allowed_count += 1
                    return True, "CONFIRMED"
                else:
                    del self._pending_confirmations[user_key]
                    log_entry["reason"] = "CONFIRMATION_EXPIRED"
                    self._log_command(log_entry)
                    return False, "Confirmation expired. Send the command again."

            # Request confirmation
            self._pending_confirmations[user_key] = {
                "command": cmd_base,
                "requested_at": now,
            }
            log_entry["reason"] = "CONFIRMATION_REQUIRED"
            self._log_command(log_entry)

            return False, (
                f"HIGH-RISK COMMAND: {cmd_base}\n"
                f"Send the command again within {CONFIRMATION_TIMEOUT_SECONDS}s to confirm."
            )

        # All gates passed
        log_entry["allowed"] = True
        log_entry["reason"] = "ALLOWED"
        self._log_command(log_entry)
        self._allowed_count += 1

        return True, "ALLOWED"

    def _log_command(self, entry: Dict[str, Any]):
        """Record command in audit log."""
        self._command_log.append(entry)
        # Keep last 500 entries
        if len(self._command_log) > 500:
            self._command_log = self._command_log[-500:]

    def validate_signature(
        self,
        payload: str,
        signature: str,
        secret_key: str,
    ) -> bool:
        """
        Validate command signature using HMAC-SHA256.

        For advanced Telegram webhook setups where commands
        carry signatures for additional verification.
        """
        expected = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        valid = hmac.compare_digest(expected, signature)

        if not valid:
            self._sec.critical(
                SecurityEventCategory.TELEGRAM_AUTH,
                "Invalid command signature",
                details={"payload_hash": hashlib.sha256(payload.encode()).hexdigest()[:12]},
                source="TELEGRAM_HARDENING",
            )

        return valid

    def get_command_log(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent command audit log."""
        return self._command_log[-count:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "whitelisted_ids": len(self._allowed_chat_ids),
            "allowed_count": self._allowed_count,
            "blocked_count": self._blocked_count,
            "pending_confirmations": len(self._pending_confirmations),
            "total_commands_logged": len(self._command_log),
        }


def get_telegram_hardening() -> TelegramHardening:
    return TelegramHardening.get_instance()
