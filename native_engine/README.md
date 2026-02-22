# NEXUS Native Engine

**Phase CPP-2 — Infrastructure Foundation**

A C++ acceleration layer for the NEXUS algorithmic trading platform.
Provides low-latency numerical computation via pybind11, callable from Python.

---

## Status

| Phase | Status | Description |
|-------|--------|-------------|
| CPP-2 | **Current** | Infrastructure: structs, engine skeleton, pybind11 bindings, Python bridge |
| CPP-3 | Pending | Indicator implementations (ATR, ADX, RSI, Bollinger, pattern matcher) |
| CPP-4 | Pending | Backtest kernel, risk math, full integration into trading pipeline |

In CPP-2, all computational functions return placeholder values.
The Python system runs **identically** whether or not this library is compiled.

---

## Directory Structure

```
native_engine/
│
├── cpp/
│   ├── engine.cpp       Core engine: NexusEngine class, free-function dispatchers
│   ├── indicators.cpp   Indicator stubs (ATR, RSI, ADX, Bollinger, patterns)
│   ├── risk.cpp         Risk stubs (position sizing, drawdown, Sharpe, max DD)
│   └── bindings.cpp     pybind11 module definition (nexus_native_ext)
│
├── include/
│   ├── engine.hpp       MarketData, TickData, SignalResult, RiskResult, NexusEngine
│   ├── indicators.hpp   Indicator interfaces + IndicatorResult, BollingerResult
│   └── risk.hpp         Risk interfaces + RiskParameters, PositionSizeResult
│
├── python_bridge/
│   └── nexus_native.py  Python wrapper: safe fallback if library not compiled
│
├── CMakeLists.txt       Build system (CMake 3.18+, auto-fetches pybind11)
└── README.md            This file
```

---

## Build Instructions

### Prerequisites

| Requirement | Minimum version | Notes |
|------------|----------------|-------|
| CMake | 3.18 | `cmake --version` |
| C++ compiler | C++17 | GCC 9+, Clang 9+, MSVC 2019+ |
| Python | 3.8+ | With development headers |
| pybind11 | 2.10+ | Auto-fetched from GitHub if not installed |
| Git | any | Required for FetchContent |

On Ubuntu/Debian:
```bash
sudo apt-get install cmake g++ python3-dev git
# Optional: pre-install pybind11 to avoid fetch step
pip install pybind11
```

On macOS:
```bash
brew install cmake
xcode-select --install
pip install pybind11
```

On Windows:
Install Visual Studio 2019+ with "Desktop development with C++" workload.

---

### Build (Linux / macOS)

```bash
cd nexus-os/native_engine

# Configure
cmake -B build -DCMAKE_BUILD_TYPE=Release

# Compile (use -j to parallelise)
cmake --build build --config Release -j4

# Verify output
ls python_bridge/
# → nexus_native_ext.cpython-3X-x86_64-linux-gnu.so  (or similar)
```

### Build (Windows)

```cmd
cd nexus-os\native_engine

cmake -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release

# Output: python_bridge\nexus_native_ext.cp3X-win_amd64.pyd
```

### Debug build (with AddressSanitizer, Linux only)

```bash
cmake -B build_debug -DCMAKE_BUILD_TYPE=Debug
cmake --build build_debug -j4
```

---

## Usage from Python

```python
from native_engine.python_bridge.nexus_native import (
    compute_signal,
    compute_risk,
    process_tick,
    is_native_available,
    get_engine_status,
)

# Check if C++ engine is loaded
print(is_native_available())   # True if compiled, False if fallback
print(get_engine_status())     # version, phase, status

# Compute signal from a single bar
result = compute_signal({
    "symbol":       "EURUSD",
    "open":         1.1050,
    "high":         1.1080,
    "low":          1.1030,
    "close":        1.1065,
    "volume":       5000.0,
    "timestamp_ms": 1700000000000,
})
# CPP-2 → {"direction": 0, "direction_str": "NEUTRAL", "confidence": 0.0, ...}

# Compute risk parameters (advisory only in CPP-2)
risk = compute_risk(
    symbol          = "EURUSD",
    side            = "BUY",
    entry_price     = 1.1065,
    account_balance = 10000.0,
    risk_pct        = 0.01,
)
# CPP-2 → {"allowed": False, "reason": "CPP-2: risk engine not activated..."}

# Process a live tick
tick_result = process_tick({
    "symbol":       "EURUSD",
    "bid":          1.10648,
    "ask":          1.10652,
    "last":         1.10650,
    "volume":       100.0,
    "timestamp_ms": 1700000001234,
})
# → {"processed_price": 1.10650, "spread_pips": 0.00004, ...}
```

