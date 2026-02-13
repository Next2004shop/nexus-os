"""
NEXUS Sovereign Pipeline - Shared 6-Stage Execution Gate
=========================================================

Extracted from /trade endpoint to enforce the same safety gates
for ALL trade paths: HTTP API, scheduler heartbeat, and future
Telegram commands.

IMMUTABLE LAW: No trade without council quorum (3/5 agents agree).

Stages:
1. Stealth Mode check (system operational?)
2. Multi-Agent Council deliberation (QUORUM REQUIRED)
3. Model Ensemble prediction validation
4. Ancient Logic cycle check
5. Risk Governor validation
6. Circuit Breaker check + Execution via dual-path engine
"""

import asyncio
import logging
from typing import Dict, Any

from app.services import execution, risk_governor, ancient_logic, circuit_breaker
from app.services.agent_council import get_council
from app.services.model_ensemble import get_ensemble
from app.services.stealth_mode import get_stealth_mode

logger = logging.getLogger("nexus.sovereign_pipeline")


async def execute_sovereign_pipeline(
    symbol: str,
    side: str,
    quantity: float,
    market_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    The Sovereign Execution Flow: Stealth → Council → Ensemble → AncientLogic → Governor → CircuitBreaker → Execute.

    Args:
        symbol: Trading symbol (e.g. "BTCUSD")
        side: "BUY" or "SELL"
        quantity: Base position size (will be adjusted by council + ensemble)
        market_context: Dict with ohlcv, regime, momentum, volatility, bid, ask,
                        price, cycle, signal, atr_data, anomaly

    Returns:
        Dict with 'status' key — one of:
            EXECUTED, REJECTED_SYSTEM_PURGE, REJECTED_BY_COUNCIL,
            REJECTED_BY_ENSEMBLE, REJECTED_BY_GOVERNOR,
            REJECTED_BY_CIRCUIT_BREAKER, FAILED
    """
    logger.info(f"SOVEREIGN_PIPELINE: {side.upper()} {quantity} {symbol}")
    stealth = get_stealth_mode()

    # Log trade attempt
    stealth.log_event("TRADE_ATTEMPT", {
        "symbol": symbol, "side": side, "quantity": quantity
    }, sensitivity="HIGH")

    # ── STEP 0: STEALTH MODE CHECK ──────────────────────────────────────
    if not stealth.is_operational():
        logger.critical("System in PURGE mode — all trading halted")
        return {
            "status": "REJECTED_SYSTEM_PURGE",
            "reason": "System is in emergency purge mode",
            "stage": "STEALTH_MODE",
        }

    # Apply randomized delay for stealth
    delay = stealth.get_order_delay()
    if delay > 0:
        await asyncio.sleep(delay)

    # ── STEP 1: MULTI-AGENT COUNCIL DELIBERATION (CORE REQUIREMENT) ────
    logger.info(f"Convening Agent Council for {symbol} {side}...")
    council = get_council()

    council_data = {
        "ohlcv": market_context.get("ohlcv"),
        "regime": market_context.get("regime"),
        "momentum": market_context.get("momentum"),
        "volatility": market_context.get("volatility"),
        "bid": market_context.get("bid"),
        "ask": market_context.get("ask"),
        "circuit_breaker_status": circuit_breaker.get_manager().get_all_status(),
        "anomaly": market_context.get("anomaly"),
    }

    council_decision = council.deliberate(symbol, side, council_data)

    if not council_decision.quorum_reached:
        logger.warning(f"REJECTED BY COUNCIL: {council_decision.reasoning}")
        stealth.log_event("TRADE_REJECTED", {
            "stage": "COUNCIL",
            "reason": council_decision.reasoning,
            "votes": council_decision.vote_summary,
        }, sensitivity="NORMAL")
        return {
            "status": "REJECTED_BY_COUNCIL",
            "reason": council_decision.reasoning,
            "stage": "AGENT_COUNCIL",
            "vote_summary": council_decision.vote_summary,
            "consensus_confidence": council_decision.consensus_confidence,
        }

    # Apply position modifier from council consensus
    adjusted_quantity = quantity * council_decision.position_size_modifier
    logger.info(
        f"Council APPROVED with {council_decision.consensus_confidence:.1%} confidence. "
        f"Position modifier: {council_decision.position_size_modifier}"
    )

    # ── STEP 2: MODEL ENSEMBLE VALIDATION ───────────────────────────────
    ensemble = get_ensemble()
    ensemble_decision = ensemble.predict(council_data)

    if ensemble_decision.should_halt:
        logger.warning(f"REJECTED BY ENSEMBLE: {ensemble_decision.reasoning}")
        return {
            "status": "REJECTED_BY_ENSEMBLE",
            "reason": ensemble_decision.reasoning,
            "stage": "MODEL_ENSEMBLE",
            "agreement_score": ensemble_decision.agreement_score,
        }

    # Further adjust quantity based on ensemble agreement
    adjusted_quantity *= ensemble_decision.position_modifier

    # ── STEP 3: ANCIENT LOGIC OVERRIDE ──────────────────────────────────
    market_context["signal"] = side
    cycle_ok, cycle_msg = ancient_logic.check_cycle(market_context)
    if not cycle_ok:
        logger.warning(f"REJECTED BY GOVERNOR (Ancient Logic): {cycle_msg}")
        return {
            "status": "REJECTED_BY_GOVERNOR",
            "reason": cycle_msg,
            "stage": "ANCIENT_LOGIC",
        }

    # ── STEP 4: RISK GOVERNOR VALIDATION ────────────────────────────────
    price = market_context.get("price", 0.0)
    atr_data = market_context.get("atr_data", {})
    confidence = council_decision.consensus_confidence

    risk_ok, risk_msg = risk_governor.validate_trade(
        symbol, adjusted_quantity, price, atr_data, confidence
    )
    if not risk_ok:
        logger.warning(f"REJECTED BY GOVERNOR (Risk Filter): {risk_msg}")
        return {
            "status": "REJECTED_BY_GOVERNOR",
            "reason": risk_msg,
            "stage": "RISK_GOVERNOR",
        }

    # ── STEP 5: CIRCUIT BREAKER CHECK ───────────────────────────────────
    cb_manager = circuit_breaker.get_manager()
    trading_allowed, cb_reason = cb_manager.is_trading_allowed()
    if not trading_allowed:
        logger.warning(f"REJECTED BY CIRCUIT BREAKER: {cb_reason}")
        return {
            "status": "REJECTED_BY_CIRCUIT_BREAKER",
            "reason": cb_reason,
            "stage": "CIRCUIT_BREAKER",
        }

    # ── STEP 6: EXECUTION ───────────────────────────────────────────────
    engine = execution.get_engine()
    result = engine.execute_trade(symbol, side, adjusted_quantity)

    if result.status == execution.OrderStatus.FAILED:
        stealth.log_event("TRADE_FAILED", {
            "symbol": symbol, "error": result.error
        }, sensitivity="HIGH")
        return {
            "status": "FAILED",
            "error": result.error,
            "stage": "EXECUTION",
        }

    # Log successful execution
    stealth.log_event("TRADE_EXECUTED", {
        "symbol": symbol, "side": side,
        "original_quantity": quantity,
        "adjusted_quantity": adjusted_quantity,
        "council_confidence": council_decision.consensus_confidence,
    }, sensitivity="HIGH")

    return stealth.minimize_response({
        "status": "EXECUTED",
        "order": result.to_dict(),
        "council_decision": {
            "quorum_reached": True,
            "confidence": council_decision.consensus_confidence,
            "vote_summary": council_decision.vote_summary,
            "position_modifier": council_decision.position_size_modifier,
        },
        "ensemble_agreement": ensemble_decision.agreement_score,
        "risk_message": risk_msg,
    })
