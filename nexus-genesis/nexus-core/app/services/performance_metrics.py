"""
NEXUS Performance Metrics Engine — Phase 7, Part 8
=====================================================

Tracks and calculates institutional performance metrics:
  - Win rate
  - Risk-reward ratio
  - Average holding time
  - Slippage per trade
  - Execution latency
  - Profit factor
  - Max drawdown

Stored in metrics.json. Updated after each closed trade.
"""

import json
import logging
import os
import statistics
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.performance_metrics")

# =============================================================================
# CONFIGURATION
# =============================================================================
METRICS_FILE = os.environ.get("NEXUS_METRICS_FILE", "logs/metrics.json")
METRICS_SAVE_INTERVAL = 10  # save after every N trades


# =============================================================================
# TRADE RECORD
# =============================================================================

@dataclass
class ClosedTradeRecord:
    """Record of a closed trade for metrics calculation."""
    trade_id: str
    symbol: str
    side: str
    lot_size: float
    entry_price: float
    exit_price: float
    pnl_dollars: float
    pnl_pct: float
    holding_time_mins: float
    slippage_pct: float
    execution_latency_ms: float
    exit_reason: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side,
            "lot_size": self.lot_size,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl_dollars": round(self.pnl_dollars, 2),
            "pnl_pct": round(self.pnl_pct, 4),
            "holding_time_mins": round(self.holding_time_mins, 1),
            "slippage_pct": round(self.slippage_pct, 4),
            "execution_latency_ms": round(self.execution_latency_ms, 1),
            "exit_reason": self.exit_reason,
            "timestamp": self.timestamp,
        }


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

