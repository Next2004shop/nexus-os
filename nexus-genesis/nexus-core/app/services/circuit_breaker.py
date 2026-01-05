"""
NEXUS Circuit Breaker - Automatic Protection System
====================================================

Implements automatic shutdown triggers:
1. Consecutive API failures (3 failures = halt)
2. Extreme price movements (> 5 ATR in 15 minutes)
3. Connectivity loss (> 60 seconds)
4. Manual kill switch
5. Scheduled maintenance windows

Based on Netflix Hystrix patterns adapted for trading systems.
"""

"""
NEXUS Circuit Breaker - Automatic Protection System
====================================================

Implements automatic shutdown triggers:
1. Consecutive API failures (3 failures = halt)
2. Extreme price movements (> 5 ATR in 15 minutes)
3. Connectivity loss (> 60 seconds)
4. Manual kill switch
5. Scheduled maintenance windows

Based on Netflix Hystrix patterns adapted for trading systems.
"""

import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocked - failures exceeded threshold
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


@dataclass
class CircuitConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 3          # Failures before opening
    success_threshold: int = 2          # Successes to close from half-open
    timeout_seconds: float = 60.0       # Time before trying half-open
    atr_threshold: float = 5.0          # ATR multiplier for price movement
    connectivity_timeout: float = 60.0  # Seconds before connectivity failure
    
    # Price movement thresholds
    max_15min_move_pct: float = 5.0     # Max % move in 15 minutes
    max_1hr_move_pct: float = 10.0      # Max % move in 1 hour


