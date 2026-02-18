"""
NEXUS Telegram Deployment Report — Phase 12 (G)
==================================================

When production boots, send structured report via Telegram:
    - Version
    - Environment
    - Risk mode
    - Active strategies
    - Capital available
    - System state
    - Last backup date
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("nexus.deployment_report")


async def send_deployment_report(
    version_info: Dict[str, Any],
    config_info: Dict[str, Any],
    deployment_report: Optional[Dict[str, Any]] = None,
):
    """
    Send a structured deployment report via Telegram.

    Called once at production boot after all systems initialize.
    """
    try:
        from app.services.telegram_bot import get_telegram_service
    except ImportError:
        logger.warning("Telegram service not available — skipping deployment report")
        return

    telegram = get_telegram_service()

    # Build report
    version = version_info.get("version", "unknown")
    commit = version_info.get("git_commit", "unknown")
    branch = version_info.get("git_branch", "unknown")
    env_mode = config_info.get("env_mode", "unknown")
    risk_level = config_info.get("risk_level", "unknown")
    execution = "LIVE" if config_info.get("execution_allowed") else "PAPER"
    paper = config_info.get("paper_trading", True)
    telegram_verbosity = config_info.get("telegram_verbosity", "NORMAL")
    deployment_lock = config_info.get("deployment_lock", False)

    # Get capital info
    capital_str = "N/A"
    try:
        from app.services.risk_governor import get_risk_status
        risk = get_risk_status()
        equity = risk.get("equity", {})
        capital_str = f"${equity.get('current', 0):,.2f}"
    except Exception:
        pass

    # Get failsafe state
    failsafe_str = "N/A"
    try:
        from security.failsafe import get_failsafe
        failsafe_str = get_failsafe().mode.value
    except Exception:
        pass

    # Get last backup date
    backup_date = "N/A"
    try:
        from deployment.backup import get_backup_manager
        last = get_backup_manager().get_last_backup_date()
        if last:
            backup_date = last
    except Exception:
        pass

    # Get active strategies count
    strategies_str = "N/A"
    try:
        from app.services.agent_council import get_council
        council = get_council()
        strategies_str = f"{len(council.agents)} agents active"
    except Exception:
        pass

    # Deployment check summary
    deploy_status = "N/A"
    if deployment_report:
        if deployment_report.get("can_deploy"):
            deploy_status = "ALL CHECKS PASSED"
        else:
            failures = deployment_report.get("failures", [])
            deploy_status = f"BLOCKED: {', '.join(failures)}"

    message = (
        "NEXUS DEPLOYMENT REPORT\n"
        "=" * 30 + "\n\n"
        f"Version:     v{version}\n"
        f"Commit:      {commit}\n"
        f"Branch:      {branch}\n"
        f"Environment: {env_mode}\n"
        f"Risk Mode:   {risk_level}\n"
        f"Execution:   {execution}\n"
        f"Paper Mode:  {'ON' if paper else 'OFF'}\n"
        f"Strategies:  {strategies_str}\n"
        f"Capital:     {capital_str}\n"
        f"System:      {failsafe_str}\n"
        f"Deploy Lock: {'ON' if deployment_lock else 'OFF'}\n"
        f"Last Backup: {backup_date}\n"
        f"Pre-Check:   {deploy_status}\n"
        f"Telegram:    {telegram_verbosity}\n\n"
        f"Boot Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        "=" * 30
    )

    try:
        await telegram.send_message(message)
        logger.info("Deployment report sent via Telegram")
    except Exception as e:
        logger.error(f"Failed to send deployment report: {e}")
