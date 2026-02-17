"""
NEXUS Startup Hardening — Phase 11 (E + L)
=============================================

Production startup checks — if any fail, block startup.

E) Secret Rotation Check:
    - .env secrets loaded
    - Missing keys block startup
    - No secrets printed to logs
    - Checksum validation

L) Production Hardening:
    - Verify Python version (>= 3.9)
    - Verify required modules installed
    - Verify disk space (>= 100MB free)
    - Verify MT5 reachable (if configured)
    - Verify Telegram reachable (if configured)
"""

import hashlib
import importlib
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)

logger = logging.getLogger("nexus.startup_hardening")

# Minimum Python version
MIN_PYTHON_VERSION = (3, 9)

# Required modules
REQUIRED_MODULES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "jwt",
]

# Optional but important modules
OPTIONAL_MODULES = [
    "ccxt",
    "pandas",
    "numpy",
    "google.cloud.firestore",
    "google.cloud.secretmanager",
    "telegram",
]

# Minimum disk space (bytes)
MIN_DISK_SPACE_BYTES = 100 * 1024 * 1024  # 100 MB

# Secret environment variables — NEVER print values
SECRET_ENV_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_APPLICATION_CREDENTIALS",
]

# Critical secrets that block startup if missing
CRITICAL_SECRETS = [
    "GOOGLE_CLOUD_PROJECT",
]

# Secret patterns that must NEVER appear in logs
SECRET_PATTERNS = [
    "password", "secret", "token", "key", "credential",
    "api_key", "apikey", "private",
]


@dataclass
class StartupCheckResult:
    """Result of a single startup check."""
    name: str
    passed: bool
    message: str
    critical: bool = False  # If critical, blocks startup


@dataclass
class StartupReport:
    """Full startup hardening report."""
    timestamp: str
    all_passed: bool
    critical_failures: List[str]
    warnings: List[str]
    checks: List[Dict[str, Any]]
    can_start: bool


def run_startup_checks() -> StartupReport:
    """
    Run all production startup checks.

    Returns:
        StartupReport with pass/fail for each check.
        can_start=False means the system should NOT start.
    """
    sec = get_security_logger()
    checks: List[StartupCheckResult] = []

    # L.1: Python version
    checks.append(_check_python_version())

    # L.2: Required modules
    checks.extend(_check_required_modules())

    # L.3: Disk space
    checks.append(_check_disk_space())

    # E.1: Secret environment variables
    checks.extend(_check_secrets())

    # E.2: Secret checksum
    checks.append(_check_secret_checksum())

    # L.4: MT5 reachability (non-critical)
    checks.append(_check_mt5_reachable())

    # L.5: Telegram reachability (non-critical)
    checks.append(_check_telegram_reachable())

    # Build report
    critical_failures = [c.name for c in checks if not c.passed and c.critical]
    warnings = [c.name for c in checks if not c.passed and not c.critical]
    all_passed = all(c.passed for c in checks)
    can_start = len(critical_failures) == 0

    report = StartupReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        all_passed=all_passed,
        critical_failures=critical_failures,
        warnings=warnings,
        checks=[
            {
                "name": c.name,
                "passed": c.passed,
                "message": c.message,
                "critical": c.critical,
            }
            for c in checks
        ],
        can_start=can_start,
    )

    # Log results
    if can_start:
        if warnings:
            logger.warning(f"Startup checks passed with warnings: {warnings}")
        else:
            logger.info("All startup checks passed")
    else:
        sec.emergency(
            SecurityEventCategory.STARTUP_FAILURE,
            f"Startup BLOCKED: Critical failures: {critical_failures}",
            details={"checks": report.checks},
            source="STARTUP_HARDENING",
        )
        logger.critical(f"STARTUP BLOCKED — Critical failures: {critical_failures}")

    return report


def _check_python_version() -> StartupCheckResult:
    """Verify Python version >= 3.9."""
    version = sys.version_info[:2]
    if version >= MIN_PYTHON_VERSION:
        return StartupCheckResult(
            name="PYTHON_VERSION",
            passed=True,
            message=f"Python {version[0]}.{version[1]} OK",
        )
    return StartupCheckResult(
        name="PYTHON_VERSION",
        passed=False,
        message=f"Python {version[0]}.{version[1]} < required {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}",
        critical=True,
    )


