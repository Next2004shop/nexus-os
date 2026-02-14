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
import asyncio
import json
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Body, Depends, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.services import intelligence
from app.services import execution
from app.services import risk_governor
from app.services import ancient_logic
from app.services import scheduler
from app.services import strategy_engine
from app.services import circuit_breaker
from app.services import market_data
from app.services.live_data import get_live_data, initialize_live_data
from app.services.ws_manager import get_ws_manager

# New Multi-Agent Council and Ensemble imports
from app.services.agent_council import get_council, require_quorum, Vote
from app.services.model_ensemble import get_ensemble, ensemble_predict
from app.services.stealth_mode import get_stealth_mode
from app.services.sovereign_pipeline import execute_sovereign_pipeline
from app.services.watchdog import get_watchdog
from app.services.env_validator import validate_environment
from app.services.ai_decision_layer import (
    get_ai_decision_engine, get_conversation_memory,
    AISystemMode, fallback_response, LLM_TIMEOUT_SECS,
)
from app.services.ai_audit_logger import get_ai_audit_logger

# Phase 4 imports
from app.services.broker_validator import validate_broker_connection, get_frequency_guard
from app.services.capital_protection import (
    get_daily_tracker, get_floating_guard, get_equity_monitor, get_black_swan,
)
from app.services.heartbeat_monitor import (
    get_heartbeat, get_watchdog_thread, get_graceful_shutdown,
    install_crash_handler,
)
from app.services.telegram_reporter import get_telegram_reporter

# Phase 5 imports
from app.services.market_regime import get_regime_store
from app.services.confluence_engine import (
    analyze_timeframe, calculate_confluence, TimeframeRole,
    get_confluence_context_for_ai,
)
from app.services.news_awareness import get_news_calendar
from app.services.performance_memory import get_performance_memory
from app.services.self_audit import get_self_audit
from app.services.intelligence_context import (
    build_intelligence_context, build_full_ai_prompt,
)

# Phase 6 imports
from app.services.capital_tiers import get_tier_engine
from app.services.position_distribution import get_distribution_engine
from app.services.dynamic_lots import calculate_dynamic_lot, get_lot_config
from app.services.session_intelligence import (
    get_current_session, get_session_tracker, check_session_suitability,
)
from app.services.trade_lifecycle import get_lifecycle_engine
from app.services.system_health import get_health_guard
from app.services.weekly_report import generate_weekly_intelligence_report, format_report_for_telegram

# Configure central logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.nervous_system")

app = FastAPI(
    title="NEXUS SOVEREIGN SYSTEM",
    description="Private Trading System - Ancient Laws × Axelrod Discipline × Multi-Agent Council",
    version="6.0.0"  # Phase 6: scalable growth
)


