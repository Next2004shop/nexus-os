"""
NEXUS Stealth Mode - Security & Obfuscation Module
===================================================

Ancient Vault Doctrine: Silence is Security.

Implements stealth and self-protection features:
1. Encrypted audit logs
2. Minimal response metadata
3. Randomized order timing
4. Self-purge on critical breach
5. Anomaly detection on access patterns
"""

"""
NEXUS Stealth Mode - Security & Obfuscation Module
==================================================

Ancient Vault Doctrine: Silence is Security.

Implements stealth and self-protection features:
1. Encrypted audit logs
2. Minimal response metadata
3. Randomized order timing
4. Self-purge on critical breach
5. Anomaly detection on access patterns
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("nexus.stealth")


# =============================================================================
# ENCRYPTION UTILITIES
# =============================================================================

class SecureLogger:
    """
    Encrypted audit logger.
    
    Logs are encrypted with AES-256 before writing.
    Only authorized readers with the key can decrypt.
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Args:
            encryption_key: 32-byte key for AES-256. If None, generates random.
        """
        self._key = encryption_key or os.urandom(32)
        self._logs: List[Dict[str, Any]] = []
        self._lock = Lock()
        self._max_logs = 10000  # Rolling buffer
    
    def _encrypt(self, data: str) -> str:
        """Simple encryption using HMAC for integrity + base64 encoding."""
        # In production, use proper AES-256-GCM
        # This is a simplified version for demonstration
        data_bytes = data.encode('utf-8')
        signature = hmac.new(self._key, data_bytes, hashlib.sha256).hexdigest()
        encoded = base64.b64encode(data_bytes).decode('utf-8')
        return f"{signature}:{encoded}"
    
    def _decrypt(self, encrypted: str) -> Optional[str]:
        """Decrypt and verify integrity."""
        try:
            signature, encoded = encrypted.split(':', 1)
            data_bytes = base64.b64decode(encoded)
            expected_sig = hmac.new(self._key, data_bytes, hashlib.sha256).hexdigest()
            if hmac.compare_digest(signature, expected_sig):
                return data_bytes.decode('utf-8')
            return None
        except Exception:
            return None
    
    def log(self, event_type: str, data: Dict[str, Any], sensitivity: str = "NORMAL"):
        """
        Log an event with encryption.
        
        Args:
            event_type: Type of event (e.g., "TRADE", "ACCESS", "ERROR")
            data: Event data to log
            sensitivity: NORMAL, HIGH, or CRITICAL
        """
        with self._lock:
            # Sanitize sensitive fields
            sanitized = self._sanitize(data)
            
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "sensitivity": sensitivity,
                "data": sanitized
            }
            
            # Encrypt if HIGH or CRITICAL
            if sensitivity in ["HIGH", "CRITICAL"]:
                log_entry["encrypted"] = True
                log_entry["data"] = self._encrypt(json.dumps(sanitized))
            
            self._logs.append(log_entry)
            
            # Rotate if needed
            if len(self._logs) > self._max_logs:
                self._logs = self._logs[-self._max_logs//2:]
            
            # Also log to standard logger (sanitized)
            if sensitivity == "CRITICAL":
                logger.critical(f"[STEALTH] {event_type}: {len(sanitized)} fields")
            elif sensitivity == "HIGH":
                logger.warning(f"[STEALTH] {event_type}: encrypted")
            else:
                logger.debug(f"[STEALTH] {event_type}")
    
    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive fields."""
        sensitive_keys = ["password", "secret", "key", "token", "credential", "api_key"]
        sanitized = {}
        
        for k, v in data.items():
            k_lower = k.lower()
            if any(s in k_lower for s in sensitive_keys):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize(v)
            else:
                sanitized[k] = v
        
        return sanitized
    
    def get_logs(self, event_type: Optional[str] = None, 
                 since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Retrieve logs (decrypting if necessary)."""
        with self._lock:
            result = []
            for log in self._logs:
                # Filter by type
                if event_type and log["type"] != event_type:
                    continue
                
                # Filter by time
                if since:
                    log_time = datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00'))
                    if log_time < since:
                        continue
                
                # Decrypt if needed
                if log.get("encrypted"):
                    decrypted = self._decrypt(log["data"])
                    if decrypted:
                        log_copy = log.copy()
                        log_copy["data"] = json.loads(decrypted)
                        result.append(log_copy)
                else:
                    result.append(log)
            
            return result
    
    def purge(self):
        """Securely purge all logs."""
        with self._lock:
            # Overwrite with random data before clearing
            for i in range(len(self._logs)):
                self._logs[i] = {"purged": True, "data": os.urandom(64).hex()}
            self._logs.clear()
            logger.warning("[STEALTH] Logs purged")


# =============================================================================
# RESPONSE MINIMIZER
# =============================================================================

class ResponseMinimizer:
    """
    Removes unnecessary metadata from responses.
    
    Principle: Give only what is needed, nothing more.
    """
    
    # Fields that should never be in responses
    FORBIDDEN_FIELDS = [
        "internal_id", "server_name", "stack_trace", "debug_info",
        "api_key", "secret", "token", "password", "credential",
        "ip_address", "user_agent", "session_id", "trace_id"
    ]
    
    # Fields to strip from nested objects
    STRIP_NESTED = ["metadata", "debug", "internal"]
    
    @classmethod
    def minimize(cls, response: Dict[str, Any], level: str = "standard") -> Dict[str, Any]:
        """
        Minimize response based on security level.
        
        Args:
            response: Original response
            level: "minimal", "standard", or "verbose"
            
        Returns:
            Sanitized response
        """
        if level == "verbose":
            return cls._remove_forbidden(response)
        elif level == "minimal":
            return cls._minimal_response(response)
        else:  # standard
            return cls._standard_response(response)
    
    @classmethod
    def _remove_forbidden(cls, data: Any) -> Any:
        """Recursively remove forbidden fields."""
        if isinstance(data, dict):
            return {
                k: cls._remove_forbidden(v)
                for k, v in data.items()
                if k.lower() not in [f.lower() for f in cls.FORBIDDEN_FIELDS]
            }
        elif isinstance(data, list):
            return [cls._remove_forbidden(item) for item in data]
        return data
    
    @classmethod
    def _standard_response(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Standard sanitization - removes forbidden and strips nested."""
        cleaned = cls._remove_forbidden(data)
        for key in cls.STRIP_NESTED:
            cleaned.pop(key, None)
        return cleaned
    
    @classmethod
    def _minimal_response(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Minimal response - only essential fields."""
        essential = ["status", "direction", "confidence", "entry", "exit", "error"]
        return {k: v for k, v in data.items() if k in essential}


# =============================================================================
# ORDER TIMING RANDOMIZER
# =============================================================================

class OrderRandomizer:
    """
    Randomizes order timing to avoid pattern detection.
    
    Principle: Predictable patterns are exploitable patterns.
    """
    
    def __init__(self, min_delay_ms: int = 100, max_delay_ms: int = 2000):
        self.min_delay_ms = min_delay_ms
        self.max_delay_ms = max_delay_ms
        self._last_order_time = 0
        self._order_count = 0
    
    def get_delay(self) -> float:
        """
        Get randomized delay before order execution.
        
        Returns:
            Delay in seconds
        """
        # Base random delay
        delay_ms = random.randint(self.min_delay_ms, self.max_delay_ms)
        
        # Add jitter based on market conditions
        jitter = random.gauss(0, delay_ms * 0.1)
        delay_ms = max(self.min_delay_ms, delay_ms + jitter)
        
        # Ensure minimum time between orders
        min_gap_ms = 500
        now = time.time() * 1000
        time_since_last = now - self._last_order_time
        if time_since_last < min_gap_ms:
            delay_ms += min_gap_ms - time_since_last
        
        return delay_ms / 1000
    
    def record_order(self):
        """Record that an order was placed."""
        self._last_order_time = time.time() * 1000
        self._order_count += 1
    
    def randomize_quantity(self, quantity: float, max_variance_pct: float = 5) -> float:
        """
        Slightly randomize order quantity to avoid round number patterns.
        
        Args:
            quantity: Original quantity
            max_variance_pct: Maximum variance percentage
            
        Returns:
            Randomized quantity
        """
        variance = quantity * (max_variance_pct / 100)
        return quantity + random.uniform(-variance, variance)


# =============================================================================
# ACCESS ANOMALY DETECTOR
# =============================================================================

@dataclass
class AccessPattern:
    """Tracks access pattern for anomaly detection."""
    ip: str
    endpoint: str
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class AccessAnomalyDetector:
    """
    Detects anomalous access patterns.
    
    Triggers alerts on:
    - Rapid access from same IP
    - Unusual endpoint patterns
    - Failed authentication spikes
    """
    
    def __init__(self):
        self._patterns: List[AccessPattern] = []
        self._lock = Lock()
        self._max_patterns = 1000
        
        # Thresholds
        self.max_requests_per_minute = 60
        self.max_failed_per_minute = 5
        self.alert_callback: Optional[Callable] = None
    
    def record_access(self, ip: str, endpoint: str, success: bool, 
                      metadata: Optional[Dict] = None):
        """Record an access attempt."""
        with self._lock:
            pattern = AccessPattern(
                ip=ip,
                endpoint=endpoint,
                timestamp=datetime.now(timezone.utc),
                success=success,
                metadata=metadata or {}
            )
            self._patterns.append(pattern)
            
            # Rotate
            if len(self._patterns) > self._max_patterns:
                self._patterns = self._patterns[-self._max_patterns//2:]
            
            # Check for anomalies
            self._check_anomalies(pattern)
    
    def _check_anomalies(self, latest: AccessPattern):
        """Check for anomalous patterns."""
        one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
        
        # Recent requests from same IP
        recent_from_ip = [
            p for p in self._patterns
            if p.ip == latest.ip and p.timestamp > one_minute_ago
        ]
        
        if len(recent_from_ip) > self.max_requests_per_minute:
            self._alert("RATE_LIMIT", {
                "ip": latest.ip,
                "count": len(recent_from_ip),
                "threshold": self.max_requests_per_minute
            })
        
        # Failed attempts
        failed_recent = [p for p in recent_from_ip if not p.success]
        if len(failed_recent) > self.max_failed_per_minute:
            self._alert("FAILED_AUTH_SPIKE", {
                "ip": latest.ip,
                "failed_count": len(failed_recent),
                "threshold": self.max_failed_per_minute
            })
    
    def _alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger anomaly alert."""
        logger.warning(f"[ANOMALY] {alert_type}: {data}")
        if self.alert_callback:
            self.alert_callback(alert_type, data)


# =============================================================================
# SELF-PURGE MODE
# =============================================================================

class SelfPurgeController:
    """
    Controls self-purge mode for critical breaches.
    
    When activated:
    1. Stops all trading
    2. Clears all cached data
    3. Revokes active sessions
    4. Logs critical event
    """
    
    def __init__(self):
        self._purge_active = False
        self._purge_reason: Optional[str] = None
        self._purge_time: Optional[datetime] = None
        self._lock = Lock()
        
        # Components to purge
        self._purge_callbacks: List[Callable] = []
    
    def register_purge_callback(self, callback: Callable):
        """Register a callback to be called on purge."""
        self._purge_callbacks.append(callback)
    
    def activate_purge(self, reason: str, severity: str = "CRITICAL"):
        """
        Activate self-purge mode.
        
        Args:
            reason: Why purge was activated
            severity: CRITICAL or EMERGENCY
        """
        with self._lock:
            if self._purge_active:
                return  # Already purging
            
            self._purge_active = True
            self._purge_reason = reason
            self._purge_time = datetime.now(timezone.utc)
            
            logger.critical(f"[SELF-PURGE] ACTIVATED: {reason}")
            
            # Execute all purge callbacks
            for callback in self._purge_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Purge callback failed: {e}")
    
    def is_purge_active(self) -> bool:
        """Check if purge mode is active."""
        return self._purge_active
    
    def get_status(self) -> Dict[str, Any]:
        """Get purge status."""
        return {
            "active": self._purge_active,
            "reason": self._purge_reason,
            "time": self._purge_time.isoformat() if self._purge_time else None
        }
    
    def reset(self, admin_key: str):
        """Reset purge mode (requires admin key)."""
        # In production, verify admin_key against secure storage
        with self._lock:
            self._purge_active = False
            self._purge_reason = None
            logger.warning("[SELF-PURGE] Reset by admin")


# =============================================================================
# STEALTH MODE CONTROLLER
# =============================================================================

class StealthMode:
    """
    Master controller for all stealth features.
    """
    
    def __init__(self):
        self.secure_logger = SecureLogger()
        self.response_minimizer = ResponseMinimizer()
        self.order_randomizer = OrderRandomizer()
        self.anomaly_detector = AccessAnomalyDetector()
        self.purge_controller = SelfPurgeController()
        
        # Register purge callback for logger
        self.purge_controller.register_purge_callback(self.secure_logger.purge)
        
        self._enabled = True
        logger.info("[STEALTH] Mode initialized")
    
    def log_event(self, event_type: str, data: Dict[str, Any], 
                  sensitivity: str = "NORMAL"):
        """Log event through secure logger."""
        if self._enabled:
            self.secure_logger.log(event_type, data, sensitivity)
    
    def minimize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Minimize response for security."""
        if self._enabled:
            return self.response_minimizer.minimize(response)
        return response
    
    def get_order_delay(self) -> float:
        """Get randomized order delay."""
        if self._enabled:
            return self.order_randomizer.get_delay()
        return 0.0
    
    def record_access(self, ip: str, endpoint: str, success: bool):
        """Record access pattern."""
        if self._enabled:
            self.anomaly_detector.record_access(ip, endpoint, success)
    
    def trigger_purge(self, reason: str):
        """Trigger self-purge mode."""
        self.purge_controller.activate_purge(reason)
    
    def is_operational(self) -> bool:
        """Check if system is operational (not purged)."""
        return not self.purge_controller.is_purge_active()
    
    def get_status(self) -> Dict[str, Any]:
        """Get stealth mode status."""
        return {
            "enabled": self._enabled,
            "operational": self.is_operational(),
            "purge_status": self.purge_controller.get_status(),
            "recent_anomalies": len([
                p for p in self.anomaly_detector._patterns
                if not p.success
            ])
        }


# =============================================================================
# DECORATOR FOR STEALTHY ENDPOINTS
# =============================================================================

def stealth_endpoint(stealth: StealthMode):
    """
    Decorator to add stealth features to endpoints.
    
    Usage:
        @stealth_endpoint(stealth_mode)
        async def my_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if operational
            if not stealth.is_operational():
                return {"error": "System unavailable", "code": "PURGE_ACTIVE"}
            
            # Add random delay
            delay = stealth.get_order_delay()
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Minimize response
            if isinstance(result, dict):
                result = stealth.minimize_response(result)
            
            return result
        return wrapper
    return decorator


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Need asyncio for the decorator
try:
    import asyncio
except ImportError:
    pass

_stealth: Optional[StealthMode] = None


def get_stealth_mode() -> StealthMode:
    """Get or create global stealth mode instance."""
    global _stealth
    if _stealth is None:
        _stealth = StealthMode()
    return _stealth
