"""
NEXUS Failsafe Mode Manager — Phase 11 (G)
=============================================

Three system states with logged transitions:
    1. NORMAL    — full trading allowed
    2. SAFE_MODE — reduced risk, restricted strategies
    3. LOCKDOWN  — no trading allowed, manual unlock required

Transitions are enforced, logged, and auditable.
"""

import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)

logger = logging.getLogger("nexus.failsafe")


class SystemMode(str, Enum):
    NORMAL = "NORMAL"
    SAFE_MODE = "SAFE_MODE"
    LOCKDOWN = "LOCKDOWN"


# Valid transitions: from → [allowed_to]
_VALID_TRANSITIONS = {
    SystemMode.NORMAL: [SystemMode.SAFE_MODE, SystemMode.LOCKDOWN],
    SystemMode.SAFE_MODE: [SystemMode.NORMAL, SystemMode.LOCKDOWN],
    SystemMode.LOCKDOWN: [SystemMode.SAFE_MODE, SystemMode.NORMAL],
}


class FailsafeManager:
    """
    Manages system operating mode with strict transition rules.
    All transitions are logged to security events.
    """

    _instance = None

    def __init__(self):
        self._mode: SystemMode = SystemMode.NORMAL
        self._transitions: List[Dict[str, Any]] = []
        self._locked_at: Optional[float] = None
        self._lock_reason: str = ""
        self._sec = get_security_logger()

    @classmethod
    def get_instance(cls) -> "FailsafeManager":
        if cls._instance is None:
            cls._instance = FailsafeManager()
        return cls._instance

    @property
    def mode(self) -> SystemMode:
        return self._mode

    @property
    def is_trading_allowed(self) -> bool:
        return self._mode != SystemMode.LOCKDOWN

    @property
    def is_normal(self) -> bool:
        return self._mode == SystemMode.NORMAL

    def transition_to(self, new_mode: SystemMode, reason: str, source: str = "SYSTEM") -> bool:
        """
        Transition to a new system mode.

        Returns True if transition succeeded, False if invalid.
        """
        if new_mode == self._mode:
            return True

        if new_mode not in _VALID_TRANSITIONS.get(self._mode, []):
            self._sec.warning(
                SecurityEventCategory.FAILSAFE_TRANSITION,
                f"Invalid transition: {self._mode.value} -> {new_mode.value}",
                details={"reason": reason, "source": source},
                source=source,
            )
            return False

        old_mode = self._mode
        self._mode = new_mode

        if new_mode == SystemMode.LOCKDOWN:
            self._locked_at = time.time()
            self._lock_reason = reason

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": old_mode.value,
            "to": new_mode.value,
            "reason": reason,
            "source": source,
        }
        self._transitions.append(record)

        severity = (
            SecuritySeverity.CRITICAL if new_mode == SystemMode.LOCKDOWN
            else SecuritySeverity.WARNING if new_mode == SystemMode.SAFE_MODE
            else SecuritySeverity.INFO
        )
        self._sec.log(
            SecurityEventCategory.FAILSAFE_TRANSITION,
            severity,
            f"Mode transition: {old_mode.value} -> {new_mode.value} | {reason}",
            details=record,
            source=source,
        )

        logger.warning(
            f"FAILSAFE: {old_mode.value} -> {new_mode.value} | {reason} | by {source}"
        )
        return True

    def enter_safe_mode(self, reason: str, source: str = "SYSTEM"):
        """Convenience: enter SAFE_MODE."""
        self.transition_to(SystemMode.SAFE_MODE, reason, source)

    def enter_lockdown(self, reason: str, source: str = "SYSTEM"):
        """Convenience: enter LOCKDOWN."""
        self.transition_to(SystemMode.LOCKDOWN, reason, source)

    def restore_normal(self, reason: str = "Manual restore", source: str = "ADMIN"):
        """Convenience: return to NORMAL."""
        self.transition_to(SystemMode.NORMAL, reason, source)

    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": self._mode.value,
            "is_trading_allowed": self.is_trading_allowed,
            "locked_at": self._locked_at,
            "lock_reason": self._lock_reason,
            "transition_count": len(self._transitions),
            "recent_transitions": self._transitions[-10:],
        }


def get_failsafe() -> FailsafeManager:
    return FailsafeManager.get_instance()
