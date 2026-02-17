"""
NEXUS Meta-Intelligence API
============================

Exposes the SYSTEM EVOLUTION dashboard panel and adaptation controls.

Endpoints:
    GET  /api/meta/evolution     — Dashboard data for SYSTEM EVOLUTION panel
    GET  /api/meta/ledger        — Recent trade journal entries
    GET  /api/meta/regime        — Current market regime
    GET  /api/meta/weights       — Current strategy weight distribution
    POST /api/meta/classify      — Manually trigger regime classification
    POST /api/meta/analyze       — Force an analysis cycle
    POST /api/meta/daily-review  — Generate daily meta report
    POST /api/meta/exit-protective — Exit protective mode (admin)
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from meta.performance_intelligence import get_performance_intelligence, BASELINE_WEIGHTS

router = APIRouter(prefix="/api/meta", tags=["Meta-Intelligence"])


# ---- Request Models ----

class RegimeClassifyRequest(BaseModel):
    current_atr: float
    avg_atr_20: float
    price_change_pct: float
    volume_ratio: float = 1.0
    ema_alignment: Optional[str] = None


class DailyReviewRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD format


# ---- H) SYSTEM EVOLUTION Dashboard Panel ----

@router.get("/evolution")
async def get_system_evolution():
    """
    SYSTEM EVOLUTION telemetry panel data.

    Returns:
        - Current regime
        - Strategy weight distribution
        - Risk modulation level
        - Adaptation state
        - 30-trade performance snapshot
        - Weight and risk adjustment history
    """
    pi = get_performance_intelligence()
    return pi.get_dashboard_data()


# ---- Trade Ledger ----

@router.get("/ledger")
async def get_trade_ledger(count: int = 30):
    """Get recent trade journal entries."""
    pi = get_performance_intelligence()
    count = min(count, 200)
    return {
        "total_trades": pi.journal.total_trades,
        "recent": pi.journal.get_recent(count),
    }


# ---- C) Regime ----

@router.get("/regime")
async def get_current_regime():
    """Get current market regime classification."""
    pi = get_performance_intelligence()
    return pi.regime_classifier.get_state()


@router.post("/classify")
async def classify_regime(req: RegimeClassifyRequest):
    """Manually trigger regime classification with market data."""
    pi = get_performance_intelligence()
    regime = pi.classify_regime(
        current_atr=req.current_atr,
        avg_atr_20=req.avg_atr_20,
        price_change_pct=req.price_change_pct,
        volume_ratio=req.volume_ratio,
        ema_alignment=req.ema_alignment,
    )
    return {
        "regime": regime,
        "classified_at": pi.regime_classifier.get_state().get("classified_at"),
    }


# ---- D) Strategy Weights ----

@router.get("/weights")
async def get_strategy_weights():
    """Get current strategy weight distribution vs baseline."""
    pi = get_performance_intelligence()
    return {
        "current": pi.weight_manager.get_weights(),
        "baseline": dict(BASELINE_WEIGHTS),
        "history": pi.weight_manager.get_history(10),
    }


# ---- Force Analysis ----

@router.post("/analyze")
async def force_analysis():
    """Force an analysis cycle (admin action)."""
    pi = get_performance_intelligence()
    pi.force_analysis()
    return {
        "status": "ANALYSIS_TRIGGERED",
        "total_trades": pi.journal.total_trades,
        "dashboard": pi.get_dashboard_data(),
    }


# ---- I) Daily Review ----

@router.post("/daily-review")
async def generate_daily_review(req: DailyReviewRequest):
    """Generate daily meta report."""
    pi = get_performance_intelligence()
    report = pi.generate_daily_review(date_str=req.date)
    return {
        "status": "REPORT_GENERATED",
        "report": report,
    }


# ---- J) Exit Protective Mode ----

@router.post("/exit-protective")
async def exit_protective_mode():
    """Exit protective mode after manual review."""
    pi = get_performance_intelligence()
    if not pi.is_protective_mode():
        raise HTTPException(status_code=400, detail="System is not in protective mode")

    pi.exit_protective_mode()
    return {
        "status": "PROTECTIVE_MODE_EXITED",
        "risk_multiplier": pi.get_risk_multiplier(),
        "mode": pi.risk_modulator.mode.value,
    }
