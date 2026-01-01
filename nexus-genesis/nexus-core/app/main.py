"""
NEXUS Sovereign System - FastAPI Main Application
==================================================

Central nervous system orchestrating:
1. Multi-Agent Council decision making (5 agents, quorum required)
2. Model Ensemble voting (AI + rule-based consensus)
3. Trade execution (with council + governor approval)
4. Risk status and monitoring
5. Emergency controls with stealth mode
6. Health and heartbeat

IMMUTABLE LAW: Council Over King - No trade without quorum.
All frontend access is READ-ONLY.
"""

import logging
from fastapi import FastAPI, HTTPException, Body, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import asyncio

from app.services import intelligence
from app.services import execution
from app.services import risk_governor
from app.services import ancient_logic
from app.services import scheduler
from app.services import strategy_engine
from app.services import circuit_breaker
from app.services import market_data

# New Multi-Agent Council and Ensemble imports
from app.services.agent_council import get_council, require_quorum, Vote
from app.services.model_ensemble import get_ensemble, ensemble_predict
from app.services.stealth_mode import get_stealth_mode

# Configure central logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.nervous_system")

app = FastAPI(
    title="NEXUS SOVEREIGN SYSTEM",
    description="Private Trading System - Ancient Laws × Axelrod Discipline × Multi-Agent Council",
    version="3.0.0"  # Version bump for council integration
)


