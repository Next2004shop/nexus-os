# NEXUS Native Engine Architecture
## CPP-2 — Hybrid Python + C++ Design Document

**Prepared by:** Systems Engineer, NEXUS Performance Program
**Date:** 2026-02-22

---

## 1. Why Hybrid Python + C++

### 1.1 The Problem with Pure Python for Numerical Hot Paths

The CPP-1 audit identified 11 performance hotspots in the Nexus codebase. The highest-ranked are pure numerical computations:

| Hotspot | Python behavior | Root cause |
|---------|----------------|------------|
| `_calculate_atr_percentile` | 36-iteration Python loop with per-iteration numpy sub-allocations | No single-pass rolling API used |
| `_calculate_adx` | 4 × `pd.Series().rolling().mean()` calls on same data | 8 numpy↔pandas object conversions |
| `PatternModel.predict` | Python for-loop, `O(n)` with list append per iteration | Not vectorized |
| `BacktestEngine.run` | `data.iloc[:i+1]` per bar — O(n²) memory copies | No incremental state |

These computations share one property: they are **pure arithmetic on arrays of floats**. There is no I/O, no AI inference, no network call. Every nanosecond spent in the Python interpreter executing bytecode, acquiring/releasing the GIL, and managing object reference counts is avoidable overhead.

C++ with SIMD-eligible inner loops eliminates this overhead. A rolling ATR that takes 5ms in Python takes < 10 microseconds in C++ — a 500x improvement on the same hardware.

### 1.2 Why Not Pure C++

Rewriting Nexus in pure C++ is not viable:

- **Vertex AI integration**: The Gemini Pro API has a Python/gRPC SDK. No C++ equivalent.
- **Firestore**: Google Cloud Firestore SDK is Python/Java/Node. The Python `google-cloud-firestore` library is the production path.
- **FastAPI routing**: Python's FastAPI + Pydantic provides rapid, maintainable API development with automatic OpenAPI generation.
- **APScheduler**: Market-aligned scheduling with cron-like syntax; no C++ equivalent with the same ergonomics.
- **pybind11 and asyncio**: Async I/O (aiohttp, websockets) requires Python's event loop. C++ coroutines exist but would require a complete rewrite of the connectivity layer.
- **Agent Council / Model Ensemble**: Business logic with complex state machines, weighted voting, and AI API calls. Python is the correct language for this.

**Conclusion:** The system's value is in its AI orchestration, risk management, and multi-venue execution logic — all correctly implemented in Python. The cost center is a small set of numerical hot paths that run many times per second.

### 1.3 The Hybrid Advantage

The hybrid model provides:

1. **Targeted acceleration**: Replace only the identified hot paths. Everything else remains unchanged.
2. **No architectural disruption**: Python calls C++ as a function call. The call sites in agent_council.py, intelligence.py, and model_ensemble.py change one import and one function call.
3. **Immediate fallback**: If C++ compilation fails or the library is absent, Python fallback stubs activate automatically. The system degrades gracefully, not catastrophically.
4. **Incremental migration**: CPP-2 builds the foundation. CPP-3, CPP-4 progressively replace stubs with real implementations. Each phase is independently testable.

---

## 2. Execution Boundary

The boundary between Python and C++ is defined precisely:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PYTHON DOMAIN                                │
│                                                                     │
│  FastAPI routes      risk_governor.py    intelligence.py            │
│  scheduler.py        agent_council.py    model_ensemble.py          │
│  execution.py        live_data.py        circuit_breaker.py         │
│  Vertex AI calls     Firestore calls     MT5/Binance calls          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              python_bridge/nexus_native.py                  │   │
│  │    (type conversion: Python dict ↔ C++ struct)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↕ pybind11                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │               C++ DOMAIN (nexus_native_ext.so)              │   │
│  │                                                             │   │
│  │  indicators.cpp   risk.cpp   engine.cpp                     │   │
│  │  ATR, ADX, RSI    position   signal scoring                 │   │
│  │  Bollinger, ROC   sizing     tick normalization              │   │
│  │  pattern match    drawdown   latency measurement            │   │
│  │                                                             │   │
│  │  NO I/O. NO network. NO AI. NO Firestore.                   │   │
│  │  Pure numerical computation on float arrays only.           │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Python owns:**
- All external service calls (Vertex AI, Firestore, MT5, Binance, Polygon)
- All state management (risk state, circuit breaker state, session state)
- All business logic decisions (quorum rules, position modifiers, kill switch)
- All orchestration (scheduler, agent council, model ensemble, command router)

