# NEXUS C++ Migration Candidates
## CPP-1 Audit — Exact Modules for Native Acceleration

**Prepared by:** System Performance Architect
**Audit Date:** 2026-02-22

---

## Classification Framework

**CATEGORY_A_CPP_REQUIRED:**
Ultra-hot paths where Python GIL + interpreter overhead is a measurable contributor to latency. These are pure numerical computations with no I/O, no AI calls, no framework dependencies. C++ acceleration via pybind11 provides 10x–100x speedups for these cases.

**CATEGORY_B_PYTHON_CORE:**
Must remain Python. Contains AI API calls, async I/O, business logic orchestration, or external service integrations. C++ would require rewriting the entire integration stack with no performance benefit.

**CATEGORY_C_OPTIMIZE_ONLY:**
Stays in Python but can be made significantly faster through structural fixes: async refactoring, caching, vectorization, or algorithmic corrections. No C++ required.

---

## CATEGORY_A_CPP_REQUIRED

### A1 — Technical Indicator Library (Highest Priority)

**Consolidation target:** Replace all independent indicator implementations across three modules with a single C++ shared library exposed via pybind11.

**Current locations and implementations to replace:**

#### A1.1 — ATR (Average True Range)
Three independent Python implementations, none shared:

| Location | Lines | Implementation |
|----------|-------|----------------|
| `agent_council.py:459-470` | VolatilityRiskAgent._calculate_atr | np.maximum chains, returns float |
| `intelligence.py:131-157` | RegimeDetector._calculate_atr | pd.Series rolling + z-score |
| `intelligence.py:362-371` | AnomalyDetector.detect | inline np.mean(tr[-14:]) |

All compute True Range as `max(H-L, abs(H-prev_C), abs(L-prev_C))` then take a rolling mean. In C++, this is a Wilder-smoothed or simple rolling ATR with SIMD-eligible inner loops. Single call, shared result.

**C++ function signature (proposed):**
```cpp
// Returns (current_atr, atr_series, atr_zscore, percentile)
std::tuple<double, std::vector<double>, double, double>
compute_atr_full(
    const double* high, const double* low, const double* close,
    int n, int period
);
```

#### A1.2 — ATR Percentile (Rolling Historical)
**Location:** `agent_council.py:472-496` — VolatilityRiskAgent._calculate_atr_percentile

Current: explicit Python loop, 36 iterations for 50-bar data, each with array slice + 3-element-wise numpy ops.

```python
for i in range(self.atr_period, len(df)):   # Python loop — GIL held each iteration
    h = high[i-self.atr_period:i]           # new numpy array allocated
    ...
    tr_all.append(np.mean(tr))              # Python list append
```

C++ replacement: single-pass rolling ATR using a circular buffer. No heap allocations in the hot loop. Wilder smoothing or SMA, user-selectable.

**C++ function signature (proposed):**
```cpp
double compute_atr_percentile(
    const double* high, const double* low, const double* close,
    int n, int period
);
// Returns: percentile (0-100) of current ATR vs historical
```

#### A1.3 — ADX and Directional Indicators
**Location:** `intelligence.py:98-129` — RegimeDetector._calculate_adx

Current: 4 separate `pd.Series().rolling(window=...).mean()` calls, 8 numpy↔pandas conversions.

**C++ replacement:** Wilder smoothed DM/TR accumulator, single-pass computation. All intermediate series in stack-allocated arrays.

**C++ function signature (proposed):**
```cpp
std::tuple<double, double, double>
compute_adx(
    const double* high, const double* low, const double* close,
    int n, int period
);
// Returns: (adx, plus_di, minus_di)
```

#### A1.4 — RSI (Relative Strength Index)
**Locations:**
- `agent_council.py:355-371` — MomentumAgent._calculate_rsi
- `strategies/mean_reversion.py:60-65` — inline pandas RSI

Current (agent_council): `np.diff` + `np.where` + `np.mean` — simple Cutler RSI, not Wilder smoothed.
Current (mean_reversion): `rolling.mean()` on gains/losses — not true Wilder RSI.

