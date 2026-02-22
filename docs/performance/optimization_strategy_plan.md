# NEXUS Optimization Strategy Plan
## CPP-1 Audit — Staged Migration Plan (No Implementation)

**Prepared by:** System Performance Architect
**Audit Date:** 2026-02-22

---

## Principles

1. **Observed evidence only.** Every recommendation is grounded in code read during this audit. No speculative optimizations.
2. **Staged progression.** No phase depends on a later phase. Each phase is independently deployable.
3. **No architecture changes in early phases.** The high-level design (FastAPI, agent council, ensemble, Firestore) is preserved. Optimizations replace internal implementations, not external contracts.
4. **Measure before and after each phase.** Performance assertions must be validated with latency instrumentation before advancing.
5. **Risk priority drives phase ordering.** RISK-1 (Vertex AI latency) and RISK-2 (Firestore) are the highest-impact items and addressed first in Phase 1 despite being Python-only changes.

---

## Phase 1 — Python Structural Fixes (No C++)

**Goal:** Eliminate the highest-impact latency sources using pure Python changes.

**Target:** Reduce trade pipeline P50 from ~800ms to ~200ms.

---

### P1.1 — Decouple Gemini Regime Analysis from Per-Trade Pipeline

**File:** `app/services/model_ensemble.py` + `app/services/scheduler.py`

**Problem:** `GeminiModel.predict()` adds 200ms–2,000ms to every trade. Gemini is analyzing market *regime*, which changes slowly (minutes to hours), not per-tick.

**Proposed change (no code):**
- Move `GeminiModel.predict()` out of the per-trade model ensemble.
- Run it on a scheduled basis (every 60 seconds or triggered by significant market state change).
- Cache the result in memory: `_cached_gemini_prediction: ModelPrediction` with a timestamp.
- `ModelEnsemble.predict()` reads from cache instead of calling the API.
- If cache is older than N seconds, the model is flagged NEUTRAL/ERROR until refreshed.

**Expected result:** Trade pipeline loses 200ms–2,000ms per trade. Gemini analysis becomes eventually consistent with 60-second max staleness — acceptable for all strategies running on 1-minute or longer timeframes.

---

### P1.2 — Add In-Process Cache to Risk Governor State

**File:** `app/services/risk_governor.py`

**Problem:** `validate_trade()` may issue Firestore reads on every call. `register_position()` always writes.

**Proposed change (no code):**
- Add a time-to-live (TTL) for `_state_manager._state`. Default: 30 seconds.
- On `_get_state()`: check if in-memory state is fresher than TTL. If yes, return it without Firestore read.
- On `_save_state()`: write to Firestore asynchronously via `asyncio.create_task()` rather than blocking. Accept eventual consistency for the persisted state (in-memory is authoritative, Firestore is for crash recovery).
- Invalidate cache on position registration and drawdown breach events.

**Expected result:** Firestore latency removed from trade hot path (20–160ms reduction per trade).

---

### P1.3 — Fix Sync/Async Impedance in ExecutionEngine

**File:** `app/services/execution.py:668-714`

**Problem:** `asyncio.run_coroutine_threadsafe(...).result()` inside a synchronous function called from the async event loop thread. Currently silently fails and skips optimization.

**Proposed change (no code):**
- Convert `ExecutionEngine.execute_trade()` to `async def execute_trade()`.
- Directly `await self.optimizer.optimize_entry()` instead of thread-safe workaround.
- Update all callers: `command/router.py`, `scheduler.py`, and any direct callers.

**Expected result:** Optimization step reliably runs. Removes risk of future deadlock. Enables proper async broker calls in future phases.

---

### P1.4 — Replace List-Based RateLimiter with Deque

**File:** `app/main.py:150-181`

**Problem:** `[t for t in timestamps if now - t < window]` rebuilds list on every request.

