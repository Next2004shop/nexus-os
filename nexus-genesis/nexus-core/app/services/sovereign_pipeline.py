"""
NEXUS Sovereign Pipeline - Shared Execution Gate
==================================================

ALL trade paths (HTTP API, scheduler, AI decision layer, Telegram)
flow through this single gate.

IMMUTABLE LAW: No trade without council quorum (3/5 agents agree).

Phase 2 — execution hardening (timeout, locks, watchdog)
Phase 4 — capital protection (spread, margin, frequency, daily cap,
          floating DD, black swan, slippage, Telegram)
Phase 5 — intelligence (regime, news, confluence)
Phase 6 — scaling (tiers, distribution, sessions, dynamic lots, lifecycle)
"""

import asyncio
import logging
import math
from typing import Dict, Any, Optional

from app.services import execution, risk_governor, ancient_logic, circuit_breaker
from app.services.agent_council import get_council
from app.services.model_ensemble import get_ensemble
from app.services.stealth_mode import get_stealth_mode
from app.services.execution_lock import get_execution_lock
from app.services.watchdog import get_watchdog

# Phase 4 imports
from app.services.broker_validator import (
    check_spread, check_slippage, check_margin,
    estimate_required_margin, get_frequency_guard,
)
from app.services.capital_protection import (
    get_daily_tracker, get_floating_guard, get_equity_monitor,
    get_black_swan, auto_adjust_lots, MAX_LOT_LIMIT,
)

# Phase 5 imports
from app.services.news_awareness import get_news_calendar
from app.services.market_regime import get_regime_store, Regime

# Phase 6 imports
from app.services.capital_tiers import get_tier_engine
from app.services.position_distribution import get_distribution_engine
from app.services.session_intelligence import check_session_suitability
from app.services.dynamic_lots import calculate_dynamic_lot

logger = logging.getLogger("nexus.sovereign_pipeline")

# Maximum time the entire pipeline may run before being aborted
PIPELINE_TIMEOUT_SECS = 45

# Allowed symbols (extend via config in production)
ALLOWED_SYMBOLS = {
    "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "XAUUSD",
    "BTC/USDT", "ETH/USDT",
}

ALLOWED_SIDES = {"BUY", "SELL"}


def _validate_inputs(
    symbol: str, side: str, quantity: float, market_context: Dict[str, Any]
) -> Optional[str]:
    """
    Validate pipeline inputs. Returns an error string or None if valid.
    """
    if not symbol or not isinstance(symbol, str):
        return "INVALID_SYMBOL: empty or non-string"
    if symbol.upper() not in ALLOWED_SYMBOLS:
        return f"UNKNOWN_SYMBOL: {symbol} not in approved list"
    if not side or side.upper() not in ALLOWED_SIDES:
        return f"INVALID_SIDE: must be BUY or SELL, got {side}"
    if not isinstance(quantity, (int, float)):
        return "INVALID_QUANTITY: not a number"
    if math.isnan(quantity) or math.isinf(quantity) or quantity <= 0:
        return f"INVALID_QUANTITY: {quantity}"
    if not isinstance(market_context, dict):
        return "INVALID_MARKET_CONTEXT: must be a dict"
    return None


