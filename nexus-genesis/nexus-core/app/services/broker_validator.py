"""
NEXUS Broker Validator — MT5 Live Safety Layer
================================================

Phase 4, Part A: Broker Hardening

1. Connection Validator — confirm account, broker, type, leverage, flags
2. Spread Filter — reject if spread > dynamic ATR-based threshold
3. Slippage Guard — reject if execution price deviates beyond threshold
4. Margin Check — verify free margin before sending order
5. Trade Frequency Guard — max trades/hour, per-symbol cooldowns
"""

import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.broker_validator")


# =============================================================================
# CONFIGURATION
# =============================================================================
EXPECTED_BROKER = os.environ.get("NEXUS_EXPECTED_BROKER", "")  # e.g. "FxPro"
MAX_SPREAD_ATR_RATIO = 0.10       # spread must be < 10% of ATR
MAX_SPREAD_PRICE_PCT = 0.05       # absolute cap: spread < 0.05% of price
MAX_SLIPPAGE_PCT = 0.10           # 0.10% max slippage
MIN_MARGIN_SAFETY_RATIO = 1.5     # free margin >= 1.5x required margin
MAX_TRADES_PER_HOUR = 20          # global hard cap
MAX_TRADES_PER_SYMBOL_PER_HOUR = 5
SYMBOL_COOLDOWN_SECS = 30         # minimum seconds between trades on same symbol


# =============================================================================
# BROKER CONNECTION VALIDATOR
# =============================================================================
@dataclass
class BrokerInfo:
    """Snapshot of broker account state."""
    connected: bool = False
    login: Optional[int] = None
    broker_name: str = ""
    account_type: str = ""      # "demo" or "live"
    leverage: int = 0
    trading_allowed: bool = False
    balance: float = 0.0
    equity: float = 0.0
    free_margin: float = 0.0
    currency: str = "USD"
    validated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "login": self.login,
            "broker_name": self.broker_name,
            "account_type": self.account_type,
            "leverage": self.leverage,
            "trading_allowed": self.trading_allowed,
            "balance": self.balance,
            "equity": self.equity,
            "free_margin": self.free_margin,
            "currency": self.currency,
            "validated_at": self.validated_at,
        }


def validate_broker_connection() -> Tuple[bool, List[str], BrokerInfo]:
    """
    Validate MT5 broker connection on startup.

    Checks:
      - Account login succeeds
      - Broker name matches expected (if configured)
      - Account type is detected (demo/live)
      - Leverage is within acceptable range
      - Trading is allowed on this account

    Returns:
        (all_ok, list_of_issues, BrokerInfo)
    """
    issues: List[str] = []
    info = BrokerInfo()

    try:
        import MetaTrader5 as mt5
    except ImportError:
        issues.append("MT5_NOT_AVAILABLE: MetaTrader5 package not installed (Windows only)")
        logger.warning("MT5 not available — broker validation skipped (non-Windows environment)")
        info.validated_at = datetime.now(timezone.utc).isoformat()
        return True, issues, info  # Allow startup on non-Windows (mock/paper mode)

    # Attempt connection
    from app.services import vault
    try:
        login = int(vault.get_secret("MT5_LOGIN"))
        password = vault.get_secret("MT5_PASSWORD")
        server = vault.get_secret("MT5_SERVER")
    except Exception as e:
        issues.append(f"MT5_CREDENTIALS_MISSING: {e}")
        return False, issues, info

    if not mt5.initialize(login=login, password=password, server=server):
        error = mt5.last_error()
        issues.append(f"MT5_CONNECTION_FAILED: {error}")
        return False, issues, info

    info.connected = True

    # Account info
    account = mt5.account_info()
    if account is None:
        issues.append("MT5_ACCOUNT_INFO_UNAVAILABLE")
        mt5.shutdown()
        return False, issues, info

    info.login = account.login
    info.broker_name = account.company
    info.leverage = account.leverage
    info.trading_allowed = account.trade_allowed
    info.balance = account.balance
    info.equity = account.equity
    info.free_margin = account.margin_free
    info.currency = account.currency
    info.validated_at = datetime.now(timezone.utc).isoformat()

    # Detect account type from server name or trade mode
    server_lower = server.lower()
    if "demo" in server_lower:
        info.account_type = "demo"
    elif "live" in server_lower or "real" in server_lower:
        info.account_type = "live"
    else:
        info.account_type = "unknown"

    # Validate broker name
    if EXPECTED_BROKER and EXPECTED_BROKER.lower() not in info.broker_name.lower():
        issues.append(
            f"BROKER_MISMATCH: expected '{EXPECTED_BROKER}', got '{info.broker_name}'"
        )

    # Validate trading allowed
    if not info.trading_allowed:
        issues.append("TRADING_NOT_ALLOWED: account flag trade_allowed=False")

    # Validate leverage is reasonable
    if info.leverage < 1 or info.leverage > 2000:
        issues.append(f"LEVERAGE_SUSPECT: {info.leverage} — verify account settings")

    # Don't shutdown MT5 here — leave it connected for the engine
    logger.info(
        f"Broker validated: {info.broker_name} | "
        f"Account: {info.login} ({info.account_type}) | "
        f"Leverage: 1:{info.leverage} | "
        f"Equity: ${info.equity:,.2f}"
    )

    all_ok = len(issues) == 0
    return all_ok, issues, info


