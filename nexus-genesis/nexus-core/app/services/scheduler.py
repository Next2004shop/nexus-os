"""
NEXUS Heartbeat Scheduler
==========================

15-minute candle-period heartbeat that:
1. Syncs equity from MT5
2. Fetches real OHLCV + live tick data
3. Runs the strategy engine for signal generation
4. Routes ALL trades through the full sovereign pipeline
   (Council → Ensemble → AncientLogic → Governor → CircuitBreaker → Execute)

IMMUTABLE LAW: No trade bypasses the sovereign pipeline.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import numpy as np
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services import (
    risk_governor,
    broker_mt5,
    market_data,
    strategy_engine,
)
from app.services.live_data import get_live_data
from app.services.sovereign_pipeline import execute_sovereign_pipeline

logger = logging.getLogger("nexus.heartbeat")

# ── Configuration (environment-driven, no hardcodes) ────────────────────
TRADING_SYMBOLS = [
    s.strip() for s in os.environ.get("NEXUS_TRADING_SYMBOLS", "BTCUSD").split(",") if s.strip()
]

ASSET_CLASS_MAP: Dict[str, str] = {
    "BTCUSD": "crypto",
    "ETHUSD": "crypto",
    "EURUSD": "forex",
    "GBPUSD": "forex",
    "XAUUSD": "forex",
}

# Regime-to-cycle mapping for Ancient Logic
_REGIME_TO_CYCLE: Dict[str, str] = {
    "TRENDING_UP": "EXPANSION",
    "TRENDING_DOWN": "DECAY",
    "RANGING": "ACCUMULATION",
    "VOLATILE": "DISTRIBUTION",
}

OHLCV_BARS = 200          # Need 200 for MA200 in strategy engine
OHLCV_TIMEOUT_SECS = 30   # Max wait for market data fetch
ATR_FAST_PERIOD = 14
ATR_SLOW_PERIOD = 50


def _compute_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> float:
    """Compute Average True Range over the last *period* bars."""
    if len(highs) < period + 1:
        return 0.0
    h = highs[-(period + 1):]
    l = lows[-(period + 1):]
    c = closes[-(period + 1):]
    prev_c = c[:-1]
    h = h[1:]
    l = l[1:]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    return float(np.mean(tr))


def _detect_cycle(strategy_result: Dict[str, Any]) -> str:
    """Map strategy engine regime to Ancient Logic market cycle."""
    trend_result = strategy_result.get("individual_results", {}).get("TrendFollower", {})
    regime = trend_result.get("metadata", {}).get("regime", "RANGING")
    return _REGIME_TO_CYCLE.get(str(regime).upper(), "ACCUMULATION")


async def _notify_telegram(symbol: str, signal: str, result: Dict[str, Any]):
    """
    Placeholder for Telegram integration (Phase E.2).
    TODO: Implement Telegram Bot API notification when ready.
    """
    logger.debug(f"TELEGRAM_STUB: {symbol} {signal} -> {result.get('status')}")


async def _process_symbol(symbol: str, equity: float):
    """Run the full analysis-and-trade cycle for a single symbol."""
    asset_class = ASSET_CLASS_MAP.get(symbol, "crypto")

    # ── 1. Fetch real OHLCV data ────────────────────────────────────────
    try:
        ohlcv = await asyncio.wait_for(
            market_data.fetch_ohlcv(symbol, asset_class, "M15", OHLCV_BARS),
            timeout=OHLCV_TIMEOUT_SECS,
        )
    except (asyncio.TimeoutError, Exception) as exc:
        logger.warning(f"OHLCV_FETCH_FAILED: {symbol} — {exc}")
        return

    if ohlcv is None or ohlcv.empty:
        logger.warning(f"OHLCV_EMPTY: {symbol} — skipping")
        return

    # ── 2. Get live tick for bid/ask/price ──────────────────────────────
    live = get_live_data()
    tick = live.get_tick(symbol) if live else None

    if tick:
        bid, ask = tick.bid, tick.ask
        price = tick.last
    else:
        # Fallback to last OHLCV close
        bid = ask = price = float(ohlcv["close"].iloc[-1])

    # ── 3. Run strategy engine ──────────────────────────────────────────
    orchestrator = strategy_engine.create_orchestrator()
    strategy_result = orchestrator.analyze_all(ohlcv)
    signal = strategy_result.get("composite_signal", "WAIT")
    confidence = strategy_result.get("composite_confidence", 0.0)

    if signal == "WAIT":
        logger.info(f"STRATEGY_NO_SIGNAL: {symbol} (confidence={confidence:.3f})")
        return

    logger.info(f"STRATEGY_SIGNAL: {symbol} {signal} confidence={confidence:.3f}")

    # ── 4. Compute ATR from real data ───────────────────────────────────
    highs = ohlcv["high"].values
    lows = ohlcv["low"].values
    closes = ohlcv["close"].values

    current_atr = _compute_atr(highs, lows, closes, ATR_FAST_PERIOD)
    normal_atr = _compute_atr(highs, lows, closes, ATR_SLOW_PERIOD)

    # ── 5. Detect market cycle from strategy regime ─────────────────────
    cycle = _detect_cycle(strategy_result)

    # ── 6. Compute base position size from Risk Governor state ──────────
    risk_state = risk_governor._get_state()
    if price > 0:
        base_quantity = (risk_state.current_equity * risk_state.max_position_size_pct) / price
    else:
        logger.warning(f"PRICE_ZERO: {symbol} — cannot size position")
        return

    # ── 7. Assemble market context ──────────────────────────────────────
    market_context: Dict[str, Any] = {
        "ohlcv": ohlcv,
        "regime": {
            "regime": strategy_result.get("individual_results", {})
                .get("TrendFollower", {}).get("metadata", {}).get("regime", "RANGING"),
            "trend_strength": confidence,
        },
        "momentum": {
            "score": strategy_result.get("buy_score", 0) - strategy_result.get("sell_score", 0),
        },
        "volatility": {
            "current_atr": current_atr,
            "normal_atr": normal_atr,
        },
        "bid": bid,
        "ask": ask,
        "price": price,
        "cycle": cycle,
        "signal": signal,
        "atr_data": {
            "current_atr": current_atr,
            "normal_atr": normal_atr,
        },
        "anomaly": {},
    }

    # ── 8. Execute through sovereign pipeline ───────────────────────────
    logger.info(f"SOVEREIGN_DISPATCH: {symbol} {signal} qty={base_quantity:.6f}")
    result = await execute_sovereign_pipeline(symbol, signal, base_quantity, market_context)

    # ── 9. Audit log ────────────────────────────────────────────────────
    status = result.get("status", "UNKNOWN")
    logger.info(f"HEARTBEAT_RESULT: {symbol} {signal} -> {status}")

    council_info = result.get("council_decision", {})
    if council_info:
        logger.info(
            f"  COUNCIL: quorum={council_info.get('quorum_reached')}, "
            f"confidence={council_info.get('confidence')}"
        )

    if result.get("ensemble_agreement") is not None:
        logger.info(f"  ENSEMBLE: agreement={result['ensemble_agreement']}")

    # ── 10. Future Telegram notification ────────────────────────────────
    await _notify_telegram(symbol, signal, result)


async def heartbeat_task():
    """
    The 15-minute Candle Period Heartbeat.
    Processes each configured symbol through the full sovereign pipeline.
    """
    logger.info(f"HEARTBEAT_INITIATED: {datetime.now(timezone.utc).isoformat()}")

    try:
        # Sync equity from broker
        account = broker_mt5.get_account_info()
        if account and account.get("equity"):
            risk_governor.update_equity(account["equity"])
            equity = account["equity"]
        else:
            equity = risk_governor._get_state().current_equity
            logger.warning(f"BROKER_EQUITY_UNAVAILABLE — using cached: {equity}")

        # Process each symbol independently (one failure doesn't block others)
        for symbol in TRADING_SYMBOLS:
            try:
                await _process_symbol(symbol, equity)
            except Exception as exc:
                logger.error(f"HEARTBEAT_SYMBOL_ERROR: {symbol} — {exc}", exc_info=True)

    except Exception as e:
        logger.error(f"HEARTBEAT_FAILURE: {e}", exc_info=True)

    logger.info("HEARTBEAT_COMPLETE")


def start_scheduler():
    """Start the APScheduler with 15-minute heartbeat aligned to M15 candles."""
    sched = AsyncIOScheduler()
    sched.add_job(heartbeat_task, "interval", minutes=15)
    sched.start()
    logger.info("HEARTBEAT_SCHEDULER_ACTIVE. INTERVAL: 15M.")
    return sched
