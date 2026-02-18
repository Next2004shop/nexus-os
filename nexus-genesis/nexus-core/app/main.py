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

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import (
    Body,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.services import (
    ancient_logic,
    circuit_breaker,
    execution,
    intelligence,
    market_data,
    risk_governor,
    scheduler,
    strategy_engine
)
from app.services.agent_council import get_council
from app.services.auth_service import (
    UserSession,
    get_current_session,
    require_trader,
    require_admin,
    require_master,
    get_auth_service
)
from app.services.env_validator import validate_environment, get_env_status
from app.services.live_data import get_live_data, initialize_live_data
from app.services.model_ensemble import get_ensemble
from app.services.nexus_logger import configure_nexus_logging
from app.services.stealth_mode import get_stealth_mode
from app.services.vault import VaultError, SecretRetrievalError
from app.services.ws_manager import get_ws_manager
from app.services.telegram_bot import get_telegram_service

# Auth Layer
from auth import auth_router, AuthMiddleware, seed_admin

# Command & Intelligence APIs
from command.api import router as command_api_router
from risk.api import router as risk_api_router
from intelligence.api import router as intelligence_api_router
from telemetry.api import router as telemetry_api_router
from risk.api import router as risk_api_router
from intelligence.api import router as intelligence_api_router
from telemetry.api import router as telemetry_api_router
from telemetry.telemetry_engine import get_telemetry
from system.runtime_guard import get_guard

# Meta-Intelligence Layer (Phase 10)
from meta.api import router as meta_api_router
from meta.performance_intelligence import get_performance_intelligence

# Security & Infrastructure Hardening (Phase 11)
from security.api import router as security_api_router
from security.startup_hardening import run_startup_checks
from security.failsafe import get_failsafe
from security.capital_lock import get_capital_lock
from security.state_integrity import get_state_integrity
from security.position_shadow import get_position_shadow

# Deployment Architecture & Global Stability (Phase 12)
from config.config_loader import get_config
from config.version_tag import stamp_deployment, get_version_info
from deployment.api import router as deployment_api_router
from deployment.backup import get_backup_manager
from deployment.deployment_check import run_deployment_checks
from deployment.deployment_lock import get_deployment_lock
from deployment.resource_monitor import get_resource_monitor
from deployment.rollback import save_stable_state
from deployment.stability_loop import get_stability_loop
from deployment.update_guard import get_update_guard

# =============================================================================
# LOGGING + UPTIME
# =============================================================================

configure_nexus_logging(json_format=True)
logger = logging.getLogger("nexus.nervous_system")

_startup_time: float = 0.0  # Set during startup_event()

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="NEXUS SOVEREIGN SYSTEM",
    description="Private Trading System - Ancient Laws × Axelrod Discipline × Multi-Agent Council",
    version="4.0.0"
)

# Mount Auth
app.include_router(auth_router)
app.add_middleware(AuthMiddleware)

# Mount Command API
app.include_router(command_api_router)

# Mount Risk API
app.include_router(risk_api_router)

# Mount Intelligence API
app.include_router(intelligence_api_router)

# Mount Telemetry API
app.include_router(telemetry_api_router)

# Mount Meta-Intelligence API (Phase 10)
app.include_router(meta_api_router)

# Mount Security API (Phase 11)
app.include_router(security_api_router)

# Mount Deployment API (Phase 12)
app.include_router(deployment_api_router)