@dataclass
class PerformanceSnapshot:
    """Current performance metrics snapshot."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate_pct: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    risk_reward_ratio: float = 0.0
    profit_factor: float = 0.0
    total_pnl_dollars: float = 0.0
    total_pnl_pct: float = 0.0
    avg_holding_time_mins: float = 0.0
    avg_slippage_pct: float = 0.0
    avg_execution_latency_ms: float = 0.0
    max_drawdown_pct: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    best_trade_pct: float = 0.0
    worst_trade_pct: float = 0.0
    sharpe_approximation: float = 0.0
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate_pct": round(self.win_rate_pct, 1),
            "avg_win_pct": round(self.avg_win_pct, 4),
            "avg_loss_pct": round(self.avg_loss_pct, 4),
            "risk_reward_ratio": round(self.risk_reward_ratio, 2),
            "profit_factor": round(self.profit_factor, 2),
            "total_pnl_dollars": round(self.total_pnl_dollars, 2),
            "total_pnl_pct": round(self.total_pnl_pct, 4),
            "avg_holding_time_mins": round(self.avg_holding_time_mins, 1),
            "avg_slippage_pct": round(self.avg_slippage_pct, 4),
            "avg_execution_latency_ms": round(self.avg_execution_latency_ms, 1),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "max_consecutive_wins": self.max_consecutive_wins,
            "max_consecutive_losses": self.max_consecutive_losses,
            "best_trade_pct": round(self.best_trade_pct, 4),
            "worst_trade_pct": round(self.worst_trade_pct, 4),
            "sharpe_approximation": round(self.sharpe_approximation, 2),
            "last_updated": self.last_updated,
        }


# =============================================================================
# METRICS ENGINE
# =============================================================================

class PerformanceMetricsEngine:
    """
    Tracks all trade outcomes and calculates institutional performance metrics.

    Updates after each closed trade. Persists to metrics.json.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._trades: List[ClosedTradeRecord] = []
        self._snapshot: PerformanceSnapshot = PerformanceSnapshot()
        self._trades_since_save: int = 0
        self._equity_curve: List[float] = []  # for drawdown calculation

        # Load existing metrics
        self._load_metrics()

    # ── Trade Recording ──────────────────────────────────────────

    def record_closed_trade(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        lot_size: float,
        entry_price: float,
        exit_price: float,
        pnl_dollars: float,
        pnl_pct: float,
        holding_time_mins: float,
        slippage_pct: float = 0.0,
        execution_latency_ms: float = 0.0,
        exit_reason: str = "",
    ) -> None:
        """Record a closed trade and recalculate metrics."""
        record = ClosedTradeRecord(
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            lot_size=lot_size,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl_dollars=pnl_dollars,
            pnl_pct=pnl_pct,
            holding_time_mins=holding_time_mins,
            slippage_pct=slippage_pct,
            execution_latency_ms=execution_latency_ms,
            exit_reason=exit_reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._trades.append(record)
            self._trades_since_save += 1

        self._recalculate()

        # Auto-save periodically
        if self._trades_since_save >= METRICS_SAVE_INTERVAL:
            self._save_metrics()

        logger.info(
            f"METRICS: recorded {symbol} {side} — P&L: {pnl_pct:+.4f}% "
            f"({pnl_dollars:+.2f}), holding: {holding_time_mins:.0f}min"
        )

    # ── Recalculation ────────────────────────────────────────────

    def _recalculate(self) -> None:
        """Recalculate all performance metrics from trade history."""
        with self._lock:
            trades = list(self._trades)

        if not trades:
            return

        total = len(trades)
        wins = [t for t in trades if t.pnl_pct >= 0]
        losses = [t for t in trades if t.pnl_pct < 0]

        win_count = len(wins)
        loss_count = len(losses)

        # Win rate
        win_rate = (win_count / total * 100) if total > 0 else 0

        # Average win/loss
        avg_win = statistics.mean([t.pnl_pct for t in wins]) if wins else 0
        avg_loss = statistics.mean([abs(t.pnl_pct) for t in losses]) if losses else 0

        # Risk-reward ratio
        rr_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0

        # Profit factor
        gross_profit = sum(t.pnl_dollars for t in wins) if wins else 0
        gross_loss = sum(abs(t.pnl_dollars) for t in losses) if losses else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (
            float("inf") if gross_profit > 0 else 0
        )

        # Total P&L
        total_pnl_dollars = sum(t.pnl_dollars for t in trades)
        total_pnl_pct = sum(t.pnl_pct for t in trades)

        # Averages
        avg_holding = statistics.mean([t.holding_time_mins for t in trades])
        avg_slippage = statistics.mean([t.slippage_pct for t in trades])
        avg_latency = statistics.mean([t.execution_latency_ms for t in trades])

        # Max drawdown
        max_dd = self._calculate_max_drawdown(trades)

        # Consecutive wins/losses
        max_con_wins, max_con_losses = self._calculate_streaks(trades)

        # Best/worst
        best = max(t.pnl_pct for t in trades)
        worst = min(t.pnl_pct for t in trades)

        # Sharpe approximation (annualized)
        returns = [t.pnl_pct for t in trades]
        sharpe = 0.0
        if len(returns) > 1:
            mean_ret = statistics.mean(returns)
            std_ret = statistics.stdev(returns)
            if std_ret > 0:
                # Approximate annualization: assume ~250 trading days, ~10 trades/day
                sharpe = (mean_ret / std_ret) * (250 ** 0.5)

        with self._lock:
            self._snapshot = PerformanceSnapshot(
                total_trades=total,
                winning_trades=win_count,
                losing_trades=loss_count,
                win_rate_pct=win_rate,
                avg_win_pct=avg_win,
                avg_loss_pct=avg_loss,
                risk_reward_ratio=rr_ratio,
                profit_factor=min(profit_factor, 999.0),  # cap for display
                total_pnl_dollars=total_pnl_dollars,
                total_pnl_pct=total_pnl_pct,
                avg_holding_time_mins=avg_holding,
                avg_slippage_pct=avg_slippage,
                avg_execution_latency_ms=avg_latency,
                max_drawdown_pct=max_dd,
                max_consecutive_wins=max_con_wins,
                max_consecutive_losses=max_con_losses,
                best_trade_pct=best,
                worst_trade_pct=worst,
                sharpe_approximation=sharpe,
                last_updated=datetime.now(timezone.utc).isoformat(),
            )

    def _calculate_max_drawdown(self, trades: List[ClosedTradeRecord]) -> float:
        """Calculate maximum drawdown from trade sequence."""
        if not trades:
            return 0.0

        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0

        for t in trades:
            cumulative += t.pnl_pct
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_streaks(self, trades: List[ClosedTradeRecord]) -> tuple:
        """Calculate max consecutive wins and losses."""
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for t in trades:
            if t.pnl_pct >= 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    # ── Persistence ──────────────────────────────────────────────

    def _save_metrics(self) -> None:
        """Save metrics to metrics.json."""
        try:
            os.makedirs(os.path.dirname(METRICS_FILE) or ".", exist_ok=True)

            with self._lock:
                data = {
                    "metrics": self._snapshot.to_dict(),
                    "trade_count": len(self._trades),
                    "recent_trades": [t.to_dict() for t in self._trades[-50:]],
                }
                self._trades_since_save = 0

            with open(METRICS_FILE, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Metrics saved to {METRICS_FILE}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def _load_metrics(self) -> None:
        """Load metrics from metrics.json if available."""
        if not os.path.exists(METRICS_FILE):
            return

        try:
            with open(METRICS_FILE, "r") as f:
                data = json.load(f)

            recent = data.get("recent_trades", [])
            for t in recent:
                record = ClosedTradeRecord(
                    trade_id=t.get("trade_id", ""),
                    symbol=t.get("symbol", ""),
                    side=t.get("side", ""),
                    lot_size=t.get("lot_size", 0),
                    entry_price=t.get("entry_price", 0),
                    exit_price=t.get("exit_price", 0),
                    pnl_dollars=t.get("pnl_dollars", 0),
                    pnl_pct=t.get("pnl_pct", 0),
                    holding_time_mins=t.get("holding_time_mins", 0),
                    slippage_pct=t.get("slippage_pct", 0),
                    execution_latency_ms=t.get("execution_latency_ms", 0),
                    exit_reason=t.get("exit_reason", ""),
                    timestamp=t.get("timestamp", ""),
                )
                self._trades.append(record)

            if self._trades:
                self._recalculate()
                logger.info(f"Loaded {len(self._trades)} trade records from {METRICS_FILE}")

        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")

    def force_save(self) -> None:
        """Force immediate save of metrics."""
        self._save_metrics()

    # ── Status ───────────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics snapshot."""
        with self._lock:
            return self._snapshot.to_dict()

    def get_per_symbol_metrics(self) -> Dict[str, Any]:
        """Get metrics broken down by symbol."""
        with self._lock:
            trades = list(self._trades)

        symbols: Dict[str, List[ClosedTradeRecord]] = {}
        for t in trades:
            if t.symbol not in symbols:
                symbols[t.symbol] = []
            symbols[t.symbol].append(t)

        result = {}
        for symbol, sym_trades in symbols.items():
            wins = [t for t in sym_trades if t.pnl_pct >= 0]
            total = len(sym_trades)
            result[symbol] = {
                "total_trades": total,
                "win_rate_pct": round(len(wins) / total * 100, 1) if total > 0 else 0,
                "total_pnl_pct": round(sum(t.pnl_pct for t in sym_trades), 4),
                "avg_holding_mins": round(
                    statistics.mean([t.holding_time_mins for t in sym_trades]), 1
                ),
            }

        return result

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_trades_tracked": len(self._trades),
                "metrics_file": METRICS_FILE,
                "trades_since_save": self._trades_since_save,
                "snapshot": self._snapshot.to_dict(),
            }


# =============================================================================
# SINGLETON
# =============================================================================

_engine: Optional[PerformanceMetricsEngine] = None


def get_performance_metrics_engine() -> PerformanceMetricsEngine:
    global _engine
    if _engine is None:
        _engine = PerformanceMetricsEngine()
    return _engine