If the library is not compiled, the same code runs with Python fallbacks —
no code changes needed in callers.

---

## Safety Model

1. **Non-breaking:** The compiled library is never imported by existing
   Nexus Python code. Python imports it only through `nexus_native.py`.

2. **Graceful fallback:** If `nexus_native_ext.so` is absent, missing, or
   raises an `ImportError`, `nexus_native.py` catches it and activates stubs.

3. **Per-call exception isolation:** Every public function in `nexus_native.py`
   wraps the C++ call in a `try/except`. A segfault in C++ would terminate
   the process (unavoidable), but any Python-visible exception is caught.

4. **No business-logic ownership:** The C++ layer computes numbers.
   It never reads from Firestore, never calls MT5, never calls Binance.
   The Python `risk_governor.py` retains all authority over trade approval.

5. **CPP-2 safe defaults:**
   - `compute_signal()` returns NEUTRAL (direction=0).
   - `compute_risk()` returns `allowed=False`.
   - `process_tick()` returns passthrough mid-price.

---

## Verification

After building, run the smoke test:

```bash
cd nexus-os

python -c "
from native_engine.python_bridge.nexus_native import (
    is_native_available, get_engine_status,
    compute_signal, compute_risk, process_tick
)
print('Native available:', is_native_available())
print('Status:', get_engine_status())

sig = compute_signal({'symbol': 'TEST', 'open': 1.0, 'high': 1.1,
                      'low': 0.9, 'close': 1.05, 'volume': 100, 'timestamp_ms': 0})
print('Signal:', sig)

risk = compute_risk('TEST', 'BUY', 1.05, 10000.0)
print('Risk:', risk)

tick = process_tick({'symbol': 'TEST', 'bid': 1.049, 'ask': 1.051,
                     'last': 1.050, 'volume': 10, 'timestamp_ms': 0})
print('Tick:', tick)
"
```

Expected output with compiled engine:
```
Native available: True
Status: {'native_available': True, 'version': '0.1.0-alpha', 'phase': 'CPP-2', 'status': 'operational'}
Signal: {'direction': 0, 'direction_str': 'NEUTRAL', ..., 'native': True}
Risk:   {'allowed': False, ..., 'native': True}
Tick:   {'processed_price': 1.05, 'spread_pips': 0.002, ..., 'native': True}
```

Expected output without compiled engine (fallback):
```
Native available: False
Signal: {'direction': 0, ..., 'native': False}
...
```

---

## Phase CPP-3 Preview

When CPP-3 is activated, the stub implementations in `indicators.cpp` and
`risk.cpp` will be replaced with fully vectorized C++ functions. The Python
bridge and bindings do not change — only internal implementations update.

Functions targeted for CPP-3:
- `indicators::atr_percentile()` — replaces O(n²) Python loop in agent_council.py
- `indicators::adx()`            — replaces 4x pandas rolling chains in intelligence.py
- `indicators::rsi()`            — unifies two divergent Python RSI implementations
- `indicators::bollinger_bands()`— replaces two-pass pandas rolling in strategies/
- `indicators::pattern_match()`  — replaces Python loop in model_ensemble.py
- `risk::evaluate_trade()`       — fast pre-check before Firestore validation
- `risk::sharpe_ratio()`         — O(n) replacement for backtest_engine.py metrics
- `risk::max_drawdown()`         — O(n) replacement for expanding().max() chain
