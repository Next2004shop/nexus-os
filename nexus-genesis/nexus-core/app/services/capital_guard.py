"""
NEXUS Capital Guard — Phase 7, Part 3
=======================================

Institutional-grade capital defense engine.

Monitors equity vs balance continuously:
  - Drawdown > configured threshold → disable new trades + notify operator
  - Drawdown > critical threshold → close weakest positions first → SAFE mode

Rules:
  - No emotional logic
  - Pure capital defense
  - Deterministic decision making
  - Human override remains absolute
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.capital_guard")

# =============================================================================
# CONFIGURATION
# =============================================================================
DRAWDOWN_DISABLE_PCT = 3.0     # disable new trades at 3% drawdown
DRAWDOWN_CRITICAL_PCT = 5.0    # close weakest positions at 5% drawdown
GUARD_CHECK_INTERVAL_SECS = 15  # check every 15 seconds
MAX_POSITIONS_TO_CLOSE = 2     # close at most 2 weakest positions per cycle


# =============================================================================
# GUARD STATE
# =============================================================================

@dataclass
class GuardEvent:
    """Record of a guard action."""
    event_type: str  # TRADE_DISABLED, POSITION_CLOSED, SAFE_MODE
    reason: str
    drawdown_pct: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "reason": self.reason,
            "drawdown_pct": round(self.drawdown_pct, 2),
            "details": self.details,
            "timestamp": self.timestamp,
        }


class CapitalGuard:
    """
    Monitors equity vs balance and enforces capital protection.

    Two thresholds:
      - DRAWDOWN_DISABLE_PCT: blocks new trades, notifies operator
      - DRAWDOWN_CRITICAL_PCT: closes weakest positions, enters SAFE mode
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._trades_disabled: bool = False
        self._safe_mode_triggered: bool = False
        self._current_drawdown_pct: float = 0.0
        self._current_equity: float = 0.0
        self._current_balance: float = 0.0
        self._events: List[GuardEvent] = []
        self._positions_closed: int = 0

    # ── Core Check ───────────────────────────────────────────────

    def check_capital(
        self,
        equity: float,
        balance: float,
    ) -> Tuple[str, float]:
        """
        Check equity vs balance and enforce capital protection.

        Returns:
            (status, drawdown_pct)
            status: "OK", "TRADES_DISABLED", "CRITICAL"
        """
        if balance <= 0:
            return "OK", 0.0

        drawdown_pct = ((balance - equity) / balance) * 100 if equity < balance else 0.0

        with self._lock:
            self._current_equity = equity
            self._current_balance = balance
            self._current_drawdown_pct = drawdown_pct

        # Critical threshold: close weakest positions
        if drawdown_pct >= DRAWDOWN_CRITICAL_PCT:
            if not self._safe_mode_triggered:
                self._handle_critical_drawdown(equity, balance, drawdown_pct)
            return "CRITICAL", drawdown_pct

        # Disable threshold: block new trades
        if drawdown_pct >= DRAWDOWN_DISABLE_PCT:
            if not self._trades_disabled:
                self._handle_disable_trades(drawdown_pct)
            return "TRADES_DISABLED", drawdown_pct

        # Recovery: re-enable trades if drawdown recovered
        if self._trades_disabled and drawdown_pct < DRAWDOWN_DISABLE_PCT * 0.5:
            with self._lock:
                self._trades_disabled = False
            logger.info(f"CAPITAL_GUARD: trades re-enabled, drawdown recovered to {drawdown_pct:.2f}%")

        return "OK", drawdown_pct

    def should_block_new_trades(self) -> Tuple[bool, str]:
        """Check if new trades should be blocked."""
        with self._lock:
            if self._safe_mode_triggered:
                return True, f"CAPITAL_GUARD_CRITICAL: drawdown={self._current_drawdown_pct:.2f}%"
            if self._trades_disabled:
                return True, f"CAPITAL_GUARD_DISABLED: drawdown={self._current_drawdown_pct:.2f}%"
            return False, "OK"

    # ── Threshold Handlers ───────────────────────────────────────

    def _handle_disable_trades(self, drawdown_pct: float) -> None:
        """Handle drawdown exceeding disable threshold."""
        with self._lock:
            self._trades_disabled = True

        event = GuardEvent(
            event_type="TRADE_DISABLED",
            reason=f"Drawdown {drawdown_pct:.2f}% >= {DRAWDOWN_DISABLE_PCT}%",
            drawdown_pct=drawdown_pct,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._record_event(event)

        logger.critical(
            f"CAPITAL_GUARD: NEW TRADES DISABLED — drawdown {drawdown_pct:.2f}% "
            f">= {DRAWDOWN_DISABLE_PCT}%"
        )

        # Notify operator via Telegram
        self._notify_operator(
            f"CAPITAL GUARD: TRADES DISABLED\n\n"
            f"Drawdown: {drawdown_pct:.2f}%\n"
            f"Threshold: {DRAWDOWN_DISABLE_PCT}%\n"
            f"Equity: ${self._current_equity:,.2f}\n"
            f"Balance: ${self._current_balance:,.2f}\n\n"
            f"New trades blocked. Monitoring continues."
        )

    def _handle_critical_drawdown(self, equity: float, balance: float, drawdown_pct: float) -> None:
        """Handle critical drawdown: close weakest positions, enter SAFE mode."""
        with self._lock:
            self._safe_mode_triggered = True
            self._trades_disabled = True

        logger.critical(
            f"CAPITAL_GUARD: CRITICAL DRAWDOWN {drawdown_pct:.2f}% "
            f">= {DRAWDOWN_CRITICAL_PCT}% — closing weakest positions"
        )

        # Close weakest positions
        closed = self._close_weakest_positions()

        event = GuardEvent(
            event_type="CRITICAL_DRAWDOWN",
            reason=f"Drawdown {drawdown_pct:.2f}% >= {DRAWDOWN_CRITICAL_PCT}%",
            drawdown_pct=drawdown_pct,
            details={"positions_closed": closed},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._record_event(event)

        # Enter SAFE mode
        try:
            from app.services.watchdog import get_watchdog
            wd = get_watchdog()
            if wd.is_trading_allowed():
                wd.enter_safe_mode(
                    f"Capital guard: critical drawdown {drawdown_pct:.2f}%"
                )
        except Exception as e:
            logger.error(f"Failed to enter safe mode: {e}")

        # Emergency Telegram notification
        self._notify_operator(
            f"CAPITAL GUARD: CRITICAL DRAWDOWN\n\n"
            f"Drawdown: {drawdown_pct:.2f}%\n"
            f"Critical Threshold: {DRAWDOWN_CRITICAL_PCT}%\n"
            f"Equity: ${equity:,.2f}\n"
            f"Balance: ${balance:,.2f}\n"
            f"Positions Closed: {closed}\n\n"
            f"SAFE MODE ACTIVATED.\n"
            f"Manual intervention required."
        )

    def _close_weakest_positions(self) -> int:
        """
        Close the weakest (most negative P&L) open positions.

        Returns number of positions closed.
        """
        closed_count = 0
        try:
            from app.services import risk_governor
            state = risk_governor._get_state()

            if not state.open_positions:
                return 0

            # Sort by P&L (weakest first) — using notional as proxy
            positions = list(state.open_positions.items())
            # Attempt to get actual P&L from MT5
            position_pnl = []
            try:
                import MetaTrader5 as mt5
                for symbol, pos_data in positions:
                    mt5_positions = mt5.positions_get(symbol=symbol)
                    if mt5_positions:
                        total_profit = sum(p.profit for p in mt5_positions)
                        position_pnl.append((symbol, total_profit, pos_data))
                    else:
                        position_pnl.append((symbol, 0, pos_data))
            except ImportError:
                # No MT5 — use registry data only
                for symbol, pos_data in positions:
                    position_pnl.append((symbol, 0, pos_data))

            # Sort by P&L ascending (weakest first)
            position_pnl.sort(key=lambda x: x[1])

            # Close up to MAX_POSITIONS_TO_CLOSE weakest positions
            from app.services import execution
            engine = execution.get_engine()

            for symbol, pnl, pos_data in position_pnl[:MAX_POSITIONS_TO_CLOSE]:
                try:
                    side = pos_data.get("side", "BUY")
                    close_side = "SELL" if side == "BUY" else "BUY"
                    qty = pos_data.get("quantity", 0.01)

                    result = engine.execute_trade(symbol, close_side, qty)
                    if result.status.value == "FILLED":
                        closed_count += 1
                        logger.critical(
                            f"CAPITAL_GUARD: closed {symbol} ({side} {qty}) — P&L: ${pnl:.2f}"
                        )
                except Exception as e:
                    logger.error(f"CAPITAL_GUARD: failed to close {symbol}: {e}")

        except Exception as e:
            logger.error(f"CAPITAL_GUARD: close_weakest error: {e}")

        with self._lock:
            self._positions_closed += closed_count
        return closed_count

    # ── Operator Notification ────────────────────────────────────

    def _notify_operator(self, message: str) -> None:
        """Send alert to operator via Telegram."""
        try:
            from app.services.telegram_reporter import get_telegram_reporter
            reporter = get_telegram_reporter()
            reporter.send_emergency_sync(message)
        except Exception as e:
            logger.error(f"Capital guard Telegram notification failed: {e}")

    # ── Event Tracking ───────────────────────────────────────────

    def _record_event(self, event: GuardEvent) -> None:
        with self._lock:
            self._events.append(event)
            if len(self._events) > 100:
                self._events = self._events[-100:]

    # ── Background Monitor ───────────────────────────────────────

    def start(self) -> None:
        """Start background capital monitoring."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._guard_loop, daemon=True, name="nexus-capital-guard"
        )
        self._thread.start()
        logger.info("Capital guard started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Capital guard stopped")

    def _guard_loop(self) -> None:
        while self._running:
            try:
                from app.services import risk_governor
                risk = risk_governor.get_risk_status()
                equity = risk.get("equity", {}).get("current", 0)
                # Use initial equity as balance baseline
                balance = risk.get("equity", {}).get("initial", equity)
                if equity > 0:
                    self.check_capital(equity, balance)
            except Exception as e:
                logger.error(f"Capital guard loop error: {e}")
            time.sleep(GUARD_CHECK_INTERVAL_SECS)

    def reset(self) -> None:
        """Reset guard state (requires manual intervention)."""
        with self._lock:
            self._trades_disabled = False
            self._safe_mode_triggered = False
        logger.info("CAPITAL_GUARD: reset by operator")

    # ── Status ───────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "trades_disabled": self._trades_disabled,
                "safe_mode_triggered": self._safe_mode_triggered,
                "current_drawdown_pct": round(self._current_drawdown_pct, 2),
                "current_equity": round(self._current_equity, 2),
                "current_balance": round(self._current_balance, 2),
                "positions_closed_total": self._positions_closed,
                "thresholds": {
                    "disable_trades_pct": DRAWDOWN_DISABLE_PCT,
                    "critical_pct": DRAWDOWN_CRITICAL_PCT,
                },
                "recent_events": [e.to_dict() for e in self._events[-10:]],
            }


# =============================================================================
# SINGLETON
# =============================================================================

_guard: Optional[CapitalGuard] = None


def get_capital_guard() -> CapitalGuard:
    global _guard
    if _guard is None:
        _guard = CapitalGuard()
    return _guard
