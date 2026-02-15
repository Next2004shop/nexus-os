"""
NEXUS Structured Logger
========================

Unified logging with deterministic format:
    timestamp | layer | action | status | error_code

All NEXUS services must use this logger instead of raw logging.getLogger().
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class NexusFormatter(logging.Formatter):
    """Structured log formatter: timestamp | layer | action | status | error_code"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Extract NEXUS-specific fields injected via extra={}
        layer = getattr(record, 'layer', 'SYSTEM')
        action = getattr(record, 'action', record.funcName or '-')
        status = getattr(record, 'status', 'INFO')
        error_code = getattr(record, 'error_code', None)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        parts = [timestamp, layer, action, status]
        if error_code:
            parts.append(f"ERR:{error_code}")
        
        structured = " | ".join(parts)
        
        # Append the actual message
        return f"{structured} | {record.getMessage()}"


class NexusJSONFormatter(logging.Formatter):
    """JSON-structured log formatter for production."""
    
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": getattr(record, 'layer', 'SYSTEM'),
            "action": getattr(record, 'action', record.funcName or '-'),
            "status": getattr(record, 'status', record.levelname),
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        error_code = getattr(record, 'error_code', None)
        if error_code:
            entry["error_code"] = error_code
        
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = str(record.exc_info[1])
        
        return json.dumps(entry)


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


def configure_nexus_logging(json_format: bool = False):
    """
    Configure root NEXUS logging with structured formatter.
    
    Call once at startup (e.g., in main.py lifespan).
    
    Args:
        json_format: If True, use JSON format (production). Otherwise pipe-delimited (dev).
    """
    formatter = NexusJSONFormatter() if json_format else NexusFormatter()
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # Configure all nexus.* loggers
    nexus_root = logging.getLogger("nexus")
    nexus_root.handlers.clear()
    nexus_root.addHandler(handler)
    nexus_root.setLevel(logging.INFO)
    nexus_root.propagate = False