**Proposed change (no code):**
- Replace `List[datetime]` with `collections.deque`.
- On each request: `popleft()` expired entries, append current timestamp.
- O(1) amortized vs O(k) current.

**Expected result:** Negligible at current RPS, but removes a structural anti-pattern before scaling.

---

### P1.5 — Fix Redundant ATR Computations (Vectorization)

**Files:** `agent_council.py:459-496`, `intelligence.py:131-157`, `intelligence.py:362-371`

**Problem:** ATR computed 3 independent times, including one O(n²) Python loop.

**Proposed change (no code):**
- Replace `VolatilityRiskAgent._calculate_atr_percentile`'s explicit Python loop with fully vectorized numpy: compute the rolling ATR as a single `pd.Series(tr).rolling(period).mean()`, then use `scipy.stats.percentileofscore()` or a numpy percentile call.
- Consolidate `_calculate_atr` into a shared utility function in `app/utils/indicators.py`.
- `RegimeDetector`, `AnomalyDetector`, and `VolatilityRiskAgent` all call this single function.

**Expected result:** ATR computed once per analysis cycle. ATR percentile reduces from O(n) Python loop with 36 sub-allocations to 2 numpy operations.

---

### P1.6 — Parallelize Model Ensemble (Where Safe)

**File:** `app/services/model_ensemble.py:436-444`

**Problem:** 3 models run sequentially. `RuleBasedModel` and `PatternModel` are CPU-bound Python, not I/O.

**Proposed change (no code):**
- `GeminiModel.predict()` is now async (fetches cached result per P1.1) — trivially fast.
- `RuleBasedModel` and `PatternModel` can run in a `ThreadPoolExecutor` via `asyncio.to_thread()`.
- Use `asyncio.gather()` across the 3 model predictions.

**Expected result:** After P1.1 (Gemini cached), ensemble latency = max(RuleBased, Pattern) in parallel ≈ 2–4ms total vs 8–15ms serial.

---

### P1.7 — Delta-Based Status Broadcaster

**File:** `app/main.py:349-358`

**Problem:** Full system state serialized and broadcast every 2 seconds regardless of changes.

**Proposed change (no code):**
- Maintain a hash or version counter per subsystem in a `StateTracker` object.
- On each 2-second tick: compute delta — which subsystem states have changed since last broadcast.
- Serialize and broadcast only changed sections.
- Frontend receives delta patches rather than full state.

**Expected result:** ~80–90% reduction in serialization work during steady-state operation.

---

## Phase 2 — C++ Indicator Library (Core Hotspot Elimination)

**Goal:** Replace all Python numerical indicator computations with compiled C++ via pybind11.

**Target:** Reduce per-trade compute latency (council + ensemble numerical steps) from 8–30ms to sub-1ms.

**Prerequisites:** Phase 1 complete. `execute_trade` converted to async (P1.3). ATR centralized (P1.5).

---

### P2.1 — Build nexus_indicators C++ Extension

**Structure (as documented in cpp_migration_candidates.md):**

```
cpp_indicators/
├── src/
│   ├── atr.cpp          (ATR, ATR percentile — replaces RANK-1 and RANK-5)
│   ├── adx.cpp          (ADX, +DI, -DI — replaces RANK-3)
│   ├── rsi.cpp          (RSI, ROC — replaces all RSI computations)
│   ├── bollinger.cpp    (Bollinger Bands — replaces RANK-8 strategy loop)
│   ├── regression.cpp   (R-squared — replaces RANK-7)
│   ├── volatility.cpp   (Volatility clustering — replaces intelligence.py:288-328)
│   └── pattern.cpp      (Pattern matcher — replaces RANK-2)
├── bindings/bindings.cpp
└── CMakeLists.txt
```

**Implementation order (within this phase):**

1. `atr.cpp` first — highest impact, used in 3 locations
2. `pattern.cpp` — replaces PatternModel's Python loop
3. `adx.cpp` — replaces RegimeDetector._calculate_adx
4. `bollinger.cpp` + `rsi.cpp` — replace strategy indicator calculations
5. `regression.cpp` + `volatility.cpp` — intelligence module completeness

