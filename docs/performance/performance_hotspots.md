# NEXUS Performance Hotspots
## CPP-1 Audit — Ranked Bottleneck Analysis

**Prepared by:** System Performance Architect
**Audit Date:** 2026-02-22

---

## Ranking Methodology

Each hotspot is scored on three axes:
- **Frequency:** How often this code executes per minute
- **CPU cost:** Observed algorithmic complexity and Python overhead
- **Latency impact:** Does blocking this path delay a trade decision?

Combined score drives the priority rank.

---

## RANK 1 — VolatilityRiskAgent._calculate_atr_percentile
**File:** `app/services/agent_council.py:472-496`
**Frequency:** Every trade request (up to 10/min) + every 15 minutes via scheduler
**Category:** CATEGORY_A_CPP_REQUIRED

```python
tr_all = []
for i in range(self.atr_period, len(df)):          # O(n) outer loop
    h = high[i-self.atr_period:i]                  # array slice per iteration
    l = low[i-self.atr_period:i]
    c = close[i-self.atr_period:i]
    tr1 = h - l                                    # 14-element vectorized ops
    tr2 = np.abs(h - np.roll(c, 1))
    tr3 = np.abs(l - np.roll(c, 1))
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    tr_all.append(np.mean(tr))                     # append to Python list
```

**Problem:** This is a sliding-window ATR computation implemented as an explicit Python loop. For a 50-bar lookback with atr_period=14, this is `50 - 14 = 36` iterations. Each iteration: 3 array slices (memory allocation), 3 element-wise ops, 1 np.roll, 2 np.maximum, 1 np.mean. All return to Python for each iteration due to `tr_all.append()`.

**Correct vectorized form exists** (rolling window TR + rolling mean) but is not used here. The final `np.sum(np.array(tr_all) <= current_atr) / len(tr_all) * 100` percentile calculation also converts back from Python list to numpy unnecessarily.

**Estimated overhead:** On 50-bar data, roughly 36 numpy sub-array allocations per call. In C++ with a single-pass algorithm, this reduces to O(n) with no heap allocations.

---

## RANK 2 — PatternModel.predict (Model Ensemble)
**File:** `app/services/model_ensemble.py:326-346`
**Frequency:** Every trade request (model ensemble, up to 10/min)
**Category:** CATEGORY_A_CPP_REQUIRED

```python
for i in range(len(historical) - 10):             # O(n) Python loop
    window = historical[i:i+10]                    # numpy slice per iteration
    window_change = (window[-1] - window[0]) / (window[0] + 1e-10)
    similarity = 1 - abs(recent_change - window_change)
    if similarity > self.min_similarity:
        if i + 15 < len(close):
            future_change = (close[i+15] - close[i+10]) / (close[i+10] + 1e-10)
            similar_outcomes.append(future_change)
```

**Problem:** Sequential pattern scan through historical price data. With `historical = close[-50:-10]` (40 elements) and 10-element window, this is 30 iterations. Each iteration involves numpy array slicing, scalar arithmetic, and a Python list append. The GIL is acquired/released per loop iteration.

In C++, this is a vectorized sliding-window correlation that can be computed in a single pass with SIMD instructions, reducing latency to sub-microsecond for this data size.

---

## RANK 3 — RegimeDetector._calculate_adx
**File:** `app/services/intelligence.py:98-129`
**Frequency:** Every 15-minute scheduler tick + on-demand `/analyze` calls
**Category:** CATEGORY_A_CPP_REQUIRED

```python
tr1 = high[1:] - low[1:]
tr2 = np.abs(high[1:] - close[:-1])
tr3 = np.abs(low[1:] - close[:-1])
tr = np.maximum(np.maximum(tr1, tr2), tr3)

plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

atr = pd.Series(tr).rolling(window=self.adx_period).mean().values
plus_di = 100 * pd.Series(plus_dm).rolling(window=self.adx_period).mean().values / (atr + 1e-10)
minus_di = 100 * pd.Series(minus_dm).rolling(window=self.adx_period).mean().values / (atr + 1e-10)

dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
adx = pd.Series(dx).rolling(window=self.adx_period).mean().values
```

**Problem:** Correct numpy vectorization, but the four `pd.Series().rolling().mean()` calls each construct a pandas Series object, run a rolling window calculation, and extract a numpy array. This is four separate Python→C→Python round trips through pandas internals. The data is converted between numpy and pandas 8 times.

A C++ implementation of ADX uses a single-pass Wilder smoothing algorithm with no intermediate object allocations.

---

