"""
NEXUS AI Audit Logger — Hedge-Fund Grade Audit Trail
=====================================================

Every AI output must log:
  - raw_prompt
  - ai_response
  - parsed_json
  - validation_result
  - execution_result
  - timestamp

This builds an immutable, queryable audit trail for
regulatory compliance and post-incident analysis.

Storage: in-memory ring buffer (configurable max size)
         + structured log emission for external sinks.
"""

import logging
import threading
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.ai_audit")

# Maximum audit entries kept in memory before rolling
MAX_AUDIT_ENTRIES = 5000


# =============================================================================
# AUDIT ENTRY
# =============================================================================

@dataclass
class AuditEntry:
    """Single audit record for one AI decision cycle."""
    entry_id: str
    timestamp: str
    raw_prompt: str
    ai_response: str
    parsed_json: Optional[Dict[str, Any]]
    validation_result: Dict[str, Any]
    confidence_gate: Optional[str]
    execution_result: Optional[Dict[str, Any]]
    system_mode: str
    user_id: Optional[str] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# AUDIT LOGGER
# =============================================================================

class AIAuditLogger:
    """
    Thread-safe, in-memory ring-buffer audit logger.

    Every AI decision cycle creates exactly one AuditEntry.
    Entries are also emitted via Python logging for external sinks.
    """

    def __init__(self, max_entries: int = MAX_AUDIT_ENTRIES):
        self._entries: deque = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        self._counter = 0
        logger.info(f"AI Audit Logger initialized (max_entries={max_entries})")

    # ── Record ───────────────────────────────────────────────────────────
    def record(
        self,
        raw_prompt: str,
        ai_response: str,
        parsed_json: Optional[Dict[str, Any]],
        validation_result: Dict[str, Any],
        confidence_gate: Optional[str],
        execution_result: Optional[Dict[str, Any]],
        system_mode: str,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> AuditEntry:
        """Create and store one audit entry."""
        with self._lock:
            self._counter += 1
            entry_id = f"AUDIT-{self._counter:08d}"

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_prompt=raw_prompt[:2000],          # cap prompt size
            ai_response=ai_response[:5000],        # cap response size
            parsed_json=parsed_json,
            validation_result=validation_result,
            confidence_gate=confidence_gate,
            execution_result=execution_result,
            system_mode=system_mode,
            user_id=user_id,
            duration_ms=duration_ms,
        )

        with self._lock:
            self._entries.append(entry)

        # Emit structured log for external aggregation (ELK, BigQuery, etc.)
        logger.info(
            "AI_AUDIT_RECORD",
            extra={
                "audit_entry_id": entry_id,
                "intent": parsed_json.get("intent") if parsed_json else None,
                "asset": parsed_json.get("asset") if parsed_json else None,
                "confidence": parsed_json.get("confidence_score") if parsed_json else None,
                "gate": confidence_gate,
                "validation_ok": validation_result.get("valid", False),
                "executed": execution_result is not None,
                "mode": system_mode,
            },
        )
        return entry

    # ── Query ────────────────────────────────────────────────────────────
    def get_recent(self, n: int = 20) -> List[Dict[str, Any]]:
        """Return the last N audit entries."""
        with self._lock:
            entries = list(self._entries)
        return [e.to_dict() for e in entries[-n:]]

    def get_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Lookup a single entry by ID."""
        with self._lock:
            for entry in self._entries:
                if entry.entry_id == entry_id:
                    return entry.to_dict()
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Summary statistics for the audit trail."""
        with self._lock:
            entries = list(self._entries)

        total = len(entries)
        if total == 0:
            return {"total_entries": 0}

        valid_count = sum(1 for e in entries if e.validation_result.get("valid"))
        executed_count = sum(1 for e in entries if e.execution_result is not None)
        gate_counts = {}
        for e in entries:
            g = e.confidence_gate or "none"
            gate_counts[g] = gate_counts.get(g, 0) + 1

        return {
            "total_entries": total,
            "valid_intents": valid_count,
            "executed_trades": executed_count,
            "rejected": total - valid_count,
            "confidence_gate_distribution": gate_counts,
        }

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._entries)


# =============================================================================
# SINGLETON
# =============================================================================

_audit_logger: Optional[AIAuditLogger] = None


def get_ai_audit_logger() -> AIAuditLogger:
    """Get or create the singleton AI audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AIAuditLogger()
    return _audit_logger