# =============================================================================
# STARTUP & SHUTDOWN
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize all systems on startup."""
    logger.info("=" * 60)
    logger.info("NEXUS SOVEREIGN SYSTEM INITIALIZING...")
    logger.info("Architecture: Ancient Laws × Axelrod Game Theory × Netflix Resilience")
    logger.info("Decision: Multi-Agent Council (5 Agents, 3/5 Quorum)")
    logger.info("Brain: Model Ensemble (Gemini Pro + Rule-Based + Pattern)")
    logger.info("Execution: Dual-Path (MT5 + Binance)")
    logger.info("Security: Stealth Mode Active")
    logger.info("=" * 60)
    
    # Start the Heartbeat Scheduler
    scheduler.start_scheduler()
    
    # Initialize circuit breaker manager
    cb_manager = circuit_breaker.get_manager()
    cb_manager.connectivity.heartbeat("nexus_core")
    
    # Initialize Multi-Agent Council
    council = get_council()
    logger.info(f"Agent Council initialized with {len(council.agents)} agents")
    
    # Initialize Model Ensemble
    ensemble = get_ensemble()
    logger.info(f"Model Ensemble initialized with {len(ensemble.models)} models")
    
    # Initialize Stealth Mode
    stealth = get_stealth_mode()
    logger.info(f"Stealth Mode: {stealth.get_status()}")
    
    logger.info("NEXUS SOVEREIGN SYSTEM ONLINE")


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
    council = get_council()
    ensemble = get_ensemble()
    stealth = get_stealth_mode()
    
    return {
        "system": {
            "status": "ONLINE",
            "version": "3.0.0",
            "architecture": "Multi-Agent Council",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "agent_council": council.get_status(),
        "model_ensemble": ensemble.get_status(),
        "stealth_mode": stealth.get_status(),
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
    The Sovereign Execution Flow: Council → Ensemble → Governor → Execute.
    
    IMMUTABLE LAW: No trade without council quorum (3/5 agents agree).
    
    Flow:
    1. Stealth Mode check (system operational?)
    2. Multi-Agent Council deliberation (QUORUM REQUIRED)
    3. Model Ensemble prediction validation
    4. Ancient Logic cycle check
    5. Risk Governor validation
    6. Circuit Breaker check
    7. Execution via dual-path engine
    """
    logger.info(f"NEXUS_TRADE_COMMAND: {side.upper()} {quantity} {symbol}")
    stealth = get_stealth_mode()
    
    # Log trade attempt
    stealth.log_event("TRADE_ATTEMPT", {
        "symbol": symbol, "side": side, "quantity": quantity
    }, sensitivity="HIGH")
    
    try:
        # STEP 0: STEALTH MODE CHECK
        if not stealth.is_operational():
            logger.critical("System in PURGE mode - all trading halted")
            return {
                "status": "REJECTED_SYSTEM_PURGE",
                "reason": "System is in emergency purge mode",
                "stage": "STEALTH_MODE"
            }
        
        # Apply randomized delay for stealth
        delay = stealth.get_order_delay()
        if delay > 0:
            await asyncio.sleep(delay)
        
        # STEP 1: MULTI-AGENT COUNCIL DELIBERATION (CORE REQUIREMENT)
        logger.info(f"Convening Agent Council for {symbol} {side}...")
        council = get_council()
        
        # Prepare market data for council
        council_data = {
            "ohlcv": market_context.get("ohlcv"),
            "regime": market_context.get("regime"),
            "momentum": market_context.get("momentum"),
            "volatility": market_context.get("volatility"),
            "bid": market_context.get("bid"),
            "ask": market_context.get("ask"),
            "circuit_breaker_status": circuit_breaker.get_manager().get_all_status(),
            "anomaly": market_context.get("anomaly")
        }
        
        council_decision = council.deliberate(symbol, side, council_data)
        
        if not council_decision.quorum_reached:
            logger.warning(f"REJECTED BY COUNCIL: {council_decision.reasoning}")
            stealth.log_event("TRADE_REJECTED", {
                "stage": "COUNCIL", "reason": council_decision.reasoning,
                "votes": council_decision.vote_summary
            }, sensitivity="NORMAL")
            return {
                "status": "REJECTED_BY_COUNCIL",
                "reason": council_decision.reasoning,
                "stage": "AGENT_COUNCIL",
                "vote_summary": council_decision.vote_summary,
                "consensus_confidence": council_decision.consensus_confidence
            }
        
        # Apply position modifier from council consensus
        adjusted_quantity = quantity * council_decision.position_size_modifier
        logger.info(f"Council APPROVED with {council_decision.consensus_confidence:.1%} confidence. "
                   f"Position modifier: {council_decision.position_size_modifier}")
        
        # STEP 2: MODEL ENSEMBLE VALIDATION
        ensemble = get_ensemble()
        ensemble_decision = ensemble.predict(council_data)
        
        if ensemble_decision.should_halt:
            logger.warning(f"REJECTED BY ENSEMBLE: {ensemble_decision.reasoning}")
            return {
                "status": "REJECTED_BY_ENSEMBLE",
                "reason": ensemble_decision.reasoning,
                "stage": "MODEL_ENSEMBLE",
                "agreement_score": ensemble_decision.agreement_score
            }
        
        # Further adjust quantity based on ensemble agreement
        adjusted_quantity *= ensemble_decision.position_modifier
        
        # STEP 3: ANCIENT LOGIC OVERRIDE
        market_context["signal"] = side
        cycle_ok, cycle_msg = ancient_logic.check_cycle(market_context)
        if not cycle_ok:
            logger.warning(f"REJECTED BY GOVERNOR (Ancient Logic): {cycle_msg}")
            return {
                "status": "REJECTED_BY_GOVERNOR",
                "reason": cycle_msg,
                "stage": "ANCIENT_LOGIC"
            }

        # STEP 4: RISK GOVERNOR VALIDATION
        price = market_context.get("price", 0.0)
        atr_data = market_context.get("atr_data", {})
        confidence = council_decision.consensus_confidence  # Use council confidence
        
        risk_ok, risk_msg = risk_governor.validate_trade(
            symbol, adjusted_quantity, price, atr_data, confidence
        )
        if not risk_ok:
            logger.warning(f"REJECTED BY GOVERNOR (Risk Filter): {risk_msg}")
            return {
                "status": "REJECTED_BY_GOVERNOR",
                "reason": risk_msg,
                "stage": "RISK_GOVERNOR"
            }

        # STEP 5: CIRCUIT BREAKER CHECK
        cb_manager = circuit_breaker.get_manager()
        trading_allowed, cb_reason = cb_manager.is_trading_allowed()
        if not trading_allowed:
            logger.warning(f"REJECTED BY CIRCUIT BREAKER: {cb_reason}")
            return {
                "status": "REJECTED_BY_CIRCUIT_BREAKER",
                "reason": cb_reason,
                "stage": "CIRCUIT_BREAKER"
            }

        # STEP 6: EXECUTION
        engine = execution.get_engine()
        result = engine.execute_trade(symbol, side, adjusted_quantity)
        
        if result.status == execution.OrderStatus.FAILED:
            stealth.log_event("TRADE_FAILED", {
                "symbol": symbol, "error": result.error
            }, sensitivity="HIGH")
            raise HTTPException(status_code=400, detail=result.error)
        
        # Log successful execution
        stealth.log_event("TRADE_EXECUTED", {
            "symbol": symbol, "side": side,
            "original_quantity": quantity,
            "adjusted_quantity": adjusted_quantity,
            "council_confidence": council_decision.consensus_confidence
        }, sensitivity="HIGH")
        
        return stealth.minimize_response({
            "status": "EXECUTED",
            "order": result.to_dict(),
            "council_decision": {
                "quorum_reached": True,
                "confidence": council_decision.consensus_confidence,
                "vote_summary": council_decision.vote_summary,
                "position_modifier": council_decision.position_size_modifier
            },
            "ensemble_agreement": ensemble_decision.agreement_score,
            "risk_message": risk_msg
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade route error: {e}")
        stealth.log_event("TRADE_ERROR", {"error": str(e)}, sensitivity="CRITICAL")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EMERGENCY CONTROLS
# =============================================================================
@app.post("/kill")
async def emergency_kill(symbol: str = Body(None), purge: bool = Body(False)):
    """Emergency Kill Switch: Cancels all orders and disables trading."""
    logger.critical("EMERGENCY KILL TRIGGERED VIA API")
    stealth = get_stealth_mode()
    
    # Log critical event
    stealth.log_event("KILL_SWITCH", {
        "symbol": symbol, "purge_requested": purge
    }, sensitivity="CRITICAL")
    
    try:
        # Trigger global halt
        cb_manager = circuit_breaker.get_manager()
        cb_manager.global_halt("API Kill Switch")
        
        # Cancel all orders
        engine = execution.get_engine()
        kill_result = engine.kill_switch(symbol)
        
        # Shutdown via risk governor
        risk_governor.emergency_shutdown("API Kill Switch")
        
        # Activate stealth purge if requested
        if purge:
            stealth.trigger_purge("API Kill Switch with Purge")
        
        return {
            "status": "KILLED",
            "symbol": symbol or "ALL",
            "execution_result": kill_result,
            "purge_activated": purge,
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
