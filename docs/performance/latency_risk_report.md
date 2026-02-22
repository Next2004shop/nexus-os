# NEXUS Latency Risk Report
## CPP-1 Audit — Where Delays Impact Trading Decisions

**Prepared by:** System Performance Architect
**Audit Date:** 2026-02-22

---

## Overview

This report identifies latency sources in the Nexus trading pipeline and quantifies their impact on trade decision timeliness. Latency in algorithmic trading is not merely a performance concern — it is a risk factor. Delayed execution relative to signal generation means the market has moved, spreads have widened, or the trade opportunity has expired.

---

## 1. Trade Pipeline Latency Breakdown

End-to-end latency from `POST /trade` to order submission:

| Stage | Component | Estimated Latency | Type |
|-------|-----------|------------------|------|
| 0 | RateLimiter.check | < 0.1ms | Compute |
| 1 | Auth middleware | 1–5ms | Compute (token validation) |
| 2 | Stealth mode check | < 0.1ms | Flag check |
| 2a | Stealth mode delay (if configured) | 0–10,000ms | Intentional sleep |
| 3 | AgentCouncil.deliberate — 5 agents | 5–30ms | Compute (numpy/pandas) |
| 3a | VolatilityRiskAgent._calculate_atr_percentile | 1–5ms | Python loop (hotspot) |
| 4 | ModelEnsemble.predict | 200–2,200ms | Dominated by Vertex AI |
| 4a | GeminiModel.predict (Vertex AI) | 200–2,000ms | External network call |
| 4b | RuleBasedModel.predict | < 1ms | Pure Python |
| 4c | PatternModel.predict | 1–3ms | Python loop |
| 5 | ancient_logic.check_cycle | < 0.1ms | Dict lookup |
| 6 | risk_governor.validate_trade | 5–50ms | Firestore read/write |
| 7 | circuit_breaker.is_trading_allowed | < 0.1ms | Dict iteration |
| 8 | ExecutionOptimizer.optimize_entry | 10–200ms | Polygon REST + EMA |
| 8a | mt5.get_current_price | 1–10ms | MT5 SDK call |
| 9 | MT5Executor.execute / BinanceExecutor.execute | 50–500ms | Broker round-trip |
| 10 | risk_governor.register_position | 5–50ms | Firestore write |

**Best-case total:** ~280ms (fast Vertex AI, Firestore cache hit, fast broker)
**Typical total:** ~600ms–1,200ms
**Worst-case total:** ~3,500ms+ (slow Vertex AI, Firestore cold, retries)

---

## 2. Critical Latency Risks

### RISK-1: Vertex AI Latency Gates Every Trade Decision

**Severity: CRITICAL**

`GeminiModel.predict()` is synchronous and sits inside the model ensemble hot path. The ensemble runs sequentially:

```python
for model in self.models:      # GeminiModel runs first (weight 1.5)
    if model.is_healthy:
        pred = model.predict(market_data)  # blocks here for 200ms–2s
```

The system will not submit a trade until Gemini responds. If Vertex AI is slow (regional quota pressure, cold start, network jitter), the signal generated 2 seconds ago is now 2 seconds stale. For scalping or intraday signals on 1-minute charts, the signal's valid window may have already closed.

**Market impact:** Price can move 0.1%–0.5% in 2 seconds on volatile assets (BTC, NAS100). The expected slippage increases proportionally with pipeline latency.

**No C++ fix available.** This is a network call. The risk mitigation is architectural: either run Gemini predictions asynchronously and cache the most recent regime opinion (decoupled from per-trade invocation), or cap Vertex AI with a timeout fallback to rule-based + pattern models.

---

### RISK-2: Synchronous Firestore in Trade Validation

**Severity: HIGH**

`risk_governor.validate_trade()` calls `_get_state()` and `_save_state()`, each potentially touching Firestore. These are synchronous calls wrapped in async context.

`_get_state()` → `StateManager.load_state()` — if state is stale or not yet loaded, this issues a Firestore document read. Firestore P99 read latency from Cloud Run to Firestore (same region): 10–30ms. Cold-path (document not in local cache): 30–80ms.

`_save_state()` — Firestore write after position registration. Same latency profile.

**Observed pattern:** validate_trade is called at Gate 6 AND register_position is called at step 10. Two Firestore writes per successful trade, plus potential reads, adds 20–160ms to the pipeline on top of everything else.

**Market impact:** Not critical for swing/daily strategies. Significant for 1-minute strategies where 100ms matters.

---

### RISK-3: Sync/Async Impedance in ExecutionEngine.execute_trade

**Severity: HIGH (stability risk, not just latency)**

`ExecutionEngine.execute_trade()` is defined as a synchronous function (`def execute_trade`). It is called from async route handlers and from the async StrategyEngine. Inside it:

```python
opt_result = asyncio.run_coroutine_threadsafe(
    self.optimizer.optimize_entry(symbol, side, price_to_check, spread),
    asyncio.get_event_loop()
).result()
```

**Problem:** `asyncio.get_event_loop()` in this context returns the running loop. Submitting a coroutine to the *running* loop and then calling `.result()` (which blocks the current thread) will deadlock if the current thread IS the event loop thread. This is the case when called from FastAPI route handlers.

**Observed mitigation:** The code wraps this in `try/except Exception as e: logger.warning(...)` with `proceed anyway`, so in practice the optimize step silently fails and is skipped. The deadlock risk is masked by the fallback. But if the asyncio environment changes (e.g., thread executor), the deadlock could surface.

**Latency impact:** When optimization does work correctly, `optimize_entry()` adds `get_ohlcv()` latency (10–200ms Polygon REST) to the synchronous execution path.

---

### RISK-4: MT5 Bridge Polling Lag