**C++ owns:**
- Indicator computation (ATR, RSI, ADX, Bollinger, pattern matching)
- Risk math (position sizing formulas, drawdown arithmetic, Sharpe ratio)
- Tick normalization (mid-price, raw spread)
- Latency measurement (std::chrono wall-clock timing)

**Explicitly excluded from C++:**
- Any Firestore read or write
- Any network socket operation
- Any Python object lifetime management beyond the binding layer
- Any trade approval decision
- Any AI model inference

---

## 3. Safety Isolation Model

### 3.1 Import Safety

`nexus_native.py` wraps the entire import in a `try/except ImportError`:

```python
try:
    import nexus_native_ext as _native
    _NATIVE_AVAILABLE = True
except ImportError:
    _NATIVE_AVAILABLE = False
    # Python stubs activated automatically
```

This ensures that if the compiled library is absent (e.g., first deploy before build step), the Python system starts normally and logs a warning.

### 3.2 Call-Site Safety

Every public function in `nexus_native.py` wraps the C++ call:

```python
def compute_signal(data):
    try:
        if _NATIVE_AVAILABLE:
            return _native_compute_signal(data)
        return _stub_compute_signal(data)
    except Exception as exc:
        logger.error("compute_signal error: %s", exc)
        return _stub_compute_signal(data)  # safe fallback
```

A Python-visible exception from C++ (e.g., pybind11 type error) is caught per-call. The calling code receives a valid (stub) result and continues.

Note: A C++ segfault or `std::terminate` would kill the process. This is standard behavior — the same would happen in any Python C extension. Mitigation: well-defined precondition checks at C++ function entry (nullptr guards, range checks).

### 3.3 CPP-2 Safe Defaults

While the engine is in placeholder state:

| Function | Return value | Reasoning |
|----------|-------------|-----------|
| `compute_signal()` | `direction=0` (NEUTRAL) | Do not generate spurious signals |
| `compute_risk()` | `allowed=False` | Never approve trades from an unactivated risk engine |
| `process_tick()` | passthrough mid-price | Tick processing is benign; passthrough is correct |

These defaults ensure that even if a caller accidentally uses C++ results for trade decisions before CPP-3 activates the engine, no erroneous trades are generated.

### 3.4 Authority Model

The C++ risk functions are explicitly advisory:

```
Python risk_governor.py                        ← AUTHORITATIVE
    ↓ calls
C++ risk::evaluate_trade()                     ← ADVISORY (fast pre-check)
    ↓ returns RiskResult{allowed=False} in CPP-2
Python risk_governor.validate_trade()          ← AUTHORITATIVE decision
    ↓
execution.execute_trade()                      ← trade placed or rejected
```

This layering ensures that even when CPP-3 activates `evaluate_trade()`, the Python layer retains final authority. The C++ pre-check can block trades early (saving Firestore round trips), but cannot approve trades that the Python layer would reject.

---

## 4. pybind11 Integration

### 4.1 Binding Architecture

```
bindings.cpp  defines  PYBIND11_MODULE(nexus_native_ext, m)
    ↓
Compiled to: nexus_native_ext.cpython-3X-linux-gnu.so
                or nexus_native_ext.cp3X-win_amd64.pyd
    ↓
nexus_native.py imports: import nexus_native_ext as _native
    ↓
Public API wraps calls to _native.compute_signal(), etc.
```

### 4.2 Type Conversion Layer

Python callers pass dicts. The bridge converts:

```python
# Python dict → C++ struct
md = _native.MarketData()
md.symbol = str(data.get("symbol", ""))
md.close  = float(data.get("close", 0.0))
# ...
result = _native.compute_signal(md)

# C++ struct → Python dict
d = result.to_dict()   # defined in bindings.cpp
d["native"] = True
return d
```

This conversion adds ~1–5 microseconds of Python overhead per call — negligible compared to the computation time saved.

### 4.3 CPP-3 Array Protocol

In CPP-3, indicator functions that accept numpy arrays will use pybind11's buffer protocol for zero-copy array access:

