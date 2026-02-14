"""
NEXUS Dynamic Lot Logic — Phase 6, Part C
===========================================

Safely constrained lot sizing that adapts to account state.

Defaults:
  - Base: 0.1 lots
  - Low balance: auto-reduce to 0.05
  - Strong streak: allow up to 0.2 (only if risk % supports it)

Hard caps:
  - NEVER exceed broker max lot setting (0.5 from Phase 4)
  - NEVER exceed risk per trade %
  - Capital tier CANNOT override these limits
"""

import logging
import os
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("nexus.dynamic_lots")


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_LOT_SIZE = 0.10
REDUCED_LOT_SIZE = 0.05
STREAK_LOT_SIZE = 0.20
MIN_LOT_SIZE = 0.01
BROKER_MAX_LOT = 0.50                   # from Phase 4 MAX_LOT_LIMIT

LOW_BALANCE_THRESHOLD = 500.0            # below this → reduce lots
STREAK_WIN_THRESHOLD = 5                 # consecutive wins for streak bonus
MAX_RISK_PER_TRADE_PCT = 1.0            # never risk more than 1% per trade


# =============================================================================
# DYNAMIC LOT CALCULATOR
# =============================================================================

def calculate_dynamic_lot(
    equity: float,
    entry_price: float,
    stop_loss_distance: float,
    consecutive_wins: int = 0,
    consecutive_losses: int = 0,
    tier: str = "STABLE",
    risk_multiplier: float = 1.0,
) -> Tuple[float, str]:
    """
    Calculate dynamic lot size based on account state.

    Hierarchy (highest priority first):
      1. Risk-based sizing (never exceed 1% risk)
      2. Broker max lot (0.5)
      3. Balance-based reduction
      4. Streak-based adjustment
      5. Tier-based floor

    Args:
        equity: Current account equity
        entry_price: Expected entry price
        stop_loss_distance: Distance to SL in price units
        consecutive_wins: Current win streak
        consecutive_losses: Current loss streak
        tier: Capital tier (SURVIVAL, STABLE, EXPANSION)
        risk_multiplier: Equity curve risk multiplier (0.25-1.0)

    Returns:
        (lot_size, reasoning)
    """
    reasons = []

    # ── Step 1: Start with default ────────────────────────────────
    lot = DEFAULT_LOT_SIZE
    reasons.append(f"base={DEFAULT_LOT_SIZE}")

    # ── Step 2: Low balance reduction ─────────────────────────────
    if equity < LOW_BALANCE_THRESHOLD:
        lot = REDUCED_LOT_SIZE
        reasons.append(f"low_balance(${equity:,.0f}<${LOW_BALANCE_THRESHOLD:,.0f})→{REDUCED_LOT_SIZE}")

    # ── Step 3: Loss streak reduction ─────────────────────────────
    if consecutive_losses >= 3:
        lot = min(lot, REDUCED_LOT_SIZE)
        reasons.append(f"loss_streak({consecutive_losses})→capped_at_{REDUCED_LOT_SIZE}")

    # ── Step 4: Tier adjustment ───────────────────────────────────
    if tier == "SURVIVAL":
        lot = min(lot, REDUCED_LOT_SIZE)
        reasons.append(f"survival_tier→capped_at_{REDUCED_LOT_SIZE}")
    elif tier == "EXPANSION" and consecutive_wins >= STREAK_WIN_THRESHOLD:
        # Allow streak bonus ONLY in expansion tier with strong performance
        lot = min(STREAK_LOT_SIZE, lot * 1.5)
        reasons.append(f"expansion_streak({consecutive_wins}wins)→{lot:.2f}")

    # ── Step 5: Risk multiplier from equity curve ─────────────────
    if risk_multiplier < 1.0:
        lot = lot * risk_multiplier
        reasons.append(f"risk_mult={risk_multiplier:.2f}")

    # ── Step 6: Risk-based cap (HARD LIMIT) ───────────────────────
    if stop_loss_distance > 0 and equity > 0:
        max_risk_amount = equity * (MAX_RISK_PER_TRADE_PCT / 100.0)
        risk_based_max = max_risk_amount / stop_loss_distance
        if lot > risk_based_max:
            lot = risk_based_max
            reasons.append(f"risk_cap({MAX_RISK_PER_TRADE_PCT}%→{risk_based_max:.2f})")

    # ── Step 7: Broker max (ABSOLUTE HARD LIMIT) ──────────────────
    lot = min(lot, BROKER_MAX_LOT)

    # ── Step 8: Floor at minimum ──────────────────────────────────
    lot = max(MIN_LOT_SIZE, lot)

    # Round to 2 decimals
    lot = round(lot, 2)

    reasoning = "; ".join(reasons) + f" → final={lot}"
    logger.info(f"DYNAMIC_LOT: {reasoning}")

    return lot, reasoning


def get_lot_config() -> Dict[str, Any]:
    """Get current lot configuration for display."""
    return {
        "default_lot": DEFAULT_LOT_SIZE,
        "reduced_lot": REDUCED_LOT_SIZE,
        "streak_lot": STREAK_LOT_SIZE,
        "min_lot": MIN_LOT_SIZE,
        "broker_max_lot": BROKER_MAX_LOT,
        "low_balance_threshold": LOW_BALANCE_THRESHOLD,
        "streak_win_threshold": STREAK_WIN_THRESHOLD,
        "max_risk_per_trade_pct": MAX_RISK_PER_TRADE_PCT,
    }
