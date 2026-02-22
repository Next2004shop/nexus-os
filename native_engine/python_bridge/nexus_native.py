"""
NEXUS Native Engine — Python Bridge
=====================================
Provides a safe, stable Python interface to the compiled C++ native engine.

Load behavior:
  1. Attempts to import nexus_native_ext (compiled .so / .pyd from CMake build).
  2. If the extension is not found (library not compiled):
     → Falls back to pure-Python stub implementations.
     → Logs a warning with build instructions.
     → The rest of Nexus continues running normally.
  3. If the extension loads but raises an unexpected exception at call time:
     → Per-call try/except returns the safe fallback value.
     → Error is logged; execution continues.

SAFETY CONTRACT:
  None of the public functions in this module raise exceptions.
  Callers receive either a native result or a safe Python fallback.

AUTHORITY MODEL:
  This module is advisory. The Python risk_governor.py (Firestore-backed)
  remains the sole authority on trade approval. C++ outputs are supplementary
  fast-path computations, not business-logic replacements.

Usage:
    from native_engine.python_bridge.nexus_native import (
        compute_signal, compute_risk, process_tick,
        is_native_available, get_engine_status,
    )

    # Compute signal (returns neutral if engine not compiled)
    result = compute_signal({
        "symbol": "EURUSD", "open": 1.10, "high": 1.11,
        "low": 1.09, "close": 1.105, "volume": 1000, "timestamp_ms": 0
    })
    # → {"direction": 0, "direction_str": "NEUTRAL", "confidence": 0.0, ...}
"""

import logging
import os
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger("nexus.native_engine")

# ===========================================================
# EXTENSION LOAD — attempt once at import time
# ===========================================================

_NATIVE_AVAILABLE: bool = False
_native: Optional[Any] = None   # holds nexus_native_ext module if loaded

try:
    # Compiled extension is emitted into this directory by CMake.
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    if _this_dir not in sys.path:
        sys.path.insert(0, _this_dir)

    import nexus_native_ext as _native  # type: ignore[import]

    _NATIVE_AVAILABLE = True
    logger.info(
        "NEXUS native engine loaded — "
        "version=%s phase=%s",
        getattr(_native, "__version__", "unknown"),
        getattr(_native, "__phase__",   "unknown"),
    )

except ImportError as _ie:
    logger.warning(
        "NEXUS native engine not available (%s). "
        "Using Python fallbacks. "
        "To build: cd native_engine && "
        "cmake -B build -DCMAKE_BUILD_TYPE=Release && "
        "cmake --build build --config Release -j4",
        _ie,
    )
    _native = None
    _NATIVE_AVAILABLE = False

except Exception as _ex:
    logger.error("NEXUS native engine load error: %s. Using Python fallbacks.", _ex)
    _native = None
    _NATIVE_AVAILABLE = False


# ===========================================================
# PUBLIC STATUS FUNCTIONS
# ===========================================================

def is_native_available() -> bool:
    """Return True if the compiled C++ extension is loaded."""
    return _NATIVE_AVAILABLE


def get_engine_status() -> Dict[str, Any]:
    """
    Return a status dict for monitoring / health checks.

    Keys:
        native_available (bool): compiled extension loaded
        version          (str):  library version, or "N/A"
        phase            (str):  development phase, e.g. "CPP-2"
        status           (str):  human-readable status message
    """
    if _NATIVE_AVAILABLE and _native is not None:
        return {
            "native_available": True,
            "version": getattr(_native, "__version__", "unknown"),
            "phase":   getattr(_native, "__phase__",   "unknown"),
            "status":  "operational",
        }
    return {
        "native_available": False,
        "version": "N/A",
        "phase":   "CPP-2",
        "status":  "fallback — run: cmake -B build && cmake --build build",
    }


# ===========================================================
# PYTHON FALLBACK STUBS
# Called when the compiled extension is unavailable.
# Must preserve the exact interface contract of the C++ implementations.
# ===========================================================

