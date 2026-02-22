#pragma once

/**
 * NEXUS Native Engine — Core Data Structures and Engine Interface
 * ==============================================================
 * Phase CPP-2: Infrastructure foundation.
 *
 * Defines:
 *   - MarketData   : normalized OHLCV bar
 *   - TickData     : real-time bid/ask tick
 *   - SignalResult : output of signal computation
 *   - RiskResult   : output of risk computation
 *   - TickResult   : output of tick processing
 *   - NexusEngine  : primary engine class
 *
 * All trading logic is placeholder in CPP-2.
 * Indicator implementations arrive in CPP-3.
 */

#include <cstdint>
#include <string>

namespace nexus {

// ===========================================================
// MARKET DATA STRUCTURES
// ===========================================================

/**
 * Normalized OHLCV bar. Mirrors the Python MarketData contract
 * used throughout nexus-core strategies and intelligence modules.
 */
struct MarketData {
    std::string symbol;
    double      open         = 0.0;
    double      high         = 0.0;
    double      low          = 0.0;
    double      close        = 0.0;
    double      volume       = 0.0;
    int64_t     timestamp_ms = 0;   // Unix epoch, milliseconds

    MarketData() = default;

    MarketData(const std::string& sym,
               double o, double h, double l, double c,
               double v, int64_t ts)
        : symbol(sym)
        , open(o), high(h), low(l), close(c)
        , volume(v), timestamp_ms(ts)
    {}
};

/**
 * Real-time bid/ask tick from a live market feed.
 * Source: Binance WebSocket, MT5 bridge, or Polygon.io.
 */
struct TickData {
    std::string symbol;
    double      bid          = 0.0;
    double      ask          = 0.0;
    double      last         = 0.0;
    double      volume       = 0.0;
    int64_t     timestamp_ms = 0;

    /// Raw spread (ask - bid). Not pip-normalized.
    double spread() const noexcept { return ask - bid; }

    /// Mid-price (arithmetic mean of bid and ask).
    double mid()    const noexcept { return (bid + ask) * 0.5; }
};


// ===========================================================
// RESULT STRUCTURES
// ===========================================================

/**
 * Output of compute_signal().
 *
 * direction:
 *   +1 = BUY signal
 *    0 = NEUTRAL / no signal
 *   -1 = SELL signal
 *
 * confidence: [0.0, 1.0] — model certainty
 * score:      [0, 100]   — composite quality score
 * valid:      false only on internal error (caller should treat
 *             as NEUTRAL when false)
 */
struct SignalResult {
    int         direction  = 0;
    double      confidence = 0.0;
    int         score      = 0;
    std::string reason;
    bool        valid      = false;

    SignalResult() = default;

    /// Convenience: human-readable direction string.
    const char* direction_str() const noexcept {
        if (direction ==  1) return "BUY";
        if (direction == -1) return "SELL";
        return "NEUTRAL";
    }
};

/**
 * Output of compute_risk().
 *
 * allowed:       false = do not place trade
 * position_size: computed lot size
 * stop_loss:     suggested stop-loss price level
 * take_profit:   suggested take-profit price level
 * risk_reward:   TP distance / SL distance ratio
 */
struct RiskResult {
    bool        allowed       = false;
    double      position_size = 0.0;
    double      stop_loss     = 0.0;
    double      take_profit   = 0.0;
    double      risk_reward   = 0.0;
    std::string reason;

    RiskResult() = default;
};

/**
 * Output of process_tick().
 *
 * processing_latency_us: wall-clock time spent inside C++ (microseconds).
 * is_stale:              true if tick data was not freshly received.
 */
struct TickResult {
    std::string symbol;
    double      processed_price       = 0.0;
    double      spread_pips           = 0.0;
    bool        is_stale              = false;
    int64_t     processing_latency_us = 0;

    TickResult() = default;
};


// ===========================================================
// ENGINE CLASS
// ===========================================================

/**
 * NexusEngine — primary computation class.
 *
 * CPP-2: All methods return placeholder values.
 * CPP-3: compute_signal and compute_risk will be wired to
 *         the indicator and risk sub-libraries.
 *
 * Thread safety: Each NexusEngine instance is independent.
 * The global singleton (accessed via free functions below) is
 * safe for single-threaded use. Multi-threaded callers should
 * maintain per-thread instances or add a mutex.
 */
class NexusEngine {
public:
    NexusEngine();
    ~NexusEngine() = default;

    // Non-copyable (owns internal state)
    NexusEngine(const NexusEngine&)            = delete;
    NexusEngine& operator=(const NexusEngine&) = delete;

    /// Analyze a MarketData bar and produce a directional signal.
    SignalResult compute_signal(const MarketData& data);

    /// Evaluate risk parameters for a proposed trade.
    RiskResult   compute_risk(const std::string& symbol,
                               const std::string& side,
                               double             entry_price,
                               double             account_balance,
                               double             risk_pct = 0.01);

    /// Process an incoming tick (normalize, validate, time).
    TickResult   process_tick(const TickData& tick);

    /// Library version string.
    const char* version() const noexcept;

    /// True once constructor completes successfully.
    bool is_ready() const noexcept;

private:
    bool        m_initialized;
    std::string m_version;
};


// ===========================================================
// MODULE-LEVEL FREE FUNCTIONS
// (delegate to a process-scoped singleton NexusEngine)
// ===========================================================

SignalResult compute_signal(const MarketData& data);

RiskResult   compute_risk(const std::string& symbol,
                           const std::string& side,
                           double             entry_price,
                           double             account_balance,
                           double             risk_pct = 0.01);

TickResult   process_tick(const TickData& tick);

} // namespace nexus
