"""
NEXUS Fail-Safe Protocols — Phase 7, Part 7
==============================================

Fail-safe protocols for critical system failures.

Monitors for:
  - Repeated execution failures
  - Position mismatch (MT5 vs registry)
  - Rapid unexpected losses
  - Desync between MT5 and registry
  - Corrupted state file

On ANY of these:
  - Freeze new trades
  - Log incident
  - Alert operator
  - Require manual reset

No autonomous resume. Human override required.
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.fail_safe")

# =============================================================================
# CONFIGURATION
# =============================================================================
MAX_CONSECUTIVE_EXEC_FAILURES = 3     # 3 failed executions → freeze
RAPID_LOSS_WINDOW_SECS = 300          # 5 minute window
RAPID_LOSS_COUNT_THRESHOLD = 3        # 3 losses in 5 min → freeze
RAPID_LOSS_TOTAL_PCT_THRESHOLD = 2.0  # 2% total loss in 5 min → freeze
POSITION_MISMATCH_TOLERANCE = 0       # zero tolerance for position desync
FAIL_SAFE_CHECK_INTERVAL_SECS = 30    # check every 30 seconds


# =============================================================================
# INCIDENT TYPES
# =============================================================================

@dataclass
class FailSafeIncident:
    """Record of a fail-safe incident."""
    incident_type: str
    description: str
    severity: str  # WARNING, CRITICAL
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_type": self.incident_type,
            "description": self.description,
            "severity": self.severity,
            "details": self.details,
            "resolved": self.resolved,
            "timestamp": self.timestamp,
        }


# =============================================================================
# FAIL-SAFE PROTOCOL ENGINE
# =============================================================================

class FailSafeProtocol:
    """
    Monitors for critical failures and enforces fail-safe freeze.

    Once triggered:
      - All new trades are blocked
      - Operator is alerted
      - System requires manual reset

    No autonomous resume.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._frozen: bool = False
        self._freeze_reason: str = ""
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        # Tracking
        self._consecutive_exec_failures: int = 0
        self._recent_losses: deque = deque(maxlen=50)  # (timestamp, pnl_pct)
        self._incidents: List[FailSafeIncident] = []
        self._total_incidents: int = 0

    # ── Trade Outcome Recording ──────────────────────────────────

    def record_execution_success(self) -> None:
        """Record a successful trade execution — resets failure counter."""
        with self._lock:
            self._consecutive_exec_failures = 0

    def record_execution_failure(self, symbol: str, error: str) -> None:
        """Record a failed trade execution."""
        with self._lock:
            self._consecutive_exec_failures += 1
            count = self._consecutive_exec_failures

        logger.warning(
            f"FAIL_SAFE: execution failure #{count} — {symbol}: {error}"
        )

        if count >= MAX_CONSECUTIVE_EXEC_FAILURES:
            self._trigger_freeze(
                "REPEATED_EXECUTION_FAILURES",
                f"{count} consecutive execution failures (latest: {symbol} — {error})",
                {"symbol": symbol, "error": error, "consecutive": count},
            )

    def record_trade_loss(self, pnl_pct: float) -> None:
        """Record a trade loss for rapid-loss detection."""
        now = time.monotonic()
        with self._lock:
            self._recent_losses.append((now, pnl_pct))

        self._check_rapid_losses()

    # ── Checks ───────────────────────────────────────────────────

    def _check_rapid_losses(self) -> None:
        """Check for rapid unexpected losses."""
        now = time.monotonic()
        cutoff = now - RAPID_LOSS_WINDOW_SECS

        with self._lock:
            recent = [(t, pnl) for t, pnl in self._recent_losses if t > cutoff and pnl < 0]

        if len(recent) >= RAPID_LOSS_COUNT_THRESHOLD:
            total_loss = sum(abs(pnl) for _, pnl in recent)
            if total_loss >= RAPID_LOSS_TOTAL_PCT_THRESHOLD:
                self._trigger_freeze(
                    "RAPID_UNEXPECTED_LOSSES",
                    f"{len(recent)} losses totaling {total_loss:.2f}% in {RAPID_LOSS_WINDOW_SECS}s",
                    {"loss_count": len(recent), "total_loss_pct": total_loss},
                )

    def check_position_mismatch(self) -> bool:
        """Check for position count mismatch between MT5 and registry."""
        try:
            import MetaTrader5 as mt5
            from app.services import risk_governor

            mt5_count = mt5.positions_total()
            state = risk_governor._get_state()
            registry_count = len(state.open_positions)

            if abs(mt5_count - registry_count) > POSITION_MISMATCH_TOLERANCE:
                self._trigger_freeze(
                    "POSITION_MISMATCH",
                    f"MT5 has {mt5_count} positions, registry has {registry_count}",
                    {"mt5_count": mt5_count, "registry_count": registry_count},
                )
                return True
        except ImportError:
            pass  # Non-Windows
        except Exception as e:
            logger.error(f"Position mismatch check error: {e}")

        return False

    def check_state_integrity(self) -> bool:
        """Check for corrupted state file."""
        try:
            from app.services import risk_governor
            state = risk_governor._get_state()

            # Basic integrity checks
            if state.current_equity < 0:
                self._trigger_freeze(
                    "CORRUPTED_STATE",
                    f"Negative equity detected: {state.current_equity}",
                    {"equity": state.current_equity},
                )
                return True

            if state.trading_enabled and state.current_equity == 0:
                self._trigger_freeze(
                    "CORRUPTED_STATE",
                    "Zero equity with trading enabled",
                    {"equity": 0, "trading_enabled": True},
                )
                return True

        except Exception as e:
            self._trigger_freeze(
                "STATE_READ_ERROR",
                f"Cannot read state registry: {e}",
                {"error": str(e)},
            )
            return True

        return False

    def check_mt5_desync(self) -> bool:
        """Check for desync between MT5 account and internal state."""
        try:
            import MetaTrader5 as mt5
            from app.services import risk_governor

            account = mt5.account_info()
            if account is None:
                return False  # MT5 not connected — handled by health monitor

            state = risk_governor._get_state()

            # Check if equity is wildly different
            if state.current_equity > 0 and account.equity > 0:
                diff_pct = abs(state.current_equity - account.equity) / account.equity * 100
                if diff_pct > 10:  # 10% discrepancy
                    self._trigger_freeze(
                        "MT5_REGISTRY_DESYNC",
                        f"Equity mismatch: MT5=${account.equity:.2f}, registry=${state.current_equity:.2f} ({diff_pct:.1f}%)",
                        {
                            "mt5_equity": account.equity,
                            "registry_equity": state.current_equity,
                            "diff_pct": diff_pct,
                        },
                    )
                    return True
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"MT5 desync check error: {e}")

        return False

    # ── Freeze Trigger ───────────────────────────────────────────

    def _trigger_freeze(
        self,
        incident_type: str,
        description: str,
        details: Dict[str, Any],
    ) -> None:
        """Trigger fail-safe freeze."""
        with self._lock:
            if self._frozen and self._freeze_reason == incident_type:
                return  # Already frozen for this reason

            self._frozen = True
            self._freeze_reason = incident_type
            self._total_incidents += 1

        incident = FailSafeIncident(
            incident_type=incident_type,
            description=description,
            severity="CRITICAL",
            details=details,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._incidents.append(incident)
            if len(self._incidents) > 100:
                self._incidents = self._incidents[-100:]

        logger.critical(f"FAIL_SAFE_FREEZE: {incident_type} — {description}")

        # Enter SAFE mode via watchdog
        try:
            from app.services.watchdog import get_watchdog
            wd = get_watchdog()
            if wd.is_trading_allowed():
                wd.enter_safe_mode(f"Fail-safe: {incident_type}")
        except Exception:
            pass

        # Alert operator
        try:
            from app.services.telegram_reporter import get_telegram_reporter
            reporter = get_telegram_reporter()
            reporter.send_emergency_sync(
                f"FAIL-SAFE PROTOCOL TRIGGERED\n\n"
                f"Incident: {incident_type}\n"
                f"Description: {description}\n\n"
                f"ALL TRADING FROZEN.\n"
                f"Manual reset required."
            )
        except Exception:
            pass

    # ── State Query ──────────────────────────────────────────────

    def is_frozen(self) -> bool:
        with self._lock:
            return self._frozen

    def should_block_trade(self) -> tuple:
        """Check if trades should be blocked by fail-safe."""
        with self._lock:
            if self._frozen:
                return True, f"FAIL_SAFE_FROZEN: {self._freeze_reason}"
            return False, "OK"

    def manual_reset(self, operator_reason: str = "") -> None:
        """
        Manual reset by operator.

        This is the ONLY way to unfreeze after a fail-safe event.
        No autonomous resume.
        """
        with self._lock:
            self._frozen = False
            self._freeze_reason = ""
            self._consecutive_exec_failures = 0
            self._recent_losses.clear()

        logger.critical(f"FAIL_SAFE_RESET: operator reset — {operator_reason}")

    # ── Background Monitor ───────────────────────────────────────

    def start(self) -> None:
        """Start background fail-safe monitoring."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="nexus-fail-safe"
        )
        self._thread.start()
        logger.info("Fail-safe protocol monitor started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _monitor_loop(self) -> None:
        while self._running:
            try:
                if not self._frozen:
                    self.check_position_mismatch()
                    self.check_state_integrity()
                    self.check_mt5_desync()
            except Exception as e:
                logger.error(f"Fail-safe monitor error: {e}")
            time.sleep(FAIL_SAFE_CHECK_INTERVAL_SECS)

    # ── Status ───────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "frozen": self._frozen,
                "freeze_reason": self._freeze_reason,
                "consecutive_exec_failures": self._consecutive_exec_failures,
                "total_incidents": self._total_incidents,
                "recent_incidents": [i.to_dict() for i in self._incidents[-10:]],
            }


# =============================================================================
# SINGLETON
# =============================================================================

_protocol: Optional[FailSafeProtocol] = None


def get_fail_safe() -> FailSafeProtocol:
    global _protocol
    if _protocol is None:
        _protocol = FailSafeProtocol()
    return _protocol
