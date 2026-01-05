"""
NEXUS Risk Governor - Axelrod Discipline Module
=================================================

Implements institutional-grade risk management:
1. Max drawdown enforcement with Firestore persistence
2. Position size governance with Kelly Criterion
3. Correlation limits across positions
4. Emergency shutdown with audit logging
5. Circuit breaker integration

Based on Axelrod's game theory principles:
- Cooperation (follow rules) yields long-term survival
- Defection (break limits) leads to capital destruction
"""

"""
NEXUS Risk Governor - Axelrod Discipline Module
================================================

Implements institutional-grade risk management:
1. Max drawdown enforcement with Firestore persistence
2. Position size governance with Kelly Criterion
3. Correlation limits across positions
4. Emergency shutdown with audit logging
5. Circuit breaker integration

Based on Axelrod's game theory principles:
- Cooperation (follow rules) yields long-term survival
- Defection (break limits) leads to capital destruction
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Attempt Firestore import (optional for local dev)
try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False

logger = logging.getLogger("nexus.risk_governor")


class RiskLevel(Enum):
    """Risk level classifications."""
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class RiskState:
    """Persistent risk state - stored in Firestore."""
    peak_equity: float = 10000.0
    current_equity: float = 10000.0
    initial_equity: float = 10000.0
    
    # Limits
    max_drawdown_limit: float = 0.02  # 2% hard limit
    warning_drawdown: float = 0.01    # 1% warning threshold
    max_position_size_pct: float = 0.05  # 5% per position
    max_total_exposure_pct: float = 0.20  # 20% total
    max_correlation: float = 0.70     # 70% correlation limit
    
    # State flags
    trading_enabled: bool = True
    circuit_breaker_active: bool = False
    risk_level: str = "NORMAL"
    
    # Tracking
    consecutive_losses: int = 0
    max_consecutive_losses: int = 5
    last_updated: str = ""
    
    # Open positions for correlation tracking
    open_positions: Dict[str, Any] = field(default_factory=dict)


class FirestoreStateManager:
    """
    Manages risk state persistence in Firestore.
    Falls back to in-memory state if Firestore unavailable.
    """
    
    COLLECTION = "nexus_risk_state"
    DOCUMENT = "global_state"
    
    def __init__(self, project_id: str = "nexus-dyron-777"):
        self.project_id = project_id
        self._db = None
        self._state: Optional[RiskState] = None
        
    @property
    def db(self):
        """Lazy initialize Firestore client."""
        if self._db is None and FIRESTORE_AVAILABLE:
            try:
                self._db = firestore.Client(project=self.project_id)
                logger.info("Firestore client initialized")
            except Exception as e:
                logger.warning(f"Firestore unavailable: {e}. Using in-memory state.")
        return self._db
    
    def load_state(self) -> RiskState:
        """Load state from Firestore or initialize default."""
        if self._state is not None:
            return self._state
        
        if self.db:
            try:
                doc = self.db.collection(self.COLLECTION).document(self.DOCUMENT).get()
                if doc.exists:
                    data = doc.to_dict()
                    self._state = RiskState(**{k: v for k, v in data.items() if hasattr(RiskState, k)})
                    logger.info("Loaded risk state from Firestore")
                    return self._state
            except Exception as e:
                logger.error(f"Failed to load state from Firestore: {e}")
        
        # Default state
        self._state = RiskState()
        logger.info("Initialized default risk state")
        return self._state
    
    def save_state(self, state: RiskState) -> bool:
        """Persist state to Firestore."""
        state.last_updated = datetime.now(timezone.utc).isoformat()
        self._state = state
        
        if self.db:
            try:
                data = {
                    "peak_equity": state.peak_equity,
                    "current_equity": state.current_equity,
                    "initial_equity": state.initial_equity,
                    "max_drawdown_limit": state.max_drawdown_limit,
                    "warning_drawdown": state.warning_drawdown,
                    "max_position_size_pct": state.max_position_size_pct,
                    "max_total_exposure_pct": state.max_total_exposure_pct,
                    "max_correlation": state.max_correlation,
                    "trading_enabled": state.trading_enabled,
                    "circuit_breaker_active": state.circuit_breaker_active,
                    "risk_level": state.risk_level,
                    "consecutive_losses": state.consecutive_losses,
                    "max_consecutive_losses": state.max_consecutive_losses,
                    "last_updated": state.last_updated,
                    "open_positions": state.open_positions
                }
                self.db.collection(self.COLLECTION).document(self.DOCUMENT).set(data)
                logger.debug("Risk state persisted to Firestore")
                return True
            except Exception as e:
                logger.error(f"Failed to save state to Firestore: {e}")
        
        return False


# Global state manager
_state_manager = FirestoreStateManager()


def _get_state() -> RiskState:
    """Get current risk state."""
    return _state_manager.load_state()


def _save_state(state: RiskState):
    """Save risk state."""
    _state_manager.save_state(state)


# =============================================================================
# DRAWDOWN CALCULATIONS
# =============================================================================
def calculate_drawdown() -> float:
    """
    Calculate current drawdown.
    DD = (PeakValue - CurrentValue) / PeakValue
    """
    state = _get_state()
    if state.peak_equity <= 0:
        return 0.0
    return (state.peak_equity - state.current_equity) / state.peak_equity


def calculate_total_pnl() -> float:
    """Calculate total P&L from initial equity."""
    state = _get_state()
    if state.initial_equity <= 0:
        return 0.0
    return (state.current_equity - state.initial_equity) / state.initial_equity


# =============================================================================
# KELLY CRITERION POSITION SIZING
# =============================================================================
def kelly_position_size(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    kelly_fraction: float = 0.25  # Quarter Kelly for safety
) -> float:
    """
    Calculate optimal position size using Kelly Criterion.
    
    Kelly % = W - [(1-W) / R]
    Where:
        W = Win probability
        R = Win/Loss ratio
    
    Args:
        win_rate: Historical win rate (0-1)
        avg_win: Average winning trade size
        avg_loss: Average losing trade size
        kelly_fraction: Fraction of Kelly to use (default 25%)
    
    Returns:
        Optimal position size as fraction of equity
    """
    if avg_loss == 0:
        return 0.0
    
    r_ratio = avg_win / avg_loss
    kelly = win_rate - ((1 - win_rate) / r_ratio)
    
    # Apply fraction and limits
    position_size = max(0, kelly * kelly_fraction)
    
    state = _get_state()
    max_size = state.max_position_size_pct
    
    return min(position_size, max_size)


# =============================================================================
# CORRELATION LIMITS
# =============================================================================
def check_correlation_limit(
    new_symbol: str,
    asset_correlations: Dict[str, Dict[str, float]]
) -> Tuple[bool, str]:
    """
    Check if adding a new position would violate correlation limits.
    
    Args:
        new_symbol: Symbol to add
        asset_correlations: Dict of symbol -> {other_symbol: correlation}
    
    Returns:
        (is_allowed, message)
    """
    state = _get_state()
    
    if new_symbol in state.open_positions:
        # Already have this position, allow adjustment
        return True, "Position adjustment allowed"
    
    # Check correlations with existing positions
    high_correlations = []
    
    for existing_symbol in state.open_positions.keys():
        if new_symbol in asset_correlations and existing_symbol in asset_correlations[new_symbol]:
            corr = asset_correlations[new_symbol][existing_symbol]
            if abs(corr) > state.max_correlation:
                high_correlations.append((existing_symbol, corr))
    
    if high_correlations:
        details = ", ".join([f"{s}({c:.2f})" for s, c in high_correlations])
        return False, f"CORRELATION_LIMIT_EXCEEDED: {details}"
    
    return True, "Correlation check passed"


# =============================================================================
# MAIN VALIDATION FUNCTION
# =============================================================================
def validate_trade(
    symbol: str,
    quantity: float,
    price: float,
    atr_data: Optional[Dict[str, float]] = None,
    strategy_confidence: float = 0.5
) -> Tuple[bool, str]:
    """
    The Survival Filter: Validates trade parameters against risk limits.
    
    Checks:
    1. Trading enabled
    2. Circuit breaker status
    3. Drawdown limit
    4. Position size limit
    5. Total exposure limit
    6. Volatility check (ATR)
    7. Consecutive loss check
    
    Args:
        symbol: Trading symbol
        quantity: Position size
        price: Current price
        atr_data: Optional ATR data for volatility check
        strategy_confidence: Signal confidence from strategy engine
    
    Returns:
        (is_allowed, reason_message)
    """
    state = _get_state()
    
    # 1. Trading Enabled Check
    if not state.trading_enabled:
        return False, "TRADING_DISABLED_BY_GOVERNOR"
    
    # 2. Circuit Breaker Check
    if state.circuit_breaker_active:
        return False, "CIRCUIT_BREAKER_ACTIVE"
    
    # 3. Drawdown Check
    current_dd = calculate_drawdown()
    if current_dd > state.max_drawdown_limit:
        state.trading_enabled = False
        state.risk_level = RiskLevel.SHUTDOWN.value
        _save_state(state)
        logger.critical(f"MAX DRAWDOWN EXCEEDED: {current_dd:.2%}. SYSTEM SHUTDOWN.")
        return False, "MAX_DRAWDOWN_EXCEEDED"
    
    if current_dd > state.warning_drawdown:
        state.risk_level = RiskLevel.ELEVATED.value
        logger.warning(f"DRAWDOWN WARNING: {current_dd:.2%} approaching limit")
    
    # 4. Position Size Check
    notional_value = quantity * price
    max_position_value = state.current_equity * state.max_position_size_pct
    if notional_value > max_position_value:
        logger.warning(f"POSITION SIZE EXPOSURE: {notional_value} > {max_position_value}. REDUCING SIZE REQUIRED.")
        return False, f"MAX_POSITION_SIZE_EXCEEDED: Max allowed ${max_position_value:.2f}"
    
    # 5. Total Exposure Check
    current_exposure = sum(
        pos.get("notional", 0) for pos in state.open_positions.values()
    )
    if (current_exposure + notional_value) > state.current_equity * state.max_total_exposure_pct:
        return False, "MAX_TOTAL_EXPOSURE_EXCEEDED"
    
    # 6. Volatility Check (ATR)
    if atr_data:
        current_atr = atr_data.get("current_atr", 0)
        normal_atr = atr_data.get("normal_atr", 0)
        if normal_atr > 0 and current_atr > (3 * normal_atr):
            state.risk_level = RiskLevel.CRITICAL.value
            state.circuit_breaker_active = True
            _save_state(state)
            logger.critical("EXCESSIVE VOLATILITY (3x ATR). CIRCUIT BREAKER ARMED.")
            return False, "VOLATILITY_ANOMALY_DETECTED"
    
    # 7. Consecutive Loss Check
    if state.consecutive_losses >= state.max_consecutive_losses:
        state.risk_level = RiskLevel.ELEVATED.value
        _save_state(state)
        logger.warning(f"CONSECUTIVE LOSSES: {state.consecutive_losses}. Reducing exposure.")
        # Allow trade but flag for reduced size
        return True, f"RISK_VALIDATED_WITH_CAUTION: {state.consecutive_losses} consecutive losses"
    
    # 8. Low Confidence Filter
    if strategy_confidence < 0.4:
        return False, f"CONFIDENCE_TOO_LOW: {strategy_confidence:.2f}"
    
    _save_state(state)
    return True, "RISK_VALIDATED"


# =============================================================================
# EQUITY MANAGEMENT
# =============================================================================
def update_equity(new_equity: float):
    """
    Updates the governor state with new equity values.
    
    Args:
        new_equity: Current account equity
    """
    state = _get_state()
    
    old_equity = state.current_equity
    state.current_equity = new_equity
    
    # Track consecutive losses
    if new_equity < old_equity:
        state.consecutive_losses += 1
    else:
        state.consecutive_losses = 0
    
    # Update peak
    if new_equity > state.peak_equity:
        state.peak_equity = new_equity
        state.risk_level = RiskLevel.NORMAL.value
        logger.info(f"NEW PEAK EQUITY: ${new_equity:,.2f}")
    
    # Update risk level based on drawdown
    dd = calculate_drawdown()
    if dd > state.max_drawdown_limit:
        state.risk_level = RiskLevel.SHUTDOWN.value
        state.trading_enabled = False
    elif dd > state.warning_drawdown:
        state.risk_level = RiskLevel.ELEVATED.value
    else:
        state.risk_level = RiskLevel.NORMAL.value
    
    _save_state(state)
    logger.info(f"Equity updated: ${new_equity:,.2f} | DD: {dd:.2%} | Risk: {state.risk_level}")


def record_trade_result(symbol: str, pnl: float, is_win: bool):
    """
    Record trade result for tracking.
    """
    state = _get_state()
    
    if is_win:
        state.consecutive_losses = 0
    else:
        state.consecutive_losses += 1
        
        if state.consecutive_losses >= state.max_consecutive_losses:
            logger.warning(f"LOSS STREAK: {state.consecutive_losses} consecutive losses!")
    
    _save_state(state)


def register_position(symbol: str, quantity: float, price: float, side: str):
    """Register an open position for tracking."""
    state = _get_state()
    state.open_positions[symbol] = {
        "quantity": quantity,
        "entry_price": price,
        "side": side,
        "notional": quantity * price,
        "opened_at": datetime.now(timezone.utc).isoformat()
    }
    _save_state(state)


def close_position(symbol: str):
    """Remove a position from tracking."""
    state = _get_state()
    if symbol in state.open_positions:
        del state.open_positions[symbol]
        _save_state(state)


# =============================================================================
# EMERGENCY CONTROLS
# =============================================================================
def emergency_shutdown(reason: str = "Manual trigger"):
    """
    Emergency shutdown - disables all trading.
    """
    state = _get_state()
    state.trading_enabled = False
    state.risk_level = RiskLevel.SHUTDOWN.value
    state.circuit_breaker_active = True
    _save_state(state)
    
    logger.critical(f"EMERGENCY SHUTDOWN: {reason}")
    
    return {
        "status": "SHUTDOWN",
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def reset_circuit_breaker(admin_key: str):
    """
    Reset circuit breaker - requires admin confirmation.
    """
    # In production, verify admin_key against Secret Manager
    if not admin_key:
        return {"error": "Admin key required"}
    
    state = _get_state()
    
    # Only reset if drawdown is acceptable
    dd = calculate_drawdown()
    if dd > state.max_drawdown_limit:
        return {"error": "Cannot reset - drawdown still exceeds limit"}
    
    state.circuit_breaker_active = False
    state.trading_enabled = True
    state.risk_level = RiskLevel.NORMAL.value
    _save_state(state)
    
    logger.info("CIRCUIT BREAKER RESET by admin")
    return {"status": "RESET", "trading_enabled": True}


def get_risk_status() -> Dict[str, Any]:
    """
    Get current risk status for dashboard display.
    """
    state = _get_state()
    dd = calculate_drawdown()
    total_pnl = calculate_total_pnl()
    
    return {
        "risk_level": state.risk_level,
        "trading_enabled": state.trading_enabled,
        "circuit_breaker_active": state.circuit_breaker_active,
        "drawdown": {
            "current": round(dd * 100, 2),
            "warning_threshold": round(state.warning_drawdown * 100, 2),
            "max_limit": round(state.max_drawdown_limit * 100, 2)
        },
        "equity": {
            "current": round(state.current_equity, 2),
            "peak": round(state.peak_equity, 2),
            "initial": round(state.initial_equity, 2)
        },
        "total_pnl_pct": round(total_pnl * 100, 2),
        "consecutive_losses": state.consecutive_losses,
        "open_positions_count": len(state.open_positions),
        "last_updated": state.last_updated
    }


# =============================================================================
# COMPATIBILITY - Maintain existing interface
# =============================================================================
# Global state for backward compatibility
STATE = {
    "peak_equity": 10000.0,
    "current_equity": 10000.0,
    "max_drawdown_limit": 0.02,
    "max_position_size_pct": 0.05,
    "trading_enabled": True
}


def _sync_legacy_state():
    """Sync legacy STATE dict with new state system."""
    state = _get_state()
    STATE["peak_equity"] = state.peak_equity
    STATE["current_equity"] = state.current_equity
    STATE["max_drawdown_limit"] = state.max_drawdown_limit
    STATE["max_position_size_pct"] = state.max_position_size_pct
    STATE["trading_enabled"] = state.trading_enabled
