"""
NEXUS Structured Logger
========================

Unified logging with deterministic format:
    timestamp | layer | action | status | error_code

File outputs:
    logs/system.log — all INFO+ messages (JSON)
    logs/error.log  — ERROR+ only (JSON with stack traces)

All NEXUS services must use this logger instead of raw logging.getLogger().
"""

import logging
import json
import os
import traceback
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

# =============================================================================
# LOG DIRECTORY (auto-created)
# =============================================================================
LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "logs"
)


def _ensure_log_dir():
    """Create logs directory if it doesn't exist."""
    os.makedirs(LOG_DIR, exist_ok=True)


# =============================================================================
# FORMATTERS
# =============================================================================

class NexusFormatter(logging.Formatter):
    """Structured log formatter: timestamp | layer | action | status | error_code"""
    
    def format(self, record: logging.LogRecord) -> str:
        layer = getattr(record, 'layer', 'SYSTEM')
        action = getattr(record, 'action', record.funcName or '-')
        status = getattr(record, 'status', 'INFO')
        error_code = getattr(record, 'error_code', None)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        parts = [timestamp, layer, action, status]
        if error_code:
            parts.append(f"ERR:{error_code}")
        
        structured = " | ".join(parts)
        return f"{structured} | {record.getMessage()}"


class NexusJSONFormatter(logging.Formatter):
    """JSON-structured log formatter for production with full schema."""
    
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "layer": getattr(record, 'layer', 'SYSTEM'),
            "action": getattr(record, 'action', record.funcName or '-'),
            "status": getattr(record, 'status', record.levelname),
            "message": record.getMessage(),
        }
        
        error_code = getattr(record, 'error_code', None)
        if error_code:
            entry["error_code"] = error_code
        
        # Stack trace on errors
        if record.exc_info and record.exc_info[1]:
            entry["stack_trace"] = ''.join(
                traceback.format_exception(*record.exc_info)
            )
        
        return json.dumps(entry)


# =============================================================================
# LAYER LOGGER
# =============================================================================

class NexusLayerLogger:
    """
    Layer-bound logger that automatically injects layer context.
    
    Usage:
        log = get_layer_logger("EXECUTION")
        log.info("Trade submitted", action="EXECUTE_TRADE", status="PENDING")
        log.error("Risk gate failed", action="RISK_CHECK", status="REJECTED", error_code="RISK_001")
    """
    
    def __init__(self, layer: str, logger_name: str):
        self._logger = logging.getLogger(logger_name)
        self._layer = layer
    
    def _log(self, level: int, msg: str, action: str = "-", status: str = "INFO", 
             error_code: Optional[str] = None, **kwargs):
        extra = {
            'layer': self._layer,
            'action': action,
            'status': status,
            'error_code': error_code,
        }
        self._logger.log(level, msg, extra=extra, **kwargs)
    
    def info(self, msg: str, action: str = "-", status: str = "OK", **kwargs):
        self._log(logging.INFO, msg, action=action, status=status, **kwargs)
    
    def warning(self, msg: str, action: str = "-", status: str = "WARN", 
                error_code: Optional[str] = None, **kwargs):
        self._log(logging.WARNING, msg, action=action, status=status, error_code=error_code, **kwargs)
    
    def error(self, msg: str, action: str = "-", status: str = "ERROR", 
              error_code: Optional[str] = None, **kwargs):
        self._log(logging.ERROR, msg, action=action, status=status, error_code=error_code, **kwargs)
    
    def critical(self, msg: str, action: str = "-", status: str = "CRITICAL", 
                 error_code: Optional[str] = None, **kwargs):
        self._log(logging.CRITICAL, msg, action=action, status=status, error_code=error_code, **kwargs)


# =============================================================================
# LAYER CONSTANTS
# =============================================================================
LAYER_INTERFACE = "INTERFACE"
LAYER_INTENT = "INTENT"
LAYER_RISK = "RISK"
LAYER_EXECUTION = "EXECUTION"
LAYER_SYSTEM = "SYSTEM"


def get_layer_logger(layer: str, name: Optional[str] = None) -> NexusLayerLogger:
    """
    Get a structured logger bound to a specific layer.
    
    Args:
        layer: One of INTERFACE, INTENT, RISK, EXECUTION, SYSTEM
        name: Optional logger name (defaults to nexus.{layer.lower()})
    
    Returns:
        NexusLayerLogger with layer context auto-injected
    """
    logger_name = name or f"nexus.{layer.lower()}"
    return NexusLayerLogger(layer, logger_name)


def configure_nexus_logging(json_format: bool = True):
    """
    Configure root NEXUS logging with file + console handlers.
    
    Creates:
        logs/system.log — all INFO+ messages (10MB rotate, 5 backups)
        logs/error.log  — ERROR+ only (5MB rotate, 5 backups)
        Console          — pipe-delimited dev format
    
    Call once at startup (in main.py startup_event).
    """
    _ensure_log_dir()
    
    nexus_root = logging.getLogger("nexus")
    nexus_root.handlers.clear()
    nexus_root.setLevel(logging.INFO)
    nexus_root.propagate = False
    
    # --- Console handler (dev-friendly pipe format) ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(NexusFormatter())
    console_handler.setLevel(logging.INFO)
    nexus_root.addHandler(console_handler)
    
    # --- system.log (all INFO+, JSON, rotating) ---
    system_log_path = os.path.join(LOG_DIR, "system.log")
    system_handler = RotatingFileHandler(
        system_log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    system_handler.setFormatter(NexusJSONFormatter())
    system_handler.setLevel(logging.INFO)
    nexus_root.addHandler(system_handler)
    
    # --- error.log (ERROR+ only, JSON with stack traces, rotating) ---
    error_log_path = os.path.join(LOG_DIR, "error.log")
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setFormatter(NexusJSONFormatter())
    error_handler.setLevel(logging.ERROR)
    nexus_root.addHandler(error_handler)
    
    nexus_root.info("Structured logging initialized", extra={
        'layer': 'SYSTEM', 'action': 'LOGGING_INIT', 'status': 'OK', 'error_code': None
    })
