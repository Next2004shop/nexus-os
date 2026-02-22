#pragma once

/**
 * NEXUS Native Engine — Indicator Interface
 * ==========================================
 * Phase CPP-2: Declarations only. Stub implementations in indicators.cpp.
 * Phase CPP-3: Full vectorized implementations replace stubs.
 *
 * All functions operate on raw C arrays (const double*) to allow
 * zero-copy use with numpy array buffer protocol via pybind11.
 *
 * Naming convention:
 *   - Functions returning a single scalar value use double return type.
 *   - Functions returning a series use IndicatorResult.
 *   - Functions with multiple outputs use a dedicated Result struct.
 *
 * Error contract:
 *   - If inputs are nullptr or n < minimum required bars, functions
 *     return IndicatorResult{valid=false} or 0.0 for scalar variants.
 *   - No exceptions are thrown. Callers check the `valid` flag.
 */

#include <cstddef>
#include <vector>

namespace nexus {
namespace indicators {

// ===========================================================
// GENERIC INDICATOR RESULT
// ===========================================================

/**
 * Holds a computed indicator series plus the most-recent value.
 *
 * For scalar indicators (e.g., current RSI), `values` contains
 * a single element and `current` mirrors it.
 *
 * For series indicators (e.g., full Bollinger band history),
 * `values` holds the complete output series.
 */
struct IndicatorResult {
    std::vector<double> values;
    double              current = 0.0;
    bool                valid   = false;

    IndicatorResult() = default;

    /// Construct from a single scalar (used by scalar indicators).
    explicit IndicatorResult(double val)
        : values{val}, current(val), valid(true) {}
};

/**
 * Bollinger Band output: three parallel series.
 * Lengths match the input `n` (NaN-padded for the warm-up period
 * in the CPP-3 full implementation; stubs return single-element vectors).
 */
struct BollingerResult {
    std::vector<double> upper;
    std::vector<double> middle;
    std::vector<double> lower;
    bool                valid = false;