## RANK 4 — BacktestEngine.run — DataFrame Slice Per Bar
**File:** `simulation/backtest_engine.py:95-129`
**Frequency:** On-demand (backtesting sessions), but O(n²) memory behavior
**Category:** CATEGORY_A_CPP_REQUIRED

```python
for i in range(warmup, len(data)):                 # O(n) outer loop
    window = data.iloc[:i+1]                       # DataFrame copy/view per bar ⚠
    current_bar = window.iloc[-1]
    mock_provider = MockProvider(window)           # new object per bar
    signals = await strategy.analyze(mock_provider)# full indicator recalc per bar
    self._process_signals(signals, current_bar, timestamp)
    self._update_equity(current_bar, timestamp)
```

**Problem:** `data.iloc[:i+1]` creates an increasingly large DataFrame view on every iteration. For 10,000 bars: bar 0 sees 1 row, bar 9999 sees 10,000 rows. The strategy then calls `provider.get_ohlcv()` which returns this entire growing slice. Rolling indicator calculations (Bollinger, RSI) re-process all data up to the current bar every iteration.

Total pandas rolling work = O(n²) in practice. For 10,000 bars at 50-bar lookback, this means 10,000 × rolling computations, not 10,000 × O(1) updates.

A C++ event-driven backtester maintains rolling indicator state and advances it O(1) per bar.

---

## RANK 5 — Redundant ATR Calculations (3 Independent Sites)
**Files:**
- `app/services/agent_council.py:459-470` (VolatilityRiskAgent._calculate_atr)
- `app/services/intelligence.py:131-157` (RegimeDetector._calculate_atr)
- `app/services/intelligence.py:362-371` (AnomalyDetector.detect)
**Frequency:** All 3 called per trade or per analysis cycle
**Category:** CATEGORY_A_CPP_REQUIRED

Three separate implementations compute ATR for the same underlying OHLCV data. No shared cache. Each implementation constructs a `pd.Series(tr).rolling(window=...).mean()` chain.

**Code duplication audit:**
- `VolatilityRiskAgent._calculate_atr`: uses rolling slice approach
- `RegimeDetector._calculate_atr`: uses `pd.Series(tr).rolling()` + z-score
- `AnomalyDetector.detect`: inline TR computation with `np.mean(tr[-14:])`

All three are computing fundamentally the same quantity on the same data with slightly different output shapes. Consolidating into a single cached computation and exposing from a C++ indicator library eliminates 2 of 3 computations per trade cycle.

---

## RANK 6 — Vertex AI API Calls (GeminiModel.predict + analyze_market)
**Files:** `app/services/model_ensemble.py:126-192`, `app/services/intelligence.py:425-496`
**Frequency:** Every trade request (GeminiModel) + every 15 minutes (scheduler)
**Category:** CATEGORY_B_PYTHON_CORE (cannot eliminate, must optimize path)

```python
response = self._model.generate_content(
    prompt,
    generation_config={"temperature": 0.2, "max_output_tokens": 500}
)
```

**Problem:** Round-trip HTTP call to Vertex AI. Observed latency: 200ms–2000ms depending on quota, region, and model load. This is a synchronous call inside the ModelEnsemble hot path, blocking the entire trade pipeline while waiting.

**This cannot be moved to C++** — it is an external service call. The problem is structural: Gemini predictions are synchronous gating operations in the trade pipeline. Mitigation requires pre-fetching, caching, or parallelizing with council analysis.

The 3 model predictions in `ModelEnsemble.predict()` run sequentially (Python for-loop over `self.models`). GeminiModel latency dominates.

---

## RANK 7 — RegimeDetector._calculate_trend_strength (Manual Linear Regression)
**File:** `app/services/intelligence.py:159-194`
**Frequency:** Every 15-minute scheduler tick + on-demand
**Category:** CATEGORY_A_CPP_REQUIRED

```python
n = len(close)
sum_x = np.sum(x)
sum_y = np.sum(close)
sum_xy = np.sum(x * close)
sum_x2 = np.sum(x ** 2)
sum_y2 = np.sum(close ** 2)
```

**Problem:** Manual implementation of OLS R-squared using 5 separate `np.sum()` calls. Each `np.sum()` is a full pass through the array. This is 5 array passes where 2 passes suffice (compute all sums in a single vectorized loop).

The implementation also computes `sum_y2` but never uses it. In C++, this computes in a single SIMD pass.

---

## RANK 8 — StrategyEngine._process_loop (1Hz Polling, Network-Bound)
**File:** `strategies/strategy_engine.py:71-110`
**Frequency:** 1Hz continuous
**Category:** CATEGORY_C_OPTIMIZE_ONLY