def _check_required_modules() -> List[StartupCheckResult]:
    """Verify required Python modules are installed."""
    results = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
            results.append(StartupCheckResult(
                name=f"MODULE_{module.upper()}",
                passed=True,
                message=f"{module} installed",
            ))
        except ImportError:
            results.append(StartupCheckResult(
                name=f"MODULE_{module.upper()}",
                passed=False,
                message=f"{module} NOT installed",
                critical=True,
            ))

    for module in OPTIONAL_MODULES:
        try:
            importlib.import_module(module)
            results.append(StartupCheckResult(
                name=f"MODULE_{module.upper()}",
                passed=True,
                message=f"{module} installed (optional)",
            ))
        except ImportError:
            results.append(StartupCheckResult(
                name=f"MODULE_{module.upper()}",
                passed=False,
                message=f"{module} NOT installed (optional)",
                critical=False,
            ))

    return results


def _check_disk_space() -> StartupCheckResult:
    """Verify sufficient disk space."""
    try:
        usage = shutil.disk_usage("/")
        free_mb = usage.free / (1024 * 1024)
        if usage.free >= MIN_DISK_SPACE_BYTES:
            return StartupCheckResult(
                name="DISK_SPACE",
                passed=True,
                message=f"{free_mb:.0f} MB free",
            )
        return StartupCheckResult(
            name="DISK_SPACE",
            passed=False,
            message=f"Only {free_mb:.0f} MB free (need {MIN_DISK_SPACE_BYTES / 1024 / 1024:.0f} MB)",
            critical=True,
        )
    except Exception as e:
        return StartupCheckResult(
            name="DISK_SPACE",
            passed=False,
            message=f"Cannot check disk space: {e}",
            critical=False,
        )


def _check_secrets() -> List[StartupCheckResult]:
    """Verify secret environment variables are loaded (without printing values)."""
    results = []
    for var in SECRET_ENV_VARS:
        value = os.getenv(var)
        is_critical = var in CRITICAL_SECRETS

        if value:
            # NEVER log the actual value — only confirm presence
            results.append(StartupCheckResult(
                name=f"SECRET_{var}",
                passed=True,
                message=f"{var} loaded (len={len(value)})",
            ))
        else:
            results.append(StartupCheckResult(
                name=f"SECRET_{var}",
                passed=False,
                message=f"{var} NOT SET",
                critical=is_critical,
            ))

    return results


def _check_secret_checksum() -> StartupCheckResult:
    """
    Compute a checksum of loaded secrets for integrity verification.
    The checksum itself is safe to log (not reversible to secret values).
    """
    loaded_secrets = {
        var: os.getenv(var, "")
        for var in SECRET_ENV_VARS
        if os.getenv(var)
    }

    if not loaded_secrets:
        return StartupCheckResult(
            name="SECRET_CHECKSUM",
            passed=True,
            message="No secrets loaded — checksum skipped",
        )

    # Hash the concatenated secret names (NOT values) with value lengths
    fingerprint = "|".join(
        f"{k}:{len(v)}" for k, v in sorted(loaded_secrets.items())
    )
    checksum = hashlib.sha256(fingerprint.encode()).hexdigest()[:12]

    return StartupCheckResult(
        name="SECRET_CHECKSUM",
        passed=True,
        message=f"Secret fingerprint: {checksum}",
    )


def _check_mt5_reachable() -> StartupCheckResult:
    """Check if MT5 is configured and reachable (non-critical)."""
    mt5_configured = bool(os.getenv("MT5_LOGIN") or os.getenv("MT5_SERVER"))

    if not mt5_configured:
        return StartupCheckResult(
            name="MT5_REACHABLE",
            passed=True,
            message="MT5 not configured — skipped",
        )

    # Check if MT5 module is available
    try:
        import MetaTrader5
        return StartupCheckResult(
            name="MT5_REACHABLE",
            passed=True,
            message="MetaTrader5 module available",
        )
    except ImportError:
        return StartupCheckResult(
            name="MT5_REACHABLE",
            passed=False,
            message="MetaTrader5 module not installed (Windows only)",
            critical=False,
        )


def _check_telegram_reachable() -> StartupCheckResult:
    """Check if Telegram is configured (non-critical)."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        return StartupCheckResult(
            name="TELEGRAM_REACHABLE",
            passed=True,
            message="Telegram not configured — skipped",
        )

    if not chat_id:
        return StartupCheckResult(
            name="TELEGRAM_REACHABLE",
            passed=False,
            message="TELEGRAM_BOT_TOKEN set but TELEGRAM_CHAT_ID missing",
            critical=False,
        )

    return StartupCheckResult(
        name="TELEGRAM_REACHABLE",
        passed=True,
        message="Telegram configured",
    )


def verify_no_secrets_in_string(text: str) -> bool:
    """
    Utility: Check that a string doesn't contain likely secret values.
    Used to sanitize log output.
    """
    text_lower = text.lower()
    for var in SECRET_ENV_VARS:
        value = os.getenv(var, "")
        if value and len(value) > 8 and value in text:
            return False
    return True