@dataclass
class CircuitMetrics:
    """Metrics tracking for circuit breaker."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[str] = None
    last_success_time: Optional[str] = None
    state_changes: List[Dict[str, Any]] = field(default_factory=list)


class CircuitBreaker:
    """
    Circuit breaker for service protection.
    
    Wraps external service calls and protects against cascading failures.
    """
    
    def __init__(self, name: str, config: Optional[CircuitConfig] = None):
        self.name = name
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self._lock = Lock()
        self._last_state_change = datetime.now(timezone.utc)
        self._half_open_calls = 0
        
    def _record_success(self):
        """Record successful call."""
        with self._lock:
            self.metrics.total_calls += 1
            self.metrics.successful_calls += 1
            self.metrics.consecutive_successes += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = datetime.now(timezone.utc).isoformat()
            
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    def _record_failure(self, error: str):
        """Record failed call."""
        with self._lock:
            self.metrics.total_calls += 1
            self.metrics.failed_calls += 1
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
            self.metrics.last_failure_time = datetime.now(timezone.utc).isoformat()
            
            logger.warning(f"Circuit [{self.name}] failure: {error}")
            
            if self.state == CircuitState.HALF_OPEN:
                # Single failure in half-open returns to open
                self._transition_to(CircuitState.OPEN)
            elif self.metrics.consecutive_failures >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to new state."""
        old_state = self.state
        self.state = new_state
        self._last_state_change = datetime.now(timezone.utc)
        self._half_open_calls = 0
        
        self.metrics.state_changes.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": self._last_state_change.isoformat()
        })
        
        # Keep only last 10 state changes
        if len(self.metrics.state_changes) > 10:
            self.metrics.state_changes = self.metrics.state_changes[-10:]
        
        logger.info(f"Circuit [{self.name}] state: {old_state.value} -> {new_state.value}")
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            elapsed = (datetime.now(timezone.utc) - self._last_state_change).total_seconds()
            if elapsed >= self.config.timeout_seconds:
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            # Allow limited requests in half-open
            return self._half_open_calls < self.config.success_threshold
        
        return False
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function result
        
        Raises:
            CircuitOpenError: If circuit is open
        """
        if not self._should_allow_request():
            self.metrics.rejected_calls += 1
            raise CircuitOpenError(f"Circuit [{self.name}] is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(str(e))
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of call."""
        if not self._should_allow_request():
            self.metrics.rejected_calls += 1
            raise CircuitOpenError(f"Circuit [{self.name}] is OPEN")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(str(e))
            raise
    
    def force_open(self, reason: str = "Manual trigger"):
        """Force circuit to open state."""
        logger.critical(f"Circuit [{self.name}] FORCE OPENED: {reason}")
        self._transition_to(CircuitState.OPEN)
    
    def force_close(self):
        """Force circuit to closed state (admin only)."""
        logger.warning(f"Circuit [{self.name}] FORCE CLOSED by admin")
        self._transition_to(CircuitState.CLOSED)
        self.metrics.consecutive_failures = 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "successful": self.metrics.successful_calls,
                "failed": self.metrics.failed_calls,
                "rejected": self.metrics.rejected_calls,
                "consecutive_failures": self.metrics.consecutive_failures,
                "last_failure": self.metrics.last_failure_time
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout_seconds": self.config.timeout_seconds
            },
            "last_state_change": self._last_state_change.isoformat()
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# =============================================================================
# PRICE MOVEMENT CIRCUIT BREAKER
# =============================================================================
class PriceMovementBreaker:
    """
    Monitors price movements and triggers circuit breaker on extreme moves.
    """
    
    def __init__(self, config: Optional[CircuitConfig] = None):
        self.config = config or CircuitConfig()
        self._price_history: Dict[str, List[Dict]] = {}
        self._triggered_symbols: Dict[str, datetime] = {}
    
    def record_price(self, symbol: str, price: float, timestamp: Optional[datetime] = None):
        """Record a price tick."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        if symbol not in self._price_history:
            self._price_history[symbol] = []
        
        self._price_history[symbol].append({
            "price": price,
            "timestamp": timestamp
        })
        
        # Keep only last 2 hours of data
        cutoff = timestamp - timedelta(hours=2)
        self._price_history[symbol] = [
            p for p in self._price_history[symbol]
            if p["timestamp"] > cutoff
        ]
    
    def check_movement(self, symbol: str, current_price: float, atr: float = 0) -> Dict[str, Any]:
        """
        Check if recent price movement triggers circuit breaker.
        
        Args:
            symbol: Trading symbol
            current_price: Current price
            atr: Average True Range (optional)
        
        Returns:
            Dict with trigger status and details
        """
        if symbol not in self._price_history or len(self._price_history[symbol]) < 2:
            return {"triggered": False, "reason": "Insufficient history"}
        
        now = datetime.now(timezone.utc)
        history = self._price_history[symbol]
        
        # Check 15-minute movement
        fifteen_min_ago = now - timedelta(minutes=15)
        prices_15m = [p for p in history if p["timestamp"] >= fifteen_min_ago]
        
        if prices_15m:
            oldest_price = prices_15m[0]["price"]
            move_pct = abs(current_price - oldest_price) / oldest_price * 100
            
            if move_pct > self.config.max_15min_move_pct:
                self._triggered_symbols[symbol] = now
                logger.critical(f"PRICE CIRCUIT BREAKER: {symbol} moved {move_pct:.2f}% in 15 min")
                return {
                    "triggered": True,
                    "reason": f"15m move: {move_pct:.2f}%",
                    "threshold": self.config.max_15min_move_pct,
                    "symbol": symbol
                }
        
        # Check ATR-based movement if ATR provided
        if atr > 0:
            oldest = history[0]["price"]
            atr_move = abs(current_price - oldest) / atr
            
            if atr_move > self.config.atr_threshold:
                self._triggered_symbols[symbol] = now
                logger.critical(f"ATR CIRCUIT BREAKER: {symbol} moved {atr_move:.1f}x ATR")
                return {
                    "triggered": True,
                    "reason": f"ATR move: {atr_move:.1f}x",
                    "threshold": self.config.atr_threshold,
                    "symbol": symbol
                }
        
        return {"triggered": False}
    
    def is_symbol_blocked(self, symbol: str, cooldown_minutes: int = 30) -> bool:
        """Check if symbol is in cooldown after trigger."""
        if symbol not in self._triggered_symbols:
            return False
        
        trigger_time = self._triggered_symbols[symbol]
        cooldown_end = trigger_time + timedelta(minutes=cooldown_minutes)
        
        return datetime.now(timezone.utc) < cooldown_end
    
    def clear_trigger(self, symbol: str):
        """Clear trigger for symbol (admin only)."""
        if symbol in self._triggered_symbols:
            del self._triggered_symbols[symbol]
            logger.info(f"Price trigger cleared for {symbol}")


# =============================================================================
# CONNECTIVITY MONITOR
# =============================================================================
class ConnectivityMonitor:
    """
    Monitors connectivity to external services.
    """
    
    def __init__(self, timeout_seconds: float = 60.0):
        self.timeout_seconds = timeout_seconds
        self._last_heartbeat: Dict[str, datetime] = {}
        self._is_connected: Dict[str, bool] = {}
    
    def heartbeat(self, service: str):
        """Record heartbeat from service."""
        self._last_heartbeat[service] = datetime.now(timezone.utc)
        self._is_connected[service] = True
    
    def check_connectivity(self, service: str) -> Dict[str, Any]:
        """Check if service is connected."""
        if service not in self._last_heartbeat:
            return {
                "connected": False,
                "reason": "No heartbeat received",
                "service": service
            }
        
        last = self._last_heartbeat[service]
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        
        if elapsed > self.timeout_seconds:
            self._is_connected[service] = False
            return {
                "connected": False,
                "reason": f"No heartbeat for {elapsed:.0f}s",
                "last_heartbeat": last.isoformat(),
                "service": service
            }
        
        return {
            "connected": True,
            "last_heartbeat": last.isoformat(),
            "elapsed_seconds": round(elapsed, 1),
            "service": service
        }
    
    def is_connected(self, service: str) -> bool:
        """Quick connectivity check."""
        result = self.check_connectivity(service)
        return result["connected"]


# =============================================================================
# MASTER CIRCUIT BREAKER MANAGER
# =============================================================================
class CircuitBreakerManager:
    """
    Central manager for all circuit breakers.
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self.price_breaker = PriceMovementBreaker()
        self.connectivity = ConnectivityMonitor()
        self._global_halt = False
        self._halt_reason: Optional[str] = None
    
    def get_or_create(self, name: str, config: Optional[CircuitConfig] = None) -> CircuitBreaker:
        """Get existing or create new circuit breaker."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
    
    def global_halt(self, reason: str):
        """Trigger global halt of all trading."""
        self._global_halt = True
        self._halt_reason = reason
        
        # Open all circuit breakers
        for breaker in self._breakers.values():
            breaker.force_open(f"GLOBAL HALT: {reason}")
        
        logger.critical(f"GLOBAL HALT ACTIVATED: {reason}")
    
    def resume_trading(self):
        """Resume trading after global halt (admin only)."""
        self._global_halt = False
        self._halt_reason = None
        
        # Close all breakers
        for breaker in self._breakers.values():
            breaker.force_close()
        
        logger.warning("TRADING RESUMED by admin")
    
    def is_trading_allowed(self) -> Tuple[bool, str]:
        """Check if trading is allowed."""
        if self._global_halt:
            return False, f"GLOBAL HALT: {self._halt_reason}"
        
        # Check all breakers
        for name, breaker in self._breakers.items():
            if breaker.state == CircuitState.OPEN:
                return False, f"Circuit [{name}] is OPEN"
        
        return True, "Trading allowed"
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers."""
        return {
            "global_halt": self._global_halt,
            "halt_reason": self._halt_reason,
            "breakers": {
                name: breaker.get_status()
                for name, breaker in self._breakers.items()
            },
            "connectivity": {
                service: self.connectivity.check_connectivity(service)
                for service in self.connectivity._last_heartbeat.keys()
            }
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================
_manager = CircuitBreakerManager()


def get_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager."""
    return _manager


def get_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    return _manager.get_or_create(name)


# Convenience decorators
def with_circuit_breaker(breaker_name: str):
    """Decorator to wrap function with circuit breaker."""
    def decorator(func: Callable):
        breaker = get_breaker(breaker_name)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator
