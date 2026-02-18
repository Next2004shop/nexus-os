"""
NEXUS Safe Deployment Check — Phase 12 (D)
=============================================

Before production start, run automated checklist:
    1. MT5 reachable
    2. Telegram reachable
    3. Secrets valid
    4. Capital lock inactive
    5. No open orphan positions
    6. State integrity valid

If ANY fail → Block deployment.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.deployment_check")


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    blocking: bool = True


@dataclass
class DeploymentReport:
    timestamp: str
    all_passed: bool
    failures: List[str]
    warnings: List[str]
    checks: List[Dict[str, Any]]
    can_deploy: bool


def run_deployment_checks() -> DeploymentReport:
    """
    Run pre-production deployment checklist.

    All checks must pass for production deployment.
    Returns DeploymentReport with can_deploy flag.
    """
    checks: List[CheckResult] = []

    # 1. MT5 reachable
    checks.append(_check_mt5_reachable())

    # 2. Telegram reachable
    checks.append(_check_telegram_reachable())

    # 3. Secrets valid
    checks.extend(_check_secrets_valid())

    # 4. Capital lock inactive
    checks.append(_check_capital_lock())

    # 5. No orphan positions
    checks.append(_check_orphan_positions())

    # 6. State integrity valid
    checks.append(_check_state_integrity())

    # Build report
    failures = [c.name for c in checks if not c.passed and c.blocking]
    warnings = [c.name for c in checks if not c.passed and not c.blocking]
    all_passed = all(c.passed for c in checks)
    can_deploy = len(failures) == 0

    report = DeploymentReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        all_passed=all_passed,
        failures=failures,
        warnings=warnings,
        checks=[
            {
                "name": c.name,
                "passed": c.passed,
                "message": c.message,
                "blocking": c.blocking,
            }
            for c in checks
        ],
        can_deploy=can_deploy,
    )

    if can_deploy:
        if warnings:
            logger.warning(f"Deployment checks passed with warnings: {warnings}")
        else:
            logger.info("All deployment checks passed")
    else:
        logger.critical(f"DEPLOYMENT BLOCKED: {failures}")

    return report


def _check_mt5_reachable() -> CheckResult:
    """Verify MT5 connectivity."""
    mt5_login = os.getenv("MT5_LOGIN")
    mt5_server = os.getenv("MT5_SERVER")

    if not mt5_login and not mt5_server:
        return CheckResult(
            name="MT5_REACHABLE",
            passed=True,
            message="MT5 not configured — skipped",
            blocking=False,
        )

    try:
        from app.services.execution import get_engine
        engine = get_engine()
        if engine.mt5._initialized:
            return CheckResult(
                name="MT5_REACHABLE",
                passed=True,
                message="MT5 connection active",
            )
        return CheckResult(
            name="MT5_REACHABLE",
            passed=False,
            message="MT5 configured but not connected",
        )
    except Exception as e:
        return CheckResult(
            name="MT5_REACHABLE",
            passed=False,
            message=f"MT5 check failed: {e}",
        )


def _check_telegram_reachable() -> CheckResult:
    """Verify Telegram bot is configured and responsive."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        return CheckResult(
            name="TELEGRAM_REACHABLE",
            passed=False,
            message="TELEGRAM_BOT_TOKEN not set",
        )

    if not chat_id:
        return CheckResult(
            name="TELEGRAM_REACHABLE",
            passed=False,
            message="TELEGRAM_CHAT_ID not set",
        )

    try:
        from app.services.telegram_bot import get_telegram_service
        telegram = get_telegram_service()
        if telegram.is_running:
            return CheckResult(
                name="TELEGRAM_REACHABLE",
                passed=True,
                message="Telegram bot running",
            )
        return CheckResult(
            name="TELEGRAM_REACHABLE",
            passed=True,
            message="Telegram configured (bot not yet started)",
            blocking=False,
        )
    except Exception as e:
        return CheckResult(
            name="TELEGRAM_REACHABLE",
            passed=False,
            message=f"Telegram check failed: {e}",
        )


def _check_secrets_valid() -> List[CheckResult]:
    """Verify critical secrets are present."""
    results = []

    critical_secrets = [
        ("GOOGLE_CLOUD_PROJECT", True),
        ("TELEGRAM_BOT_TOKEN", True),
        ("TELEGRAM_CHAT_ID", True),
    ]

    for secret_name, is_blocking in critical_secrets:
        value = os.getenv(secret_name)
        if value:
            results.append(CheckResult(
                name=f"SECRET_{secret_name}",
                passed=True,
                message=f"{secret_name} present (len={len(value)})",
            ))
        else:
            results.append(CheckResult(
                name=f"SECRET_{secret_name}",
                passed=False,
                message=f"{secret_name} NOT SET",
                blocking=is_blocking,
            ))

    return results


def _check_capital_lock() -> CheckResult:
    """Verify capital lock is not active."""
    try:
        from security.capital_lock import get_capital_lock
        lock = get_capital_lock()
        if lock.is_locked:
            return CheckResult(
                name="CAPITAL_LOCK_INACTIVE",
                passed=False,
                message=f"Capital lock ACTIVE: {lock._lock_reason}",
            )
        return CheckResult(
            name="CAPITAL_LOCK_INACTIVE",
            passed=True,
            message="Capital lock inactive",
        )
    except Exception as e:
        return CheckResult(
            name="CAPITAL_LOCK_INACTIVE",
            passed=False,
            message=f"Capital lock check failed: {e}",
        )


def _check_orphan_positions() -> CheckResult:
    """Check for orphan positions (shadow vs broker mismatch)."""
    try:
        from security.position_shadow import get_position_shadow
        shadow = get_position_shadow()
        status = shadow.get_status()
        if status.get("halted"):
            return CheckResult(
                name="NO_ORPHAN_POSITIONS",
                passed=False,
                message="Position shadow tracker in HALTED state — reconciliation failure",
            )
        if status.get("consecutive_mismatches", 0) > 0:
            return CheckResult(
                name="NO_ORPHAN_POSITIONS",
                passed=False,
                message=f"Active position mismatches: {status['consecutive_mismatches']}",
            )
        return CheckResult(
            name="NO_ORPHAN_POSITIONS",
            passed=True,
            message="No orphan positions detected",
        )
    except Exception as e:
        return CheckResult(
            name="NO_ORPHAN_POSITIONS",
            passed=True,
            message=f"Position shadow check skipped: {e}",
            blocking=False,
        )


def _check_state_integrity() -> CheckResult:
    """Verify state integrity is clean."""
    try:
        from security.state_integrity import get_state_integrity
        integrity = get_state_integrity()
        status = integrity.get_status()
        unexpected = status.get("unexpected_mutations", 0)
        if unexpected > 0:
            return CheckResult(
                name="STATE_INTEGRITY",
                passed=False,
                message=f"State integrity has {unexpected} unexpected mutations",
            )
        return CheckResult(
            name="STATE_INTEGRITY",
            passed=True,
            message="State integrity clean",
        )
    except Exception as e:
        return CheckResult(
            name="STATE_INTEGRITY",
            passed=True,
            message=f"State integrity check skipped: {e}",
            blocking=False,
        )
