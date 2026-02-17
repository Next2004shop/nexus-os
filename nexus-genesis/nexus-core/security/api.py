"""
NEXUS Security API — Phase 11
================================

Exposes security infrastructure status and controls.

All endpoints are read-only or admin-gated.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from security.execution_guard import get_execution_guard
from security.capital_lock import get_capital_lock
from security.failsafe import get_failsafe, SystemMode
from security.state_integrity import get_state_integrity
from security.latency_monitor import get_latency_monitor
from security.position_shadow import get_position_shadow
from security.telegram_hardening import get_telegram_hardening
from security.startup_hardening import run_startup_checks
from recovery.emergency_restore import get_emergency_restore

router = APIRouter(prefix="/api/security", tags=["Security"])


# ---- Request Models ----

class FailsafeTransitionRequest(BaseModel):
    mode: str          # NORMAL, SAFE_MODE, LOCKDOWN
    reason: str


class CapitalUnlockRequest(BaseModel):
    reason: str = "Manual admin unlock"


# ---- Overview ----

@router.get("/status")
async def get_security_status():
    """Comprehensive security status dashboard."""
    return {
        "failsafe": get_failsafe().get_status(),
        "capital_lock": get_capital_lock().get_status(),
        "execution_guard": get_execution_guard().get_stats(),
        "state_integrity": get_state_integrity().get_status(),
        "latency": get_latency_monitor().get_metrics(),
        "position_shadow": get_position_shadow().get_status(),
        "telegram": get_telegram_hardening().get_stats(),
    }


# ---- Failsafe Controls (G) ----

@router.get("/failsafe")
async def get_failsafe_status():
    """Get current failsafe mode and transition history."""
    return get_failsafe().get_status()


@router.post("/failsafe/transition")
async def transition_failsafe(req: FailsafeTransitionRequest):
    """Transition system to a new failsafe mode (admin)."""
    try:
        target = SystemMode(req.mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {req.mode}. Valid: NORMAL, SAFE_MODE, LOCKDOWN",
        )

    success = get_failsafe().transition_to(target, req.reason, source="API_ADMIN")
    if not success:
        raise HTTPException(status_code=400, detail="Invalid mode transition")

    return {
        "status": "TRANSITIONED",
        "mode": get_failsafe().mode.value,
    }


# ---- Capital Lock (C) ----

@router.get("/capital-lock")
async def get_capital_lock_status():
    """Get capital lock status."""
    return get_capital_lock().get_status()


@router.post("/capital-lock/unlock")
async def unlock_capital(req: CapitalUnlockRequest):
    """Manually unlock capital lock (admin)."""
    lock = get_capital_lock()
    if not lock.is_locked:
        raise HTTPException(status_code=400, detail="Capital is not locked")

    lock.manual_unlock(req.reason)
    return {
        "status": "UNLOCKED",
        "failsafe_mode": get_failsafe().mode.value,
    }


# ---- Execution Guard (A) ----

@router.get("/execution-guard")
async def get_execution_guard_status():
    """Get execution guard statistics."""
    guard = get_execution_guard()
    return {
        "stats": guard.get_stats(),
        "pending_confirmations": guard.get_pending_confirmations(),
    }


# ---- Latency Monitor (H) ----

@router.get("/latency")
async def get_latency_metrics():
    """Get latency monitoring metrics."""
    return get_latency_monitor().get_metrics()


# ---- Position Shadow (I) ----

@router.get("/position-shadow")
async def get_position_shadow_status():
    """Get position shadow tracker status."""
    return get_position_shadow().get_status()


# ---- State Integrity (F) ----

@router.get("/state-integrity")
async def get_state_integrity_status():
    """Get state integrity monitor status."""
    return get_state_integrity().get_status()


@router.post("/state-integrity/check")
async def force_integrity_check():
    """Force an immediate state integrity check."""
    monitor = get_state_integrity()
    is_clean = monitor.check()
    return {
        "clean": is_clean,
        "status": monitor.get_status(),
    }


# ---- Disaster Recovery (J) ----

@router.post("/recovery/execute")
async def execute_disaster_recovery():
    """Execute full disaster recovery procedure (admin)."""
    restore = get_emergency_restore()
    result = restore.execute_recovery()
    return result


@router.get("/recovery/status")
async def get_recovery_status():
    """Get disaster recovery status and history."""
    return get_emergency_restore().get_status()


# ---- Telegram Audit (D) ----

@router.get("/telegram/audit")
async def get_telegram_audit(count: int = 50):
    """Get Telegram command audit log."""
    hardening = get_telegram_hardening()
    count = min(count, 200)
    return {
        "stats": hardening.get_stats(),
        "commands": hardening.get_command_log(count),
    }


# ---- Startup Check (E + L) ----

@router.post("/startup-check")
async def run_startup_verification():
    """Run all startup hardening checks."""
    report = run_startup_checks()
    return {
        "can_start": report.can_start,
        "all_passed": report.all_passed,
        "critical_failures": report.critical_failures,
        "warnings": report.warnings,
        "checks": report.checks,
    }