Both compute different variants and give different results for the same data. C++ unification provides consistent behavior and eliminates the discrepancy.

**C++ function signature (proposed):**
```cpp
double compute_rsi(const double* close, int n, int period, bool wilder_smoothing = true);
```

#### A1.5 — Rate of Change (ROC)
**Location:** `agent_council.py:349-353` — MomentumAgent._calculate_roc

Current: single scalar Python computation:
```python
return (close[-1] - close[-self.roc_period - 1]) / (close[-self.roc_period - 1] + 1e-10)
```

This is a single float division — C++ benefit is minimal on its own, but included in the indicator library for consistency when the library is a dependency anyway.

#### A1.6 — Bollinger Bands
**Locations:**
- `strategies/breakout.py:52-56` — pandas rolling SMA + std
- `strategies/mean_reversion.py:55-58` — same

Current: `df['close'].rolling(period).mean()` + `df['close'].rolling(period).std()` — two separate rolling passes over the same series.

**C++ replacement:** Single-pass online algorithm for mean and variance (Welford's algorithm), zero re-computation on bar advance.

**C++ function signature (proposed):**
```cpp
std::tuple<std::vector<double>, std::vector<double>, std::vector<double>>
compute_bollinger_bands(
    const double* close, int n, int period, double num_std
);
// Returns: (upper, middle, lower) band series
```

#### A1.7 — Linear Regression R-squared (Trend Strength)
**Location:** `intelligence.py:159-194` — RegimeDetector._calculate_trend_strength

Current: 5 separate `np.sum()` calls on the same array.

```python
sum_x = np.sum(x)          # pass 1
sum_y = np.sum(close)      # pass 2
sum_xy = np.sum(x * close) # pass 3 (+ temp array allocation)
sum_x2 = np.sum(x ** 2)    # pass 4 (+ temp array allocation)
sum_y2 = np.sum(close ** 2) # pass 5 — never used
```

C++ computes all sums in a single SIMD-eligible loop. `sum_y2` is removed (dead code).

**C++ function signature (proposed):**
```cpp
double compute_trend_r_squared(const double* close, int n);
// Returns: R-squared [0, 1]
```

#### A1.8 — Volatility Clustering (Squared Returns Autocorrelation)
**Location:** `intelligence.py:288-328` — VolatilityClustering.analyze

Current:
```python
returns = np.diff(np.log(close))           # log returns
squared_returns = returns ** 2             # elementwise square
vol_series = pd.Series(squared_returns).rolling(window=5).mean().values
autocorr = np.corrcoef(squared_returns[:-1], squared_returns[1:])[0, 1]
```

`np.corrcoef` computes a 2x2 correlation matrix for 1D lag-1 autocorrelation — 4x more work than needed. A direct lag-1 autocorrelation formula in C++ uses a single pass.

**C++ function signature (proposed):**
```cpp
std::tuple<double, double>
compute_vol_clustering(const double* close, int n, int lookback);
// Returns: (volatility_ratio, lag1_autocorrelation)
```

---

### A2 — Pattern Matcher (Model Ensemble)

**Location:** `app/services/model_ensemble.py:326-346` — PatternModel.predict

Current: Python for-loop over historical windows, scalar similarity comparison.

```python
for i in range(len(historical) - 10):
    window = historical[i:i+10]
    window_change = (window[-1] - window[0]) / (window[0] + 1e-10)
    similarity = 1 - abs(recent_change - window_change)
    if similarity > self.min_similarity:
        ...
```

**C++ replacement:** Vectorized sliding window comparison. The `window_change` for every window position can be computed as `(close[i+9] - close[i]) / close[i]` — this is a vectorized difference of strided elements, computable with SIMD in a single pass.

The similarity threshold filter and outcome collection can also be vectorized using masked operations.

**C++ function signature (proposed):**
```cpp
std::pair<double, double>
pattern_match_predict(
    const double* close, int n,
    int pattern_len,     // = 10
    int lookback_start,  // start of historical range
    int lookback_end,    // end of historical range
    int forward_bars,    // = 15
    double min_similarity // = 0.7
);
// Returns: (avg_outcome, outcome_std)
```

---

### A3 — Backtest Bar-Loop Kernel

**Location:** `simulation/backtest_engine.py:83-129` — BacktestRunner.run

Current: full Python async loop, creates MockProvider (DataFrame slice) per bar.

The inner simulation kernel does not require Python once data is loaded. The bar-loop logic (process_signals, update_equity, close_position) is pure arithmetic on float state: entry_price, size, equity, pnl.

**C++ replacement:** A vectorized backtest kernel that takes full OHLCV arrays and a precomputed signal array (computed separately by the strategy), then computes the full equity curve and trade list in a single C++ loop.

```cpp
struct BacktestMetrics {
    double total_pnl;
    double max_drawdown;
    double sharpe_ratio;
    double win_rate;
    int total_trades;
};

BacktestMetrics run_backtest_kernel(
    const double* close,       // close prices
    const int*    signals,     // precomputed signal array (+1 BUY, -1 SELL, 0 WAIT)
    int n,
    double initial_capital,
    double commission,
    double position_size_pct   // e.g. 0.10 for 10%
);
```

Python strategy analysis generates the `signals` array; C++ handles the equity simulation. This separates the compute-intensive event loop from the Python strategy logic.

---

## CATEGORY_B_PYTHON_CORE

These must remain Python. No C++ migration.

| Module | File | Reason |
|--------|------|--------|
| `intelligence.analyze_market` | services/intelligence.py | Vertex AI Gemini API integration |
| `GeminiModel.predict` | services/model_ensemble.py | Vertex AI API call |
| `detect_regime_ai` | services/intelligence.py | Vertex AI + JSON parsing |
| `AgentCouncil.deliberate` (orchestration) | services/agent_council.py | Python business logic, quorum rules |
| `ModelEnsemble.predict` (orchestration) | services/model_ensemble.py | Ensemble aggregation logic |
| `FastAPI main.py` | app/main.py | Web framework routing, middleware |
| `scheduler.py` | app/services/scheduler.py | APScheduler async tasks |
| `risk_governor` | app/services/risk_governor.py | Firestore state management |
| `auth/*` | auth/ | Firebase auth, JWT handling |
| `telegram_bot.py` | app/services/telegram_bot.py | Telegram Bot API |
| `master_ai.py` | app/services/master_ai.py | AI orchestration layer |
| `vault.py` | app/services/vault.py | Google Secret Manager |
| `stealth_mode.py` | app/services/stealth_mode.py | System-level control |
| `command/router.py` | command/router.py | Command orchestration |
| `command/validator.py` | command/validator.py | Command validation logic |
| `ws_manager.py` | app/services/ws_manager.py | WebSocket session management |
| `live_data.py` (connectors) | app/services/live_data.py | Async WebSocket/REST connectors |
| `mt_bridge.py` | app/services/mt_bridge.py | aiohttp bridge client |
| `execution.py` (execution orchestration) | app/services/execution.py | MT5/Binance routing logic |
| `circuit_breaker.py` | app/services/circuit_breaker.py | State machine, threading |
| `telemetry_engine.py` | telemetry/telemetry_engine.py | Telemetry collection |
| `runtime_guard.py` | system/runtime_guard.py | Process monitoring |

**Rationale for blocking C++ migration in these modules:**
- AI API calls are network I/O — no CPU benefit from C++
- Async I/O (aiohttp, websockets) requires Python asyncio
- Firebase/Firestore/GCP SDK only available in Python
- Business logic (quorum rules, risk parameters) must be auditable in Python
- FastAPI routing, Pydantic models, middleware — Python-native framework

---

## CATEGORY_C_OPTIMIZE_ONLY

These stay in Python but require structural fixes.

### C1 — ExecutionOptimizer.optimize_entry
**File:** `execution/execution_optimizer.py:60-117`

**Problem:** Async function called from synchronous `execute_trade` via `asyncio.run_coroutine_threadsafe(...).result()`. This is a potential deadlock vector when called from within the asyncio event loop thread.

**Fix:** Convert `ExecutionEngine.execute_trade` to async, or pre-fetch micro-structure data before entering `execute_trade` and pass it as a parameter. No C++ required — the EMA calculation on 5 M1 bars is negligible.

### C2 — Risk Governor State Access
**File:** `app/services/risk_governor.py:153-160`

**Problem:** `_get_state()` may hit Firestore on every call. `validate_trade` calls `_get_state()` once and `_save_state()` once — that is two potential Firestore round trips per trade attempt.

**Fix:** Add a 30-second in-process TTL cache. State is already held in `_state_manager._state` but the `load_state()` path checks Firestore on first access. The fix is a time-based invalidation, not a C++ migration.

### C3 — RateLimiter
**File:** `app/main.py:150-181`

**Fix:** Replace `list` with `collections.deque`. Use `popleft()` to remove expired entries amortized O(1). No C++ required.

### C4 — Status Broadcaster
**File:** `app/main.py:349-358`

**Fix:** Track a hash or version counter of each subsystem's state. Only reserialize and broadcast when state has changed. Reduces 99% of serialization work between state changes.

### C5 — MetaTrader Connector Polling Upgrade
**File:** `app/services/live_data.py:428-450`

**Fix:** Upgrade MT bridge REST endpoint to WebSocket or Server-Sent Events. Eliminate polling loop entirely. The bridge (on the Windows VM) can push quotes on price change rather than the Python side pulling every 500ms.

### C6 — DataNormalizer.bars_to_dataframe
**File:** `app/services/market_data.py:320-329`

```python
data = [bar.to_dict() for bar in bars]    # list of dicts
df = pd.DataFrame(data)                   # dict → DataFrame
```

**Fix:** Construct DataFrame directly from typed arrays rather than via dict list. Use `pd.DataFrame({'open': open_array, 'high': high_array, ...})` with pre-allocated numpy arrays. Eliminates per-bar dict construction.

---

## Implementation Architecture: C++ Indicator Library

The recommended approach is a single pybind11 extension module:

```
nexus-core/
└── cpp_indicators/
    ├── src/
    │   ├── atr.cpp          (ATR, ATR percentile, ATR z-score)
    │   ├── adx.cpp          (ADX, +DI, -DI, Wilder smoothing)
    │   ├── rsi.cpp          (RSI, ROC, momentum)
    │   ├── bollinger.cpp    (Bollinger Bands, SMA, stddev)
    │   ├── regression.cpp   (Linear regression R-squared, trend strength)
    │   ├── volatility.cpp   (Volatility clustering, squared returns autocorr)
    │   ├── pattern.cpp      (Sliding window pattern matcher)
    │   └── backtest.cpp     (Backtest kernel: equity loop, metrics)
    ├── include/
    │   └── nexus_indicators.h
    ├── bindings/
    │   └── bindings.cpp     (pybind11 module definition)
    └── CMakeLists.txt
```

**Python interface:**
```python
import nexus_indicators as ni

# Replace VolatilityRiskAgent._calculate_atr_percentile
percentile = ni.atr_percentile(high, low, close, period=14)

# Replace RegimeDetector._calculate_adx
adx, plus_di, minus_di = ni.adx(high, low, close, period=14)

# Replace all RSI calculations
rsi = ni.rsi(close, period=14, wilder=True)

# Replace Bollinger Bands
upper, mid, lower = ni.bollinger_bands(close, period=20, num_std=2.0)

# Replace PatternModel pattern scan
avg_outcome, outcome_std = ni.pattern_match(close, pattern_len=10, lookback=40, forward=15)

# Replace BacktestRunner inner loop
metrics = ni.run_backtest(close, signals, capital=10000.0, commission=0.001)
```

All functions accept numpy arrays as input (via pybind11 buffer protocol) and return numpy arrays or scalars. Zero-copy where possible.

**Build dependency:** The library compiles against NumPy headers only. No pandas dependency in C++ layer.
