#pragma once

/**
 * NEXUS Native Engine — Risk Interface
 * =====================================
 * Phase CPP-2: Declarations only. Stub implementations in risk.cpp.
 * Phase CPP-3: Full implementations replacing Python risk_governor hot paths.
 *
 * IMPORTANT: This layer does NOT replace the Python risk_governor.
 * It provides a fast numerical sub-layer for compute-intensive risk math
 * (position sizing, drawdown arithmetic, exposure calculation).
 * All business decisions (Firestore state, circuit breaker, kill switch)
 * remain in Python.
 *
 * Separation of concerns:
 *   Python risk_governor  → orchestration, state management, Firestore
 *   nexus::risk            → pure numerical computation, no I/O
 */

#include <cstddef>
#include <string>
#include "engine.hpp"   // for RiskResult

namespace nexus {
namespace risk {

// ===========================================================
// RISK PARAMETERS
// ===========================================================

/**
 * Input parameters for risk computation.
 * Mirrors the fields of Python's RiskState (risk_governor.py).
 * Populated by the Python layer before calling into C++.
 */
struct RiskParameters {
    double account_balance      = 10000.0;
    double max_risk_per_trade   = 0.01;     // fraction, e.g. 0.01 = 1%
    double max_daily_drawdown   = 0.05;     // fraction, e.g. 0.05 = 5%
    double current_drawdown     = 0.0;      // fraction, current session
    double max_position_size    = 1.0;      // maximum lot size
    int    open_positions       = 0;
    int    max_positions        = 5;
    double total_exposure_usd   = 0.0;      // sum of all open position values
    double max_exposure_usd     = 50000.0;  // hard exposure cap

    RiskParameters() = default;
};

/**
 * Position sizing result.
 * Used internally and as intermediate output for evaluate_trade().
 */
struct PositionSizeResult {
    double lot_size            = 0.0;
    double dollar_risk         = 0.0;
    double stop_distance_price = 0.0;
    bool   valid               = false;
    std::string reason;

    PositionSizeResult() = default;
};


// ===========================================================
// POSITION SIZING
// ===========================================================

/**
 * Calculate lot size based on fixed fractional risk.
 *
 * Formula (CPP-3 will add symbol-specific pip value):
 *   dollar_risk  = account_balance * max_risk_per_trade
 *   lot_size     = dollar_risk / (|entry - stop_loss| * contract_size)
 *
 * Stub: uses simplified formula without pip/contract normalization.
 * CPP-3: adds per-symbol pip value lookup table.
 *
 * Returns PositionSizeResult{valid=false} if:
 *   - entry_price == stop_loss_price (zero stop distance)
 *   - either price is <= 0
 *   - computed lot_size < 0.01 (minimum lot)
 */
PositionSizeResult calculate_position_size(const RiskParameters& params,
                                           const std::string&    symbol,
                                           double                entry_price,
                                           double                stop_loss_price);


// ===========================================================
// VALIDATION PREDICATES
// ===========================================================

/**
 * True if current_drawdown < max_daily_drawdown.
 * Direct numerical check — no I/O.
 */
bool validate_drawdown(const RiskParameters& params) noexcept;

/**
 * True if open_positions < max_positions AND
 *      total_exposure_usd < max_exposure_usd.
 */
bool validate_exposure(const RiskParameters& params) noexcept;

/**
 * True if lot_size <= max_position_size.
 */
bool validate_lot_size(double lot_size, const RiskParameters& params) noexcept;


// ===========================================================
// UNIFIED TRADE EVALUATOR
// ===========================================================

/**
 * Evaluate a proposed trade against all risk constraints.
 *
 * Runs in order:
 *   1. validate_drawdown()
 *   2. validate_exposure()
 *   3. calculate_position_size()
 *   4. validate_lot_size()
 *
 * Short-circuits on first failure (returns allowed=false with reason).
 *
 * CPP-2: always returns allowed=false with explanation.
 *        The Python risk_governor.py remains authoritative.
 * CPP-3: will be wired into the Python risk pipeline as an optional
 *        fast-path pre-check before Firestore validation.
 *
 * Returns RiskResult (defined in engine.hpp).
 */
RiskResult evaluate_trade(const RiskParameters& params,
                           const std::string&    symbol,
                           const std::string&    side,
                           double                entry_price,
                           double                stop_loss_price);


// ===========================================================
// PERFORMANCE METRICS
// ===========================================================

/**
 * Compute Sharpe ratio from a daily returns series.
 * annualized_factor: sqrt(252) for daily, sqrt(252*24) for hourly.
 *
 * Returns 0.0 if n < 2 or std_dev == 0.
 *
 * CPP-3: replaces backtest_engine.py:261-262 Sharpe calculation.
 */
double sharpe_ratio(const double* daily_returns,
                    std::size_t   n,
                    double        annualized_factor = 15.874); // sqrt(252)

/**
 * Maximum drawdown from an equity curve.
 * Returns value in (-1.0, 0.0] — negative fraction.
 * e.g. -0.15 means peak-to-trough decline of 15%.
 *
 * CPP-3: replaces backtest_engine.py:252-255 drawdown computation.
 */
double max_drawdown(const double* equity_curve, std::size_t n);

} // namespace risk
} // namespace nexus
