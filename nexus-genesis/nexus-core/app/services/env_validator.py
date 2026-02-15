"""
NEXUS Environment Validator
============================

Validates required environment variables at startup.
Prevents silent misconfiguration in production.

Called during FastAPI startup_event() — before accepting traffic.
"""

import os
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("nexus.env_validator")


# =============================================================================
# ENVIRONMENT REQUIREMENTS
# =============================================================================

# Critical: System will not start without these
CRITICAL_VARS = [
    "GOOGLE_CLOUD_PROJECT",
]

# Required for trading: System starts but trading disabled
TRADING_VARS = [
    "GOOGLE_APPLICATION_CREDENTIALS",
]

# Optional: System starts with warnings
OPTIONAL_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "POLYGON_API_KEY",
    "ALLOWED_ORIGINS",
]


# =============================================================================
# VALIDATION
# =============================================================================

class EnvironmentStatus:
    """Result of environment validation."""
    
    def __init__(self):
        self.is_valid: bool = False
        self.critical_missing: List[str] = []
        self.trading_missing: List[str] = []
        self.optional_missing: List[str] = []
        self.trading_ready: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "environment_valid": self.is_valid,
            "trading_ready": self.trading_ready,
            "critical_missing": self.critical_missing,
            "trading_missing": self.trading_missing,
            "optional_missing": self.optional_missing,
        }


def validate_environment() -> EnvironmentStatus:
    """
    Validate all required environment variables.
    
    Returns EnvironmentStatus with details.
    Raises RuntimeError if critical vars are missing.
    """
    status = EnvironmentStatus()
    
    # Check critical vars
    for var in CRITICAL_VARS:
        if not os.getenv(var):
            status.critical_missing.append(var)
    
    # Check trading vars
    for var in TRADING_VARS:
        if not os.getenv(var):
            status.trading_missing.append(var)
    
    # Check optional vars
    for var in OPTIONAL_VARS:
        if not os.getenv(var):
            status.optional_missing.append(var)
    
    # Determine status
    status.is_valid = len(status.critical_missing) == 0
    status.trading_ready = status.is_valid and len(status.trading_missing) == 0
    
    # Log results
    if status.critical_missing:
        logger.critical(f"CRITICAL ENV VARS MISSING: {status.critical_missing}")
        logger.critical("System cannot start safely. Set these variables.")
        raise RuntimeError(
            f"Missing critical environment variables: {', '.join(status.critical_missing)}. "
            "Set these before starting NEXUS."
        )
    
    if status.trading_missing:
        logger.warning(f"Trading env vars missing: {status.trading_missing}")
        logger.warning("Trading functionality will be limited.")
    
    if status.optional_missing:
        logger.info(f"Optional env vars not set: {status.optional_missing}")
    
    logger.info(f"Environment validation: valid={status.is_valid}, trading_ready={status.trading_ready}")
    
    return status


# Global status (set during startup)
_env_status: EnvironmentStatus = None


def get_env_status() -> EnvironmentStatus:
    """Get cached environment status."""
    global _env_status
    if _env_status is None:
        _env_status = validate_environment()
    return _env_status