```python
while self._running:
    for name, strategy in self.strategies.items():
        signals = await strategy.analyze(self.market_provider)  # Polygon REST
        for signal in signals:
            await self._route_signal(signal)
    await asyncio.sleep(1)
```

**Problem:** Each 1Hz tick triggers `provider.get_ohlcv()` which hits Polygon REST (or 5-min cache). On cache hit, pandas rolling operations run on 50-bar data for indicator computation. The polling model is fundamentally less efficient than an event-driven architecture subscribing to a live candle stream.

Additionally, `asyncio.sleep(1)` with a single-threaded event loop means all other tasks (WS broadcasts, status polling) are competing for the same event loop during strategy analysis.

---

## RANK 9 — MetaTraderConnector._poll_quotes (2Hz Polling)
**File:** `app/services/live_data.py:428-450`
**Frequency:** 2Hz continuous (500ms interval)
**Category:** CATEGORY_C_OPTIMIZE_ONLY

```python
while self._running:
    async with self._session.get(f"{self.bridge_url}/quotes") as resp:
        quotes = await resp.json()
        for q in quotes.get("quotes", []):
            tick = LiveTick(...)
            await self._notify_callbacks(tick)
    await asyncio.sleep(0.5)
```

**Problem:** REST polling to MT bridge is not true real-time. Each 500ms cycle creates new HTTP connections (or reuses connection from session), parses JSON, constructs Python objects, and iterates callback chains. The MT5 bridge itself runs on a Windows VM — the HTTP round-trip adds network latency on top of the 500ms interval.

For forex, price movement happens on tick — 500ms polling introduces systematic lag between market move and system awareness.

---

## RANK 10 — RateLimiter.check (List Comprehension on Every Request)
**File:** `app/main.py:163-181`
**Frequency:** Every HTTP request
**Category:** CATEGORY_C_OPTIMIZE_ONLY

```python
self._requests[group][client_ip] = [
    t for t in self._requests[group][client_ip]
    if now - t < window
]
```

**Problem:** On every request, this rebuilds the entire timestamp list from scratch. If a client has made 60 requests in the current window, this is 60 comparisons and 60 allocation operations per request. A `collections.deque` with popleft() provides O(1) amortized cleanup.

Not a CPU bottleneck at current scale, but a structural inefficiency.

---

## RANK 11 — status_broadcaster (Full State Serialization Every 2 Seconds)
**File:** `app/main.py:349-358`
**Frequency:** 0.5Hz continuous
**Category:** CATEGORY_C_OPTIMIZE_ONLY

```python
async def status_broadcaster():
    while True:
        status = await system_status()        # queries 6 subsystems
        await ws_hub.broadcast_status(status) # JSON serialize + WS send
        await asyncio.sleep(2)
```

`system_status()` queries: risk_governor (Firestore), circuit_breaker, execution stats, agent council, model ensemble, stealth mode. Every 2 seconds it serializes the entire system state to JSON and broadcasts to all connected WebSocket clients.

**Problem:** Most of this data does not change between 2-second intervals. Full reserializaton of static state (agent weights, model names, config values) on every broadcast. A delta-based publisher would reduce serialization work by 70–90%.

---

## Summary Table

| Rank | Module | File | Freq | Type | Impact |
|------|--------|------|------|------|--------|
| 1 | VolatilityRiskAgent._calculate_atr_percentile | agent_council.py:472 | Per trade | O(n²) Python loop | HIGH |
| 2 | PatternModel.predict | model_ensemble.py:326 | Per trade | O(n) Python loop | HIGH |
| 3 | RegimeDetector._calculate_adx | intelligence.py:98 | Per 15min | pandas object churn | HIGH |
| 4 | BacktestEngine.run | backtest_engine.py:95 | On-demand | O(n²) DataFrame copies | MEDIUM |
| 5 | Triple ATR duplication | 3 files | Per trade | Redundant computation | HIGH |
| 6 | Vertex AI API calls | model_ensemble.py:126 | Per trade | 200ms–2s network | CRITICAL |
| 7 | _calculate_trend_strength | intelligence.py:159 | Per 15min | 5 array passes for 2 | MEDIUM |
| 8 | StrategyEngine 1Hz loop | strategy_engine.py:71 | 1Hz | Poll-based, network-bound | MEDIUM |
| 9 | MT bridge 2Hz poll | live_data.py:428 | 2Hz | REST poll, 500ms lag | MEDIUM |
| 10 | RateLimiter.check | main.py:163 | Per request | List rebuild | LOW |
| 11 | status_broadcaster | main.py:349 | 0.5Hz | Full state serialize | LOW |
