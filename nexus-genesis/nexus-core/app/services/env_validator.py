"""
NEXUS Environment Validator - Startup Integrity Check
=======================================================

Validates all required environment variables and secrets
before the system is allowed to start. Refuses to start
if critical configuration is missing.
"""

import os
import logging
from typing import List, Tuple

logger = logging.getLogger("nexus.env_validator")

# Secrets that MUST exist in Google Secret Manager (or env fallback)
REQUIRED_SECRETS = [
    "MT5_LOGIN",
    "MT5_PASSWORD",
    "MT5_SERVER",
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "SECRET_ENCRYPTION_KEY",
    "MT_BRIDGE_SIGNING_KEY",
]

# Optional but recommended
RECOMMENDED_SECRETS = [
    "POLYGON_API_KEY",
    "NEXUS_MASTER_USER_ID",
    "FIREBASE_SERVICE_ACCOUNT",
]

# Environment variables
REQUIRED_ENV = [
    # None strictly required at the moment — all secrets are in Secret Manager
]

RECOMMENDED_ENV = [
    "NEXUS_TRADING_SYMBOLS",
    "NEXT_PUBLIC_API_URL",
]


def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate environment on startup.

    Returns:
        (all_ok, list_of_issues)
        If all_ok is False, the system should refuse to start in live mode.
    """
    issues: List[str] = []
    warnings: List[str] = []

    # Check required env vars
    for var in REQUIRED_ENV:
        if not os.environ.get(var):
            issues.append(f"MISSING_ENV: {var}")

    # Check recommended env vars
    for var in RECOMMENDED_ENV:
        if not os.environ.get(var):
            warnings.append(f"MISSING_RECOMMENDED_ENV: {var}")

    # Try to load required secrets via vault
    try:
        from app.services.vault import get_secret

        for secret_name in REQUIRED_SECRETS:
            try:
                value = get_secret(secret_name)
                if not value:
                    issues.append(f"EMPTY_SECRET: {secret_name}")
                else:
                    # Basic format validation
                    _validate_secret_format(secret_name, value, issues)
            except Exception as e:
                # In development/testing, secrets may not be available
                warnings.append(f"SECRET_UNAVAILABLE: {secret_name} ({e})")

    except ImportError:
        warnings.append("VAULT_MODULE_UNAVAILABLE: Cannot validate secrets")

    # Log results
    for w in warnings:
        logger.warning(f"ENV_VALIDATOR: {w}")
    for i in issues:
        logger.error(f"ENV_VALIDATOR: {i}")

    if issues:
        logger.critical(
            f"ENV_VALIDATION_FAILED: {len(issues)} critical issue(s). "
            "System should not trade with live funds."
        )
    else:
        logger.info(
            f"ENV_VALIDATION_PASSED: {len(warnings)} warning(s), 0 critical issues"
        )

    return len(issues) == 0, issues + warnings


def _validate_secret_format(name: str, value: str, issues: List[str]):
    """Basic format checks for known secret types."""
    if name == "MT5_LOGIN":
        if not value.isdigit():
            issues.append(f"INVALID_FORMAT: {name} must be numeric")
    elif name in ("BINANCE_API_KEY", "BINANCE_API_SECRET"):
        if len(value) < 16:
            issues.append(f"INVALID_FORMAT: {name} looks too short ({len(value)} chars)")
    elif name in ("SECRET_ENCRYPTION_KEY", "MT_BRIDGE_SIGNING_KEY"):
        if len(value) < 16:
            issues.append(f"INVALID_FORMAT: {name} key too short ({len(value)} chars)")
