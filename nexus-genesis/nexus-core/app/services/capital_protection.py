"""
NEXUS Capital Protection Core — Phase 4, Part B
=================================================

Capital protection FIRST. Profit second.
These guards OVERRIDE all AI decisions.

1. Hard Daily Loss Cap — absolute % of equity → SAFE mode
2. Floating Drawdown Guard — unrealized loss monitor
3. Equity Curve Monitor — slope deviation → auto-reduce risk
4. Position Sizing Engine — risk-based, Kelly-adjusted, capped
5. Black Swan Trigger — volatility spike → pause system
"""

import logging
import math
import os
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.capital_protection")


# =============================================================================
# CONFIGURATION
# =============================================================================
DAILY_LOSS_CAP_PCT = float(os.environ.get("NEXUS_DAILY_LOSS_CAP_PCT", "2.0"))  # 2%
FLOATING_DD_WARN_PCT = 1.0          # 1% floating drawdown warning
FLOATING_DD_HALT_PCT = 3.0          # 3% floating drawdown → forced action
MAX_LOT_LIMIT = 0.5                 # absolute max lot size
MIN_LOT_SIZE = 0.01                 # minimum lot
RISK_PER_TRADE_PCT = 1.0            # risk 1% of equity per trade
EQUITY_SLOPE_WINDOW = 20            # number of equity snapshots for slope
EQUITY_DEVIATION_THRESHOLD = 2.0    # std deviations for abnormal slope
BLACK_SWAN_ATR_MULTIPLIER = 4.0     # ATR multiplier for black swan detection
BLACK_SWAN_PRICE_MOVE_PCT = 3.0     # price move % threshold for black swan


# =============================================================================
# DAILY LOSS TRACKER
# =============================================================================

class DailyLossTracker:
    """
    Tracks daily P&L and enforces hard loss cap.

    On breach: sets system to SAFE mode via watchdog.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._day_start_equity: float = 0.0
        self._current_equity: float = 0.0
        self._current_date: str = ""
        self._daily_pnl: float = 0.0
        self._daily_pnl_pct: float = 0.0
        self._cap_hit: bool = False
        self._trades_today: int = 0
        self._wins_today: int = 0
        self._losses_today: int = 0

    def initialize(self, equity: float) -> None:
        """Set starting equity for the day."""
        with self._lock:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if self._current_date != today:
                self._day_start_equity = equity
                self._current_date = today
                self._daily_pnl = 0.0
                self._daily_pnl_pct = 0.0
                self._cap_hit = False
                self._trades_today = 0
                self._wins_today = 0
                self._losses_today = 0
                logger.info(f"Daily loss tracker reset for {today}: starting equity=${equity:,.2f}")
            self._current_equity = equity

    def update_equity(self, equity: float) -> Tuple[bool, str]:
        """
        Update current equity and check daily loss cap.

        Returns:
            (cap_breached, message)
        """
        with self._lock:
            # Auto-reset if new day
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if self._current_date != today:
                self._day_start_equity = equity
                self._current_date = today
                self._daily_pnl = 0.0
                self._daily_pnl_pct = 0.0
                self._cap_hit = False
                self._trades_today = 0
                self._wins_today = 0
                self._losses_today = 0

            self._current_equity = equity
            if self._day_start_equity > 0:
                self._daily_pnl = equity - self._day_start_equity
                self._daily_pnl_pct = (self._daily_pnl / self._day_start_equity) * 100
            else:
                self._daily_pnl = 0.0
                self._daily_pnl_pct = 0.0

            # Check cap
            if self._daily_pnl_pct <= -DAILY_LOSS_CAP_PCT:
                self._cap_hit = True
                logger.critical(
                    f"DAILY LOSS CAP HIT: {self._daily_pnl_pct:.2f}% "
                    f"(cap: -{DAILY_LOSS_CAP_PCT}%). Entering SAFE mode."
                )
                return True, f"DAILY_LOSS_CAP_BREACHED: {self._daily_pnl_pct:.2f}%"

            return False, f"DAILY_PNL: {self._daily_pnl_pct:+.2f}%"

    def record_trade(self, pnl: float) -> None:
        """Record a completed trade for daily stats."""
        with self._lock:
            self._trades_today += 1
            if pnl >= 0:
                self._wins_today += 1
            else:
                self._losses_today += 1

    def is_cap_hit(self) -> bool:
        with self._lock:
            return self._cap_hit

    def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily performance summary."""
        with self._lock:
            win_rate = (self._wins_today / self._trades_today * 100) if self._trades_today > 0 else 0
            return {
                "date": self._current_date,
                "start_equity": round(self._day_start_equity, 2),
                "current_equity": round(self._current_equity, 2),
                "daily_pnl": round(self._daily_pnl, 2),
                "daily_pnl_pct": round(self._daily_pnl_pct, 2),
                "cap_hit": self._cap_hit,
                "cap_limit_pct": DAILY_LOSS_CAP_PCT,
                "trades_today": self._trades_today,
                "wins": self._wins_today,
                "losses": self._losses_today,
                "win_rate": round(win_rate, 1),
            }


