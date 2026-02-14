"""
NEXUS Performance Memory — Phase 5, Part D
============================================

Tracks per-asset trading performance for edge compounding.

Per asset:
  - Win rate
  - Average R multiple
  - Drawdown contribution
  - Best/worst regimes

Memory affects AI SUGGESTIONS ONLY.
Execution limits remain unchanged (Phase 4 protections intact).
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.performance_memory")


# =============================================================================
# TRADE RECORD
# =============================================================================

@dataclass
class TradeRecord:
    """A single completed trade for performance tracking."""
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    lot_size: float
    pnl: float
    pnl_pct: float
    r_multiple: float          # pnl / risk_amount (how many R's)
    regime: str                # market regime at time of entry
    duration_mins: float
    exit_reason: str           # TP, SL, manual, timeout
    confidence_at_entry: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "lot_size": self.lot_size,
            "pnl": round(self.pnl, 2),
            "pnl_pct": round(self.pnl_pct, 2),
            "r_multiple": round(self.r_multiple, 2),
            "regime": self.regime,
            "duration_mins": round(self.duration_mins, 1),
            "exit_reason": self.exit_reason,
            "confidence_at_entry": round(self.confidence_at_entry, 3),
            "timestamp": self.timestamp,
        }


# =============================================================================
# ASSET PERFORMANCE PROFILE
# =============================================================================

@dataclass
class AssetProfile:
    """Aggregated performance profile for a single asset."""
    symbol: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    avg_r_multiple: float = 0.0
    max_drawdown_contribution: float = 0.0
    best_regime: str = ""
    worst_regime: str = ""
    regime_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recent_trades: List[TradeRecord] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.wins / self.total_trades

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": round(self.win_rate * 100, 1),
            "total_pnl": round(self.total_pnl, 2),
            "avg_r_multiple": round(self.avg_r_multiple, 2),
            "max_drawdown_contribution": round(self.max_drawdown_contribution, 2),
            "best_regime": self.best_regime,
            "worst_regime": self.worst_regime,
            "regime_performance": self.regime_performance,
            "recent_trade_count": len(self.recent_trades),
        }


# =============================================================================
# PERFORMANCE MEMORY STORE
# =============================================================================

# Max recent trades to keep per asset
MAX_RECENT_TRADES = 50
# Minimum trades needed before memory influences decisions
MIN_TRADES_FOR_INFLUENCE = 5


class PerformanceMemory:
    """
    Thread-safe store for per-asset trade performance.

    Influences AI suggestions:
      - Reduces confidence on underperforming assets
      - Favors historically strong setups
      - Adjusts trade frequency hints (not size)
    """

    def __init__(self):
        self._profiles: Dict[str, AssetProfile] = {}
        self._lock = threading.Lock()

    def record_trade(self, trade: TradeRecord) -> None:
        """Record a completed trade."""
        with self._lock:
            sym = trade.symbol
            if sym not in self._profiles:
                self._profiles[sym] = AssetProfile(symbol=sym)

            profile = self._profiles[sym]
            profile.total_trades += 1
            if trade.pnl >= 0:
                profile.wins += 1
            else:
                profile.losses += 1
            profile.total_pnl += trade.pnl

            # Update R-multiple average
            r_values = [t.r_multiple for t in profile.recent_trades] + [trade.r_multiple]
            profile.avg_r_multiple = sum(r_values) / len(r_values)

            # Track drawdown contribution
            if trade.pnl < 0:
                profile.max_drawdown_contribution = max(
                    profile.max_drawdown_contribution, abs(trade.pnl)
                )

            # Update regime performance
            regime = trade.regime or "UNKNOWN"
            if regime not in profile.regime_performance:
                profile.regime_performance[regime] = {
                    "trades": 0, "wins": 0, "total_pnl": 0.0,
                }
            rp = profile.regime_performance[regime]
            rp["trades"] += 1
            if trade.pnl >= 0:
                rp["wins"] += 1
            rp["total_pnl"] += trade.pnl

            # Determine best/worst regimes
            self._update_best_worst_regimes(profile)

            # Keep recent trades (capped)
            profile.recent_trades.append(trade)
            if len(profile.recent_trades) > MAX_RECENT_TRADES:
                profile.recent_trades = profile.recent_trades[-MAX_RECENT_TRADES:]

        logger.info(
            f"PERF_MEMORY: {trade.symbol} trade recorded — "
            f"PnL: {trade.pnl:+.2f}, R: {trade.r_multiple:+.2f}, "
            f"regime: {trade.regime}"
        )

    def _update_best_worst_regimes(self, profile: AssetProfile) -> None:
        """Recalculate best and worst regimes."""
        best_regime = ""
        worst_regime = ""
        best_rate = -1.0
        worst_rate = 2.0

        for regime, data in profile.regime_performance.items():
            if data["trades"] < 3:
                continue
            rate = data["wins"] / data["trades"]
            if rate > best_rate:
                best_rate = rate
                best_regime = regime
            if rate < worst_rate:
                worst_rate = rate
                worst_regime = regime

        profile.best_regime = best_regime
        profile.worst_regime = worst_regime

    def get_profile(self, symbol: str) -> Optional[AssetProfile]:
        """Get performance profile for a symbol."""
        with self._lock:
            return self._profiles.get(symbol)

    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all profiles as dicts."""
        with self._lock:
            return {sym: p.to_dict() for sym, p in self._profiles.items()}

    def get_confidence_adjustment(self, symbol: str, regime: str) -> float:
        """
        Get a confidence adjustment factor based on historical performance.

        Returns:
            Float modifier (0.5–1.2):
              < 1.0 = reduce confidence (underperforming)
              1.0   = neutral (insufficient data)
              > 1.0 = boost confidence (outperforming)
        """
        with self._lock:
            profile = self._profiles.get(symbol)

        if profile is None or profile.total_trades < MIN_TRADES_FOR_INFLUENCE:
            return 1.0  # neutral — no influence

        # Base adjustment from win rate
        wr = profile.win_rate
        if wr >= 0.65:
            base_adj = 1.1
        elif wr >= 0.50:
            base_adj = 1.0
        elif wr >= 0.35:
            base_adj = 0.8
        else:
            base_adj = 0.6

        # Regime-specific adjustment
        regime_adj = 1.0
        if regime in profile.regime_performance:
            rp = profile.regime_performance[regime]
            if rp["trades"] >= 3:
                regime_wr = rp["wins"] / rp["trades"]
                if regime_wr >= 0.65:
                    regime_adj = 1.1
                elif regime_wr < 0.35:
                    regime_adj = 0.7

        # R-multiple bonus
        r_adj = 1.0
        if profile.avg_r_multiple > 1.5:
            r_adj = 1.05
        elif profile.avg_r_multiple < 0.5:
            r_adj = 0.9

        final = base_adj * regime_adj * r_adj
        return max(0.5, min(1.2, final))

    def get_frequency_hint(self, symbol: str) -> str:
        """
        Get a frequency hint for the AI layer.

        Returns:
            "NORMAL", "REDUCE", or "FAVOR"
        """
        with self._lock:
            profile = self._profiles.get(symbol)

        if profile is None or profile.total_trades < MIN_TRADES_FOR_INFLUENCE:
            return "NORMAL"

        if profile.win_rate < 0.35 and profile.total_trades >= 10:
            return "REDUCE"
        elif profile.win_rate >= 0.60 and profile.avg_r_multiple >= 1.0:
            return "FAVOR"
        else:
            return "NORMAL"

    def get_performance_context_for_ai(self, symbol: str, current_regime: str) -> str:
        """Format performance memory for AI prompt injection."""
        with self._lock:
            profile = self._profiles.get(symbol)

        if profile is None or profile.total_trades < MIN_TRADES_FOR_INFLUENCE:
            return f"PERFORMANCE MEMORY FOR {symbol}: Insufficient trade history. No bias applied."

        freq_hint = self.get_frequency_hint(symbol)
        conf_adj = self.get_confidence_adjustment(symbol, current_regime)

        lines = [
            f"PERFORMANCE MEMORY FOR {symbol}:",
            f"  Total Trades: {profile.total_trades}",
            f"  Win Rate: {profile.win_rate:.0%}",
            f"  Avg R-Multiple: {profile.avg_r_multiple:+.2f}R",
            f"  Total P&L: ${profile.total_pnl:+,.2f}",
            f"  Max DD Contribution: ${profile.max_drawdown_contribution:,.2f}",
        ]
        if profile.best_regime:
            lines.append(f"  Best Regime: {profile.best_regime}")
        if profile.worst_regime:
            lines.append(f"  Worst Regime: {profile.worst_regime}")

        lines.append(f"  Current Regime: {current_regime}")
        lines.append(f"  Confidence Adjustment: {conf_adj:.2f}x")
        lines.append(f"  Frequency Hint: {freq_hint}")

        if freq_hint == "REDUCE":
            lines.append("  Advisory: Historically weak on this asset. Consider reducing frequency.")
        elif freq_hint == "FAVOR":
            lines.append("  Advisory: Historically strong. Edge may persist.")

        return "\n".join(lines)


# =============================================================================
# SINGLETON
# =============================================================================

_memory: Optional[PerformanceMemory] = None


def get_performance_memory() -> PerformanceMemory:
    global _memory
    if _memory is None:
        _memory = PerformanceMemory()
    return _memory
