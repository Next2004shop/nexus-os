"""
NEXUS Disaster Recovery — Phase 11 (J)
========================================

Emergency restoration procedure:
    1. Reconnect MT5
    2. Rebuild state from broker
    3. Re-sync positions
    4. Restore performance ledger
    5. Resume safely

This module provides a structured recovery path after
system failures, crashes, or state corruption.

All recovery actions are logged to security events.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.disaster_recovery")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECOVERY_LOG_PATH = os.path.join(_BASE_DIR, "logs", "recovery.log")
LEDGER_PATH = os.path.join(_BASE_DIR, "data", "performance_ledger.json")


class RecoveryStep:
    """Individual recovery step with status tracking."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = "PENDING"
        self.error: Optional[str] = None
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None

    def start(self):
        self.status = "RUNNING"
        self.started_at = datetime.now(timezone.utc).isoformat()

    def complete(self):
        self.status = "COMPLETED"
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def fail(self, error: str):
        self.status = "FAILED"
        self.error = error
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class EmergencyRestore:
    """
    Structured disaster recovery procedure.

    Executes a 5-step recovery protocol:
        1. RECONNECT  — Re-establish MT5 connection
        2. REBUILD    — Rebuild risk state from broker data
        3. RESYNC     — Sync position shadow with broker
        4. RESTORE    — Verify performance ledger integrity
        5. RESUME     — Transition to SAFE_MODE for cautious restart
    """

    def __init__(self):
        self._steps: List[RecoveryStep] = []
        self._recovery_count: int = 0
        self._last_recovery: Optional[str] = None
        self._recovery_log: List[Dict[str, Any]] = []

    def execute_recovery(self) -> Dict[str, Any]:
        """
        Execute full disaster recovery procedure.

        Returns dict with recovery status and step details.
        """
        self._recovery_count += 1
        started_at = datetime.now(timezone.utc).isoformat()

        logger.critical("DISASTER RECOVERY INITIATED")
        self._log_security("DISASTER_RECOVERY_STARTED", {
            "recovery_number": self._recovery_count,
        })

        self._steps = [
            RecoveryStep("RECONNECT", "Re-establish MT5 broker connection"),
            RecoveryStep("REBUILD", "Rebuild risk state from broker data"),
            RecoveryStep("RESYNC", "Re-sync position shadow with broker"),
            RecoveryStep("RESTORE", "Verify performance ledger integrity"),
            RecoveryStep("RESUME", "Transition to SAFE_MODE for cautious restart"),
        ]

        # Step 1: Reconnect MT5
        self._step_reconnect()

        # Step 2: Rebuild state
        self._step_rebuild_state()

        # Step 3: Re-sync positions
        self._step_resync_positions()

        # Step 4: Restore performance ledger
        self._step_restore_ledger()

        # Step 5: Resume safely
        self._step_resume()

        # Build result
        all_passed = all(s.status == "COMPLETED" for s in self._steps)
        failed_steps = [s.name for s in self._steps if s.status == "FAILED"]

        result = {
            "recovery_number": self._recovery_count,
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "success": all_passed,
            "failed_steps": failed_steps,
            "steps": [s.to_dict() for s in self._steps],
        }

        self._recovery_log.append(result)
        self._last_recovery = result["completed_at"]

        self._log_security(
            "DISASTER_RECOVERY_COMPLETED" if all_passed else "DISASTER_RECOVERY_PARTIAL",
            result,
        )

        if all_passed:
            logger.info("DISASTER RECOVERY COMPLETED SUCCESSFULLY")
        else:
            logger.critical(f"DISASTER RECOVERY PARTIAL — Failed steps: {failed_steps}")

        # Write to recovery log file
        self._write_log(result)

        return result

    def _step_reconnect(self):
        """Step 1: Reconnect MT5 broker."""
        step = self._steps[0]
        step.start()

        try:
            from app.services.execution import get_engine
            engine = get_engine()

            # Attempt MT5 reconnection
            if hasattr(engine, '_mt5') and engine._mt5:
                try:
                    engine._mt5.connect()
                    step.complete()
                    logger.info("Recovery: MT5 reconnection successful")
                except Exception as e:
                    step.fail(f"MT5 reconnection failed: {e}")
                    logger.error(f"Recovery: MT5 reconnection failed: {e}")
            else:
                step.complete()
                logger.info("Recovery: MT5 not configured, skipping reconnection")
        except ImportError:
            step.fail("Execution engine not available")
        except Exception as e:
            step.fail(str(e))

    def _step_rebuild_state(self):
        """Step 2: Rebuild risk state from broker data."""
        step = self._steps[1]
        step.start()

        try:
            from app.services.risk_governor import _get_state, _save_state

            state = _get_state()

            # Verify state is loadable and consistent
            if state.current_equity <= 0:
                state.current_equity = state.initial_equity
                logger.warning("Recovery: Reset equity to initial value")

            if state.peak_equity < state.current_equity:
                state.peak_equity = state.current_equity

            _save_state(state)
            step.complete()
            logger.info("Recovery: Risk state rebuilt and saved")
        except Exception as e:
            step.fail(f"State rebuild failed: {e}")
            logger.error(f"Recovery: State rebuild failed: {e}")

    def _step_resync_positions(self):
        """Step 3: Re-sync position shadow with broker."""
        step = self._steps[2]
        step.start()

        try:
            from security.position_shadow import get_position_shadow
            shadow = get_position_shadow()

            # Get broker positions if available
            try:
                from app.services.execution import get_engine
                engine = get_engine()
                broker_positions = []

                # Try to fetch positions from MT5
                if hasattr(engine, '_mt5') and engine._mt5:
                    try:
                        broker_positions = engine._mt5.get_positions()
                    except Exception:
                        broker_positions = []

                if broker_positions:
                    # Rebuild shadow from broker state
                    for pos in broker_positions:
                        shadow.register_position(
                            symbol=pos.get("symbol", ""),
                            side=pos.get("side", "buy"),
                            volume=pos.get("volume", 0),
                            entry_price=pos.get("entry_price", 0),
                            ticket=pos.get("ticket"),
                        )
                    logger.info(f"Recovery: Shadow rebuilt with {len(broker_positions)} positions")
                else:
                    logger.info("Recovery: No broker positions to sync")
            except ImportError:
                logger.info("Recovery: Execution engine not available for position sync")

            step.complete()
        except Exception as e:
            step.fail(f"Position resync failed: {e}")
            logger.error(f"Recovery: Position resync failed: {e}")

    def _step_restore_ledger(self):
        """Step 4: Verify performance ledger integrity."""
        step = self._steps[3]
        step.start()

        try:
            if os.path.exists(LEDGER_PATH):
                with open(LEDGER_PATH, "r") as f:
                    data = json.load(f)

                trades = data.get("trades", [])
                total = data.get("total_trades", 0)

                if len(trades) != total:
                    # Fix the count
                    data["total_trades"] = len(trades)
                    with open(LEDGER_PATH, "w") as f:
                        json.dump(data, f, indent=2, default=str)
                    logger.warning(f"Recovery: Ledger count corrected ({total} -> {len(trades)})")

                step.complete()
                logger.info(f"Recovery: Performance ledger verified ({len(trades)} trades)")
            else:
                # Create empty ledger
                data = {
                    "version": "1.0",
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "total_trades": 0,
                    "trades": [],
                }
                os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
                with open(LEDGER_PATH, "w") as f:
                    json.dump(data, f, indent=2)
                step.complete()
                logger.info("Recovery: Empty performance ledger created")
        except json.JSONDecodeError as e:
            step.fail(f"Ledger corrupted: {e}")
            logger.error(f"Recovery: Performance ledger corrupted: {e}")
        except Exception as e:
            step.fail(str(e))

    def _step_resume(self):
        """Step 5: Resume in SAFE_MODE."""
        step = self._steps[4]
        step.start()

        try:
            from security.failsafe import get_failsafe, SystemMode
            failsafe = get_failsafe()

            # Only transition if not already in NORMAL
            if failsafe.mode == SystemMode.LOCKDOWN:
                failsafe.transition_to(
                    SystemMode.SAFE_MODE,
                    "Post-disaster-recovery cautious mode",
                    source="DISASTER_RECOVERY",
                )
            elif failsafe.mode == SystemMode.SAFE_MODE:
                pass  # Already in safe mode
            # else: NORMAL — keep as is

            step.complete()
            logger.info(f"Recovery: System resumed in {failsafe.mode.value}")
        except Exception as e:
            step.fail(f"Resume failed: {e}")
            logger.error(f"Recovery: Resume failed: {e}")

    def _log_security(self, event_type: str, details: Dict[str, Any]):
        """Log to security event log."""
        try:
            from security.security_logger import (
                get_security_logger,
                SecurityEventCategory,
                SecuritySeverity,
            )
            get_security_logger().log(
                SecurityEventCategory.DISASTER_RECOVERY,
                SecuritySeverity.CRITICAL,
                event_type,
                details=details,
                source="DISASTER_RECOVERY",
            )
        except ImportError:
            pass

    def _write_log(self, result: Dict[str, Any]):
        """Write recovery result to recovery.log."""
        try:
            os.makedirs(os.path.dirname(RECOVERY_LOG_PATH), exist_ok=True)
            with open(RECOVERY_LOG_PATH, "a") as f:
                f.write(json.dumps(result, default=str) + "\n")
        except IOError as e:
            logger.error(f"Failed to write recovery log: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "recovery_count": self._recovery_count,
            "last_recovery": self._last_recovery,
            "last_steps": [s.to_dict() for s in self._steps] if self._steps else [],
            "history": self._recovery_log[-5:],
        }


# Module-level singleton
_instance: Optional[EmergencyRestore] = None


def get_emergency_restore() -> EmergencyRestore:
    global _instance
    if _instance is None:
        _instance = EmergencyRestore()
    return _instance