    BollingerResult() = default;
};


// ===========================================================
// MOVING AVERAGES
// ===========================================================

/**
 * Simple Moving Average (SMA) of `close` over `period` bars.
 * Returns the most-recent SMA value in IndicatorResult::current.
 *
 * CPP-3 full implementation: O(n) single-pass with running sum.
 */
IndicatorResult sma(const double* close, std::size_t n, std::size_t period);

/**
 * Exponential Moving Average (EMA) with Wilder smoothing.
 * Seed: SMA of first `period` bars.
 *
 * CPP-3 full implementation: O(n) pass; alpha = 2 / (period + 1).
 */
IndicatorResult ema(const double* close, std::size_t n, std::size_t period);


// ===========================================================
// VOLATILITY
// ===========================================================

/**
 * Average True Range (ATR) series.
 * True Range = max(H-L, |H-prev_C|, |L-prev_C|)
 * ATR = SMA(TR, period)   [CPP-3 will use Wilder smoothing as option]
 *
 * Returns IndicatorResult::values as the full ATR series.
 * IndicatorResult::current is the most-recent ATR value.
 */
IndicatorResult atr(const double* high,
                    const double* low,
                    const double* close,
                    std::size_t   n,
                    std::size_t   period);

/**
 * ATR Percentile: position of current ATR in its historical distribution.
 *
 * Returns value in [0, 100]:
 *   < 20  = unusually low volatility
 *   > 80  = unusually high volatility
 *   50    = median (stub returns this until CPP-3)
 *
 * CPP-3 implementation: single-pass rolling ATR + percentile rank.
 * Replaces the O(n²) Python loop in agent_council.py:472-496.
 */
double atr_percentile(const double* high,
                      const double* low,
                      const double* close,
                      std::size_t   n,
                      std::size_t   period);


// ===========================================================
// MOMENTUM
// ===========================================================

/**
 * Relative Strength Index (RSI).
 *
 * Returns scalar RSI value in [0, 100].
 * 50.0 returned by stub (neutral).
 *
 * CPP-3 full implementation: Wilder smoothed RS.
 * Replaces mean_reversion.py:60-65 and agent_council.py:355-371.
 */
double rsi(const double* close, std::size_t n, std::size_t period);

/**
 * Rate of Change (ROC) — percentage change over `period` bars.
 * ROC = (close[n-1] - close[n-1-period]) / close[n-1-period] * 100
 *
 * Returns scalar ROC (%). Exact in both stub and CPP-3.
 */
double roc(const double* close, std::size_t n, std::size_t period);


// ===========================================================
// TREND
// ===========================================================

/**
 * Average Directional Index (ADX) — trend strength [0, 100].
 * Also computes +DI and -DI (Directional Indicators).
 *
 * Stub returns 25.0 (weak-trend boundary).
 *
 * CPP-3 full implementation: Wilder smoothed DM/TR accumulation.
 * Replaces intelligence.py:98-129 (_calculate_adx).
 * Single-pass, zero pandas dependency.
 */
double adx(const double* high,
           const double* low,
           const double* close,
           std::size_t   n,
           std::size_t   period);

/**
 * Trend R-squared: linear regression R² of close prices over n bars.
 * High R² → strong linear trend. Low → mean-reverting / choppy.
 *
 * Returns scalar in [0.0, 1.0].
 * Stub returns 0.0.
 *
 * CPP-3 full implementation: single-pass OLS using 2 accumulators.
 * Replaces intelligence.py:159-194 (_calculate_trend_strength).
 * Eliminates the 5 separate np.sum() passes in the Python version.
 */
double trend_r_squared(const double* close, std::size_t n);


// ===========================================================
// VOLATILITY REGIME
// ===========================================================

/**
 * Volatility clustering: lag-1 autocorrelation of squared log-returns.
 * High positive autocorrelation = volatility clustering present.
 *
 * Returns scalar autocorrelation in [-1.0, 1.0].
 * Stub returns 0.0.
 *
 * CPP-3 full implementation: single-pass Welford-style accumulation.
 * Replaces intelligence.py:288-328 (VolatilityClustering.analyze).
 * Eliminates np.corrcoef() 2x2 matrix computation for a 1D problem.
 */
double vol_clustering_autocorr(const double* close, std::size_t n);


// ===========================================================
// BOLLINGER BANDS
// ===========================================================

/**
 * Bollinger Bands: upper = SMA + num_std * σ, lower = SMA - num_std * σ.
 *
 * Returns BollingerResult with single-element vectors (most-recent values)
 * in stub. CPP-3 returns full n-length series.
 *
 * Replaces breakout.py:52-56 and mean_reversion.py:55-58.
 * CPP-3 uses Welford's online algorithm: single pass for mean and variance.
 */
BollingerResult bollinger_bands(const double* close,
                                std::size_t   n,
                                std::size_t   period,
                                double        num_std);


// ===========================================================
// PATTERN MATCHING
// ===========================================================

struct PatternMatchResult {
    double avg_outcome  = 0.0;   // mean forward return of similar patterns
    double outcome_std  = 0.0;   // standard deviation of outcomes
    int    matches_found = 0;    // number of similar historical patterns
    bool   valid         = false;
};

/**
 * Sliding-window pattern similarity scan.
 *
 * Compares the most-recent `pattern_len` bars against every window
 * of the same length in [lookback_start, lookback_end). For each
 * window whose similarity score > min_similarity, records the
 * `forward_bars`-bar forward return.
 *
 * Returns: mean and std of similar-pattern outcomes.
 * Stub returns PatternMatchResult{valid=false}.
 *
 * CPP-3 full implementation: vectorized sliding-window comparison.
 * Replaces model_ensemble.py:326-346 (PatternModel Python loop).
 */
PatternMatchResult pattern_match(const double* close,
                                 std::size_t   n,
                                 std::size_t   pattern_len,
                                 std::size_t   lookback_start,
                                 std::size_t   lookback_end,
                                 std::size_t   forward_bars,
                                 double        min_similarity);

} // namespace indicators
} // namespace nexus
