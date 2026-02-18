"""
NEXUS Deployment API — Phase 12
==================================

API endpoints for deployment management:
    GET  /api/deployment/status          — Full deployment status
    GET  /api/deployment/config          — Current config (safe view)
    GET  /api/deployment/version         — Version info
    GET  /api/deployment/resources       — Resource monitoring snapshot
    GET  /api/deployment/backup          — Backup status
    POST /api/deployment/backup/run      — Force backup now
    GET  /api/deployment/rollback        — Rollback system status
    POST /api/deployment/rollback/save   — Save current state as stable
    GET  /api/deployment/lock            — Deployment lock status
    POST /api/deployment/lock/activate   — Activate deployment lock
    POST /api/deployment/lock/deactivate — Deactivate deployment lock
    GET  /api/deployment/stability       — Stability loop status
    POST /api/deployment/check           — Run deployment checklist
    GET  /api/deployment/update-guard    — Update guard status
    POST /api/deployment/update-guard/snapshot — Snapshot checksums
    POST /api/deployment/update-guard/validate — Validate update
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Body, HTTPException

logger = logging.getLogger("nexus.deployment.api")

router = APIRouter(prefix="/api/deployment", tags=["deployment"])


@router.get("/status")
async def deployment_status():
    """Comprehensive deployment status."""
    from config.config_loader import get_config
    from config.version_tag import get_version_info
    from deployment.backup import get_backup_manager
    from deployment.deployment_lock import get_deployment_lock
    from deployment.resource_monitor import get_resource_monitor
    from deployment.rollback import get_rollback_status
    from deployment.stability_loop import get_stability_loop
    from deployment.update_guard import get_update_guard

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": get_version_info(),
        "config": get_config().to_safe_dict(),
        "deployment_lock": get_deployment_lock().get_status(),
        "backup": get_backup_manager().get_status(),
        "rollback": get_rollback_status(),
        "resources": get_resource_monitor().get_status(),
        "stability": get_stability_loop().get_status(),
        "update_guard": get_update_guard().get_status(),
    }


@router.get("/config")
async def get_current_config():
    """Get current configuration (safe view — no secrets)."""
    from config.config_loader import get_config
    return get_config().to_safe_dict()


@router.get("/version")
async def get_version():
    """Get version info."""
    from config.version_tag import get_version_info
    return get_version_info()


@router.get("/resources")
async def get_resources():
    """Get current resource monitoring snapshot."""
    from deployment.resource_monitor import get_resource_monitor
    monitor = get_resource_monitor()
    return monitor.check_now()


@router.get("/backup")
async def backup_status():
    """Get backup system status."""
    from deployment.backup import get_backup_manager
    return get_backup_manager().get_status()


@router.post("/backup/run")
async def force_backup():
    """Force an immediate backup."""
    from deployment.backup import get_backup_manager
    result = get_backup_manager().run_backup_now()
    return result


@router.get("/rollback")
async def rollback_status():
    """Get rollback system status."""
    from deployment.rollback import get_rollback_status
    return get_rollback_status()


@router.post("/rollback/save")
async def save_stable():
    """Save current state as stable (for future rollback)."""
    from deployment.rollback import save_stable_state
    save_stable_state()
    from deployment.rollback import get_rollback_status
    return {
        "status": "saved",
        "state": get_rollback_status(),
    }


@router.get("/lock")
async def lock_status():
    """Get deployment lock status."""
    from deployment.deployment_lock import get_deployment_lock
    return get_deployment_lock().get_status()


@router.post("/lock/activate")
async def activate_lock(
    reason: str = Body(default="Manual lock"),
):
    """Activate deployment lock."""
    from deployment.deployment_lock import get_deployment_lock
    lock = get_deployment_lock()
    lock.activate(reason, source="API")
    return lock.get_status()


@router.post("/lock/deactivate")
async def deactivate_lock(
    reason: str = Body(default="Manual unlock"),
):
    """Deactivate deployment lock."""
    from deployment.deployment_lock import get_deployment_lock
    lock = get_deployment_lock()
    lock.deactivate(reason, source="API")
    return lock.get_status()


@router.get("/stability")
async def stability_status():
    """Get stability loop status."""
    from deployment.stability_loop import get_stability_loop
    return get_stability_loop().get_status()


@router.post("/check")
async def run_deployment_check():
    """Run pre-production deployment checklist."""
    from deployment.deployment_check import run_deployment_checks
    report = run_deployment_checks()
    return {
        "can_deploy": report.can_deploy,
        "all_passed": report.all_passed,
        "failures": report.failures,
        "warnings": report.warnings,
        "checks": report.checks,
        "timestamp": report.timestamp,
    }


@router.get("/update-guard")
async def update_guard_status():
    """Get update guard status."""
    from deployment.update_guard import get_update_guard
    return get_update_guard().get_status()


@router.post("/update-guard/snapshot")
async def snapshot_checksums():
    """Snapshot current file checksums (mark as known-good)."""
    from deployment.update_guard import get_update_guard
    guard = get_update_guard()
    checksums = guard.snapshot_checksums()
    return {
        "status": "snapshot_saved",
        "files_tracked": len(checksums),
    }


@router.post("/update-guard/validate")
async def validate_update():
    """Validate current files against saved checksums."""
    from deployment.update_guard import get_update_guard
    guard = get_update_guard()
    is_valid, issues = guard.validate_update()
    return {
        "valid": is_valid,
        "issues": issues,
    }
