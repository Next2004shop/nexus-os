"""
NEXUS Trade Life-Cycle Manager — Phase 6, Part E
==================================================

Smart exit layer for active trade management.

Rules:
  1. At 1R profit → move stop to break-even
  2. Volatility collapse → suggest partial close
  3. Opposite regime detected → downgrade confidence
  4. NEVER widen stop loss (immutable)

This module produces RECOMMENDATIONS only.
Actual order modifications go through the execution engine.
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.trade_lifecycle")


# =============================================================================
# CONFIGURATION
# =============================================================================

BREAKEVEN_R_THRESHOLD = 1.0     # move to BE at 1R
PARTIAL_CLOSE_VOL_DROP = 0.5    # vol drops to 50% of entry vol → partial close
PARTIAL_CLOSE_PCT = 50          # close 50% of position on partial
STOP_WIDEN_ALLOWED = False      # IMMUTABLE: never widen stops


# =============================================================================
# TRADE STATE
# =============================================================================

class TradePhase(Enum):
    OPEN = "OPEN"
    AT_BREAKEVEN = "AT_BREAKEVEN"
    IN_PROFIT = "IN_PROFIT"
    PARTIAL_CLOSED = "PARTIAL_CLOSED"
    CLOSED = "CLOSED"


@dataclass
class ManagedTrade:
    """A trade being actively managed by the lifecycle engine."""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: Optional[float]
    lot_size: float
    risk_amount: float             # $ amount risked (entry - SL) * lots
    entry_atr: float               # ATR at time of entry
    entry_regime: str              # regime at time of entry
    phase: TradePhase = TradePhase.OPEN
    breakeven_moved: bool = False
    partial_closed: bool = False
    opened_at: str = ""

    @property
    def r_multiple(self) -> float:
        """Current R-multiple of the trade."""
        if self.risk_amount <= 0:
            return 0.0
        if self.side == "BUY":
            pnl = (self.current_price - self.entry_price) * self.lot_size
        else:
            pnl = (self.entry_price - self.current_price) * self.lot_size
        return pnl / self.risk_amount

    @property
    def unrealized_pnl(self) -> float:
        if self.side == "BUY":
            return (self.current_price - self.entry_price) * self.lot_size
        else:
            return (self.entry_price - self.current_price) * self.lot_size

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "lot_size": self.lot_size,
            "r_multiple": round(self.r_multiple, 2),
            "unrealized_pnl": round(self.unrealized_pnl, 2),
            "phase": self.phase.value,
            "breakeven_moved": self.breakeven_moved,
            "partial_closed": self.partial_closed,
            "entry_regime": self.entry_regime,
            "opened_at": self.opened_at,
        }


# =============================================================================
# LIFECYCLE RECOMMENDATION
# =============================================================================

class ActionType(Enum):
    HOLD = "HOLD"
    MOVE_TO_BREAKEVEN = "MOVE_TO_BREAKEVEN"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    TIGHTEN_STOP = "TIGHTEN_STOP"
    CLOSE = "CLOSE"


@dataclass
class LifecycleAction:
    """A recommended action for a managed trade."""
    trade_id: str
    symbol: str
    action: ActionType
    new_stop_loss: Optional[float] = None
    close_pct: Optional[int] = None
    reason: str = ""
    priority: str = "NORMAL"       # NORMAL, HIGH, CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "action": self.action.value,
            "new_stop_loss": self.new_stop_loss,
            "close_pct": self.close_pct,
            "reason": self.reason,
            "priority": self.priority,
        }


# =============================================================================
# LIFECYCLE ENGINE
# =============================================================================

class TradeLifecycleEngine:
    """
    Manages active trades and generates exit recommendations.
    Thread-safe.
    """

    def __init__(self):
        self._trades: Dict[str, ManagedTrade] = {}
        self._lock = threading.Lock()
        self._actions_log: List[LifecycleAction] = []

    def register_trade(self, trade: ManagedTrade) -> None:
        """Register a new trade for lifecycle management."""
        trade.opened_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._trades[trade.trade_id] = trade
        logger.info(f"LIFECYCLE: registered {trade.symbol} {trade.side} (id={trade.trade_id})")

    def close_trade(self, trade_id: str) -> None:
        """Remove a closed trade."""
        with self._lock:
            if trade_id in self._trades:
                trade = self._trades.pop(trade_id)
                trade.phase = TradePhase.CLOSED
        logger.info(f"LIFECYCLE: closed trade {trade_id}")

    def update_price(self, symbol: str, current_price: float) -> List[LifecycleAction]:
        """
        Update price for a symbol and generate lifecycle actions.

        Returns list of recommended actions.
        """
        actions: List[LifecycleAction] = []

        with self._lock:
            for trade_id, trade in self._trades.items():
                if trade.symbol != symbol or trade.phase == TradePhase.CLOSED:
                    continue

                trade.current_price = current_price
                trade_actions = self._evaluate_trade(trade)
                actions.extend(trade_actions)

        if actions:
            with self._lock:
                self._actions_log.extend(actions)

        return actions

    def _evaluate_trade(self, trade: ManagedTrade) -> List[LifecycleAction]:
        """Evaluate a single trade and generate actions."""
        actions = []

        r = trade.r_multiple

        # ── Rule 1: Move to break-even at 1R ─────────────────────
        if r >= BREAKEVEN_R_THRESHOLD and not trade.breakeven_moved:
            new_sl = trade.entry_price
            # Validate: never widen stop
            if self._is_stop_tighter(trade.side, new_sl, trade.stop_loss):
                actions.append(LifecycleAction(
                    trade_id=trade.trade_id,
                    symbol=trade.symbol,
                    action=ActionType.MOVE_TO_BREAKEVEN,
                    new_stop_loss=new_sl,
                    reason=f"Trade at {r:.1f}R — moving stop to break-even",
                    priority="HIGH",
                ))
                trade.breakeven_moved = True
                trade.stop_loss = new_sl
                trade.phase = TradePhase.AT_BREAKEVEN

        # ── Rule 2: Trailing at 2R+ ──────────────────────────────
        if r >= 2.0 and trade.breakeven_moved:
            # Trail stop to lock in 1R
            if trade.side == "BUY":
                trail_sl = trade.entry_price + (trade.entry_price - trade.stop_loss) * 0.5
            else:
                trail_sl = trade.entry_price - (trade.stop_loss - trade.entry_price) * 0.5

            if self._is_stop_tighter(trade.side, trail_sl, trade.stop_loss):
                actions.append(LifecycleAction(
                    trade_id=trade.trade_id,
                    symbol=trade.symbol,
                    action=ActionType.TIGHTEN_STOP,
                    new_stop_loss=round(trail_sl, 5),
                    reason=f"Trade at {r:.1f}R — trailing stop to lock profit",
                    priority="NORMAL",
                ))
                trade.stop_loss = trail_sl
                trade.phase = TradePhase.IN_PROFIT

        return actions

    def check_volatility_collapse(
        self, symbol: str, current_atr: float,
    ) -> List[LifecycleAction]:
        """
        Check for volatility collapse on open trades.

        If current ATR drops to PARTIAL_CLOSE_VOL_DROP of entry ATR,
        recommend partial close.
        """
        actions = []

        with self._lock:
            for trade_id, trade in self._trades.items():
                if trade.symbol != symbol or trade.partial_closed:
                    continue
                if trade.entry_atr <= 0:
                    continue

                vol_ratio = current_atr / trade.entry_atr
                if vol_ratio <= PARTIAL_CLOSE_VOL_DROP:
                    actions.append(LifecycleAction(
                        trade_id=trade.trade_id,
                        symbol=trade.symbol,
                        action=ActionType.PARTIAL_CLOSE,
                        close_pct=PARTIAL_CLOSE_PCT,
                        reason=(
                            f"Volatility collapsed to {vol_ratio:.0%} of entry. "
                            f"Recommend {PARTIAL_CLOSE_PCT}% partial close."
                        ),
                        priority="HIGH",
                    ))
                    trade.partial_closed = True
                    trade.phase = TradePhase.PARTIAL_CLOSED

        return actions

    def check_regime_change(
        self, symbol: str, current_regime: str,
    ) -> List[LifecycleAction]:
        """
        Check if regime has changed adversely for open trades.
        """
        actions = []

        with self._lock:
            for trade_id, trade in self._trades.items():
                if trade.symbol != symbol:
                    continue

                # Regime change from trending to range or high vol
                if (trade.entry_regime == "TRENDING"
                        and current_regime in ("RANGE_BOUND", "HIGH_VOLATILITY")):
                    actions.append(LifecycleAction(
                        trade_id=trade.trade_id,
                        symbol=trade.symbol,
                        action=ActionType.TIGHTEN_STOP,
                        reason=(
                            f"Regime changed: {trade.entry_regime} → {current_regime}. "
                            f"Confidence downgraded. Consider tightening stop."
                        ),
                        priority="HIGH",
                    ))

        return actions

    @staticmethod
    def _is_stop_tighter(side: str, new_sl: float, current_sl: float) -> bool:
        """Check that new stop is tighter (never wider). IMMUTABLE RULE."""
        if side == "BUY":
            return new_sl > current_sl  # higher SL = tighter for longs
        else:
            return new_sl < current_sl  # lower SL = tighter for shorts

    def get_managed_trades(self) -> List[Dict[str, Any]]:
        """Get all managed trades."""
        with self._lock:
            return [t.to_dict() for t in self._trades.values()]

    def get_recent_actions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent lifecycle actions."""
        with self._lock:
            return [a.to_dict() for a in self._actions_log[-limit:]]

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "managed_trades": len(self._trades),
                "total_actions": len(self._actions_log),
                "trades": [t.to_dict() for t in self._trades.values()],
            }


# =============================================================================
# SINGLETON
# =============================================================================

_engine: Optional[TradeLifecycleEngine] = None


def get_lifecycle_engine() -> TradeLifecycleEngine:
    global _engine
    if _engine is None:
        _engine = TradeLifecycleEngine()
    return _engine
