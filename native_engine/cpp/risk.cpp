/**
 * NEXUS Native Engine — Risk Implementations
 * ===========================================
 * Phase CPP-2: Stub implementations.
 * Phase CPP-3: Full numerical risk math replacing Python hot paths.
 *
 * AUTHORITY BOUNDARY:
 *   This module handles ONLY numerical computation.
 *   Business decisions (Firestore state, kill switch, circuit breaker)
 *   remain exclusively in app/services/risk_governor.py.
 *
 *   The Python risk_governor is the sole authority on whether a trade
 *   is permitted. C++ risk functions are fast pre-checks and helpers,
 *   not replacements.
 */

#include "risk.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace nexus {
namespace risk {

// ===========================================================
// POSITION SIZING
// ===========================================================

PositionSizeResult calculate_position_size(const RiskParameters& params,
                                            const std::string&    symbol,
                                            double                entry_price,
                                            double                stop_loss_price)
{
    PositionSizeResult result;

    // Input validation
    if (entry_price <= 0.0 || stop_loss_price <= 0.0) {
        result.reason = "Invalid price: entry or stop_loss is non-positive";
        return result;
    }

    const double stop_distance = std::abs(entry_price - stop_loss_price);
    if (stop_distance < 1e-10) {
        result.reason = "Stop distance is effectively zero — cannot size position";
        return result;
    }

    const double dollar_risk = params.account_balance * params.max_risk_per_trade;

    /*
     * CPP-2 simplified sizing (no per-symbol pip value normalisation).
     *
     * Assumption: 1 lot = 100,000 units (standard forex lot).
     * CPP-3: will add a symbol lookup table with correct contract sizes
     *        and pip values for forex, indices, crypto, and metals.
     *
     * Formula:
     *   lot_size = dollar_risk / (stop_distance * contract_size)
     *
     * Example (EURUSD, 10,000 USD account, 1% risk, 20 pip stop):
     *   dollar_risk  = 100
     *   stop_distance = 0.0020
     *   lot_size = 100 / (0.0020 * 100,000) = 0.50
     */
    const double contract_size = 100000.0;
    double lot_size = dollar_risk / (stop_distance * contract_size);

    // Clamp to allowed range
    lot_size = std::min(lot_size, params.max_position_size);
    lot_size = std::max(lot_size, 0.01);   // minimum tradeable lot

    result.lot_size            = lot_size;
    result.dollar_risk         = dollar_risk;
    result.stop_distance_price = stop_distance;
    result.valid               = true;
    result.reason              = "CPP-2 simplified sizing (no symbol-specific pip value)";

    (void)symbol; // used in CPP-3 pip table lookup

    return result;
}


// ===========================================================
// VALIDATION PREDICATES
// ===========================================================

bool validate_drawdown(const RiskParameters& params) noexcept {
    return params.current_drawdown < params.max_daily_drawdown;
}

bool validate_exposure(const RiskParameters& params) noexcept {
    return (params.open_positions  < params.max_positions) &&
           (params.total_exposure_usd < params.max_exposure_usd);
}

bool validate_lot_size(double lot_size, const RiskParameters& params) noexcept {
    return lot_size > 0.0 && lot_size <= params.max_position_size;
}


// ===========================================================
// UNIFIED TRADE EVALUATOR
// ===========================================================

RiskResult evaluate_trade(const RiskParameters& params,
                           const std::string&    symbol,
                           const std::string&    side,
                           double                entry_price,
                           double                stop_loss_price)
{
    RiskResult result;

    /*
     * CPP-2: Runs validation checks and sizing, but final
     * `allowed` is always false. The Python risk_governor.py
     * is the authority in CPP-2 and CPP-3.
     *
     * CPP-3 activation plan (from optimization_strategy_plan.md):
     *   Phase 1.2 adds in-process TTL cache to risk_governor.
     *   Phase 3 wires C++ evaluate_trade() as a fast pre-check
     *   before Firestore validation — parallel execution.
     */

    // Step 1: Drawdown gate
    if (!validate_drawdown(params)) {
        result.allowed = false;
        result.reason  = "Daily drawdown limit exceeded";
        return result;
    }

    // Step 2: Exposure gate
    if (!validate_exposure(params)) {
        result.allowed = false;
        result.reason  = "Position count or exposure limit exceeded";
        return result;
    }

    // Step 3: Position sizing
    const auto sizing = calculate_position_size(params, symbol,
                                                 entry_price, stop_loss_price);
    if (!sizing.valid) {
        result.allowed = false;
        result.reason  = sizing.reason;
        return result;
    }

    // Step 4: Lot size gate
    if (!validate_lot_size(sizing.lot_size, params)) {
        result.allowed = false;
        result.reason  = "Computed lot size outside allowed range";
        return result;
    }

    // Populate result fields (informational, even though allowed=false)
    result.position_size = sizing.lot_size;
    result.stop_loss     = stop_loss_price;
    result.take_profit   = 0.0;   // CPP-3: will add R-multiple TP computation
    result.risk_reward   = 0.0;   // CPP-3: TP_distance / SL_distance

    // CPP-2 SAFETY: Keep allowed=false until CPP-3 activates the engine.
    result.allowed = false;
    result.reason  = "CPP-2: risk engine not activated. "
                     "Python risk_governor.py is authoritative.";

    (void)side;   // used in CPP-3 for directional stop validation

    return result;
}


// ===========================================================
// PERFORMANCE METRICS
// ===========================================================

double sharpe_ratio(const double* daily_returns, std::size_t n,
                     double annualized_factor)
{
    if (daily_returns == nullptr || n < 2) return 0.0;

    // Mean
    double sum = 0.0;
    for (std::size_t i = 0; i < n; ++i) sum += daily_returns[i];
    const double mean = sum / static_cast<double>(n);

    // Standard deviation (sample)
    double sq_sum = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        const double d = daily_returns[i] - mean;
        sq_sum += d * d;
    }
    const double std_dev = std::sqrt(sq_sum / static_cast<double>(n - 1));

    if (std_dev < 1e-15) return 0.0;

    return (mean / std_dev) * annualized_factor;
}

double max_drawdown(const double* equity_curve, std::size_t n) {
    if (equity_curve == nullptr || n < 2) return 0.0;

    double peak    = equity_curve[0];
    double max_dd  = 0.0;

    for (std::size_t i = 1; i < n; ++i) {
        if (equity_curve[i] > peak) {
            peak = equity_curve[i];
        }
        if (peak > 0.0) {
            const double dd = (equity_curve[i] - peak) / peak;
            if (dd < max_dd) max_dd = dd;
        }
    }

    return max_dd;   // <= 0
}

} // namespace risk
} // namespace nexus