**Each module follows the pattern:**
- Accepts `const double*` input buffers (numpy array buffer protocol via pybind11)
- Returns scalars or `std::vector<double>` (wrapped as numpy array at the binding layer)
- No pandas dependency in C++ code
- Unit-tested against reference Python implementation before integration

---

### P2.2 — Replace Agent Council Indicator Calls

**Files:** `agent_council.py:355-496`

After P2.1 is built:

```python
# Before (Python):
atr = self._calculate_atr(df)
percentile = self._calculate_atr_percentile(df, atr)

# After (C++ via pybind11):
import nexus_indicators as ni
atr, atr_series, atr_zscore, percentile = ni.atr_full(
    df['high'].values, df['low'].values, df['close'].values, period=14
)
```

All 5 agent indicator functions become single C++ calls.

---

### P2.3 — Replace RegimeDetector Computations

**File:** `intelligence.py:98-194`

Replace `_calculate_adx`, `_calculate_trend_strength`, `_calculate_atr` with `ni.adx()`, `ni.trend_r_squared()`, `ni.atr_full()`.

---

### P2.4 — Replace Strategy Engine Indicator Calls

**Files:** `strategies/breakout.py:52-56`, `strategies/mean_reversion.py:55-65`

Replace pandas rolling computations with `ni.bollinger_bands()` and `ni.rsi()`. Eliminates per-tick pandas object construction in the 1Hz loop.

---

### P2.5 — Replace PatternModel with C++ Implementation

**File:** `model_ensemble.py:326-346`

Replace Python loop with `ni.pattern_match()`. Expected speedup: 20–50x for this function.

---

## Phase 3 — Backtest Engine Rewrite

**Goal:** Reduce backtest runtime from O(n²) to O(n).

**Prerequisites:** Phase 2 complete. `nexus_indicators` library stable.

---

### P3.1 — Separate Signal Generation from Equity Simulation

**File:** `simulation/backtest_engine.py`

Structural split (no code changes yet, design only):

1. **Signal generation pass:** Run strategy analysis on all bars, store signal array `signals[i] ∈ {-1, 0, +1}`. Strategy still runs in Python with pre-sliced data.
2. **Equity simulation pass:** Pass `close`, `signals`, and config to `ni.run_backtest()` (C++ kernel). Returns equity curve, trades list, metrics.

The C++ kernel iterates the signal array once — O(n). Position state is maintained in a simple struct. No pandas, no DataFrame copies.

---

### P3.2 — Eliminate MockProvider DataFrame Slice

**File:** `simulation/backtest_engine.py:106`

Replace `MockProvider(data.iloc[:i+1])` with a stateful indicator engine that accepts one bar at a time and maintains rolling state internally.

Each C++ indicator function will have an incremental update variant:

```cpp
class ATRCalculator {
    void update(double high, double low, double close);
    double current_value() const;
};
```

The strategy calls `provider.get_ohlcv()`, which now returns a fixed-size numpy view into a pre-allocated ring buffer rather than a DataFrame slice.

---

## Phase 4 — Market Data and I/O Architecture

**Goal:** Eliminate polling latency and reduce I/O-bound blocking in the live trading path.

**Prerequisites:** Phases 1–2 complete. System latency reduced to below 50ms for compute path.

---

### P4.1 — MT Bridge WebSocket Upgrade

**File:** `app/services/live_data.py:368-450`

Upgrade the MT bridge (on the Windows VM) to push tick data via WebSocket rather than waiting for HTTP polls. The Python side connects and receives events. Eliminates the 500ms polling floor.

This is a change to the MT bridge service, not the core Python codebase, but requires coordinating the live_data.py connector update.

---

### P4.2 — Async Risk Governor Persistence

