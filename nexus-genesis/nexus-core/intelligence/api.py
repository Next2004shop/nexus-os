"""
NEXUS Intelligence API
======================

Exposes market intelligence and analysis status.
Since intelligence is event-driven, this API serves the *latest known state* 
cached from the most recent analysis.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.intelligence import list_models, _vertex_initialized

# In-memory cache for the latest market analysis
# In production, this would be Redis or database
_LATEST_ANALYSIS: Dict[str, Any] = {
    "timestamp": None,
    "regime": "WAITING_FOR_DATA",
    "volatility": "UNKNOWN",
    "signals": [],
    "ai_active": False
}

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence Layer"])


class AnalysisUpdate(BaseModel):
    """Model for updating the intelligence cache."""
    symbol: str
    regime: str
    volatility_score: float
    signal: str
    confidence: float
    reasoning: str


@router.get("/status")
async def get_status():
    """
    Get Intelligence Layer health and configuration.
    """
    return {
        "status": "ONLINE",
        "vertex_ai_initialized": _vertex_initialized,
        "models": list_models(),
        "last_update": _LATEST_ANALYSIS["timestamp"]
    }


@router.get("/latest")
async def get_latest_intelligence():
    """
    Get the latest cached market intelligence.
    """
    return _LATEST_ANALYSIS


@router.post("/update")
async def update_intelligence(update: AnalysisUpdate):
    """
    Internal endpoint to push new analysis results to the dashboard cache.
    (Called by Strategy Engine or Cron Job)
    """
    global _LATEST_ANALYSIS
    
    _LATEST_ANALYSIS = {
        "timestamp": datetime.now().isoformat(),
        "regime": update.regime,
        "volatility": "HIGH" if update.volatility_score > 0.7 else "NORMAL",
        "signals": [{
            "symbol": update.symbol,
            "side": update.signal,
            "confidence": update.confidence,
            "reasoning": update.reasoning,
            "timestamp": datetime.now().isoformat()
        }],
        "ai_active": _vertex_initialized
    }
    
    return {"status": "UPDATED"}
