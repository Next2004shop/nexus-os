"""
NEXUS Risk API
==============

Exposes risk metrics and status for the dashboard.
"""

from fastapi import APIRouter, Depends
from app.services.risk_governor import get_risk_status

# Create router
router = APIRouter(prefix="/api/risk", tags=["Risk Governor"])

@router.get("/status")
async def get_status():
    """
    Get current risk governor status.
    Returns calculated drawdown, equity, and risk level.
    """
    return get_risk_status()