# =============================================================================
# SPREAD FILTER
# =============================================================================

def check_spread(
    bid: float,
    ask: float,
    price: float,
    atr: Optional[float] = None,
) -> Tuple[bool, str]:
    """
    Check if current spread is acceptable.

    Rejects if:
      - spread > MAX_SPREAD_PRICE_PCT of price (absolute cap)
      - spread > MAX_SPREAD_ATR_RATIO of ATR (dynamic cap)

    Returns:
        (allowed, reason)
    """
    if bid <= 0 or ask <= 0 or ask < bid:
        return False, f"INVALID_QUOTE: bid={bid}, ask={ask}"

    spread = ask - bid
    spread_pct = (spread / price) * 100 if price > 0 else 999

    # Absolute cap
    if spread_pct > MAX_SPREAD_PRICE_PCT:
        return False, f"SPREAD_TOO_WIDE: {spread_pct:.4f}% > max {MAX_SPREAD_PRICE_PCT}%"

    # Dynamic ATR-based cap
    if atr and atr > 0:
        spread_atr_ratio = spread / atr
        if spread_atr_ratio > MAX_SPREAD_ATR_RATIO:
            return False, (
                f"SPREAD_VS_ATR_TOO_HIGH: spread/ATR = {spread_atr_ratio:.3f} "
                f"> max {MAX_SPREAD_ATR_RATIO}"
            )

    return True, f"SPREAD_OK: {spread_pct:.4f}%"


# =============================================================================
# SLIPPAGE GUARD
# =============================================================================

def check_slippage(
    requested_price: float,
    filled_price: float,
) -> Tuple[bool, float, str]:
    """
    Post-execution slippage check.

    Returns:
        (acceptable, slippage_pct, reason)
    """
    if requested_price <= 0:
        return True, 0.0, "NO_REQUESTED_PRICE"

    slippage_pct = abs(filled_price - requested_price) / requested_price * 100

    if slippage_pct > MAX_SLIPPAGE_PCT:
        return False, slippage_pct, (
            f"EXCESSIVE_SLIPPAGE: {slippage_pct:.4f}% > max {MAX_SLIPPAGE_PCT}%"
        )

    return True, slippage_pct, f"SLIPPAGE_OK: {slippage_pct:.4f}%"


# =============================================================================
# MARGIN CHECK
# =============================================================================

