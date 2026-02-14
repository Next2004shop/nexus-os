"""
NEXUS Execution Verifier — Phase 7, Part 4
=============================================

Post-trade verification system.

After every trade, verifies:
  1. Ticket exists in MT5
  2. SL and TP placed correctly
  3. Lot size matches request
  4. Position logged in state registry
  5. State registry is synced

On mismatch:
  - Immediate alert
  - Attempt correction
  - If correction fails → Emergency Mode
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.execution_verifier")

# =============================================================================
# CONFIGURATION
# =============================================================================
LOT_SIZE_TOLERANCE = 0.02        # allow 0.02 lot difference
PRICE_TOLERANCE_PCT = 0.05       # 0.05% price tolerance for SL/TP check
MAX_CORRECTION_ATTEMPTS = 2


# =============================================================================
# VERIFICATION RESULT
# =============================================================================

@dataclass
class VerificationResult:
    """Result of post-trade verification."""
    trade_id: str
    symbol: str
    all_ok: bool = True
    ticket_exists: bool = True
    sl_correct: bool = True
    tp_correct: bool = True
    lot_size_correct: bool = True
    registry_logged: bool = True
    registry_synced: bool = True
    issues: List[str] = field(default_factory=list)
    corrections_applied: List[str] = field(default_factory=list)
    corrections_failed: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "all_ok": self.all_ok,
            "checks": {
                "ticket_exists": self.ticket_exists,
                "sl_correct": self.sl_correct,
                "tp_correct": self.tp_correct,
                "lot_size_correct": self.lot_size_correct,
                "registry_logged": self.registry_logged,
                "registry_synced": self.registry_synced,
            },
            "issues": self.issues,
            "corrections_applied": self.corrections_applied,
            "corrections_failed": self.corrections_failed,
            "timestamp": self.timestamp,
        }


# =============================================================================
# EXECUTION VERIFIER
# =============================================================================

class ExecutionVerifier:
    """
    Verifies every executed trade against MT5 and internal registry.

    On mismatch: alerts, attempts correction, escalates if needed.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._verification_history: List[VerificationResult] = []
        self._total_verified: int = 0
        self._total_mismatches: int = 0
        self._total_corrections: int = 0
        self._total_correction_failures: int = 0

    def verify_trade(
        self,
        trade_id: str,
        symbol: str,
        expected_side: str,
        expected_lot: float,
        expected_sl: Optional[float],
        expected_tp: Optional[float],
        ticket: Optional[int] = None,
    ) -> VerificationResult:
        """
        Run full post-trade verification.

        Args:
            trade_id: Internal trade identifier
            symbol: Trading symbol
            expected_side: BUY or SELL
            expected_lot: Expected lot size
            expected_sl: Expected stop loss price
            expected_tp: Expected take profit price
            ticket: MT5 order ticket (if available)

        Returns:
            VerificationResult with all check outcomes
        """
        result = VerificationResult(
            trade_id=trade_id,
            symbol=symbol,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 1. Ticket existence in MT5
        mt5_position = self._check_ticket(result, symbol, ticket)

        # 2. SL correctness
        if mt5_position and expected_sl:
            self._check_sl(result, mt5_position, expected_sl)

        # 3. TP correctness
        if mt5_position and expected_tp:
            self._check_tp(result, mt5_position, expected_tp)

        # 4. Lot size match
        if mt5_position:
            self._check_lot_size(result, mt5_position, expected_lot)

        # 5. Registry logged
        self._check_registry(result, symbol)

        # 6. Registry sync
        self._check_registry_sync(result, symbol)

        # Determine overall status
        result.all_ok = len(result.issues) == 0

        # Attempt corrections if needed
        if not result.all_ok:
            self._attempt_corrections(result, mt5_position, expected_sl, expected_tp, expected_lot)

        # Determine final status after corrections
        result.all_ok = len(result.corrections_failed) == 0 and len(result.issues) == 0

        # Record
        with self._lock:
            self._total_verified += 1
            if not result.all_ok:
                self._total_mismatches += 1
            self._total_corrections += len(result.corrections_applied)
            self._total_correction_failures += len(result.corrections_failed)
            self._verification_history.append(result)
            if len(self._verification_history) > 200:
                self._verification_history = self._verification_history[-200:]

        # Log
        if result.all_ok:
            logger.info(f"VERIFY_OK: {symbol} trade_id={trade_id}")
        else:
            logger.critical(
                f"VERIFY_FAILED: {symbol} trade_id={trade_id} "
                f"issues={result.issues} corrections_failed={result.corrections_failed}"
            )

            # If corrections failed → escalate
            if result.corrections_failed:
                self._escalate(result)

        return result

    # ── Individual Checks ────────────────────────────────────────

    def _check_ticket(self, result: VerificationResult, symbol: str, ticket: Optional[int]) -> Optional[Any]:
        """Check if trade ticket exists in MT5."""
        try:
            import MetaTrader5 as mt5

            if ticket:
                # Check by ticket
                positions = mt5.positions_get(ticket=ticket)
                if not positions:
                    result.ticket_exists = False
                    result.issues.append(f"TICKET_NOT_FOUND: ticket={ticket}")
                    return None
                return positions[0]
            else:
                # Check by symbol (latest position)
                positions = mt5.positions_get(symbol=symbol)
                if positions:
                    return positions[-1]  # Most recent
                # No position found — might be closed already
                return None

        except ImportError:
            # Non-Windows — skip MT5 checks
            return None
        except Exception as e:
            logger.error(f"Ticket check error: {e}")
            return None

    def _check_sl(self, result: VerificationResult, mt5_pos: Any, expected_sl: float) -> None:
        """Check if stop loss is placed correctly."""
        actual_sl = mt5_pos.sl if hasattr(mt5_pos, "sl") else 0
        if actual_sl <= 0:
            result.sl_correct = False
            result.issues.append(f"SL_MISSING: expected={expected_sl}")
            return

        if expected_sl > 0:
            diff_pct = abs(actual_sl - expected_sl) / expected_sl * 100
            if diff_pct > PRICE_TOLERANCE_PCT:
                result.sl_correct = False
                result.issues.append(
                    f"SL_MISMATCH: expected={expected_sl}, actual={actual_sl}, diff={diff_pct:.3f}%"
                )

    def _check_tp(self, result: VerificationResult, mt5_pos: Any, expected_tp: float) -> None:
        """Check if take profit is placed correctly."""
        actual_tp = mt5_pos.tp if hasattr(mt5_pos, "tp") else 0
        if actual_tp <= 0:
            result.tp_correct = False
            result.issues.append(f"TP_MISSING: expected={expected_tp}")
            return

        if expected_tp > 0:
            diff_pct = abs(actual_tp - expected_tp) / expected_tp * 100
            if diff_pct > PRICE_TOLERANCE_PCT:
                result.tp_correct = False
                result.issues.append(
                    f"TP_MISMATCH: expected={expected_tp}, actual={actual_tp}, diff={diff_pct:.3f}%"
                )

    def _check_lot_size(self, result: VerificationResult, mt5_pos: Any, expected_lot: float) -> None:
        """Check if lot size matches request."""
        actual_vol = mt5_pos.volume if hasattr(mt5_pos, "volume") else 0
        if abs(actual_vol - expected_lot) > LOT_SIZE_TOLERANCE:
            result.lot_size_correct = False
            result.issues.append(
                f"LOT_MISMATCH: expected={expected_lot}, actual={actual_vol}"
            )

    def _check_registry(self, result: VerificationResult, symbol: str) -> None:
        """Check if position is logged in internal state registry."""
        try:
            from app.services import risk_governor
            state = risk_governor._get_state()
            if symbol not in state.open_positions:
                result.registry_logged = False
                result.issues.append(f"REGISTRY_NOT_LOGGED: {symbol}")
        except Exception as e:
            result.registry_logged = False
            result.issues.append(f"REGISTRY_CHECK_ERROR: {e}")

    def _check_registry_sync(self, result: VerificationResult, symbol: str) -> None:
        """Check that registry position count matches MT5."""
        try:
            import MetaTrader5 as mt5
            from app.services import risk_governor

            mt5_count = mt5.positions_total()
            state = risk_governor._get_state()
            registry_count = len(state.open_positions)

            if mt5_count != registry_count:
                result.registry_synced = False
                result.issues.append(
                    f"REGISTRY_DESYNC: MT5={mt5_count}, registry={registry_count}"
                )
        except ImportError:
            pass  # Non-Windows
        except Exception as e:
            logger.error(f"Registry sync check error: {e}")

    # ── Correction Attempts ──────────────────────────────────────

    def _attempt_corrections(
        self,
        result: VerificationResult,
        mt5_pos: Optional[Any],
        expected_sl: Optional[float],
        expected_tp: Optional[float],
        expected_lot: float,
    ) -> None:
        """Attempt to correct detected mismatches."""
        try:
            import MetaTrader5 as mt5
        except ImportError:
            return

        if mt5_pos is None:
            return

        # Correct SL/TP if mismatched
        if not result.sl_correct or not result.tp_correct:
            for attempt in range(MAX_CORRECTION_ATTEMPTS):
                try:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": mt5_pos.ticket,
                        "symbol": result.symbol,
                        "sl": expected_sl or 0.0,
                        "tp": expected_tp or 0.0,
                    }
                    correction = mt5.order_send(request)
                    if correction and correction.retcode == mt5.TRADE_RETCODE_DONE:
                        if not result.sl_correct:
                            result.corrections_applied.append(f"SL corrected to {expected_sl}")
                            result.sl_correct = True
                            # Remove the issue
                            result.issues = [i for i in result.issues if not i.startswith("SL_")]
                        if not result.tp_correct:
                            result.corrections_applied.append(f"TP corrected to {expected_tp}")
                            result.tp_correct = True
                            result.issues = [i for i in result.issues if not i.startswith("TP_")]
                        break
                    else:
                        retcode = correction.retcode if correction else "None"
                        logger.warning(f"SL/TP correction attempt {attempt + 1} failed: {retcode}")
                except Exception as e:
                    logger.error(f"SL/TP correction error: {e}")

            # If still not corrected after all attempts
            if not result.sl_correct:
                result.corrections_failed.append("SL correction failed")
            if not result.tp_correct:
                result.corrections_failed.append("TP correction failed")

    # ── Escalation ───────────────────────────────────────────────

    def _escalate(self, result: VerificationResult) -> None:
        """Escalate unresolvable verification failure."""
        logger.critical(
            f"EXECUTION_VERIFICATION_ESCALATION: {result.symbol} — "
            f"uncorrectable issues detected → EMERGENCY"
        )
        try:
            from app.services.watchdog import get_watchdog
            wd = get_watchdog()
            if wd.is_trading_allowed():
                wd.enter_safe_mode(
                    f"Execution verifier: uncorrectable mismatch on {result.symbol}"
                )
        except Exception:
            pass

        # Telegram alert
        try:
            from app.services.telegram_reporter import get_telegram_reporter
            reporter = get_telegram_reporter()
            reporter.send_emergency_sync(
                f"EXECUTION VERIFICATION FAILED\n\n"
                f"Symbol: {result.symbol}\n"
                f"Issues: {', '.join(result.issues)}\n"
                f"Failed Corrections: {', '.join(result.corrections_failed)}\n\n"
                f"EMERGENCY MODE. Manual intervention required."
            )
        except Exception:
            pass

    # ── Status ───────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_verified": self._total_verified,
                "total_mismatches": self._total_mismatches,
                "total_corrections": self._total_corrections,
                "total_correction_failures": self._total_correction_failures,
                "mismatch_rate": (
                    round(self._total_mismatches / self._total_verified * 100, 1)
                    if self._total_verified > 0 else 0
                ),
                "recent_verifications": [
                    v.to_dict() for v in self._verification_history[-10:]
                ],
            }

    def get_recent_issues(self) -> List[Dict[str, Any]]:
        """Get recent verification issues only."""
        with self._lock:
            return [
                v.to_dict() for v in self._verification_history
                if not v.all_ok
            ][-20:]


# =============================================================================
# SINGLETON
# =============================================================================

_verifier: Optional[ExecutionVerifier] = None


def get_execution_verifier() -> ExecutionVerifier:
    global _verifier
    if _verifier is None:
        _verifier = ExecutionVerifier()
    return _verifier
