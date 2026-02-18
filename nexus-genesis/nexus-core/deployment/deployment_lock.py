"""
NEXUS Deployment Lock — Phase 12 (J)
=======================================

When DEPLOYMENT_LOCK = True:
    - Prevent major structural changes
    - Prevent risk model edits
    - Allow only parameter tuning

This prevents accidental destructive changes in production.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger("nexus.deployment_lock")


class DeploymentLock:
    """
    Deployment lock gate — blocks dangerous operations when locked.
    """

    _instance = None

    # Operations blocked when lock is active
    BLOCKED_OPERATIONS = [
        "MODIFY_RISK_MODEL",
        "MODIFY_STRATEGY_LOGIC",
        "MODIFY_COUNCIL_RULES",
        "MODIFY_ENSEMBLE_WEIGHTS",
        "MODIFY_SECURITY_CONFIG",
        "RESET_TRADE_HISTORY",
        "DROP_DATABASE",
        "MODIFY_AUTH_RULES",
        "DISABLE_SAFETY_CHECKS",
    ]

    # Operations always allowed (parameter tuning)
    ALLOWED_OPERATIONS = [
        "TUNE_POSITION_SIZE",
        "TUNE_RISK_MULTIPLIER",
        "UPDATE_EQUITY",
        "VIEW_STATUS",
        "VIEW_LOGS",
        "MANUAL_TRADE",
        "KILL_SWITCH",
        "RESUME_TRADING",
        "FORCE_BACKUP",
    ]

    def __init__(self):
        self._locked: bool = False
        self._locked_at: str = ""
        self._locked_by: str = ""
        self._blocked_attempts: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> "DeploymentLock":
        if cls._instance is None:
            cls._instance = DeploymentLock()
        return cls._instance

    def activate(self, reason: str = "Production lock", source: str = "CONFIG"):
        """Activate deployment lock."""
        self._locked = True
        self._locked_at = datetime.now(timezone.utc).isoformat()
        self._locked_by = source
        logger.warning(f"DEPLOYMENT LOCK ACTIVATED: {reason} by {source}")

    def deactivate(self, reason: str = "Manual unlock", source: str = "ADMIN"):
        """Deactivate deployment lock (admin only)."""
        self._locked = False
        logger.warning(f"DEPLOYMENT LOCK DEACTIVATED: {reason} by {source}")

    @property
    def is_locked(self) -> bool:
        return self._locked

    def check_operation(self, operation: str, source: str = "UNKNOWN") -> bool:
        """
        Check if an operation is allowed under current lock state.

        Returns True if allowed, False if blocked.
        """
        if not self._locked:
            return True

        operation_upper = operation.upper()

        # Always allowed operations pass through
        if operation_upper in self.ALLOWED_OPERATIONS:
            return True

        # Blocked operations are rejected
        if operation_upper in self.BLOCKED_OPERATIONS:
            self._blocked_attempts.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": operation_upper,
                "source": source,
                "status": "BLOCKED",
            })
            logger.warning(f"DEPLOYMENT LOCK: Blocked operation '{operation_upper}' from {source}")
            return False

        # Unknown operations — allow by default but log
        logger.info(f"DEPLOYMENT LOCK: Unknown operation '{operation_upper}' — allowing")
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "locked": self._locked,
            "locked_at": self._locked_at,
            "locked_by": self._locked_by,
            "blocked_operations": self.BLOCKED_OPERATIONS,
            "allowed_operations": self.ALLOWED_OPERATIONS,
            "blocked_attempts_count": len(self._blocked_attempts),
            "recent_blocked": self._blocked_attempts[-10:],
        }


def get_deployment_lock() -> DeploymentLock:
    return DeploymentLock.get_instance()