def check_margin(
    free_margin: float,
    required_margin: float,
) -> Tuple[bool, str]:
    """
    Pre-trade margin sufficiency check.

    Requires free_margin >= required_margin * MIN_MARGIN_SAFETY_RATIO.

    Returns:
        (sufficient, reason)
    """
    if required_margin <= 0:
        return True, "NO_MARGIN_REQUIRED"

    ratio = free_margin / required_margin if required_margin > 0 else 0
    if ratio < MIN_MARGIN_SAFETY_RATIO:
        return False, (
            f"INSUFFICIENT_MARGIN: free={free_margin:.2f}, "
            f"required={required_margin:.2f}, ratio={ratio:.2f} "
            f"< min {MIN_MARGIN_SAFETY_RATIO}"
        )

    return True, f"MARGIN_OK: ratio={ratio:.2f}"


def estimate_required_margin(
    symbol: str,
    quantity: float,
    price: float,
    leverage: int,
) -> float:
    """
    Estimate required margin for a trade.
    margin = (quantity * price) / leverage
    """
    if leverage <= 0:
        leverage = 1
    return (quantity * price) / leverage


# =============================================================================
# TRADE FREQUENCY GUARD
# =============================================================================

class TradeFrequencyGuard:
    """
    Prevents rapid-fire trade execution.

    Enforces:
      - Max N trades per hour (global)
      - Max N trades per symbol per hour
      - Minimum cooldown between trades on same symbol
    """

    def __init__(self):
        self._global_timestamps: List[float] = []
        self._symbol_timestamps: Dict[str, List[float]] = defaultdict(list)
        self._last_trade_time: Dict[str, float] = {}
        self._lock = threading.Lock()

    def check(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if a trade is allowed right now.

        Returns:
            (allowed, reason)
        """
        now = time.monotonic()
        one_hour_ago = now - 3600

        with self._lock:
            # Prune old timestamps
            self._global_timestamps = [
                t for t in self._global_timestamps if t > one_hour_ago
            ]
            self._symbol_timestamps[symbol] = [
                t for t in self._symbol_timestamps[symbol] if t > one_hour_ago
            ]

            # Global rate
            if len(self._global_timestamps) >= MAX_TRADES_PER_HOUR:
                return False, f"GLOBAL_RATE_LIMIT: {len(self._global_timestamps)}/{MAX_TRADES_PER_HOUR} trades/hour"

            # Per-symbol rate
            if len(self._symbol_timestamps[symbol]) >= MAX_TRADES_PER_SYMBOL_PER_HOUR:
                return False, (
                    f"SYMBOL_RATE_LIMIT: {symbol} has "
                    f"{len(self._symbol_timestamps[symbol])}/{MAX_TRADES_PER_SYMBOL_PER_HOUR} trades/hour"
                )

            # Cooldown
            last = self._last_trade_time.get(symbol, 0)
            elapsed = now - last
            if elapsed < SYMBOL_COOLDOWN_SECS:
                remaining = SYMBOL_COOLDOWN_SECS - elapsed
                return False, f"COOLDOWN: {symbol} has {remaining:.1f}s remaining"

        return True, "FREQUENCY_OK"

    def record_trade(self, symbol: str) -> None:
        """Record that a trade was executed."""
        now = time.monotonic()
        with self._lock:
            self._global_timestamps.append(now)
            self._symbol_timestamps[symbol].append(now)
            self._last_trade_time[symbol] = now

    def get_stats(self) -> Dict[str, Any]:
        """Get current trade frequency statistics."""
        now = time.monotonic()
        one_hour_ago = now - 3600
        with self._lock:
            global_count = sum(1 for t in self._global_timestamps if t > one_hour_ago)
            per_symbol = {
                sym: sum(1 for t in ts if t > one_hour_ago)
                for sym, ts in self._symbol_timestamps.items()
            }
        return {
            "trades_this_hour": global_count,
            "max_per_hour": MAX_TRADES_PER_HOUR,
            "per_symbol": per_symbol,
        }


# =============================================================================
# SINGLETON
# =============================================================================

_frequency_guard: Optional[TradeFrequencyGuard] = None


def get_frequency_guard() -> TradeFrequencyGuard:
    global _frequency_guard
    if _frequency_guard is None:
        _frequency_guard = TradeFrequencyGuard()
    return _frequency_guard
