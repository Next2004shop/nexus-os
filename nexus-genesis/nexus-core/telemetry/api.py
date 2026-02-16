"""
NEXUS Telemetry API
===================

Exposes real-time system metrics.
"""

from fastapi import APIRouter
from telemetry.telemetry_engine import get_telemetry

router = APIRouter(prefix="/api/system", tags=["Telemetry"])

@router.get("/telemetry")
async def get_system_telemetry():
    """
    Get comprehensive system telemetry:
    - Current metrics (Equity, P/L, Latency, Errors)
    - Historical curves (Equity, P/L)
    - Warning flags
    """
    return get_telemetry().get_snapshot()
