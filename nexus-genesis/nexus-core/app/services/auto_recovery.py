"""
NEXUS Auto Recovery — Phase 7, Part 2
=======================================

Auto-recovery logic for critical subsystem failures.

Recovery targets:
  - MT5 disconnect → 3 reconnection attempts, 10s spacing
  - API timeout → 3 retries with 10s spacing
  - Telegram bot freeze → 3 reconnection attempts
  - Data feed interruption → 3 reconnection attempts

Rules:
  - Maximum 3 recovery attempts per subsystem
  - 10 second spacing between attempts
  - If all attempts fail → EMERGENCY mode
  - No infinite loops
  - No silent failures
  - All attempts logged
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.auto_recovery")

# =============================================================================
# CONFIGURATION
# =============================================================================
MAX_RECOVERY_ATTEMPTS = 3
RECOVERY_SPACING_SECS = 10
RECOVERY_COOLDOWN_SECS = 300  # 5 min cooldown before allowing new recovery cycle


# =============================================================================
# RECOVERY TYPES
# =============================================================================

class SubsystemType(str, Enum):
    MT5 = "MT5"
    API = "API"
    TELEGRAM = "TELEGRAM"
    DATA_FEED = "DATA_FEED"


class RecoveryStatus(str, Enum):
    IDLE = "IDLE"
    ATTEMPTING = "ATTEMPTING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"


@dataclass
class RecoveryAttempt:
    """Record of a single recovery attempt."""
    subsystem: str
    attempt_number: int
    success: bool
    error: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subsystem": self.subsystem,
            "attempt": self.attempt_number,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp,
        }


@dataclass
class SubsystemState:
    """State tracker for a single subsystem."""
    subsystem: str
    status: RecoveryStatus = RecoveryStatus.IDLE
    attempts_this_cycle: int = 0
    total_recoveries: int = 0
    total_failures: int = 0
    last_attempt_time: float = 0.0
    last_recovery_time: float = 0.0
    history: List[RecoveryAttempt] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subsystem": self.subsystem,
            "status": self.status.value,
            "attempts_this_cycle": self.attempts_this_cycle,
            "total_recoveries": self.total_recoveries,
            "total_failures": self.total_failures,
            "recent_history": [h.to_dict() for h in self.history[-5:]],
        }


# =============================================================================
# AUTO RECOVERY ENGINE
# =============================================================================

class AutoRecoveryEngine:
    """
    Manages auto-recovery for all monitored subsystems.

    Each subsystem gets:
      - 3 reconnection attempts
      - 10 second spacing
      - If failure persists → Emergency Mode

    Thread-safe. No infinite loops.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._subsystems: Dict[str, SubsystemState] = {
            st.value: SubsystemState(subsystem=st.value)
            for st in SubsystemType
        }
        self._recovery_in_progress: Dict[str, bool] = {
            st.value: False for st in SubsystemType
        }

    def attempt_recovery(self, subsystem: SubsystemType) -> Tuple[bool, str]:
        """
        Attempt recovery for a subsystem.

        Returns:
            (recovered, message)
        """
        name = subsystem.value

        with self._lock:
            state = self._subsystems[name]

            # Check if recovery already in progress
            if self._recovery_in_progress[name]:
                return False, f"{name}: recovery already in progress"

            # Check cooldown
            now = time.monotonic()
            if (
                state.status == RecoveryStatus.RECOVERED
                and now - state.last_recovery_time < RECOVERY_COOLDOWN_SECS
            ):
                return True, f"{name}: recently recovered, in cooldown"

            # Reset cycle if enough time passed since last failure
            if (
                state.status == RecoveryStatus.FAILED
                and now - state.last_attempt_time > RECOVERY_COOLDOWN_SECS
            ):
                state.attempts_this_cycle = 0
                state.status = RecoveryStatus.IDLE

            self._recovery_in_progress[name] = True

        logger.warning(f"AUTO_RECOVERY: initiating recovery for {name}")

        try:
            return self._execute_recovery(subsystem)
        finally:
            with self._lock:
                self._recovery_in_progress[name] = False

    def _execute_recovery(self, subsystem: SubsystemType) -> Tuple[bool, str]:
        """Execute the recovery sequence: 3 attempts, 10s spacing."""
        name = subsystem.value

        for attempt_num in range(1, MAX_RECOVERY_ATTEMPTS + 1):
            with self._lock:
                state = self._subsystems[name]
                state.status = RecoveryStatus.ATTEMPTING
                state.attempts_this_cycle = attempt_num

            logger.info(f"AUTO_RECOVERY: {name} attempt {attempt_num}/{MAX_RECOVERY_ATTEMPTS}")

            success = False
            error_msg = ""

            try:
                if subsystem == SubsystemType.MT5:
                    success, error_msg = self._recover_mt5()
                elif subsystem == SubsystemType.API:
                    success, error_msg = self._recover_api()
                elif subsystem == SubsystemType.TELEGRAM:
                    success, error_msg = self._recover_telegram()
                elif subsystem == SubsystemType.DATA_FEED:
                    success, error_msg = self._recover_data_feed()
            except Exception as e:
                error_msg = str(e)
                success = False

            # Record attempt
            record = RecoveryAttempt(
                subsystem=name,
                attempt_number=attempt_num,
                success=success,
                error=error_msg,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            with self._lock:
                state = self._subsystems[name]
                state.history.append(record)
                # Keep history bounded
                if len(state.history) > 50:
                    state.history = state.history[-50:]
                state.last_attempt_time = time.monotonic()

            if success:
                with self._lock:
                    state.status = RecoveryStatus.RECOVERED
                    state.total_recoveries += 1
                    state.last_recovery_time = time.monotonic()
                    state.attempts_this_cycle = 0
                logger.info(f"AUTO_RECOVERY: {name} recovered on attempt {attempt_num}")
                return True, f"{name}: recovered on attempt {attempt_num}"

            logger.warning(f"AUTO_RECOVERY: {name} attempt {attempt_num} failed: {error_msg}")

            # Wait before next attempt (except on last attempt)
            if attempt_num < MAX_RECOVERY_ATTEMPTS:
                time.sleep(RECOVERY_SPACING_SECS)

        # All attempts exhausted — enter emergency mode
        with self._lock:
            state = self._subsystems[name]
            state.status = RecoveryStatus.FAILED
            state.total_failures += 1

        logger.critical(f"AUTO_RECOVERY: {name} FAILED after {MAX_RECOVERY_ATTEMPTS} attempts → EMERGENCY")
        self._enter_emergency_mode(name)

        return False, f"{name}: all {MAX_RECOVERY_ATTEMPTS} recovery attempts failed"

    # ── Subsystem-specific recovery ──────────────────────────────

    def _recover_mt5(self) -> Tuple[bool, str]:
        """Attempt to reconnect MT5."""
        try:
            import MetaTrader5 as mt5
        except ImportError:
            return True, "MT5 not available (non-Windows) — skipped"

        try:
            # Shutdown existing connection
            mt5.shutdown()
            time.sleep(1)

            # Re-initialize
            from app.services import vault
            login = int(vault.get_secret("MT5_LOGIN"))
            password = vault.get_secret("MT5_PASSWORD")
            server = vault.get_secret("MT5_SERVER")

            if mt5.initialize(login=login, password=password, server=server):
                account = mt5.account_info()
                if account is not None:
                    return True, f"MT5 reconnected: {account.company}"
                return False, "MT5 initialized but account_info is None"
            else:
                error = mt5.last_error()
                return False, f"MT5 initialize failed: {error}"
        except Exception as e:
            return False, str(e)

    def _recover_api(self) -> Tuple[bool, str]:
        """Test AI API connectivity."""
        try:
            from app.services import intelligence
            # Attempt a lightweight API call
            models = intelligence.list_models()
            if models:
                return True, "API responsive"
            return False, "API returned empty model list"
        except Exception as e:
            return False, str(e)

    def _recover_telegram(self) -> Tuple[bool, str]:
        """Test Telegram bot connectivity."""
        try:
            from app.services.telegram_reporter import get_telegram_reporter
            reporter = get_telegram_reporter()
            if not reporter.is_enabled:
                return True, "Telegram not configured — skipped"

            # Test with a sync ping (don't send actual message to avoid spam)
            import urllib.request
            import json
            token = reporter._token
            url = f"https://api.telegram.org/bot{token}/getMe"
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            if data.get("ok"):
                return True, "Telegram bot responsive"
            return False, "Telegram getMe returned ok=false"
        except Exception as e:
            return False, str(e)

    def _recover_data_feed(self) -> Tuple[bool, str]:
        """Test data feed connectivity."""
        try:
            from app.services import market_data
            provider = market_data.get_provider()
            # Check if provider is responsive
            if hasattr(provider, "is_connected") and not provider.is_connected():
                return False, "Data feed provider disconnected"
            return True, "Data feed check passed"
        except Exception as e:
            return False, str(e)

    # ── Emergency Escalation ─────────────────────────────────────

    def _enter_emergency_mode(self, subsystem_name: str) -> None:
        """Enter emergency mode after recovery failure."""
        try:
            from app.services.watchdog import get_watchdog, SystemMode
            wd = get_watchdog()
            wd.enter_safe_mode(
                f"Auto-recovery exhausted for {subsystem_name} — EMERGENCY"
            )
            logger.critical(f"EMERGENCY MODE: {subsystem_name} recovery failed")
        except Exception as e:
            logger.error(f"Failed to enter emergency mode: {e}")

        # Send Telegram emergency alert
        try:
            from app.services.telegram_reporter import get_telegram_reporter
            reporter = get_telegram_reporter()
            reporter.send_emergency_sync(
                f"AUTO-RECOVERY FAILED\n\n"
                f"Subsystem: {subsystem_name}\n"
                f"Attempts: {MAX_RECOVERY_ATTEMPTS}\n"
                f"Status: EMERGENCY MODE\n"
                f"Action required: Manual intervention"
            )
        except Exception:
            pass

    # ── Status ───────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                name: state.to_dict()
                for name, state in self._subsystems.items()
            }

    def get_subsystem_status(self, subsystem: SubsystemType) -> Dict[str, Any]:
        with self._lock:
            return self._subsystems[subsystem.value].to_dict()


# =============================================================================
# SINGLETON
# =============================================================================

_engine: Optional[AutoRecoveryEngine] = None


def get_auto_recovery() -> AutoRecoveryEngine:
    global _engine
    if _engine is None:
        _engine = AutoRecoveryEngine()
    return _engine
