"""
NEXUS Structured Logger — Phase 7, Part 5
============================================

Institutional-grade structured logging.

Output files:
  logs/system.log   — general system events
  logs/trades.log   — all trade decisions and executions
  logs/errors.log   — errors and exceptions only
  logs/health.log   — health check reports

Every log entry includes:
  - timestamp (ISO 8601 UTC)
  - module (source module name)
  - severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - message (human-readable)
  - context data (structured JSON)

No print statements allowed. Structured logging only.
"""

import json
import logging
import logging.handlers
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================
LOG_DIR = os.environ.get("NEXUS_LOG_DIR", "logs")
MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024  # 10MB per file
LOG_BACKUP_COUNT = 5                    # keep 5 rotated files
LOG_FORMAT = "%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


# =============================================================================
# STRUCTURED LOG FORMATTER
# =============================================================================

class StructuredFormatter(logging.Formatter):
    """
    Formats log records as structured entries.

    Output: timestamp<TAB>module<TAB>severity<TAB>message<TAB>context_json
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        module = record.name
        severity = record.levelname
        message = record.getMessage()

        # Extract context data if present
        context = {}
        if hasattr(record, "context_data") and record.context_data:
            context = record.context_data

        parts = [timestamp, module, severity, message]
        if context:
            parts.append(json.dumps(context, default=str))

        return "\t".join(parts)


# =============================================================================
# STRUCTURED LOGGER SETUP
# =============================================================================

_initialized = False
_init_lock = threading.Lock()


def initialize_structured_logging() -> None:
    """
    Initialize institutional-grade structured logging.

    Creates log directory and configures handlers for:
      - system.log (all INFO+ events)
      - trades.log (trade-specific events)
      - errors.log (ERROR+ events only)
      - health.log (health check events)

    Safe to call multiple times — only initializes once.
    """
    global _initialized

    with _init_lock:
        if _initialized:
            return

        # Create log directory
        os.makedirs(LOG_DIR, exist_ok=True)

        formatter = StructuredFormatter()

        # ── system.log — all system events (INFO+) ───────────
        system_handler = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "system.log"),
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=LOG_BACKUP_COUNT,
        )
        system_handler.setLevel(logging.INFO)
        system_handler.setFormatter(formatter)

        # ── trades.log — trade-specific events ───────────────
        trades_handler = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "trades.log"),
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=LOG_BACKUP_COUNT,
        )
        trades_handler.setLevel(logging.INFO)
        trades_handler.setFormatter(formatter)

        # ── errors.log — errors and exceptions only ──────────
        errors_handler = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "errors.log"),
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=LOG_BACKUP_COUNT,
        )
        errors_handler.setLevel(logging.ERROR)
        errors_handler.setFormatter(formatter)

        # ── health.log — health check events ─────────────────
        health_handler = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "health.log"),
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=LOG_BACKUP_COUNT,
        )
        health_handler.setLevel(logging.INFO)
        health_handler.setFormatter(formatter)

        # Attach handlers to appropriate loggers
        root_logger = logging.getLogger()
        root_logger.addHandler(system_handler)
        root_logger.addHandler(errors_handler)

        # Trade-specific loggers
        for name in [
            "nexus.sovereign_pipeline",
            "nexus.execution",
            "nexus.risk_governor",
            "nexus.broker_validator",
            "nexus.capital_protection",
            "nexus.execution_verifier",
        ]:
            trade_logger = logging.getLogger(name)
            trade_logger.addHandler(trades_handler)

        # Health-specific loggers
        for name in [
            "nexus.health_monitor",
            "nexus.system_health",
            "nexus.heartbeat",
            "nexus.auto_recovery",
            "nexus.fail_safe",
        ]:
            health_logger = logging.getLogger(name)
            health_logger.addHandler(health_handler)

        _initialized = True


# =============================================================================
# STRUCTURED LOG HELPER
# =============================================================================

class StructuredLog:
    """
    Helper for writing structured log entries with context data.

    Usage:
        slog = StructuredLog("nexus.trades")
        slog.info("Trade executed", {"symbol": "EURUSD", "lot": 0.1})
        slog.error("Trade failed", {"symbol": "GBPUSD", "error": "timeout"})
    """

    def __init__(self, logger_name: str):
        self._logger = logging.getLogger(logger_name)

    def _log(self, level: int, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        record = self._logger.makeRecord(
            name=self._logger.name,
            level=level,
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        if context:
            record.context_data = context
        else:
            record.context_data = {}
        self._logger.handle(record)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.DEBUG, message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.INFO, message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.WARNING, message, context)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.ERROR, message, context)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.CRITICAL, message, context)


# =============================================================================
# PRE-BUILT STRUCTURED LOGGERS
# =============================================================================

def get_system_log() -> StructuredLog:
    """Get structured logger for system events."""
    return StructuredLog("nexus.system")


def get_trade_log() -> StructuredLog:
    """Get structured logger for trade events."""
    return StructuredLog("nexus.sovereign_pipeline")


def get_error_log() -> StructuredLog:
    """Get structured logger for error events."""
    return StructuredLog("nexus.errors")


def get_health_log() -> StructuredLog:
    """Get structured logger for health events."""
    return StructuredLog("nexus.health_monitor")