def _stub_compute_signal(data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure-Python stub: returns NEUTRAL signal."""
    return {
        "direction":     0,
        "direction_str": "NEUTRAL",
        "confidence":    0.0,
        "score":         0,
        "reason":        "native engine not compiled — Python stub",
        "valid":         True,
        "native":        False,
    }


def _stub_compute_risk(
    symbol:          str,
    side:            str,
    entry_price:     float,
    account_balance: float,
    risk_pct:        float = 0.01,
) -> Dict[str, Any]:
    """
    Pure-Python stub: always denies.
    Safe default — Python risk_governor.py handles the actual decision.
    """
    return {
        "allowed":       False,
        "position_size": 0.0,
        "stop_loss":     0.0,
        "take_profit":   0.0,
        "risk_reward":   0.0,
        "reason":        (
            "native engine not compiled — Python stub. "
            "Use app/services/risk_governor.py for trade approval."
        ),
        "native":        False,
    }


def _stub_process_tick(tick: Dict[str, Any]) -> Dict[str, Any]:
    """Pure-Python stub: passthrough mid-price computation."""
    bid  = float(tick.get("bid",  0.0))
    ask  = float(tick.get("ask",  0.0))
    last = float(tick.get("last", 0.0))
    mid  = (bid + ask) / 2.0 if (bid > 0.0 and ask > 0.0) else last
    return {
        "symbol":                tick.get("symbol", ""),
        "processed_price":       mid,
        "spread_pips":           ask - bid,
        "is_stale":              False,
        "processing_latency_us": 0,
        "native":                False,
    }


# ===========================================================
# NATIVE CALL WRAPPERS
# Convert Python dicts → C++ structs, invoke extension, convert back.
# ===========================================================

def _native_compute_signal(data: Dict[str, Any]) -> Dict[str, Any]:
    """Delegate to C++ compute_signal via pybind11 binding."""
    assert _native is not None

    md = _native.MarketData()
    md.symbol       = str(data.get("symbol",       ""))
    md.open         = float(data.get("open",        0.0))
    md.high         = float(data.get("high",        0.0))
    md.low          = float(data.get("low",         0.0))
    md.close        = float(data.get("close",       0.0))
    md.volume       = float(data.get("volume",      0.0))
    md.timestamp_ms = int(data.get("timestamp_ms",  0))

    result = _native.compute_signal(md)
    d = result.to_dict()
    d["native"] = True
    return d


def _native_compute_risk(
    symbol:          str,
    side:            str,
    entry_price:     float,
    account_balance: float,
    risk_pct:        float,
) -> Dict[str, Any]:
    """Delegate to C++ compute_risk via pybind11 binding."""
    assert _native is not None

    result = _native.compute_risk(symbol, side,
                                   entry_price, account_balance,
                                   risk_pct)
    d = result.to_dict()
    d["native"] = True
    return d


def _native_process_tick(tick: Dict[str, Any]) -> Dict[str, Any]:
    """Delegate to C++ process_tick via pybind11 binding."""
    assert _native is not None

    td = _native.TickData()
    td.symbol       = str(tick.get("symbol",       ""))
    td.bid          = float(tick.get("bid",         0.0))
    td.ask          = float(tick.get("ask",         0.0))
    td.last         = float(tick.get("last",        0.0))
    td.volume       = float(tick.get("volume",      0.0))
    td.timestamp_ms = int(tick.get("timestamp_ms",  0))

    result = _native.process_tick(td)
    d = result.to_dict()
    d["native"] = True
    return d


# ===========================================================
# PUBLIC API
# Auto-selects native or fallback; never raises.
# ===========================================================

def compute_signal(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a trading signal from a single OHLCV bar.

    Args:
        data: dict with keys —
            symbol       (str)   : trading symbol, e.g. "EURUSD"
            open         (float) : bar open price
            high         (float) : bar high price
            low          (float) : bar low price
            close        (float) : bar close price
            volume       (float) : bar volume
            timestamp_ms (int)   : Unix epoch milliseconds

    Returns:
        dict with keys —
            direction     (int)  : +1=BUY, 0=NEUTRAL, -1=SELL
            direction_str (str)  : "BUY" | "NEUTRAL" | "SELL"
            confidence    (float): 0.0 – 1.0 model certainty
            score         (int)  : 0 – 100 composite quality score
            reason        (str)  : human-readable explanation
            valid         (bool) : False only on internal error
            native        (bool) : True if C++ engine was used

    Never raises. Returns neutral signal on any error.
    """
    try:
        if _NATIVE_AVAILABLE:
            return _native_compute_signal(data)
        return _stub_compute_signal(data)
    except Exception as exc:
        logger.error("compute_signal error: %s", exc)
        return _stub_compute_signal(data)


def compute_risk(
    symbol:          str,
    side:            str,
    entry_price:     float,
    account_balance: float,
    risk_pct:        float = 0.01,
) -> Dict[str, Any]:
    """
    Compute risk parameters for a proposed trade.

    NOTE: This is a supplementary fast-path computation only.
    The Python risk_governor.py (Firestore-backed) remains the
    sole authority on final trade approval.

    Args:
        symbol          : trading symbol, e.g. "EURUSD"
        side            : "BUY" or "SELL"
        entry_price     : proposed entry price
        account_balance : current account balance in base currency
        risk_pct        : fraction of balance to risk (default 0.01 = 1%)

    Returns:
        dict with keys —
            allowed       (bool)  : False in CPP-2 (always use Python risk_governor)
            position_size (float) : computed lot size
            stop_loss     (float) : suggested stop-loss price
            take_profit   (float) : suggested take-profit price (0.0 in CPP-2)
            risk_reward   (float) : TP/SL ratio (0.0 in CPP-2)
            reason        (str)   : explanation
            native        (bool)  : True if C++ engine was used

    Never raises. Returns denied result on any error (safe default).
    """
    try:
        if _NATIVE_AVAILABLE:
            return _native_compute_risk(symbol, side,
                                         entry_price, account_balance,
                                         risk_pct)
        return _stub_compute_risk(symbol, side,
                                   entry_price, account_balance,
                                   risk_pct)
    except Exception as exc:
        logger.error("compute_risk error: %s", exc)
        return _stub_compute_risk(symbol, side,
                                   entry_price, account_balance,
                                   risk_pct)


def process_tick(tick: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an incoming market tick through the native engine.

    Args:
        tick: dict with keys —
            symbol       (str)   : trading symbol
            bid          (float) : bid price
            ask          (float) : ask price
            last         (float) : last traded price
            volume       (float) : tick volume
            timestamp_ms (int)   : Unix epoch milliseconds

    Returns:
        dict with keys —
            symbol                (str)  : echoed symbol
            processed_price       (float): mid-price (bid+ask)/2
            spread_pips           (float): ask - bid (raw, not pip-normalised)
            is_stale              (bool) : True if tick flagged as stale
            processing_latency_us (int)  : C++ wall-clock time in microseconds
            native                (bool) : True if C++ engine was used

    Never raises. Returns passthrough values on any error.
    """
    try:
        if _NATIVE_AVAILABLE:
            return _native_process_tick(tick)
        return _stub_process_tick(tick)
    except Exception as exc:
        logger.error("process_tick error: %s", exc)
        return _stub_process_tick(tick)
