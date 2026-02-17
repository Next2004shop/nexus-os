"""
NEXUS Broker Response Validator — Phase 11 (B)
================================================

Before marking any trade as "executed", validates:
    - Order ID exists
    - Position visible in broker
    - Volume matches requested
    - SL/TP properly set
    - Spread within tolerance

If mismatch → rollback + log critical.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from security.security_logger import (
    get_security_logger,
    SecurityEventCategory,
    SecuritySeverity,
)

logger = logging.getLogger("nexus.broker_validator")

# Tolerance thresholds
VOLUME_TOLERANCE = 0.001       # 0.1% volume mismatch allowed
SPREAD_MAX_PIPS = 50           # Maximum acceptable spread in pips
SLTP_PRICE_TOLERANCE = 0.001   # 0.1% tolerance for SL/TP price drift


@dataclass
class ValidationResult:
    """Result of broker response validation."""
    valid: bool
    checks_passed: List[str]
    checks_failed: List[str]
    details: Dict[str, Any]
    requires_rollback: bool = False


class BrokerResponseValidator:
    """
    Validates broker execution responses before accepting trade as executed.

    Called AFTER execution engine receives a broker response,
    BEFORE updating internal state (RiskGovernor, Position Tracker, etc).
    """

    def __init__(self):
        self._sec = get_security_logger()
        self._validation_count = 0
        self._failure_count = 0
        self._rollback_count = 0

    def validate_execution(
        self,
        request: Dict[str, Any],
        response: Dict[str, Any],
        broker_positions: Optional[List[Dict[str, Any]]] = None,
    ) -> ValidationResult:
        """
        Full validation of a broker execution response.

        Args:
            request: Original trade request {symbol, side, quantity, sl, tp, ...}
            response: Broker response {order_id, status, filled_qty, price, ...}
            broker_positions: Current broker positions (for position visibility check)

        Returns:
            ValidationResult with pass/fail for each check
        """
        self._validation_count += 1
        passed = []
        failed = []
        details = {}

        # Check 1: Order ID exists
        order_id = response.get("order_id") or response.get("ticket")
        if order_id:
            passed.append("ORDER_ID_EXISTS")
            details["order_id"] = order_id
        else:
            failed.append("ORDER_ID_MISSING")
            details["order_id"] = None

        # Check 2: Execution status
        status = response.get("status", "").upper()
        if status in ("FILLED", "EXECUTED", "SUCCESS"):
            passed.append("STATUS_CONFIRMED")
        elif status in ("PARTIALLY_FILLED",):
            passed.append("STATUS_PARTIAL")
            details["partial_fill"] = True
        else:
            failed.append(f"STATUS_INVALID: {status}")

        # Check 3: Volume matches
        requested_qty = request.get("quantity", 0)
        filled_qty = response.get("filled_quantity") or response.get("volume", 0)
        if requested_qty > 0 and filled_qty > 0:
            volume_diff = abs(filled_qty - requested_qty) / requested_qty
            if volume_diff <= VOLUME_TOLERANCE:
                passed.append("VOLUME_MATCHED")
            else:
                failed.append(f"VOLUME_MISMATCH: requested={requested_qty} filled={filled_qty}")
                details["volume_diff_pct"] = round(volume_diff * 100, 3)
        elif filled_qty == 0:
            failed.append("VOLUME_ZERO")

        # Check 4: SL/TP properly set
        if request.get("sl") is not None:
            response_sl = response.get("sl") or response.get("stop_loss")
            if response_sl is not None:
                sl_diff = abs(float(response_sl) - float(request["sl"]))
                sl_pct = sl_diff / float(request["sl"]) if float(request["sl"]) > 0 else 0
                if sl_pct <= SLTP_PRICE_TOLERANCE:
                    passed.append("SL_SET_CORRECTLY")
                else:
                    failed.append(f"SL_MISMATCH: req={request['sl']} got={response_sl}")
            else:
                failed.append("SL_NOT_SET")

        if request.get("tp") is not None:
            response_tp = response.get("tp") or response.get("take_profit")
            if response_tp is not None:
                tp_diff = abs(float(response_tp) - float(request["tp"]))
                tp_pct = tp_diff / float(request["tp"]) if float(request["tp"]) > 0 else 0
                if tp_pct <= SLTP_PRICE_TOLERANCE:
                    passed.append("TP_SET_CORRECTLY")
                else:
                    failed.append(f"TP_MISMATCH: req={request['tp']} got={response_tp}")
            else:
                failed.append("TP_NOT_SET")

        # Check 5: Spread within tolerance
        spread = response.get("spread")
        if spread is not None:
            if float(spread) <= SPREAD_MAX_PIPS:
                passed.append("SPREAD_ACCEPTABLE")
            else:
                failed.append(f"SPREAD_EXCESSIVE: {spread} pips (max {SPREAD_MAX_PIPS})")
                details["spread"] = spread

        # Check 6: Position visible in broker (if positions provided)
        symbol = request.get("symbol", "")
        if broker_positions is not None and order_id:
            position_found = any(
                p.get("ticket") == order_id or p.get("symbol") == symbol
                for p in broker_positions
            )
            if position_found:
                passed.append("POSITION_VISIBLE")
            else:
                failed.append("POSITION_NOT_VISIBLE")

        # Determine result
        requires_rollback = len(failed) > 0 and any(
            f.startswith(("ORDER_ID_MISSING", "STATUS_INVALID", "VOLUME_ZERO", "VOLUME_MISMATCH"))
            for f in failed
        )

        result = ValidationResult(
            valid=len(failed) == 0,
            checks_passed=passed,
            checks_failed=failed,
            details=details,
            requires_rollback=requires_rollback,
        )

        if not result.valid:
            self._failure_count += 1
            severity = SecuritySeverity.CRITICAL if requires_rollback else SecuritySeverity.WARNING

            self._sec.log(
                SecurityEventCategory.BROKER_VALIDATION,
                severity,
                f"Broker validation failed: {', '.join(failed)}",
                details={
                    "symbol": symbol,
                    "request": {k: v for k, v in request.items() if k != "password"},
                    "response": {k: v for k, v in response.items() if k != "password"},
                    "passed": passed,
                    "failed": failed,
                    "requires_rollback": requires_rollback,
                },
                source="BROKER_VALIDATOR",
            )

            if requires_rollback:
                self._rollback_count += 1
                logger.critical(
                    f"BROKER ROLLBACK REQUIRED: {symbol} | Failed: {failed}"
                )
        else:
            logger.info(f"Broker validation passed: {symbol} | {len(passed)} checks OK")

        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_validations": self._validation_count,
            "failures": self._failure_count,
            "rollbacks": self._rollback_count,
            "success_rate": (
                round((self._validation_count - self._failure_count) / self._validation_count, 3)
                if self._validation_count > 0 else 1.0
            ),
        }
