"""
NEXUS Capital Tier System — Phase 6, Part A
=============================================

Automatically classifies account into one of 3 tiers:

  Tier 1 — SURVIVAL: Low balance or drawdown state.
    - Strictest confidence thresholds
    - Fewest allowed trades
    - Only highest-conviction assets

  Tier 2 — STABLE: Normal operations.
    - Standard confidence thresholds
    - Normal trade frequency
    - Full asset selection

  Tier 3 — EXPANSION: Equity growth phase.
    - Slightly relaxed frequency (not risk)
    - Broader asset selection
    - Lower confidence floor

Tier NEVER increases max lot size beyond system limits.
Tier affects trade frequency and confidence thresholds, not risk per trade.
"""

import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("nexus.capital_tiers")


# =============================================================================
# CONFIGURATION
# =============================================================================

# Tier transition thresholds
SURVIVAL_DRAWDOWN_PCT = 1.5         # in survival if DD > 1.5%
SURVIVAL_CONSECUTIVE_LOSSES = 4     # in survival if 4+ consecutive losses
EXPANSION_GROWTH_PCT = 3.0          # in expansion if equity grown > 3% from initial
EXPANSION_MIN_WINS = 5              # need at least 5 consecutive wins for expansion
STABLE_MIN_EQUITY_RATIO = 0.98     # must be at least 98% of initial equity for stable

# Tier-specific parameters
TIER_CONFIG = {
    "SURVIVAL": {
        "max_trades_per_day": 3,
        "min_confidence": 0.85,
        "allowed_asset_tiers": ["primary"],  # only safest assets
        "description": "Capital preservation. Minimal trading.",
    },
    "STABLE": {
        "max_trades_per_day": 10,
        "min_confidence": 0.70,
        "allowed_asset_tiers": ["primary", "secondary"],
        "description": "Normal operations. Standard parameters.",
    },
    "EXPANSION": {
        "max_trades_per_day": 15,
        "min_confidence": 0.65,
        "allowed_asset_tiers": ["primary", "secondary", "exploratory"],
        "description": "Growth phase. Broader opportunity set.",
    },
}

# Asset classification by tier
ASSET_TIERS = {
    "EURUSD": "primary",
    "GBPUSD": "primary",
    "XAUUSD": "primary",
    "BTCUSD": "secondary",
    "ETHUSD": "secondary",
    "BTC/USDT": "secondary",
    "ETH/USDT": "exploratory",
}


# =============================================================================
# TIER DEFINITIONS
# =============================================================================

class CapitalTier(Enum):
    SURVIVAL = "SURVIVAL"
    STABLE = "STABLE"
    EXPANSION = "EXPANSION"


@dataclass
class TierState:
    """Current tier classification and metadata."""
    tier: CapitalTier
    equity: float
    initial_equity: float
    equity_growth_pct: float
    drawdown_pct: float
    consecutive_wins: int
    consecutive_losses: int
    trades_today: int
    max_trades_today: int
    min_confidence: float
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier.value,
            "equity": round(self.equity, 2),
            "initial_equity": round(self.initial_equity, 2),
            "equity_growth_pct": round(self.equity_growth_pct, 2),
            "drawdown_pct": round(self.drawdown_pct, 2),
            "consecutive_wins": self.consecutive_wins,
            "consecutive_losses": self.consecutive_losses,
            "trades_today": self.trades_today,
            "max_trades_today": self.max_trades_today,
            "min_confidence": self.min_confidence,
            "config": TIER_CONFIG[self.tier.value],
            "updated_at": self.updated_at,
        }


# =============================================================================
# TIER ENGINE
# =============================================================================