async def execute_sovereign_pipeline(
    symbol: str,
    side: str,
    quantity: float,
    market_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    The Sovereign Execution Flow.

    Pre-flight:
      Input validation → Watchdog → Daily loss cap → Floating DD →
      Black swan → Trade frequency → Execution lock

    Pipeline:
      Stealth → Council → Ensemble → Ancient Logic →
      Risk Governor → Spread filter → Margin check →
      Circuit Breaker → Re-validate → Execute → Slippage check

    Post-execution:
      Telegram notification → Audit logging
    """
    # ── PRE-FLIGHT: Input validation ──────────────────────────────
    input_err = _validate_inputs(symbol, side, quantity, market_context)
    if input_err:
        logger.warning(f"PIPELINE_INPUT_REJECTED: {input_err}")
        return {"status": "REJECTED_INPUT", "reason": input_err, "stage": "INPUT_VALIDATION"}

    side = side.upper()

    # ── PRE-FLIGHT: Watchdog check ────────────────────────────────
    watchdog = get_watchdog()
    if not watchdog.is_trading_allowed():
        mode = watchdog.get_mode().value
        logger.warning(f"PIPELINE_BLOCKED_BY_WATCHDOG: system mode={mode}")
        return {"status": "REJECTED_WATCHDOG", "reason": f"System mode is {mode}", "stage": "WATCHDOG"}

    # ── PRE-FLIGHT: Daily loss cap ────────────────────────────────
    daily_tracker = get_daily_tracker()
    if daily_tracker.is_cap_hit():
        logger.warning("PIPELINE_BLOCKED: daily loss cap already hit")
        return {"status": "REJECTED_DAILY_CAP", "reason": "Daily loss cap hit — no new trades", "stage": "DAILY_CAP"}

    # ── PRE-FLIGHT: Floating drawdown ─────────────────────────────
    floating_guard = get_floating_guard()
    blocked, float_reason = floating_guard.should_block_new_trades()
    if blocked:
        logger.warning(f"PIPELINE_BLOCKED: {float_reason}")
        return {"status": "REJECTED_FLOATING_DD", "reason": float_reason, "stage": "FLOATING_DD"}

    # ── PRE-FLIGHT: Black swan ────────────────────────────────────
    black_swan = get_black_swan()
    if black_swan.is_triggered():
        logger.warning("PIPELINE_BLOCKED: black swan event active")
        return {"status": "REJECTED_BLACK_SWAN", "reason": "Black swan event detected — system paused", "stage": "BLACK_SWAN"}

    # ── PRE-FLIGHT: News blackout (Phase 5) ─────────────────────
    news_cal = get_news_calendar()
    in_blackout, news_event = news_cal.is_in_blackout_window(symbol)
    if in_blackout:
        event_name = news_event.name if news_event else "unknown"
        logger.warning(f"PIPELINE_BLOCKED: news blackout for {symbol} ({event_name})")
        return {"status": "REJECTED_NEWS_BLACKOUT", "reason": f"News blackout: {event_name}", "stage": "NEWS_FILTER"}

    # ── PRE-FLIGHT: Regime requirement (Phase 5) ──────────────────
    regime_store = get_regime_store()
    if not regime_store.has_regime(symbol):
        logger.warning(f"PIPELINE_BLOCKED: no regime classified for {symbol}")
        return {"status": "REJECTED_NO_REGIME", "reason": f"No regime data for {symbol} — classify before trading", "stage": "REGIME_CHECK"}

    # ── PRE-FLIGHT: Capital tier daily limit (Phase 6) ──────────
    tier_engine = get_tier_engine()
    tier_ok, tier_reason = tier_engine.can_trade()
    if not tier_ok:
        logger.warning(f"PIPELINE_TIER_LIMITED: {tier_reason}")
        return {"status": "REJECTED_TIER_LIMIT", "reason": tier_reason, "stage": "CAPITAL_TIER"}

    # ── PRE-FLIGHT: Tier asset restriction (Phase 6) ──────────────
    asset_ok, asset_reason = tier_engine.check_asset_allowed(symbol)
    if not asset_ok:
        logger.warning(f"PIPELINE_TIER_ASSET: {asset_reason}")
        return {"status": "REJECTED_TIER_ASSET", "reason": asset_reason, "stage": "CAPITAL_TIER"}

    # ── PRE-FLIGHT: Position distribution (Phase 6) ───────────────
    dist_engine = get_distribution_engine()
    dist_ok, dist_reason = dist_engine.can_open_position(symbol, side)
    if not dist_ok:
        logger.warning(f"PIPELINE_DISTRIBUTION: {dist_reason}")
        return {"status": "REJECTED_DISTRIBUTION", "reason": dist_reason, "stage": "POSITION_DISTRIBUTION"}

    # ── PRE-FLIGHT: Session suitability (Phase 6) ─────────────────
    session_ok, session_reason, current_session = check_session_suitability(symbol)
    if not session_ok:
        logger.warning(f"PIPELINE_SESSION: {session_reason}")
        return {"status": "REJECTED_SESSION", "reason": session_reason, "stage": "SESSION_FILTER"}

    # ── PRE-FLIGHT: Trade frequency ───────────────────────────────
    freq_guard = get_frequency_guard()
    freq_ok, freq_reason = freq_guard.check(symbol)
    if not freq_ok:
        logger.warning(f"PIPELINE_RATE_LIMITED: {freq_reason}")
        return {"status": "REJECTED_FREQUENCY", "reason": freq_reason, "stage": "TRADE_FREQUENCY"}

    # ── PRE-FLIGHT: Execution lock ────────────────────────────────
    elock = get_execution_lock()
    acquired, lock_reason = elock.acquire_symbol(symbol)
    if not acquired:
        logger.warning(f"PIPELINE_LOCK_DENIED: {lock_reason}")
        return {"status": "REJECTED_LOCK", "reason": lock_reason, "stage": "EXECUTION_LOCK"}

    trade_executed = False
    watchdog.execution_started(symbol)

    try:
        result = await asyncio.wait_for(
            _run_pipeline(symbol, side, quantity, market_context),
            timeout=PIPELINE_TIMEOUT_SECS,
        )
        trade_executed = result.get("status") == "EXECUTED"

        # Record trade in frequency guard + distribution + tier if executed
        if trade_executed:
            freq_guard.record_trade(symbol)
            dist_engine.register_position(symbol, side)
            tier_engine.record_trade()

        return result
    except asyncio.TimeoutError:
        logger.error(f"PIPELINE_TIMEOUT: {symbol} exceeded {PIPELINE_TIMEOUT_SECS}s")
        watchdog.execution_finished(symbol, success=False)
        return {"status": "TIMEOUT", "reason": f"Pipeline exceeded {PIPELINE_TIMEOUT_SECS}s", "stage": "TIMEOUT"}
    except Exception as exc:
        logger.error(f"PIPELINE_UNHANDLED_ERROR: {symbol} — {exc}", exc_info=True)
        watchdog.execution_finished(symbol, success=False)
        return {"status": "FAILED", "error": str(exc), "stage": "UNHANDLED"}
    finally:
        elock.release_symbol(symbol, trade_executed=trade_executed)


async def _run_pipeline(
    symbol: str,
    side: str,
    quantity: float,
    market_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Inner pipeline logic, wrapped by timeout + lock in the outer function."""
    logger.info(f"SOVEREIGN_PIPELINE: {side} {quantity} {symbol}")
    stealth = get_stealth_mode()
    watchdog = get_watchdog()

    # Log trade attempt
    stealth.log_event("TRADE_ATTEMPT", {
        "symbol": symbol, "side": side, "quantity": quantity
    }, sensitivity="HIGH")

    # ── STEP 0: STEALTH MODE CHECK ──────────────────────────────
    if not stealth.is_operational():
        logger.critical("System in PURGE mode — all trading halted")
        watchdog.execution_finished(symbol, success=False)
        return {
            "status": "REJECTED_SYSTEM_PURGE",
            "reason": "System is in emergency purge mode",
            "stage": "STEALTH_MODE",
        }

    # Apply randomized delay for stealth
    delay = stealth.get_order_delay()
    if delay > 0:
        await asyncio.sleep(delay)

    # ── STEP 1: MULTI-AGENT COUNCIL DELIBERATION (CORE REQUIREMENT) ──
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
        watchdog.execution_finished(symbol, success=False)
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

    # ── STEP 2: MODEL ENSEMBLE VALIDATION ────────────────────────
    ensemble = get_ensemble()
    ensemble_decision = ensemble.predict(council_data)

    if ensemble_decision.should_halt:
        logger.warning(f"REJECTED BY ENSEMBLE: {ensemble_decision.reasoning}")
        watchdog.execution_finished(symbol, success=False)
        return {
            "status": "REJECTED_BY_ENSEMBLE",
            "reason": ensemble_decision.reasoning,
            "stage": "MODEL_ENSEMBLE",
            "agreement_score": ensemble_decision.agreement_score,
        }

    # Further adjust quantity based on ensemble agreement
    adjusted_quantity *= ensemble_decision.position_modifier

    # ── STEP 2b: EQUITY CURVE RISK ADJUSTMENT (Phase 4) ──────────
    equity_monitor = get_equity_monitor()
    risk_multiplier = equity_monitor.get_risk_multiplier()
    if risk_multiplier < 1.0:
        adjusted_quantity = auto_adjust_lots(0, adjusted_quantity, risk_multiplier)
        logger.info(f"Equity curve risk adjustment: multiplier={risk_multiplier:.2f}, qty={adjusted_quantity}")

    # Cap at absolute lot limit
    adjusted_quantity = min(adjusted_quantity, MAX_LOT_LIMIT)

    # ── STEP 3: ANCIENT LOGIC OVERRIDE ───────────────────────────
    market_context["signal"] = side
    cycle_ok, cycle_msg = ancient_logic.check_cycle(market_context)
    if not cycle_ok:
        logger.warning(f"REJECTED BY GOVERNOR (Ancient Logic): {cycle_msg}")
        watchdog.execution_finished(symbol, success=False)
        return {
            "status": "REJECTED_BY_GOVERNOR",
            "reason": cycle_msg,
            "stage": "ANCIENT_LOGIC",
        }

    # ── STEP 4: RISK GOVERNOR VALIDATION ─────────────────────────
    price = market_context.get("price", 0.0)
    atr_data = market_context.get("atr_data", {})
    confidence = council_decision.consensus_confidence

    risk_ok, risk_msg = risk_governor.validate_trade(
        symbol, adjusted_quantity, price, atr_data, confidence
    )
    if not risk_ok:
        logger.warning(f"REJECTED BY GOVERNOR (Risk Filter): {risk_msg}")
        watchdog.execution_finished(symbol, success=False)
        return {
            "status": "REJECTED_BY_GOVERNOR",
            "reason": risk_msg,
            "stage": "RISK_GOVERNOR",
        }

    # ── STEP 4b: SPREAD FILTER (Phase 4) ─────────────────────────
    bid = market_context.get("bid", 0.0)
    ask = market_context.get("ask", 0.0)
    atr_val = atr_data.get("current_atr") if atr_data else None

    if bid > 0 and ask > 0:
        spread_ok, spread_reason = check_spread(bid, ask, price, atr_val)
        if not spread_ok:
            logger.warning(f"REJECTED BY SPREAD FILTER: {spread_reason}")
            watchdog.execution_finished(symbol, success=False)
            return {
                "status": "REJECTED_SPREAD",
                "reason": spread_reason,
                "stage": "SPREAD_FILTER",
            }

    # ── STEP 4c: MARGIN CHECK (Phase 4) ──────────────────────────
    risk_state = risk_governor._get_state()
    leverage = int(market_context.get("leverage", 100))
    if price > 0 and risk_state.current_equity > 0:
        req_margin = estimate_required_margin(symbol, adjusted_quantity, price, leverage)
        free_margin = risk_state.current_equity * 0.8  # conservative estimate
        margin_ok, margin_reason = check_margin(free_margin, req_margin)
        if not margin_ok:
            logger.warning(f"REJECTED BY MARGIN CHECK: {margin_reason}")
            watchdog.execution_finished(symbol, success=False)
            return {
                "status": "REJECTED_MARGIN",
                "reason": margin_reason,
                "stage": "MARGIN_CHECK",
            }

    # ── STEP 5: CIRCUIT BREAKER CHECK ────────────────────────────
    cb_manager = circuit_breaker.get_manager()
    trading_allowed, cb_reason = cb_manager.is_trading_allowed()
    if not trading_allowed:
        logger.warning(f"REJECTED BY CIRCUIT BREAKER: {cb_reason}")
        watchdog.execution_finished(symbol, success=False)
        return {
            "status": "REJECTED_BY_CIRCUIT_BREAKER",
            "reason": cb_reason,
            "stage": "CIRCUIT_BREAKER",
        }

    # ── STEP 5b: RE-VALIDATE trading_enabled right before execution ──
    final_state = risk_governor._get_state()
    if not final_state.trading_enabled:
        logger.warning("REJECTED: trading_enabled flipped between validation and execution")
        watchdog.execution_finished(symbol, success=False)
        return {
            "status": "REJECTED_BY_GOVERNOR",
            "reason": "TRADING_DISABLED_DURING_PIPELINE",
            "stage": "RISK_GOVERNOR_RECHECK",
        }

    # ── STEP 6: EXECUTION ────────────────────────────────────────
    engine = execution.get_engine()
    result = engine.execute_trade(symbol, side, adjusted_quantity)

    if result.status == execution.OrderStatus.FAILED:
        stealth.log_event("TRADE_FAILED", {
            "symbol": symbol, "error": result.error
        }, sensitivity="HIGH")
        watchdog.execution_finished(symbol, success=False)
        return {
            "status": "FAILED",
            "error": result.error,
            "stage": "EXECUTION",
        }

    # ── STEP 6b: POST-EXECUTION SLIPPAGE CHECK (Phase 4) ─────────
    if result.slippage is not None and result.requested_price and result.filled_price:
        from app.services.broker_validator import check_slippage
        slip_ok, slip_pct, slip_reason = check_slippage(result.requested_price, result.filled_price)
        if not slip_ok:
            logger.warning(f"SLIPPAGE_ALERT: {slip_reason} — trade executed but flagged")
            # Trade already executed — log alert, don't reject
            stealth.log_event("SLIPPAGE_ALERT", {
                "symbol": symbol, "slippage_pct": slip_pct, "reason": slip_reason,
            }, sensitivity="HIGH")

    # ── STEP 7: POST-EXECUTION NOTIFICATIONS (Phase 4) ───────────
    # Telegram trade open notification (fire-and-forget)
    try:
        from app.services.telegram_reporter import get_telegram_reporter
        reporter = get_telegram_reporter()
        if reporter.is_enabled:
            asyncio.create_task(reporter.notify_trade_open(
                symbol=symbol,
                side=side,
                lot_size=adjusted_quantity,
                entry_price=result.filled_price or price,
                stop_loss=market_context.get("stop_loss"),
                take_profit=market_context.get("take_profit"),
                risk_pct=market_context.get("risk_pct", 1.0),
                confidence=confidence,
            ))
    except Exception as e:
        logger.error(f"Telegram notification error: {e}")

    # Log successful execution
    stealth.log_event("TRADE_EXECUTED", {
        "symbol": symbol, "side": side,
        "original_quantity": quantity,
        "adjusted_quantity": adjusted_quantity,
        "council_confidence": council_decision.consensus_confidence,
    }, sensitivity="HIGH")

    watchdog.execution_finished(symbol, success=True)

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