```cpp
// CPP-3 binding for atr_percentile
m.def("atr_percentile", [](py::buffer high_buf,
                            py::buffer low_buf,
                            py::buffer close_buf,
                            std::size_t period) {
    py::buffer_info hi = high_buf.request();
    py::buffer_info lo = low_buf.request();
    py::buffer_info cl = close_buf.request();

    return nexus::indicators::atr_percentile(
        static_cast<const double*>(hi.ptr), hi.size,
        static_cast<const double*>(lo.ptr),
        static_cast<const double*>(cl.ptr),
        period
    );
});
```

Python call site:
```python
# No copy — numpy array passed directly to C++
pct = nexus_native_ext.atr_percentile(
    df['high'].values, df['low'].values, df['close'].values, period=14
)
```

---

## 5. Build System

CMake 3.18+ is used for:

1. **Python discovery** (`find_package(Python)`) — locates the correct interpreter and headers for the active virtualenv or system Python.
2. **pybind11** — `find_package(pybind11)` checks for system install; falls back to `FetchContent` downloading v2.13.6 from GitHub.
3. **`pybind11_add_module()`** — handles all platform-specific shared library configuration (.so vs .pyd, soabi suffix, visibility flags).
4. **Output routing** — compiled extension is placed in `python_bridge/` alongside `nexus_native.py` so the bridge can `import nexus_native_ext` by inserting one sys.path entry.

**Build is entirely offline-optional**: if pybind11 is pre-installed (e.g., via `pip install pybind11`), no network access is required during build.

---

## 6. Future Migration Plan

### Phase CPP-3: Indicator Implementations

**Target files to update (no signature changes):**
- `cpp/indicators.cpp` — replace all stub bodies with vectorized implementations
- `cpp/risk.cpp` — replace `evaluate_trade()` stub; implement `sharpe_ratio()`, `max_drawdown()`

**Python integration points to update:**
- `agent_council.py:459-496` → import `nexus_native_ext.atr_percentile()`
- `intelligence.py:98-129` → import `nexus_native_ext.adx()`
- `intelligence.py:159-194` → import `nexus_native_ext.trend_r_squared()`
- `model_ensemble.py:326-346` → import `nexus_native_ext.pattern_match()`
- `strategies/breakout.py` → import `nexus_native_ext.bollinger_bands()`
- `strategies/mean_reversion.py` → import `nexus_native_ext.bollinger_bands()`, `rsi()`

No other Python files change.

### Phase CPP-4: Backtest Kernel

Add `cpp/backtest.cpp` with the equity simulation kernel. Python retains signal generation logic; C++ handles the per-bar loop.

New binding:
```python
metrics = nexus_native_ext.run_backtest(
    close_prices, signals, capital=10000.0, commission=0.001
)
```

### Phase CPP-5: Tick Ring Buffer

Add a per-symbol tick ring buffer in C++ for O(1) rolling ATR updates in the live path. MT bridge ticks are pushed into C++ via `process_tick()` on arrival; rolling indicators update incrementally.

---

## 7. Observed vs. Expected Latency After Full Migration

| Operation | Python (current) | C++ (target CPP-3) | Improvement |
|-----------|-----------------|---------------------|-------------|
| ATR percentile (50 bars) | 3–10ms | < 0.1ms | 30–100x |
| ADX (50 bars, 4 rolling chains) | 2–5ms | < 0.05ms | 40–100x |
| Bollinger Bands (50 bars) | 1–3ms | < 0.02ms | 50–150x |
| RSI (50 bars) | 1–3ms | < 0.02ms | 50–150x |
| Pattern match (40-bar scan) | 1–4ms | < 0.05ms | 20–80x |
| Agent council (5 agents, post-CPP-3) | 8–22ms | < 1ms | 8–22x |
| Backtest (10,000 bars) | 30–120s | < 1s | 30–120x |

These are order-of-magnitude estimates based on known Python/numpy vs. C++ SIMD performance ratios for equivalent operations. Actual measurements required after CPP-3 implementation.

The dominant remaining latency after CPP-3 will be Vertex AI API calls (200ms–2s) and broker round-trips (50–500ms) — both irreducible without architectural changes to the AI pipeline and co-location, respectively.