class CapitalTierEngine:
    """
    Determines capital tier based on account state.
    Thread-safe. Updated on each equity refresh.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._tier = CapitalTier.STABLE
        self._consecutive_wins = 0
        self._consecutive_losses = 0
        self._trades_today = 0
        self._current_date = ""

    def classify(
        self,
        equity: float,
        initial_equity: float,
        peak_equity: float,
        consecutive_losses: int = 0,
        consecutive_wins: int = 0,
    ) -> TierState:
        """
        Classify current capital tier.

        Args:
            equity: Current account equity
            initial_equity: Starting equity
            peak_equity: Peak equity recorded
            consecutive_losses: Current loss streak
            consecutive_wins: Current win streak

        Returns:
            TierState with classification
        """
        with self._lock:
            self._consecutive_wins = consecutive_wins
            self._consecutive_losses = consecutive_losses

            # Reset daily counter if new day
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if self._current_date != today:
                self._trades_today = 0
                self._current_date = today

            # Calculate metrics
            drawdown_pct = 0.0
            if peak_equity > 0:
                drawdown_pct = ((peak_equity - equity) / peak_equity) * 100

            growth_pct = 0.0
            if initial_equity > 0:
                growth_pct = ((equity - initial_equity) / initial_equity) * 100

            equity_ratio = equity / initial_equity if initial_equity > 0 else 1.0

            # ── Tier determination (priority: SURVIVAL > EXPANSION > STABLE) ──
            if (drawdown_pct >= SURVIVAL_DRAWDOWN_PCT
                    or consecutive_losses >= SURVIVAL_CONSECUTIVE_LOSSES
                    or equity_ratio < 0.95):
                tier = CapitalTier.SURVIVAL
            elif (growth_pct >= EXPANSION_GROWTH_PCT
                    and consecutive_wins >= EXPANSION_MIN_WINS
                    and drawdown_pct < 0.5):
                tier = CapitalTier.EXPANSION
            else:
                tier = CapitalTier.STABLE

            # Log tier change
            if tier != self._tier:
                logger.info(
                    f"TIER_CHANGE: {self._tier.value} → {tier.value} "
                    f"(equity=${equity:,.2f}, DD={drawdown_pct:.2f}%, "
                    f"growth={growth_pct:.2f}%)"
                )
                self._tier = tier

            config = TIER_CONFIG[tier.value]

            return TierState(
                tier=tier,
                equity=equity,
                initial_equity=initial_equity,
                equity_growth_pct=growth_pct,
                drawdown_pct=drawdown_pct,
                consecutive_wins=consecutive_wins,
                consecutive_losses=consecutive_losses,
                trades_today=self._trades_today,
                max_trades_today=config["max_trades_per_day"],
                min_confidence=config["min_confidence"],
                updated_at=datetime.now(timezone.utc).isoformat(),
            )

    def record_trade(self) -> None:
        """Increment daily trade counter."""
        with self._lock:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if self._current_date != today:
                self._trades_today = 0
                self._current_date = today
            self._trades_today += 1

    def can_trade(self) -> Tuple[bool, str]:
        """Check if current tier allows more trades today."""
        with self._lock:
            config = TIER_CONFIG[self._tier.value]
            if self._trades_today >= config["max_trades_per_day"]:
                return False, (
                    f"TIER_TRADE_LIMIT: {self._tier.value} allows "
                    f"{config['max_trades_per_day']} trades/day, "
                    f"used {self._trades_today}"
                )
            return True, "OK"

    def check_confidence(self, confidence: float) -> Tuple[bool, str]:
        """Check if confidence meets tier minimum."""
        with self._lock:
            config = TIER_CONFIG[self._tier.value]
            min_conf = config["min_confidence"]
            if confidence < min_conf:
                return False, (
                    f"TIER_CONFIDENCE_TOO_LOW: {self._tier.value} requires "
                    f">= {min_conf}, got {confidence:.2f}"
                )
            return True, "OK"

    def check_asset_allowed(self, symbol: str) -> Tuple[bool, str]:
        """Check if asset is allowed in current tier."""
        with self._lock:
            config = TIER_CONFIG[self._tier.value]
            asset_tier = ASSET_TIERS.get(symbol, "exploratory")
            if asset_tier not in config["allowed_asset_tiers"]:
                return False, (
                    f"TIER_ASSET_RESTRICTED: {symbol} ({asset_tier}) "
                    f"not allowed in {self._tier.value}"
                )
            return True, "OK"

    def get_current_tier(self) -> CapitalTier:
        with self._lock:
            return self._tier

    def get_tier_context_for_ai(self) -> str:
        """Format tier context for AI prompt injection."""
        with self._lock:
            config = TIER_CONFIG[self._tier.value]
            return (
                f"CAPITAL TIER: {self._tier.value}\n"
                f"  Description: {config['description']}\n"
                f"  Max Trades/Day: {config['max_trades_per_day']} "
                f"(used: {self._trades_today})\n"
                f"  Min Confidence: {config['min_confidence']}\n"
                f"  Asset Access: {', '.join(config['allowed_asset_tiers'])}"
            )


# =============================================================================
# SINGLETON
# =============================================================================

_engine: Optional[CapitalTierEngine] = None


def get_tier_engine() -> CapitalTierEngine:
    global _engine
    if _engine is None:
        _engine = CapitalTierEngine()
    return _engine