# =============================================================================
# RATE LIMITER (In-Memory Token Bucket)
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter using token bucket.
    
    Tracks requests per client IP per endpoint group.
    Resets every window_seconds.
    """
    
    def __init__(self):
        # {endpoint_group: {client_ip: [timestamps]}}
        self._requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        
        # Limits: (max_requests, window_seconds)
        self.limits: Dict[str, tuple] = {
            "trade": (10, 60),        # 10 req/min
            "kill": (5, 60),          # 5 req/min
            "auth": (20, 60),         # 20 req/min
            "ai": (30, 60),           # 30 req/min
            "default": (60, 60),      # 60 req/min
        }
    
    def check(self, group: str, client_ip: str) -> bool:
        """
        Check if request is allowed.
        Returns True if allowed, False if rate limited.
        """
        max_requests, window = self.limits.get(group, self.limits["default"])
        now = time.time()
        
        # Clean old entries
        self._requests[group][client_ip] = [
            t for t in self._requests[group][client_ip]
            if now - t < window
        ]
        
        if len(self._requests[group][client_ip]) >= max_requests:
            return False
        
        self._requests[group][client_ip].append(now)
        return True


_rate_limiter = RateLimiter()


def rate_limit(group: str = "default"):
    """FastAPI dependency for rate limiting."""
    async def _check_rate(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        if not _rate_limiter.check(group, client_ip):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {group}. Try again later."
            )
    return _check_rate


# =============================================================================
# TRADE AUDIT LOGGER
# =============================================================================

class TradeAuditLogger:
    """
    Structured audit log for all trade pipeline activity.
    
    Every trade attempt is logged with:
    - Timestamp (UTC ISO)
    - User ID
    - Symbol, side, quantity
    - Pipeline stages passed
    - Result (EXECUTED / REJECTED_AT_{stage})
    """
    
    MAX_LOG_SIZE = 500  # Keep last 500 entries in memory
    
    def __init__(self):
        self._log: List[Dict[str, Any]] = []
    
    def log_trade(self, entry: Dict[str, Any]):
        """Add a trade audit entry."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._log.append(entry)
        
        # Trim if over limit
        if len(self._log) > self.MAX_LOG_SIZE:
            self._log = self._log[-self.MAX_LOG_SIZE:]
        
        logger.info(f"TRADE_AUDIT: {json.dumps(entry)}")
    
    def get_recent(self, count: int = 50) -> List[Dict]:
        """Get most recent audit entries."""
        return self._log[-count:]


_trade_audit = TradeAuditLogger()


