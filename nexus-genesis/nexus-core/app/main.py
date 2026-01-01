"""
NEXUS Sovereign System - FastAPI Main Application
==================================================

Central nervous system orchestrating:
1. Market analysis endpoints
2. Trade execution (with risk governor approval)
3. Risk status and monitoring
4. Emergency controls
5. Health and heartbeat

All frontend access is READ-ONLY.
AI signals are advisory - governor has final approval.
"""

import logging
from fastapi import FastAPI, HTTPException, Body, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import asyncio

from app.services import (
    intelligence,
    execution,
    risk_governor,
    ancient_logic,
    scheduler,
    strategy_engine,
    circuit_breaker,
    market_data
)

# Configure central logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.nervous_system")

app = FastAPI(
    title="NEXUS SOVEREIGN SYSTEM",
    description="Private Trading System - Ancient Laws × Axelrod Discipline",
    version="2.0.0"
)


# =============================================================================
# STARTUP & SHUTDOWN
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize all systems on startup."""
    logger.info("=" * 60)
    logger.info("NEXUS CORE INITIALIZING...")
    logger.info("Architecture: Ancient Laws × Axelrod Game Theory")
    logger.info("Brain: Gemini Pro (Vertex AI)")
    logger.info("Execution: Dual-Path (MT5 + Binance)")
    logger.info("=" * 60)
    
    # Start the Heartbeat Scheduler
    scheduler.start_scheduler()
    
    # Initialize circuit breaker manager
    cb_manager = circuit_breaker.get_manager()
    cb_manager.connectivity.heartbeat("nexus_core")
    
    logger.info("NEXUS CORE ONLINE")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("NEXUS CORE SHUTTING DOWN...")
    
    # Cleanup market data connections
    provider = market_data.get_provider()
    await provider.close()
    
    # Shutdown execution engine
    engine = execution.get_engine()
    engine.shutdown()
    
    logger.info("NEXUS CORE OFFLINE")


# =============================================================================
# CORS CONFIGURATION
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://nexus-terminal.web.app"  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================
@app.get("/health")
async def health_check():
    """System health check."""
    cb_manager = circuit_breaker.get_manager()
    trading_allowed, reason = cb_manager.is_trading_allowed()
    
    return {
        "status": "ONLINE",
        "trading_enabled": trading_allowed,
        "trading_status": reason,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/status")
async def system_status():
    """Comprehensive system status for dashboard."""
    risk_status = risk_governor.get_risk_status()
    cb_manager = circuit_breaker.get_manager()
    exec_stats = execution.get_engine().get_execution_stats()
    
    return {
        "system": {
            "status": "ONLINE",
            "version": "2.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "risk": risk_status,
        "circuit_breakers": cb_manager.get_all_status(),
        "execution": exec_stats
    }


@app.get("/risk-status")
async def get_risk_status():
    """Get current risk status for frontend display."""
    return risk_governor.get_risk_status()


# =============================================================================
# MARKET ANALYSIS ENDPOINTS
# =============================================================================
@app.post("/analyze")
async def analyze_market(data: Dict[str, Any] = Body(...)):
    """
    Analyze market data using AI + Strategy Engine.
    
    This is advisory only - does not place trades.
    """
    logger.info("Received analysis request")
    
    try:
        # Run AI analysis
        ai_result = intelligence.analyze_market(data)
        
        return {
            "status": "analyzed",
            "ai_analysis": ai_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analysis route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/full")
async def full_market_analysis(
    symbol: str = Body(...),
    asset_class: str = Body(default="forex"),
    timeframe: str = Body(default="M15")
):
    """
    Full analysis using market data + all strategy modules.
    """
    logger.info(f"Full analysis request: {symbol}")
    
    try:
        # Fetch market data
        ohlcv = await market_data.fetch_ohlcv(symbol, asset_class, timeframe, 100)
        
        if ohlcv.empty:
            return {
                "status": "error",
                "message": "No market data available",
                "symbol": symbol
            }
        
        # Run strategy engine
        orchestrator = strategy_engine.create_orchestrator()
        strategy_result = orchestrator.analyze_all(ohlcv)
        
        # Run intelligence analysis
        intel = intelligence.NexusIntelligence()
        intel_result = intel.full_analysis(ohlcv, use_ai=False)  # Skip AI for speed
        
        return {
            "status": "analyzed",
            "symbol": symbol,
            "strategy_signals": strategy_result,
            "intelligence": intel_result,
            "data_bars": len(ohlcv),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Full analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TRADE EXECUTION ENDPOINTS
# =============================================================================
@app.post("/trade")
async def place_trade(
    symbol: str = Body(...),
    side: str = Body(...),
    quantity: float = Body(...),
    market_context: Dict[str, Any] = Body(default={})
):
    """
    The Nervous System: Orchestrates Trade Execution with Governor Overrides.
    
    Flow:
    1. Ancient Logic cycle check
    2. Risk Governor validation
    3. Execution via dual-path engine
    """
    logger.info(f"NEXUS_TRADE_COMMAND: {side.upper()} {quantity} {symbol}")
    
    try:
        # STEP 1: ANCIENT LOGIC OVERRIDE
        market_context["signal"] = side
        cycle_ok, cycle_msg = ancient_logic.check_cycle(market_context)
        if not cycle_ok:
            logger.warning(f"REJECTED BY GOVERNOR (Ancient Logic): {cycle_msg}")
            return {
                "status": "REJECTED_BY_GOVERNOR",
                "reason": cycle_msg,
                "stage": "ANCIENT_LOGIC"
            }

        # STEP 2: RISK GOVERNOR VALIDATION
        price = market_context.get("price", 0.0)
        atr_data = market_context.get("atr_data", {})
        confidence = market_context.get("confidence", 0.5)
        
        risk_ok, risk_msg = risk_governor.validate_trade(
            symbol, quantity, price, atr_data, confidence
        )
        if not risk_ok:
            logger.warning(f"REJECTED BY GOVERNOR (Risk Filter): {risk_msg}")
            return {
                "status": "REJECTED_BY_GOVERNOR",
                "reason": risk_msg,
                "stage": "RISK_GOVERNOR"
            }

        # STEP 3: CIRCUIT BREAKER CHECK
        cb_manager = circuit_breaker.get_manager()
        trading_allowed, cb_reason = cb_manager.is_trading_allowed()
        if not trading_allowed:
            logger.warning(f"REJECTED BY CIRCUIT BREAKER: {cb_reason}")
            return {
                "status": "REJECTED_BY_CIRCUIT_BREAKER",
                "reason": cb_reason,
                "stage": "CIRCUIT_BREAKER"
            }

        # STEP 4: EXECUTION
        engine = execution.get_engine()
        result = engine.execute_trade(symbol, side, quantity)
        
        if result.status == execution.OrderStatus.FAILED:
            raise HTTPException(status_code=400, detail=result.error)
        
        return {
            "status": "EXECUTED",
            "order": result.to_dict(),
            "risk_message": risk_msg
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EMERGENCY CONTROLS
# =============================================================================
@app.post("/kill")
async def emergency_kill(symbol: str = Body(None)):
    """Emergency Kill Switch: Cancels all orders and disables trading."""
    logger.critical("EMERGENCY KILL TRIGGERED VIA API")
    
    try:
        # Trigger global halt
        cb_manager = circuit_breaker.get_manager()
        cb_manager.global_halt("API Kill Switch")
        
        # Cancel all orders
        engine = execution.get_engine()
        kill_result = engine.kill_switch(symbol)
        
        # Shutdown via risk governor
        risk_governor.emergency_shutdown("API Kill Switch")
        
        return {
            "status": "KILLED",
            "symbol": symbol or "ALL",
            "execution_result": kill_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Kill switch route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resume")
async def resume_trading(admin_key: str = Body(...)):
    """
    Resume trading after emergency halt (requires admin key).
    """
    logger.warning("RESUME TRADING REQUESTED")
    
    try:
        # Reset circuit breaker
        cb_manager = circuit_breaker.get_manager()
        cb_manager.resume_trading()
        
        # Reset risk governor
        result = risk_governor.reset_circuit_breaker(admin_key)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "RESUMED",
            "risk_status": risk_governor.get_risk_status(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume trading error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EQUITY MANAGEMENT
# =============================================================================
@app.post("/update_equity")
async def update_equity(equity: float = Body(...)):
    """Update governor equity for drawdown tracking."""
    risk_governor.update_equity(equity)
    return {
        "status": "updated",
        "current_equity": equity,
        "risk_status": risk_governor.get_risk_status()
    }


# =============================================================================
# DASHBOARD DATA (READ-ONLY)
# =============================================================================
@app.get("/dashboard/equity-curve")
async def get_equity_curve():
    """Get equity curve data for dashboard chart."""
    # In production, this would fetch from Firestore/BigQuery
    status = risk_governor.get_risk_status()
    
    return {
        "current_equity": status["equity"]["current"],
        "peak_equity": status["equity"]["peak"],
        "initial_equity": status["equity"]["initial"],
        "drawdown_pct": status["drawdown"]["current"],
        "pnl_pct": status["total_pnl_pct"]
    }


@app.get("/dashboard/positions")
async def get_open_positions():
    """Get open positions for dashboard display."""
    state = risk_governor._get_state()
    
    positions = []
    for symbol, pos in state.open_positions.items():
        positions.append({
            "symbol": symbol,
            "side": pos.get("side"),
            "quantity": pos.get("quantity"),
            "entry_price": pos.get("entry_price"),
            "notional": pos.get("notional"),
            "opened_at": pos.get("opened_at")
        })
    
    return {"positions": positions, "count": len(positions)}


@app.get("/dashboard/orders")
async def get_recent_orders():
    """Get recent order history."""
    engine = execution.get_engine()
    orders = list(engine.tracker._orders.values())[-20:]  # Last 20 orders
    
    return {
        "orders": [o.to_dict() for o in orders],
        "count": len(orders)
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
