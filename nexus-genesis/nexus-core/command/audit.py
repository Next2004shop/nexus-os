"""
NEXUS Command Layer — Audit Logger
=====================================

Writes structured audit entries to nexus-core/logs/command_audit.json.
Auto-creates logs directory if missing.

Every command — valid or invalid — is logged for accountability.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger("nexus.command.audit")

# Audit log path (relative to nexus-core/)
AUDIT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
AUDIT_LOG_FILE = os.path.join(AUDIT_LOG_DIR, "command_audit.json")


def _ensure_log_dir():
    """Create logs directory if it doesn't exist."""
    if not os.path.exists(AUDIT_LOG_DIR):
        os.makedirs(AUDIT_LOG_DIR, exist_ok=True)
        logger.info(f"Created audit log directory: {AUDIT_LOG_DIR}")


def log_command(
    command: Dict[str, Any],
    validation_status: str,
    execution_status: str
) -> None:
    """
    Write an audit entry to the command audit log.
    
    Args:
        command: The TradeCommand as dict
        validation_status: "VALID" | "INVALID" | "ERROR"
        execution_status: "EXECUTED" | "BLOCKED" | "PENDING" | "FAILED"
    """
    _ensure_log_dir()

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "validation_status": validation_status,
        "execution_status": execution_status
    }

    try:
        # Read existing entries
        entries = []
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    entries = json.loads(content)

        # Append new entry
        entries.append(entry)

        # Write back
        with open(AUDIT_LOG_FILE, "w") as f:
            json.dump(entries, f, indent=2, default=str)

        logger.info(
            f"AUDIT: {validation_status} | {execution_status} | "
            f"{command.get('asset', '?')} {command.get('direction', '?')} "
            f"{command.get('lot_size', '?')}"
        )

    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")


def get_audit_log() -> list:
    """Read and return all audit entries."""
    _ensure_log_dir()
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            return json.loads(f.read())
    except Exception:
        return []