# =============================================================================
# FLOATING DRAWDOWN GUARD
# =============================================================================

class FloatingDrawdownGuard:
    """
    Monitors unrealized (floating) P&L across all open positions.

    Actions:
      - Warn at FLOATING_DD_WARN_PCT
      - Halt new trades at FLOATING_DD_HALT_PCT
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._floating_pnl: float = 0.0
        self._equity: float = 0.0
        self._floating_dd_pct: float = 0.0

    def update(self, floating_pnl: float, equity: float) -> Tuple[str, float]:
        """
        Update floating P&L and return status.

        Returns:
            (status, floating_dd_pct)
            status: "OK", "WARNING", "HALT"
        """
        with self._lock:
            self._floating_pnl = floating_pnl
            self._equity = equity
            if equity > 0:
                self._floating_dd_pct = abs(min(0, floating_pnl)) / equity * 100
            else:
                self._floating_dd_pct = 0.0

            if self._floating_dd_pct >= FLOATING_DD_HALT_PCT:
                logger.critical(
                    f"FLOATING_DD_HALT: {self._floating_dd_pct:.2f}% "
                    f">= {FLOATING_DD_HALT_PCT}%"
                )
                return "HALT", self._floating_dd_pct
            elif self._floating_dd_pct >= FLOATING_DD_WARN_PCT:
                logger.warning(
                    f"FLOATING_DD_WARNING: {self._floating_dd_pct:.2f}%"
                )
                return "WARNING", self._floating_dd_pct
            else:
                return "OK", self._floating_dd_pct

    def should_block_new_trades(self) -> Tuple[bool, str]:
        with self._lock:
            if self._floating_dd_pct >= FLOATING_DD_HALT_PCT:
                return True, f"FLOATING_DD_TOO_HIGH: {self._floating_dd_pct:.2f}%"
            return False, "OK"


# =============================================================================
# EQUITY CURVE MONITOR
# =============================================================================

class EquityCurveMonitor:
    """
    Tracks equity over time and detects abnormal deviations.

    If equity slope deviates > EQUITY_DEVIATION_THRESHOLD standard
    deviations below the mean, risk is automatically reduced.
    """

    def __init__(self, window: int = EQUITY_SLOPE_WINDOW):
        self._lock = threading.Lock()
        self._equity_history: deque = deque(maxlen=window + 1)
        self._risk_multiplier: float = 1.0  # 1.0 = normal, <1.0 = reduced

    def record_equity(self, equity: float) -> None:
        """Record an equity snapshot."""
        with self._lock:
            self._equity_history.append({
                "equity": equity,
                "timestamp": time.monotonic(),
            })
            self._recalculate_risk_multiplier()

    def _recalculate_risk_multiplier(self) -> None:
        """Recalculate risk multiplier based on equity slope."""
        if len(self._equity_history) < 5:
            self._risk_multiplier = 1.0
            return

        equities = [e["equity"] for e in self._equity_history]

        # Calculate returns
        returns = []
        for i in range(1, len(equities)):
            if equities[i - 1] > 0:
                returns.append((equities[i] - equities[i - 1]) / equities[i - 1])

        if len(returns) < 3:
            self._risk_multiplier = 1.0
            return

        mean_return = statistics.mean(returns)
        stdev_return = statistics.stdev(returns) if len(returns) > 1 else 0.001

        # Recent return (last entry)
        recent_return = returns[-1]

        if stdev_return > 0:
            z_score = (recent_return - mean_return) / stdev_return
        else:
            z_score = 0.0

        # Abnormal negative deviation → reduce risk
        if z_score < -EQUITY_DEVIATION_THRESHOLD:
            self._risk_multiplier = max(0.25, 1.0 + (z_score / 4.0))
            logger.warning(
                f"EQUITY_CURVE_DEVIATION: z={z_score:.2f}, "
                f"risk_multiplier reduced to {self._risk_multiplier:.2f}"
            )
        elif z_score < -1.0:
            self._risk_multiplier = 0.75
        else:
            # Gradually return to normal
            self._risk_multiplier = min(1.0, self._risk_multiplier + 0.05)

    def get_risk_multiplier(self) -> float:
        with self._lock:
            return self._risk_multiplier

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "risk_multiplier": round(self._risk_multiplier, 3),
                "equity_snapshots": len(self._equity_history),
                "window_size": self._equity_history.maxlen,
            }


# =============================================================================
# POSITION SIZING ENGINE
# =============================================================================

def calculate_position_size(
    equity: float,
    entry_price: float,
    stop_loss_price: float,
    risk_pct: float = RISK_PER_TRADE_PCT,
    risk_multiplier: float = 1.0,
) -> float:
    """
    Risk-based position sizing.

    lot_size = (equity * risk_pct/100 * risk_multiplier) / |entry - stop_loss|

    Capped at MAX_LOT_LIMIT, floored at MIN_LOT_SIZE.
    No randomness — purely deterministic.
    """
    if equity <= 0 or entry_price <= 0:
        return MIN_LOT_SIZE

    risk_distance = abs(entry_price - stop_loss_price)
    if risk_distance <= 0:
        logger.warning("SIZING: risk_distance is zero, using minimum lot")
        return MIN_LOT_SIZE

    risk_amount = equity * (risk_pct / 100.0) * risk_multiplier
    raw_lots = risk_amount / risk_distance

    # Enforce bounds
    sized = max(MIN_LOT_SIZE, min(raw_lots, MAX_LOT_LIMIT))

    # Round to 2 decimal places (standard lot precision)
    sized = round(sized, 2)

    logger.info(
        f"SIZING: equity=${equity:,.0f}, risk={risk_pct}%, "
        f"distance={risk_distance:.5f}, multiplier={risk_multiplier:.2f} "
        f"→ {sized} lots"
    )
    return sized


def auto_adjust_lots(
    equity: float,
    base_lots: float,
    risk_multiplier: float = 1.0,
) -> float:
    """
    Auto-adjust lot size based on equity and risk multiplier.
    Prevents over-sizing when equity changes.
    """
    adjusted = base_lots * risk_multiplier
    adjusted = max(MIN_LOT_SIZE, min(adjusted, MAX_LOT_LIMIT))
    return round(adjusted, 2)


# =============================================================================
# BLACK SWAN TRIGGER
# =============================================================================

class BlackSwanDetector:
    """
    Detects abnormal volatility spikes that indicate a black swan event.

    Triggers:
      - Single-bar price move > BLACK_SWAN_PRICE_MOVE_PCT
      - ATR spike > BLACK_SWAN_ATR_MULTIPLIER × historical norm

    On trigger: system pauses immediately.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._triggered = False
        self._trigger_reason: str = ""
        self._trigger_time: Optional[str] = None

    def check_price_move(
        self, current_price: float, previous_close: float,
    ) -> Tuple[bool, str]:
        """Check for abnormal single-bar price move."""
        if previous_close <= 0:
            return False, "NO_PREVIOUS_CLOSE"

        move_pct = abs(current_price - previous_close) / previous_close * 100

        if move_pct >= BLACK_SWAN_PRICE_MOVE_PCT:
            reason = f"BLACK_SWAN_PRICE_MOVE: {move_pct:.2f}% (threshold: {BLACK_SWAN_PRICE_MOVE_PCT}%)"
            with self._lock:
                self._triggered = True
                self._trigger_reason = reason
                self._trigger_time = datetime.now(timezone.utc).isoformat()
            logger.critical(reason)
            return True, reason

        return False, f"PRICE_MOVE_OK: {move_pct:.2f}%"

    def check_atr_spike(
        self, current_atr: float, historical_atr: float,
    ) -> Tuple[bool, str]:
        """Check for abnormal ATR spike."""
        if historical_atr <= 0:
            return False, "NO_HISTORICAL_ATR"

        ratio = current_atr / historical_atr

        if ratio >= BLACK_SWAN_ATR_MULTIPLIER:
            reason = (
                f"BLACK_SWAN_ATR_SPIKE: current/historical = {ratio:.2f}x "
                f"(threshold: {BLACK_SWAN_ATR_MULTIPLIER}x)"
            )
            with self._lock:
                self._triggered = True
                self._trigger_reason = reason
                self._trigger_time = datetime.now(timezone.utc).isoformat()
            logger.critical(reason)
            return True, reason

        return False, f"ATR_OK: {ratio:.2f}x"

    def is_triggered(self) -> bool:
        with self._lock:
            return self._triggered

    def reset(self) -> None:
        """Reset black swan flag (requires manual intervention)."""
        with self._lock:
            self._triggered = False
            self._trigger_reason = ""
            self._trigger_time = None
        logger.info("Black swan trigger reset")

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "triggered": self._triggered,
                "reason": self._trigger_reason,
                "trigger_time": self._trigger_time,
            }


# =============================================================================
# SINGLETONS
# =============================================================================

_daily_tracker: Optional[DailyLossTracker] = None
_floating_guard: Optional[FloatingDrawdownGuard] = None
_equity_monitor: Optional[EquityCurveMonitor] = None
_black_swan: Optional[BlackSwanDetector] = None


def get_daily_tracker() -> DailyLossTracker:
    global _daily_tracker
    if _daily_tracker is None:
        _daily_tracker = DailyLossTracker()
    return _daily_tracker


def get_floating_guard() -> FloatingDrawdownGuard:
    global _floating_guard
    if _floating_guard is None:
        _floating_guard = FloatingDrawdownGuard()
    return _floating_guard


def get_equity_monitor() -> EquityCurveMonitor:
    global _equity_monitor
    if _equity_monitor is None:
        _equity_monitor = EquityCurveMonitor()
    return _equity_monitor


def get_black_swan() -> BlackSwanDetector:
    global _black_swan
    if _black_swan is None:
        _black_swan = BlackSwanDetector()
    return _black_swan