**File:** `app/services/risk_governor.py`

After P1.2 (in-memory cache), make Firestore writes non-blocking:

```python
async def _save_state_async():
    await asyncio.to_thread(self._state_manager.save_state)
```

All writes to Firestore are fire-and-forget from the hot path. Reads on startup recover state. Trade path never blocks on disk I/O.

---

### P4.3 — Market Data Symbol-Level Async Locking

**File:** `app/services/market_data.py`

The 5-minute cache does not use per-symbol locking. If two async tasks request the same symbol simultaneously, two redundant Polygon REST calls may fire. Add per-symbol asyncio locks to serialize cache population without blocking cross-symbol requests.

---

## Phase 5 — Agent Council Parallelism

**Goal:** Reduce agent council deliberation from serial to parallel.

**Prerequisites:** All agents converted to async. Phase 2 complete (agents use C++ indicators, so CPU work is minimal).

---

### P5.1 — Parallelize Agent Analysis with asyncio.gather

**File:** `app/services/agent_council.py`

After Phase 2, each agent's `analyze()` is essentially a few C++ indicator calls (< 0.5ms each). Convert all agents to `async def analyze()` and run them concurrently:

```python
results = await asyncio.gather(
    *[agent.analyze(market_context) for agent in self.agents]
)
```

Each agent runs independently. Council latency becomes the maximum of 5 agents (≈ 0.5ms) instead of the sum (≈ 5ms).

---

## Measurement Instrumentation Requirements

Before beginning any optimization phase, add instrumentation:

1. **Per-phase timer:** microsecond-precision `time.perf_counter()` wrappers on each pipeline gate.
2. **Vertex AI call latency:** Log `latency_ms` already computed in `GeminiModel.predict()`. Add P50/P95/P99 tracking.
3. **Firestore call latency:** Add timing around `load_state()` and `save_state()`.
4. **End-to-end pipeline timer:** From route handler entry to `execute_trade()` return.
5. **Backtest runtime:** Total and per-bar average.

These timers feed into the `telemetry_engine.py` already present in the system.

---

## Projected Latency Improvements by Phase

| Phase | Change | P50 Pipeline Latency |
|-------|--------|----------------------|
| Baseline (current) | — | 800ms–1,200ms |
| Phase 1 | Gemini cached, Firestore cached, async fix | 50ms–150ms |
| Phase 2 | C++ indicators (compute path sub-1ms) | 30ms–100ms |
| Phase 3 | Backtest O(n²) → O(n) | N/A for live path |
| Phase 4 | Push market data, async persistence | 25ms–80ms |
| Phase 5 | Parallel agent council | 20ms–60ms |

**Dominant remaining latency after all phases:** Broker round-trip (MT5/Binance: 50–200ms). This is irreducible without co-location.

---

## Dependencies and Risk per Phase

| Phase | External Dependencies | Risk |
|-------|----------------------|------|
| Phase 1 | None | LOW — Python-only, no infra changes |
| Phase 2 | CMake, pybind11, numpy headers, C++17 compiler | MEDIUM — build system addition |
| Phase 3 | Phase 2 library stable | MEDIUM — backtest logic change |
| Phase 4 | MT bridge service update, Firestore API | HIGH — external service changes |
| Phase 5 | Phase 2 complete | LOW — Python concurrency change |

---

## What This Plan Does NOT Cover

1. **Co-location:** Moving execution to the same data center as MT5/Binance. Would reduce broker latency from 50–200ms to < 5ms. This is an infrastructure decision outside the scope of code optimization.
2. **Order book integration:** Direct market depth analysis. Requires market data feed upgrade.
3. **ML model retraining pipeline:** PatternModel's historical data is static. A feedback loop for continuous pattern model improvement is not addressed here.
4. **Multi-strategy parallelism:** Currently one strategy runs at 1Hz. Running multiple strategies on different assets simultaneously requires event loop and market data architecture changes.
