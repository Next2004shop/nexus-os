"""
NEXUS Session Intelligence — Phase 6, Part D
==============================================

Market session awareness for strategy suitability.

Sessions (UTC):
  - Asia:        00:00–08:00 UTC
  - London:      07:00–16:00 UTC
  - New York:    12:00–21:00 UTC
  - Overlap L/NY: 12:00–16:00 UTC (highest liquidity)

Adjustments:
  - Avoid breakouts in low-liquidity hours (Asia-only for forex)
  - Favor momentum during London/NY overlap
  - Crypto trades allowed 24/7 (no session restriction)
  - Log session performance for review
"""

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.session")


# =============================================================================
# SESSION DEFINITIONS
# =============================================================================

class MarketSession(Enum):
    ASIA = "ASIA"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    OVERLAP_LN = "OVERLAP_LONDON_NY"
    OFF_HOURS = "OFF_HOURS"


# Session windows (UTC hours)
SESSION_WINDOWS = {
    MarketSession.ASIA:       (0, 8),
    MarketSession.LONDON:     (7, 16),
    MarketSession.NEW_YORK:   (12, 21),
    MarketSession.OVERLAP_LN: (12, 16),
}

# Assets exempt from session restrictions (trade 24/7)
SESSION_EXEMPT = {"BTCUSD", "ETHUSD", "BTC/USDT", "ETH/USDT"}

# Strategy suitability per session
SESSION_STRATEGY = {
    MarketSession.ASIA: {
        "suitability": "LOW",
        "preferred_strategies": ["range", "mean_reversion"],
        "avoid": ["breakout", "momentum"],
        "description": "Low liquidity. Avoid breakouts. Tight ranges expected.",
    },
    MarketSession.LONDON: {
        "suitability": "HIGH",
        "preferred_strategies": ["breakout", "trend_following", "momentum"],
        "avoid": [],
        "description": "High liquidity. Breakouts and trends are viable.",
    },
    MarketSession.NEW_YORK: {
        "suitability": "HIGH",
        "preferred_strategies": ["momentum", "trend_following"],
        "avoid": [],
        "description": "Strong momentum. Follow established trends.",
    },
    MarketSession.OVERLAP_LN: {
        "suitability": "HIGHEST",
        "preferred_strategies": ["breakout", "momentum", "trend_following"],
        "avoid": [],
        "description": "Peak liquidity. Best conditions for execution.",
    },
    MarketSession.OFF_HOURS: {
        "suitability": "VERY_LOW",
        "preferred_strategies": [],
        "avoid": ["all"],
        "description": "Off-hours. No forex trades recommended.",
    },
}


# =============================================================================
# SESSION DETECTOR
# =============================================================================

def get_current_session() -> MarketSession:
    """Determine the current market session based on UTC time."""
    hour = datetime.now(timezone.utc).hour

    # Check overlap first (most specific)
    if 12 <= hour < 16:
        return MarketSession.OVERLAP_LN
    elif 7 <= hour < 16:
        return MarketSession.LONDON
    elif 12 <= hour < 21:
        return MarketSession.NEW_YORK
    elif 0 <= hour < 8:
        return MarketSession.ASIA
    else:
        return MarketSession.OFF_HOURS


def get_session_at_hour(hour: int) -> MarketSession:
    """Get session for a specific UTC hour."""
    if 12 <= hour < 16:
        return MarketSession.OVERLAP_LN
    elif 7 <= hour < 16:
        return MarketSession.LONDON
    elif 12 <= hour < 21:
        return MarketSession.NEW_YORK
    elif 0 <= hour < 8:
        return MarketSession.ASIA
    else:
        return MarketSession.OFF_HOURS


# =============================================================================
# SESSION FILTER
# =============================================================================

def check_session_suitability(
    symbol: str,
    strategy_type: str = "momentum",
) -> Tuple[bool, str, MarketSession]:
    """
    Check if the current session is suitable for trading this symbol.

    Args:
        symbol: Trading symbol
        strategy_type: Type of strategy (momentum, breakout, range, etc.)

    Returns:
        (suitable, reason, current_session)
    """
    session = get_current_session()

    # Crypto is exempt from session restrictions
    if symbol in SESSION_EXEMPT:
        return True, f"SESSION_EXEMPT: {symbol} trades 24/7", session

    config = SESSION_STRATEGY.get(session, SESSION_STRATEGY[MarketSession.OFF_HOURS])

    # Check if strategy is in the avoid list
    if "all" in config["avoid"]:
        return False, (
            f"SESSION_UNSUITABLE: {session.value} — off-hours, "
            f"no forex trades recommended"
        ), session

    if strategy_type.lower() in config["avoid"]:
        return False, (
            f"SESSION_STRATEGY_MISMATCH: {strategy_type} not suitable "
            f"during {session.value}"
        ), session

    # Check suitability level
    if config["suitability"] in ("LOW", "VERY_LOW"):
        return False, (
            f"SESSION_LOW_SUITABILITY: {session.value} ({config['suitability']}). "
            f"{config['description']}"
        ), session

    return True, f"SESSION_OK: {session.value} ({config['suitability']})", session


# =============================================================================
# SESSION PERFORMANCE TRACKER
# =============================================================================

class SessionPerformanceTracker:
    """Tracks trade performance per session for analysis."""

    def __init__(self):
        self._lock = threading.Lock()
        self._records: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0}
        )

    def record_trade(self, session: MarketSession, pnl: float) -> None:
        """Record a trade result for a session."""
        with self._lock:
            key = session.value
            self._records[key]["trades"] += 1
            if pnl >= 0:
                self._records[key]["wins"] += 1
            else:
                self._records[key]["losses"] += 1
            self._records[key]["total_pnl"] += pnl

    def get_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance breakdown by session."""
        with self._lock:
            result = {}
            for session, data in self._records.items():
                result[session] = {
                    **data,
                    "win_rate": round(
                        data["wins"] / data["trades"] * 100, 1
                    ) if data["trades"] > 0 else 0,
                    "total_pnl": round(data["total_pnl"], 2),
                }
            return result

    def get_session_context_for_ai(self) -> str:
        """Format session context for AI prompt."""
        session = get_current_session()
        config = SESSION_STRATEGY.get(session, {})
        perf = self.get_performance()
        session_perf = perf.get(session.value, {})

        lines = [
            f"CURRENT SESSION: {session.value}",
            f"  Suitability: {config.get('suitability', 'UNKNOWN')}",
            f"  Description: {config.get('description', '')}",
            f"  Preferred: {', '.join(config.get('preferred_strategies', []))}",
        ]
        if session_perf:
            lines.append(
                f"  Historical: {session_perf.get('trades', 0)} trades, "
                f"{session_perf.get('win_rate', 0):.0f}% WR, "
                f"${session_perf.get('total_pnl', 0):+,.2f}"
            )
        return "\n".join(lines)


# =============================================================================
# SINGLETON
# =============================================================================

_tracker: Optional[SessionPerformanceTracker] = None


def get_session_tracker() -> SessionPerformanceTracker:
    global _tracker
    if _tracker is None:
        _tracker = SessionPerformanceTracker()
    return _tracker
