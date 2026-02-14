"""
NEXUS Position Distribution Engine — Phase 6, Part B
======================================================

Controls concurrent exposure to prevent portfolio concentration.

Rules:
  1. Max 3 concurrent positions
  2. No stacking correlated assets (same base currency)
  3. If 2 trades in same directional group, 3rd must be different
  4. Volatility spike → reduce new trade approvals by 30%
"""

import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.position_distribution")


# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_CONCURRENT_POSITIONS = 3
MAX_SAME_DIRECTION_GROUP = 2        # max 2 positions in same currency group
VOLATILITY_REDUCTION_FACTOR = 0.7   # 30% fewer approvals when vol is high

# Currency group mapping (assets that move together)
CURRENCY_GROUPS = {
    "USD_STRENGTH": ["EURUSD", "GBPUSD"],      # USD pairs (inverse)
    "RISK_ON": ["BTCUSD", "ETHUSD", "BTC/USDT", "ETH/USDT"],  # crypto
    "SAFE_HAVEN": ["XAUUSD"],                    # gold
}

# Reverse mapping: symbol → group
SYMBOL_TO_GROUP: Dict[str, str] = {}
for group, symbols in CURRENCY_GROUPS.items():
    for sym in symbols:
        SYMBOL_TO_GROUP[sym] = group


# =============================================================================
# POSITION TRACKER
# =============================================================================

@dataclass
class OpenPosition:
    """Tracked open position."""
    symbol: str
    side: str
    group: str
    opened_at: str


from dataclasses import dataclass


@dataclass
class OpenPosition:
    symbol: str
    side: str
    group: str
    opened_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "group": self.group,
            "opened_at": self.opened_at,
        }


class PositionDistributionEngine:
    """
    Controls portfolio-level position distribution.
    Thread-safe.
    """

    def __init__(self):
        self._positions: Dict[str, OpenPosition] = {}
        self._lock = threading.Lock()
        self._high_volatility = False

    def set_high_volatility(self, is_high: bool) -> None:
        """Set volatility state (used by watchdog/heartbeat)."""
        with self._lock:
            if is_high != self._high_volatility:
                logger.info(f"DISTRIBUTION: volatility state → {'HIGH' if is_high else 'NORMAL'}")
            self._high_volatility = is_high

    def register_position(self, symbol: str, side: str) -> None:
        """Register a new open position."""
        group = SYMBOL_TO_GROUP.get(symbol, "OTHER")
        with self._lock:
            self._positions[symbol] = OpenPosition(
                symbol=symbol,
                side=side,
                group=group,
                opened_at=datetime.now(timezone.utc).isoformat(),
            )
        logger.info(f"DISTRIBUTION: registered {side} {symbol} (group={group})")

    def close_position(self, symbol: str) -> None:
        """Remove a closed position."""
        with self._lock:
            if symbol in self._positions:
                del self._positions[symbol]
        logger.info(f"DISTRIBUTION: closed {symbol}")

    def can_open_position(self, symbol: str, side: str) -> Tuple[bool, str]:
        """
        Check if a new position can be opened.

        Returns:
            (allowed, reason)
        """
        with self._lock:
            # 1. Max concurrent positions
            current_count = len(self._positions)

            # Volatility reduction: effectively lower the limit
            effective_max = MAX_CONCURRENT_POSITIONS
            if self._high_volatility:
                effective_max = max(1, int(MAX_CONCURRENT_POSITIONS * VOLATILITY_REDUCTION_FACTOR))

            if current_count >= effective_max:
                return False, (
                    f"MAX_POSITIONS_REACHED: {current_count}/{effective_max} "
                    f"{'(vol-reduced)' if self._high_volatility else ''}"
                )

            # 2. Already have this symbol
            if symbol in self._positions:
                return False, f"ALREADY_OPEN: {symbol} already has a position"

            # 3. Check same-group concentration
            new_group = SYMBOL_TO_GROUP.get(symbol, "OTHER")
            group_count = sum(
                1 for p in self._positions.values()
                if p.group == new_group and new_group != "OTHER"
            )
            if group_count >= MAX_SAME_DIRECTION_GROUP:
                existing = [
                    p.symbol for p in self._positions.values()
                    if p.group == new_group
                ]
                return False, (
                    f"GROUP_CONCENTRATION: {new_group} already has "
                    f"{group_count} positions ({', '.join(existing)}). "
                    f"Diversify into a different sector."
                )

        return True, "DISTRIBUTION_OK"

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        with self._lock:
            return [p.to_dict() for p in self._positions.values()]

    def get_status(self) -> Dict[str, Any]:
        """Get distribution status."""
        with self._lock:
            groups = defaultdict(int)
            for p in self._positions.values():
                groups[p.group] += 1

            return {
                "open_positions": len(self._positions),
                "max_positions": MAX_CONCURRENT_POSITIONS,
                "high_volatility": self._high_volatility,
                "effective_max": max(1, int(
                    MAX_CONCURRENT_POSITIONS * VOLATILITY_REDUCTION_FACTOR
                )) if self._high_volatility else MAX_CONCURRENT_POSITIONS,
                "group_distribution": dict(groups),
                "positions": [p.to_dict() for p in self._positions.values()],
            }


# =============================================================================
# SINGLETON
# =============================================================================

_engine: Optional[PositionDistributionEngine] = None


def get_distribution_engine() -> PositionDistributionEngine:
    global _engine
    if _engine is None:
        _engine = PositionDistributionEngine()
    return _engine