**Severity: MEDIUM**

The MetaTrader connector polls `/quotes` every 500ms. Between polls, price data held in `LiveDataManager.ticks{}` is up to 500ms stale. When `execution.py` calls `mt5.get_current_price(symbol)` to determine bid/ask for spread calculation, it calls the MT5 SDK directly — this bypasses the cached ticks and goes to the Windows MT5 VM.

However, the live data displayed on the frontend and used in stealth/circuit-breaker decisions comes from the 500ms-polled ticks. A price spike that occurs between polls will not be visible to the system until the next poll.

**Market impact:** During fast market events (NFP releases, earnings, Fed announcements), a 500ms blind spot is sufficient for a multi-percent gap to develop. The circuit breaker's `PriceMovementBreaker` will not trigger until the gap is captured in the next poll.

---

### RISK-5: Agent Council — 5 Agents Run in Series

**Severity: MEDIUM**

The 5 agents in `AgentCouncil.deliberate()` are iterated in a Python for-loop:

```python
for agent in self.agents:
    result = await agent.analyze(market_context)
```

Each agent does independent analysis (no data dependency between agents). Yet they run sequentially. The total council latency is the sum of all 5 agents' compute time, not the max.

**Observed agent compute times (estimated):**
- MarketStructureAgent: 2–5ms (numpy max/min, rolling means on 50 bars)
- MomentumAgent: 1–3ms (RSI, ROC)
- VolatilityRiskAgent: 3–10ms (ATR percentile loop — worst in council)
- MacroSentimentAgent: 1–3ms (MA50/MA200)
- ExecutionSafetyAgent: < 1ms (flag checks)

**Serial total:** 8–22ms
**Parallel theoretical max:** 3–10ms (bottlenecked by VolatilityRiskAgent)

Parallelizing via `asyncio.gather()` would require agents to be async, which they currently are not (they use numpy, not I/O). CPU-bound tasks in asyncio don't benefit from gather unless moved to a thread pool.

---

### RISK-6: Backtest Signal Staleness on DataFrame Slice

**Severity: MEDIUM (backtest accuracy risk)**

In `BacktestRunner.run()`, the `MockProvider` returns `data.tail(bars)` from an ever-growing window:

```python
mock_provider = MockProvider(window)          # window = data.iloc[:i+1]
signals = await strategy.analyze(mock_provider)
```

`MockProvider.get_ohlcv()` returns `self.data.tail(bars)`. If `bars=50` and the window at bar 100 has only 100 rows, but `tail(50)` returns the last 50, this is correct. However, indicators computed inside the strategy use `data.tail(50)` — but the `window` object itself is the full slice, and the strategy may index into it with `.iloc[-1]` to get `current_bar`.

The risk is that different code paths see different data windows, creating subtle look-ahead bias in backtest results. This is not a runtime latency risk but a capital risk: backtest results that overstate live performance lead to over-allocated positions.

---

### RISK-7: Scheduler Execution at 15-Minute Boundary

**Severity: MEDIUM (systemic risk)**

The APScheduler heartbeat fires at M15 candle boundaries. At the boundary:

1. `intelligence.analyze_market()` fires → Vertex AI call (200ms–2s)
2. Result determines trade direction
3. `execute_trade()` fires

The execution decision is based on data from the start of the 15-minute candle. By the time Vertex AI responds (up to 2 seconds later), the market has moved. For liquid forex pairs, 2 seconds at the open of a new M15 bar can mean 5–15 pips of movement if news was released.

Additionally, if the scheduler misses its window due to event loop saturation (heavy strategy engine or WS broadcast), the next execution attempt is deferred until the following interval (15 minutes). A missed heartbeat means a missed trade.

---

### RISK-8: no_timeout on Binance CCXT Calls

**Severity: LOW (but tail-risk)**

`BinanceExecutor.execute()` calls CCXT's `create_market_order()` or `create_limit_order()` with no explicit timeout. If Binance's API responds slowly (rare but observed during market stress), the synchronous CCXT call holds the execution thread indefinitely.

With `enableRateLimit: True` in CCXT config, the library also inserts sleep delays to respect Binance rate limits — this is correct behavior, but adds non-deterministic latency.

---

## 3. Latency Budget Recommendation

For a system targeting 1-minute chart strategies, the acceptable trade pipeline latency is:

| Phase | Budget |
|-------|--------|
| AI/analysis | ≤ 500ms total (cached regime, not per-trade Gemini) |
| Risk validation | ≤ 10ms (in-process cache mandatory) |
| Execution optimizer | ≤ 20ms (cached M1 bars) |
| Broker submission | ≤ 200ms (market order, liquid pair) |
| **Total pipeline** | **≤ 730ms target** |

Current system: 600ms–3,500ms typical range. Significant gap vs. target, dominated by Vertex AI latency.

---

## 4. Latency Risk Matrix

| Risk ID | Component | Trade Impact | Mitigation Category |
|---------|-----------|--------------|---------------------|
| RISK-1 | Vertex AI per-trade | CRITICAL — signal staleness | Architectural (async AI) |
| RISK-2 | Firestore per-trade | HIGH — adds 20–160ms | C3 (cache) |
| RISK-3 | Sync/async deadlock | HIGH — silent failure | C1 (async refactor) |
| RISK-4 | MT poll 500ms lag | MEDIUM — blind spot | C5 (upgrade to push) |
| RISK-5 | Serial agent council | MEDIUM — 8–22ms | Architectural |
| RISK-6 | Backtest look-ahead | MEDIUM — capital risk | Bug fix |
| RISK-7 | Scheduler at boundary | MEDIUM — stale signal | Architectural |
| RISK-8 | CCXT no-timeout | LOW — tail risk | Config fix |
