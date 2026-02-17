"""
NEXUS Security Event Logger — Phase 11 (K)
============================================

Dedicated security event logging to /logs/security_events.log

Events logged:
    - Unauthorized access attempts
    - Capital lock events
    - Execution mismatches
    - State corruption detections
    - Latency breaches
    - Failsafe mode transitions
    - Position shadow mismatches
    - Broker validation failures

Format: JSON lines, each entry with timestamp, severity, category, and details.
"""

import json
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(_BASE_DIR, "logs")
SECURITY_LOG_PATH = os.path.join(LOGS_DIR, "security_events.log")

os.makedirs(LOGS_DIR, exist_ok=True)


class SecurityEventCategory(str, Enum):
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    CAPITAL_LOCK = "CAPITAL_LOCK"
    EXECUTION_MISMATCH = "EXECUTION_MISMATCH"
    STATE_CORRUPTION = "STATE_CORRUPTION"
    LATENCY_BREACH = "LATENCY_BREACH"
    FAILSAFE_TRANSITION = "FAILSAFE_TRANSITION"
    POSITION_MISMATCH = "POSITION_MISMATCH"
    BROKER_VALIDATION = "BROKER_VALIDATION"
    DUPLICATE_EXECUTION = "DUPLICATE_EXECUTION"
    RACE_CONDITION = "RACE_CONDITION"
    SECRET_VIOLATION = "SECRET_VIOLATION"
    STARTUP_FAILURE = "STARTUP_FAILURE"
    TELEGRAM_AUTH = "TELEGRAM_AUTH"
    DISASTER_RECOVERY = "DISASTER_RECOVERY"


class SecuritySeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class SecurityLogger:
    """
    Dedicated security event logger.
    Writes structured JSON events to /logs/security_events.log.
    """

    _instance = None

    def __init__(self):
        self._logger = logging.getLogger("nexus.security")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        if not self._logger.handlers:
            handler = RotatingFileHandler(
                SECURITY_LOG_PATH,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=10,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)

            console = logging.StreamHandler()
            console.setLevel(logging.WARNING)
            console.setFormatter(logging.Formatter(
                "%(asctime)s | SECURITY | %(message)s"
            ))
            self._logger.addHandler(console)

    @classmethod
    def get_instance(cls) -> "SecurityLogger":
        if cls._instance is None:
            cls._instance = SecurityLogger()
        return cls._instance

    def log(
        self,
        category: SecurityEventCategory,
        severity: SecuritySeverity,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        source: str = "UNKNOWN",
    ):
        """Log a security event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity.value,
            "category": category.value,
            "source": source,
            "message": message,
        }
        if details:
            entry["details"] = details

        line = json.dumps(entry, default=str)
        level = {
            SecuritySeverity.INFO: logging.INFO,
            SecuritySeverity.WARNING: logging.WARNING,
            SecuritySeverity.CRITICAL: logging.CRITICAL,
            SecuritySeverity.EMERGENCY: logging.CRITICAL,
        }.get(severity, logging.INFO)

        self._logger.log(level, line)

    def info(self, category: SecurityEventCategory, message: str, **kwargs):
        self.log(category, SecuritySeverity.INFO, message, **kwargs)

    def warning(self, category: SecurityEventCategory, message: str, **kwargs):
        self.log(category, SecuritySeverity.WARNING, message, **kwargs)

    def critical(self, category: SecurityEventCategory, message: str, **kwargs):
        self.log(category, SecuritySeverity.CRITICAL, message, **kwargs)

    def emergency(self, category: SecurityEventCategory, message: str, **kwargs):
        self.log(category, SecuritySeverity.EMERGENCY, message, **kwargs)


def get_security_logger() -> SecurityLogger:
    return SecurityLogger.get_instance()