# =============================================================================
# GLOBAL ERROR HANDLER
# =============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler — prevents process crash on unhandled errors."""
    logger.error(
        f"UNHANDLED_EXCEPTION: {request.method} {request.url.path} — {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"status": "INTERNAL_ERROR", "detail": "An unexpected error occurred"},
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

    # Phase 4: Install crash handler
    install_crash_handler()

    # Phase 2: Environment validation
    env_ok, env_issues = validate_environment()
    if not env_ok:
        logger.critical("ENV_VALIDATION_FAILED — starting in SAFE mode (no live trading)")
        watchdog = get_watchdog()
        watchdog.enter_safe_mode("Environment validation failed on startup")
    else:
        logger.info("ENV_VALIDATION_PASSED")

    # Phase 4: Broker connection validation
    broker_ok, broker_issues, broker_info = validate_broker_connection()
    if not broker_ok and broker_issues and "MT5_NOT_AVAILABLE" not in broker_issues[0]:
        logger.critical(f"BROKER_VALIDATION_FAILED: {broker_issues}")
        watchdog = get_watchdog()
        watchdog.enter_safe_mode(f"Broker validation failed: {'; '.join(broker_issues)}")
        # Send Telegram emergency alert
        try:
            reporter = get_telegram_reporter()
            asyncio.create_task(reporter.send_emergency_alert(
                "BROKER_VALIDATION_FAILED", "; ".join(broker_issues)
            ))
        except Exception:
            pass
    else:
        logger.info(f"BROKER_VALIDATION: {broker_info.broker_name or 'mock/paper'} "
                     f"({broker_info.account_type or 'N/A'})")

    # Phase 4: Initialize capital protection
    daily_tracker = get_daily_tracker()
    try:
        risk_status = risk_governor.get_risk_status()
        daily_tracker.initialize(risk_status["equity"]["current"])
    except Exception:
        daily_tracker.initialize(10000.0)
    logger.info("Capital protection initialized (daily cap, floating DD, equity monitor, black swan)")

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

    # Initialize Live Data and register WebSocket callback
    manager = await initialize_live_data()
    ws_hub = get_ws_manager()

    async def ws_tick_callback(tick):
        await ws_hub.broadcast_tick(tick.to_frontend())

    manager.callbacks.append(ws_tick_callback)
    logger.info("Live Data WebSocket callback registered")

    # Start system status broadcaster
    asyncio.create_task(status_broadcaster())

    # Phase 4: Start heartbeat logger + watchdog thread
    heartbeat = get_heartbeat()
    heartbeat.start()
    watchdog_thread = get_watchdog_thread()
    watchdog_thread.start()

    # Phase 4: Start Telegram daily summary scheduler
    telegram = get_telegram_reporter()
    telegram.start_daily_summary_scheduler()

    # Phase 4: Install graceful shutdown handler
    shutdown_handler = get_graceful_shutdown()
    shutdown_handler.register_callback(lambda: heartbeat.stop())
    shutdown_handler.register_callback(lambda: watchdog_thread.stop())
    shutdown_handler.register_callback(lambda: telegram.stop())
    shutdown_handler.register_callback(lambda: logger.critical("NEXUS STATE SAVED — SHUTDOWN COMPLETE"))
    shutdown_handler.install_signal_handlers()

    # Phase 5: Log intelligence layer status
    logger.info("Intelligence modules loaded: regime, confluence, news, memory, self-audit")

    # Phase 6: Start system health guard + initialize tier engine
    health_guard = get_health_guard()
    health_guard.start()
    logger.info("System health guard started")

    # Initialize capital tier from current equity
    try:
        tier_engine = get_tier_engine()
        risk_status = risk_governor.get_risk_status()
        eq = risk_status["equity"]["current"]
        init_eq = risk_status["equity"]["initial"]
        peak_eq = risk_status["equity"]["peak"]
        tier_state = tier_engine.classify(eq, init_eq, peak_eq)
        logger.info(f"Capital tier: {tier_state.tier.value}")
    except Exception:
        logger.info("Capital tier: defaulting to STABLE")

    logger.info("Phase 6 modules loaded: tiers, distribution, dynamic lots, sessions, lifecycle, health")
    logger.info("NEXUS SOVEREIGN SYSTEM ONLINE (v6.0.0 — Scalable Growth)")


async def status_broadcaster():
    """Broadcast system status every 2 seconds."""
    ws_hub = get_ws_manager()
    while True:
        try:
            status = await system_status()
            await ws_hub.broadcast_status(status)
        except Exception as e:
            logger.error(f"Status broadcast error: {e}")
        await asyncio.sleep(2)


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful cleanup on shutdown."""
    logger.critical("NEXUS CORE SHUTTING DOWN...")

    # Phase 4: Notify Telegram
    try:
        reporter = get_telegram_reporter()
        await reporter.send_emergency_alert("SYSTEM_SHUTDOWN", "Nexus is shutting down gracefully")
    except Exception:
        pass

    # Phase 4 + 6: Stop background threads
    try:
        get_heartbeat().stop()
        get_watchdog_thread().stop()
        get_telegram_reporter().stop()
        get_health_guard().stop()
    except Exception:
        pass

    # Cleanup market data connections
    provider = market_data.get_provider()
    await provider.close()

    # Shutdown execution engine
    engine = execution.get_engine()
    engine.shutdown()

    logger.critical("NEXUS CORE OFFLINE")


# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================
@app.websocket("/ws/nexus")
async def websocket_endpoint(websocket: WebSocket):
    """
    NEXUS Command WebSocket Hub.
    Broadcasts real-time ticks and system state.
    """
    manager = get_ws_manager()
    connection_id = str(uuid4())
    await manager.connect(websocket, connection_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client commands (e.g., SUBSCRIBE)
            if message.get("type") == "SUBSCRIBE":
                symbols = message.get("symbols", [])
                await manager.subscribe(connection_id, symbols)
                
            elif message.get("type") == "PING":
                await websocket.send_text(json.dumps({"type": "PONG"}))
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)


# =============================================================================
# CORS CONFIGURATION
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sovereing choice: allow all for cloud flexibility
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


@app.get("/watchdog")
async def watchdog_status():
    """Get watchdog system state (mode, failures, desync, broker)."""
    return get_watchdog().get_state().to_dict()


# =============================================================================
# CAPITAL PROTECTION ENDPOINTS (Phase 4)
# =============================================================================
@app.get("/capital/daily")
async def capital_daily_status():
    """Get daily P&L and loss cap status."""
    return get_daily_tracker().get_daily_summary()


@app.get("/capital/floating")
async def capital_floating_dd():
    """Get floating drawdown status."""
    guard = get_floating_guard()
    blocked, reason = guard.should_block_new_trades()
    return {"blocked": blocked, "reason": reason}


@app.get("/capital/equity-curve")
async def capital_equity_curve():
    """Get equity curve monitor status and risk multiplier."""
    return get_equity_monitor().get_status()


@app.get("/capital/black-swan")
async def capital_black_swan():
    """Get black swan detector status."""
    return get_black_swan().get_status()


@app.get("/capital/frequency")
async def capital_frequency():
    """Get trade frequency guard stats."""
    return get_frequency_guard().get_stats()


@app.get("/heartbeat")
async def heartbeat_status():
    """Get heartbeat logger and watchdog thread status."""
    return {
        "heartbeat": get_heartbeat().get_status(),
        "watchdog_thread": get_watchdog_thread().get_status(),
        "telegram": get_telegram_reporter().get_status(),
    }


# =============================================================================
# INTELLIGENCE ENDPOINTS (Phase 5)
# =============================================================================
@app.get("/intelligence/regimes")
async def intelligence_regimes():
    """Get all current market regime classifications."""
    return get_regime_store().get_all()


@app.get("/intelligence/regime/{symbol}")
async def intelligence_regime_symbol(symbol: str):
    """Get regime classification for a specific symbol."""
    store = get_regime_store()
    state = store.get(symbol.upper())
    if state is None:
        return {"symbol": symbol, "regime": "UNKNOWN", "message": "No regime classified"}
    return state.to_dict()


@app.get("/intelligence/news")
async def intelligence_news():
    """Get all scheduled economic events."""
    return {"events": get_news_calendar().get_all_events_dict()}


@app.get("/intelligence/news/{symbol}")
async def intelligence_news_symbol(symbol: str):
    """Check news blackout status for a symbol."""
    cal = get_news_calendar()
    in_blackout, event = cal.is_in_blackout_window(symbol.upper())
    return {
        "symbol": symbol.upper(),
        "in_blackout": in_blackout,
        "event": event.to_dict() if event else None,
        "context": cal.get_news_context_for_ai(symbol.upper()),
    }


@app.get("/intelligence/performance")
async def intelligence_performance():
    """Get all asset performance profiles."""
    return get_performance_memory().get_all_profiles()


@app.get("/intelligence/performance/{symbol}")
async def intelligence_performance_symbol(symbol: str):
    """Get performance profile for a specific asset."""
    profile = get_performance_memory().get_profile(symbol.upper())
    if profile is None:
        return {"symbol": symbol, "message": "No performance data"}
    return profile.to_dict()


@app.get("/intelligence/context/{symbol}")
async def intelligence_context(symbol: str):
    """Get full intelligence context for a symbol (as AI would see it)."""
    return {"symbol": symbol.upper(), "context": build_intelligence_context(symbol.upper())}


@app.get("/intelligence/audit")
async def intelligence_audit():
    """Get recent trade audits."""
    return {"audits": get_self_audit().get_recent_audits()}


@app.get("/intelligence/review/daily")
async def intelligence_daily_review():
    """Get or generate daily review."""
    audit = get_self_audit()
    review = audit.get_latest_daily_review()
    if review is None:
        review = audit.generate_daily_review().to_dict()
    return review


@app.get("/intelligence/review/weekly")
async def intelligence_weekly_review():
    """Get or generate weekly report."""
    audit = get_self_audit()
    report = audit.get_latest_weekly_report()
    if report is None:
        report = audit.generate_weekly_report().to_dict()
    return report


# =============================================================================
# SCALING & GROWTH ENDPOINTS (Phase 6)
# =============================================================================
@app.get("/scaling/tier")
async def scaling_tier():
    """Get current capital tier and configuration."""
    engine = get_tier_engine()
    try:
        risk = risk_governor.get_risk_status()
        eq = risk["equity"]["current"]
        init_eq = risk["equity"]["initial"]
        peak_eq = risk["equity"]["peak"]
        state = engine.classify(eq, init_eq, peak_eq)
        return state.to_dict()
    except Exception:
        return {"tier": engine.get_current_tier().value}


@app.get("/scaling/distribution")
async def scaling_distribution():
    """Get position distribution status."""
    return get_distribution_engine().get_status()


@app.get("/scaling/lots")
async def scaling_lots():
    """Get dynamic lot configuration."""
    return get_lot_config()


@app.get("/scaling/session")
async def scaling_session():
    """Get current market session and suitability."""
    session = get_current_session()
    return {
        "current_session": session.value,
        "performance": get_session_tracker().get_performance(),
        "context": get_session_tracker().get_session_context_for_ai(),
    }


@app.get("/scaling/lifecycle")
async def scaling_lifecycle():
    """Get trade lifecycle management status."""
    return get_lifecycle_engine().get_status()


@app.get("/scaling/health")
async def scaling_health():
    """Get system health diagnostics."""
    guard = get_health_guard()
    report = guard.get_latest_report()
    return report or {"status": "NO_DATA", "message": "Health check not yet run"}


@app.get("/scaling/weekly-report")
async def scaling_weekly_report():
    """Generate full weekly intelligence report."""
    return generate_weekly_intelligence_report()


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

    try:
        result = await execute_sovereign_pipeline(symbol, side, quantity, market_context)

        if result.get("status") == "FAILED":
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade route error: {e}")
        stealth = get_stealth_mode()
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
# MASTER AI COMMAND INTERFACE
# =============================================================================
@app.post("/ai/command")
async def master_ai_command(
    command: str = Body(..., embed=True),
    authorization: Optional[str] = Header(None)
):
    """
    Master AI Command Interface.
    
    Send natural language commands to NEXUS.
    Only the Master can execute sensitive commands.
    """
    from app.services.master_ai import get_master_ai
    from app.services.auth_service import get_auth_service
    
    master_ai = get_master_ai()
    auth_service = get_auth_service()
    
    # Determine if user is master
    is_master = False
    user_id = "anonymous"
    
    if authorization:
        token = authorization.replace("Bearer ", "")
        session = auth_service.validate_request(token)
        if session:
            is_master = auth_service.is_master(session)
            user_id = session.user_id
    
    # Process command
    result = await master_ai.process_command(command, user_id, is_master)
    
    return result.to_response()


@app.get("/ai/status")
async def master_ai_status():
    """Get Master AI status."""
    from app.services.master_ai import get_master_ai
    
    master_ai = get_master_ai()
    
    return {
        "online": master_ai.is_online,
        "trading_paused": master_ai.trading_paused,
        "stealth_mode": master_ai.stealth_mode,
        "commands_processed": len(master_ai.command_history),
        "last_command": master_ai.command_history[-1].to_response() if master_ai.command_history else None
    }


# =============================================================================
# AI DECISION LAYER ENDPOINTS (Phase 3)
# =============================================================================
@app.post("/ai/trade-intent")
async def ai_trade_intent(
    raw_prompt: str = Body(...),
    ai_response_text: str = Body(...),
    human_confirmed: bool = Body(False),
    authorization: Optional[str] = Header(None),
):
    """
    Process an AI-generated trading intent through the 3-layer architecture.

    Layer 2: Parses + validates strict JSON schema.
    Layer 3: Routes through deterministic execution engine.

    AI CANNOT override risk governor, lot limits, or system mode.
    If AI response is malformed → safe fallback (no trade).
    """
    from app.services.auth_service import get_auth_service

    user_id = "anonymous"
    if authorization:
        token = authorization.replace("Bearer ", "")
        auth_service = get_auth_service()
        session = auth_service.validate_request(token)
        if session:
            user_id = session.user_id

    engine = get_ai_decision_engine()

    try:
        result = await asyncio.wait_for(
            engine.process_ai_output(
                raw_prompt=raw_prompt,
                ai_response_text=ai_response_text,
                user_id=user_id,
                human_confirmed=human_confirmed,
            ),
            timeout=LLM_TIMEOUT_SECS + 60,  # pipeline timeout is separate
        )
        return result
    except asyncio.TimeoutError:
        logger.error("AI trade-intent processing timed out")
        return fallback_response("Processing timed out")
    except Exception as e:
        logger.error(f"AI trade-intent error: {e}", exc_info=True)
        return fallback_response(f"Internal error: {type(e).__name__}")


@app.post("/ai/mode")
async def set_ai_mode(
    mode: str = Body(..., embed=True),
    authorization: Optional[str] = Header(None),
):
    """
    Set AI system mode.

    Modes: ANALYSIS, MANUAL_TRADE, AUTO, SAFE, EMERGENCY
    Only Master auth can change mode.
    """
    from app.services.auth_service import get_auth_service

    # Require master auth for mode changes
    if authorization:
        token = authorization.replace("Bearer ", "")
        auth_service = get_auth_service()
        session = auth_service.validate_request(token)
        if not session or not auth_service.is_master(session):
            raise HTTPException(status_code=403, detail="Only Master can change AI mode")
    else:
        raise HTTPException(status_code=401, detail="Authorization required")

    engine = get_ai_decision_engine()
    ok, message = engine.set_mode(mode.upper())

    if not ok:
        raise HTTPException(status_code=400, detail=message)

    return {"status": "MODE_CHANGED", "mode": engine.get_mode(), "message": message}


@app.get("/ai/mode")
async def get_ai_mode():
    """Get current AI system mode."""
    engine = get_ai_decision_engine()
    return {"mode": engine.get_mode()}


@app.get("/ai/audit")
async def get_ai_audit(n: int = 20):
    """Get recent AI audit trail entries."""
    audit = get_ai_audit_logger()
    return {"entries": audit.get_recent(n), "stats": audit.get_stats()}


@app.get("/ai/audit/stats")
async def get_ai_audit_stats():
    """Get AI audit statistics summary."""
    audit = get_ai_audit_logger()
    return audit.get_stats()


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================
@app.post("/auth/login")
async def login(
    id_token: str = Body(..., embed=True),
    device_id: Optional[str] = Body(None),
    request: Request = None
):
    """
    Login with Firebase ID token.
    
    Returns session token for subsequent requests.
    NO CREDENTIALS RETURNED TO FRONTEND.
    """
    from app.services.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    
    # Get IP address
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None
    
    success, session, message = auth_service.login_with_firebase(
        id_token=id_token,
        device_id=device_id,
        ip_address=ip_address
    )
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    return {
        "status": "authenticated",
        "session_token": session.session_token,
        "session_info": session.to_frontend(),
        "message": message
    }


@app.post("/auth/logout")
async def logout(authorization: str = Header(...)):
    """Logout and invalidate session."""
    from app.services.auth_service import get_auth_service
    
    token = authorization.replace("Bearer ", "")
    auth_service = get_auth_service()
    auth_service.logout(token)
    
    return {"status": "logged_out"}


@app.get("/auth/session")
async def get_session(authorization: str = Header(...)):
    """Get current session info."""
    from app.services.auth_service import get_auth_service
    
    token = authorization.replace("Bearer ", "")
    auth_service = get_auth_service()
    session = auth_service.validate_request(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return session.to_frontend()


# =============================================================================
# TRADING ACCOUNT MANAGEMENT
# =============================================================================
@app.post("/accounts/register")
async def register_trading_account(
    broker: str = Body(...),
    login: str = Body(...),
    password: str = Body(...),
    server: str = Body(...),
    authorization: str = Header(...)
):
    """
    Register a trading account.
    
    Credentials are encrypted and stored server-side only.
    FRONTEND NEVER SEES CREDENTIALS AGAIN.
    """
    from app.services.auth_service import get_auth_service, AuthLevel
    
    token = authorization.replace("Bearer ", "")
    auth_service = get_auth_service()
    session = auth_service.validate_request(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    if session.auth_level not in [AuthLevel.TRADER, AuthLevel.ADMIN, AuthLevel.MASTER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    account_id = auth_service.trading_accounts.register_account(
        user_id=session.user_id,
        broker=broker,
        login=login,
        password=password,
        server=server
    )
    
    return {
        "status": "registered",
        "account_id": account_id,
        "message": "Trading account registered. Credentials encrypted."
    }


@app.get("/accounts/list")
async def list_trading_accounts(authorization: str = Header(...)):
    """List user's trading accounts (safe info only)."""
    from app.services.auth_service import get_auth_service
    
    token = authorization.replace("Bearer ", "")
    auth_service = get_auth_service()
    session = auth_service.validate_request(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    accounts = auth_service.trading_accounts.list_user_accounts(session.user_id)
    
    return {"accounts": accounts, "count": len(accounts)}


# =============================================================================
# LIVE DATA ENDPOINTS
# =============================================================================
@app.get("/data/tick/{symbol}")
async def get_live_tick(symbol: str):
    """
    Get live tick data for symbol.
    
    Safe data only - no API keys exposed.
    """
    from app.services.live_data import get_live_data
    
    manager = get_live_data()
    data = manager.get_frontend_data(symbol.upper())
    
    if not data:
        return {"symbol": symbol, "status": "no_data"}
    
    return data


@app.get("/data/health")
async def get_data_health():
    """Check live data integrity."""
    from app.services.live_data import get_live_data
    
    manager = get_live_data()
    return manager.check_data_integrity()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