# =============================================================================
# STARTUP & SHUTDOWN
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize all systems on startup."""
    global _startup_time
    _startup_time = time.time()
    
    # PHASE 12: Load configuration and stamp version FIRST
    nexus_config = get_config()
    version_info = stamp_deployment(nexus_config.env_mode.value)

    logger.info("=" * 60)
    logger.info("NEXUS SOVEREIGN SYSTEM INITIALIZING...")
    logger.info(f"Version: v{version_info.get('version', '?')} | Commit: {version_info.get('git_commit', '?')}")
    logger.info(f"Environment: {nexus_config.env_mode.value} | Risk: {nexus_config.risk_level}")
    logger.info("Architecture: Ancient Laws × Axelrod Game Theory × Netflix Resilience")
    logger.info("Decision: Multi-Agent Council (5 Agents, 3/5 Quorum)")
    logger.info("Brain: Model Ensemble (Gemini Pro + Rule-Based + Pattern)")
    logger.info("Execution: Dual-Path (MT5 + Binance)")
    logger.info("Security: Stealth Mode Active")
    logger.info("Infrastructure: Phase 11 Hardening + Phase 12 Deployment")
    logger.info("=" * 60)

    # STEP -1: Production Startup Hardening (Phase 11)
    try:
        startup_report = run_startup_checks()
        if not startup_report.can_start:
            logger.critical(f"STARTUP BLOCKED by hardening checks: {startup_report.critical_failures}")
            print("\n" + "!" * 60)
            print("STARTUP BLOCKED — Critical hardening failures:")
            for f in startup_report.critical_failures:
                print(f"   FAIL: {f}")
            print("!" * 60 + "\n")
        else:
            if startup_report.warnings:
                logger.warning(f"Startup hardening warnings: {startup_report.warnings}")
            else:
                logger.info("Startup hardening: All checks passed")
    except Exception as e:
        logger.error(f"Startup hardening check failed: {e}")

    # STEP 0: Environment Validation Gate
    try:
        env_status = validate_environment()
        logger.info(f"Environment validation passed. Trading ready: {env_status.trading_ready}")
        
        # Clear terminal warnings for missing optional vars
        if env_status.trading_missing:
            print("\n" + "=" * 60)
            print("⚠  WARNING: Trading environment variables missing:")
            for var in env_status.trading_missing:
                print(f"   → {var}")
            print("   Trading functionality will be LIMITED.")
            print("=" * 60 + "\n")
        
        if env_status.optional_missing:
            print("ℹ  INFO: Optional variables not set:")
            for var in env_status.optional_missing:
                print(f"   → {var}")
            print()
        
    except RuntimeError as e:
        print("\n" + "!" * 60)
        print("🛑  CRITICAL: Environment validation FAILED")
        print(f"   {e}")
        print("   System starting in DEGRADED mode — trading disabled")
        print("!" * 60 + "\n")
        logger.critical(f"Environment validation FAILED: {e}")
        logger.critical("System starting in DEGRADED mode — trading disabled")
    
    # Start the Heartbeat Scheduler
    scheduler.start_scheduler()
    
    # Seed admin user on first startup
    try:
        seed_admin()
    except Exception as e:
        logger.warning(f"Admin seed skipped: {e}")
    
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
    
    # Start Telegram Bot
    telegram = get_telegram_service()
    await telegram.start()

    # Start Telemetry Engine
    await get_telemetry().start()
    
    # Start Runtime Guard
    await get_guard().start()

    # Start Meta-Intelligence Layer (Phase 10)
    await get_performance_intelligence().start()
    logger.info("Meta-Intelligence Layer (Phase 10) ACTIVE")

    # Start Security Infrastructure (Phase 11)
    await get_state_integrity().start()
    await get_position_shadow().start()
    logger.info("Security Infrastructure (Phase 11) ACTIVE")
    logger.info(f"Failsafe Mode: {get_failsafe().mode.value}")

    # ---- Phase 12: Deployment Architecture ----

    # D) Safe Deployment Check (production only)
    deployment_report = None
    if nexus_config.is_production():
        try:
            deployment_report = run_deployment_checks()
            if not deployment_report.can_deploy:
                logger.critical(f"DEPLOYMENT CHECK FAILED: {deployment_report.failures}")
                print("\n" + "!" * 60)
                print("DEPLOYMENT CHECK FAILED — Blocking issues:")
                for f in deployment_report.failures:
                    print(f"   FAIL: {f}")
                print("!" * 60 + "\n")
            else:
                logger.info("Pre-production deployment checks passed")
        except Exception as e:
            logger.error(f"Deployment check error: {e}")

    # J) Deployment Lock
    deploy_lock = get_deployment_lock()
    if nexus_config.deployment_lock:
        deploy_lock.activate("Configured via ENV/config", source="CONFIG")
    logger.info(f"Deployment Lock: {'ACTIVE' if deploy_lock.is_locked else 'INACTIVE'}")

    # H) Update Guard — snapshot checksums on clean start
    try:
        guard = get_update_guard()
        guard.snapshot_checksums()
        logger.info("Update guard checksums captured")
    except Exception as e:
        logger.error(f"Update guard error: {e}")

    # E) Save stable state for rollback
    try:
        save_stable_state()
        logger.info("Rollback stable state saved")
    except Exception as e:
        logger.error(f"Rollback state save error: {e}")

    # F) Automated Backup
    if nexus_config.backup_enabled:
        backup_mgr = get_backup_manager()
        backup_mgr.configure(retention_days=nexus_config.backup_retention_days)
        await backup_mgr.start()
        logger.info("Automated backup system ACTIVE")

    # I) Resource Monitoring
    if nexus_config.resource_monitoring_enabled:
        await get_resource_monitor().start()
        logger.info("Resource monitoring ACTIVE")

    # K) Stability Loop Supervisor
    await get_stability_loop().start()
    logger.info("Stability loop supervisor ACTIVE")

    # G) Telegram Deployment Report (production)
    if nexus_config.is_production() or nexus_config.telegram_bot_token:
        try:
            from deployment.telegram_report import send_deployment_report
            await send_deployment_report(
                version_info=version_info,
                config_info=nexus_config.to_safe_dict(),
                deployment_report=(
                    {
                        "can_deploy": deployment_report.can_deploy,
                        "failures": deployment_report.failures,
                        "warnings": deployment_report.warnings,
                    }
                    if deployment_report else None
                ),
            )
        except Exception as e:
            logger.error(f"Telegram deployment report error: {e}")

    logger.info("Deployment Architecture (Phase 12) ACTIVE")
    logger.info("NEXUS SOVEREIGN SYSTEM ONLINE")


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
    """Cleanup on shutdown."""
    logger.info("NEXUS CORE SHUTTING DOWN...")
    
    # Cleanup market data connections
    provider = market_data.get_provider()
    await provider.close()
    
    # Shutdown execution engine
    # Shutdown execution engine
    engine = execution.get_engine()
    engine.shutdown()
    
    # Stop Telemetry Engine
    await get_telemetry().stop()
    
    # Stop Runtime Guard
    await get_guard().stop()

    # Stop Meta-Intelligence Layer
    await get_performance_intelligence().stop()

    # Stop Security Infrastructure
    await get_state_integrity().stop()
    await get_position_shadow().stop()

    # Stop Deployment Infrastructure (Phase 12)
    await get_stability_loop().stop()
    await get_resource_monitor().stop()
    await get_backup_manager().stop()

    logger.info("NEXUS CORE OFFLINE")


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
# CORS CONFIGURATION (Locked Down)
# =============================================================================
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
_allowed_origins = [origin.strip() for origin in _allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


# =============================================================================
# GLOBAL ERROR HANDLERS
# =============================================================================

@app.exception_handler(SecretRetrievalError)
async def secret_error_handler(request: Request, exc: SecretRetrievalError):
    """Handle vault secret retrieval failures gracefully."""
    logger.critical(f"Secret retrieval failed: {exc.secret_id}")
    return JSONResponse(
        status_code=503,
        content={
            "status": "SERVICE_UNAVAILABLE",
            "detail": "A required service credential is unavailable. System degraded.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(VaultError)
async def vault_error_handler(request: Request, exc: VaultError):
    """Handle vault initialization errors."""
    logger.critical(f"Vault error: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "status": "SERVICE_UNAVAILABLE",
            "detail": "Secret management service unavailable.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global catch-all exception handler.
    
    Prevents raw exception messages from leaking to clients.
    Logs full error server-side, returns safe message to client.
    """
    error_id = str(uuid4())[:8]
    logger.error(f"Unhandled exception [{error_id}]: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "INTERNAL_ERROR",
            "detail": "An unexpected error occurred. Contact system administrator.",
            "error_id": error_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================
@app.get("/health")
async def health_check():
    """System health check — hardened with full control layer status."""
    cb_manager = circuit_breaker.get_manager()
    trading_allowed, reason = cb_manager.is_trading_allowed()
    
    # Include environment validation status
    try:
        env_status = get_env_status()
        env_info = env_status.to_dict()
    except Exception:
        env_info = {"environment_valid": False, "trading_ready": False}
    
    # Execution engine status
    engine = execution.get_engine()
    mt5_connected = engine.mt5._initialized
    is_paper = engine.config.use_paper_trading
    
    # Risk engine status
    try:
        risk_status = risk_governor.get_risk_status()
        risk_active = risk_status.get("trading_enabled", False)
    except Exception:
        risk_active = False
    
    # Uptime calculation
    uptime_seconds = time.time() - _startup_time if _startup_time else 0
    hours, remainder = divmod(int(uptime_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    return {
        "status": "ok",
        "uptime": uptime_str,
        "mt5_connected": mt5_connected,
        "version": "4.0.0",
        "risk_engine": "active" if risk_active else "inactive",
        "execution_layer": "ready" if (mt5_connected or is_paper) else "not_ready",
        "mode": "paper" if is_paper else "live",
        "trading_enabled": trading_allowed,
        "trading_status": reason,
        "environment": env_info,
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
            "version": "4.0.0",
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
@app.post("/analyze", dependencies=[Depends(rate_limit("default"))])
async def analyze_market(
    data: Dict[str, Any] = Body(...),
    session: UserSession = Depends(get_current_session)
):
    """
    Analyze market data using AI + Strategy Engine.
    
    This is advisory only - does not place trades.
    Requires authentication (VIEWER+).
    """
    logger.info(f"Analysis request from user {session.user_id}")
    
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
        raise HTTPException(status_code=500, detail="Analysis failed")


@app.post("/analyze/full", dependencies=[Depends(rate_limit("default"))])
async def full_market_analysis(
    symbol: str = Body(...),
    asset_class: str = Body(default="forex"),
    timeframe: str = Body(default="M15"),
    session: UserSession = Depends(get_current_session)
):
    """
    Full analysis using market data + all strategy modules.
    Requires authentication (VIEWER+).
    """
    logger.info(f"Full analysis request: {symbol} from user {session.user_id}")
    
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
        raise HTTPException(status_code=500, detail="Analysis failed")


# =============================================================================
# TRADE EXECUTION ENDPOINTS
# =============================================================================
@app.post("/trade", dependencies=[Depends(rate_limit("trade"))])
async def place_trade(
    symbol: str = Body(...),
    side: str = Body(...),
    quantity: float = Body(...),
    market_context: Dict[str, Any] = Body(default={}),
    session: UserSession = Depends(require_trader)
):
    """
    The Sovereign Execution Flow: Auth → Council → Ensemble → Governor → Execute.
    
    IMMUTABLE LAW: No trade without council quorum (3/5 agents agree).
    IMMUTABLE LAW: No trade without authenticated TRADER session.
    
    Flow:
    0. Authentication + Authorization (TRADER+)
    1. Stealth Mode check (system operational?)
    2. Multi-Agent Council deliberation (QUORUM REQUIRED)
    3. Model Ensemble prediction validation
    4. Ancient Logic cycle check
    5. Risk Governor validation
    6. Circuit Breaker check
    7. Execution via dual-path engine
    8. Audit log
    """
    logger.info(f"NEXUS_TRADE_COMMAND: {side.upper()} {quantity} {symbol} by user {session.user_id}")
    stealth = get_stealth_mode()
    
    # Initialize audit entry
    audit_entry = {
        "user_id": session.user_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "stages_passed": ["AUTH"],
        "result": None,
        "rejection_reason": None
    }
    
    # Log trade attempt
    stealth.log_event("TRADE_ATTEMPT", {
        "symbol": symbol, "side": side, "quantity": quantity,
        "user_id": session.user_id
    }, sensitivity="HIGH")
    
    try:
        # STEP 0: STEALTH MODE CHECK
        if not stealth.is_operational():
            logger.critical("System in PURGE mode - all trading halted")
            audit_entry["result"] = "REJECTED_SYSTEM_PURGE"
            audit_entry["rejection_reason"] = "System in emergency purge mode"
            _trade_audit.log_trade(audit_entry)
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
            audit_entry["stages_passed"].append("STEALTH")
            audit_entry["result"] = "REJECTED_BY_COUNCIL"
            audit_entry["rejection_reason"] = council_decision.reasoning
            _trade_audit.log_trade(audit_entry)
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
            audit_entry["stages_passed"].extend(["STEALTH", "COUNCIL"])
            audit_entry["result"] = "REJECTED_BY_ENSEMBLE"
            audit_entry["rejection_reason"] = ensemble_decision.reasoning
            _trade_audit.log_trade(audit_entry)
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
            audit_entry["stages_passed"].extend(["STEALTH", "COUNCIL", "ENSEMBLE"])
            audit_entry["result"] = "REJECTED_BY_GOVERNOR"
            audit_entry["rejection_reason"] = cycle_msg
            _trade_audit.log_trade(audit_entry)
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
            audit_entry["stages_passed"].extend(["STEALTH", "COUNCIL", "ENSEMBLE", "ANCIENT_LOGIC"])
            audit_entry["result"] = "REJECTED_BY_GOVERNOR"
            audit_entry["rejection_reason"] = risk_msg
            _trade_audit.log_trade(audit_entry)
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
            audit_entry["stages_passed"].extend(["STEALTH", "COUNCIL", "ENSEMBLE", "ANCIENT_LOGIC", "RISK"])
            audit_entry["result"] = "REJECTED_BY_CIRCUIT_BREAKER"
            audit_entry["rejection_reason"] = cb_reason
            _trade_audit.log_trade(audit_entry)
            return {
                "status": "REJECTED_BY_CIRCUIT_BREAKER",
                "reason": cb_reason,
                "stage": "CIRCUIT_BREAKER"
            }

        # STEP 6: EXECUTION
        engine = execution.get_engine()
        result = engine.execute_trade(symbol, side, adjusted_quantity, skip_risk_check=True)
        
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
        
        # Full audit trail for successful execution
        audit_entry["stages_passed"] = ["AUTH", "STEALTH", "COUNCIL", "ENSEMBLE", "ANCIENT_LOGIC", "RISK", "CIRCUIT_BREAKER", "EXECUTED"]
        audit_entry["result"] = "EXECUTED"
        audit_entry["adjusted_quantity"] = adjusted_quantity
        audit_entry["council_confidence"] = council_decision.consensus_confidence
        _trade_audit.log_trade(audit_entry)
        
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
        audit_entry["result"] = "ERROR"
        audit_entry["rejection_reason"] = str(e)
        _trade_audit.log_trade(audit_entry)
        raise HTTPException(status_code=500, detail="Trade execution failed")


# =============================================================================
# EMERGENCY CONTROLS
# =============================================================================
@app.post("/kill", dependencies=[Depends(rate_limit("kill"))])
async def emergency_kill(
    symbol: str = Body(None),
    purge: bool = Body(False),
    session: UserSession = Depends(require_trader)
):
    """Emergency Kill Switch: Cancels all orders and disables trading."""
    logger.critical(f"EMERGENCY KILL TRIGGERED VIA API by user {session.user_id}")
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
async def resume_trading(
    admin_key: str = Body(...),
    session: UserSession = Depends(require_trader)
):
    """
    Resume trading after emergency halt (requires admin key).
    """
    logger.warning(f"RESUME TRADING REQUESTED by user {session.user_id}")
    
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
async def update_equity(
    equity: float = Body(...),
    session: UserSession = Depends(require_trader)
):
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
@app.post("/ai/command", dependencies=[Depends(rate_limit("ai"))])
async def master_ai_command(
    command: str = Body(..., embed=True),
    session: UserSession = Depends(require_trader)
):
    """
    Master AI Command Interface.
    
    Send natural language commands to NEXUS.
    Only the Master can execute sensitive commands.
    """
    from app.services.master_ai import get_master_ai
    
    master_ai = get_master_ai()
    auth_service = get_auth_service()
    
    # Session already validated by Depends(require_trader)
    is_master = auth_service.is_master(session)
    
    # Process command
    result = await master_ai.process_command(command, session.user_id, is_master)
    
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
# AUTHENTICATION ENDPOINTS
# =============================================================================
@app.post("/auth/login", dependencies=[Depends(rate_limit("auth"))])
async def login(
    id_token: str = Body(..., embed=True),
    device_id: Optional[str] = Body(None),
    request: Request = None
):
    """
    Login with Firebase ID token.
    
    Returns session token for subsequent requests.
    NO CREDENTIALS RETURNED TO FRONTEND.
    Rate limited: 20 req/min per IP.
    """
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
async def logout(session: UserSession = Depends(get_current_session)):
    """Logout and invalidate session."""
    auth_service = get_auth_service()
    auth_service.logout(session.session_token)
    
    return {"status": "logged_out"}


@app.get("/auth/session")
async def get_session(session: UserSession = Depends(get_current_session)):
    """Get current session info."""
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
    session: UserSession = Depends(require_trader)
):
    """
    Register a trading account.
    
    Credentials are encrypted and stored server-side only.
    FRONTEND NEVER SEES CREDENTIALS AGAIN.
    Requires TRADER+ authorization.
    """
    auth_service = get_auth_service()
    
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
async def list_trading_accounts(session: UserSession = Depends(get_current_session)):
    """List user's trading accounts (safe info only)."""
    auth_service = get_auth_service()
    accounts = auth_service.trading_accounts.list_user_accounts(session.user_id)
    
    return {"accounts": accounts, "count": len(accounts)}


# =============================================================================
# LIVE DATA ENDPOINTS
# =============================================================================
@app.get("/data/tick/{symbol}")
async def get_live_tick(
    symbol: str,
    session: UserSession = Depends(get_current_session)
):
    """
    Get live tick data for symbol.
    
    Safe data only - no API keys exposed.
    Requires authentication (VIEWER+).
    """
    manager = get_live_data()
    data = manager.get_frontend_data(symbol.upper())
    
    if not data:
        return {"symbol": symbol, "status": "no_data"}
    
    return data


@app.get("/data/health")
async def get_data_health():
    """Check live data integrity — public endpoint."""
    manager = get_live_data()
    return manager.check_data_integrity()


# =============================================================================
# TRADE AUDIT ENDPOINT
# =============================================================================
@app.get("/audit/trades")
async def get_trade_audit(
    count: int = 50,
    session: UserSession = Depends(require_admin)
):
    """
    Get recent trade audit log.
    
    Requires ADMIN+ authorization.
    Returns timestamped log of all trade pipeline activity.
    """
    return {
        "audit_log": _trade_audit.get_recent(count),
        "total_logged": len(_trade_audit._log),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

