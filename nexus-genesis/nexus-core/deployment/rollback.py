"""
NEXUS Rollback System — Phase 12 (E)
=======================================

One-command rollback that:
    1. Reverts to previous stable commit
    2. Restores last stable config
    3. Preserves trade history
    4. Prevents duplicate re-execution

Rollback is one-command executable: python -m deployment.rollback
"""

import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.rollback")

_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROLLBACK_DIR = _BASE_DIR / "deployment" / "rollback_state"
_STABLE_CONFIG_PATH = _ROLLBACK_DIR / "last_stable_config.json"
_STABLE_COMMIT_PATH = _ROLLBACK_DIR / "last_stable_commit.txt"
_ROLLBACK_LOG_PATH = _ROLLBACK_DIR / "rollback_history.json"
_EXECUTION_LOCK_PATH = _ROLLBACK_DIR / "execution_lock.json"


@dataclass
class RollbackResult:
    success: bool
    message: str
    commit_before: str
    commit_after: str
    config_restored: bool
    trade_history_preserved: bool


def _ensure_dirs():
    _ROLLBACK_DIR.mkdir(parents=True, exist_ok=True)


def save_stable_state():
    """
    Mark current state as stable.

    Call this after a successful deployment is verified.
    Saves: Git commit hash, config snapshot.
    """
    _ensure_dirs()

    # Save current commit
    commit = _get_current_commit()
    _STABLE_COMMIT_PATH.write_text(commit)

    # Save current config
    try:
        from config.config_loader import get_config
        config = get_config()
        with open(_STABLE_CONFIG_PATH, "w") as f:
            json.dump(config.to_safe_dict(), f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save config snapshot: {e}")

    # Save execution lock state (prevent duplicate trades on rollback)
    lock_state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "trade_ids_at_snapshot": _get_recent_trade_ids(),
    }
    with open(_EXECUTION_LOCK_PATH, "w") as f:
        json.dump(lock_state, f, indent=2)

    logger.info(f"Stable state saved: commit={commit}")


def rollback(dry_run: bool = False) -> RollbackResult:
    """
    Execute rollback to previous stable state.

    Steps:
        1. Read last stable commit
        2. Stash current changes
        3. Checkout stable commit
        4. Restore stable config
        5. Set execution lock to prevent duplicate trades
        6. Log the rollback

    Args:
        dry_run: If True, only show what would happen without executing.
    """
    _ensure_dirs()

    commit_before = _get_current_commit()
    commit_after = commit_before

    # Step 1: Read stable commit
    if not _STABLE_COMMIT_PATH.exists():
        return RollbackResult(
            success=False,
            message="No stable commit found — cannot rollback. Run save_stable_state() first.",
            commit_before=commit_before,
            commit_after=commit_before,
            config_restored=False,
            trade_history_preserved=False,
        )

    stable_commit = _STABLE_COMMIT_PATH.read_text().strip()
    if not stable_commit or stable_commit == "unknown":
        return RollbackResult(
            success=False,
            message="Stable commit is invalid",
            commit_before=commit_before,
            commit_after=commit_before,
            config_restored=False,
            trade_history_preserved=False,
        )

    if dry_run:
        return RollbackResult(
            success=True,
            message=f"DRY RUN: Would rollback from {commit_before} to {stable_commit}",
            commit_before=commit_before,
            commit_after=stable_commit,
            config_restored=_STABLE_CONFIG_PATH.exists(),
            trade_history_preserved=True,
        )

    # Step 2: Preserve trade history before rollback
    trade_history_ok = _preserve_trade_history()

    # Step 3: Git operations — stash and checkout
    try:
        # Stash any local changes
        subprocess.run(
            ["git", "stash", "--include-untracked"],
            capture_output=True, text=True, timeout=30,
            cwd=str(_BASE_DIR),
        )

        # Checkout stable commit
        result = subprocess.run(
            ["git", "checkout", stable_commit],
            capture_output=True, text=True, timeout=30,
            cwd=str(_BASE_DIR),
        )

        if result.returncode != 0:
            return RollbackResult(
                success=False,
                message=f"Git checkout failed: {result.stderr}",
                commit_before=commit_before,
                commit_after=commit_before,
                config_restored=False,
                trade_history_preserved=trade_history_ok,
            )

        commit_after = _get_current_commit()

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return RollbackResult(
            success=False,
            message=f"Git rollback failed: {e}",
            commit_before=commit_before,
            commit_after=commit_before,
            config_restored=False,
            trade_history_preserved=trade_history_ok,
        )

    # Step 4: Restore stable config
    config_restored = _restore_stable_config()

    # Step 5: Set execution lock
    _set_execution_lock(commit_before, commit_after)

    # Step 6: Log rollback
    _log_rollback(commit_before, commit_after)

    logger.warning(f"ROLLBACK COMPLETE: {commit_before} -> {commit_after}")

    return RollbackResult(
        success=True,
        message=f"Rolled back from {commit_before} to {commit_after}",
        commit_before=commit_before,
        commit_after=commit_after,
        config_restored=config_restored,
        trade_history_preserved=trade_history_ok,
    )


def get_rollback_status() -> Dict[str, Any]:
    """Get current rollback system status."""
    _ensure_dirs()

    stable_commit = ""
    if _STABLE_COMMIT_PATH.exists():
        stable_commit = _STABLE_COMMIT_PATH.read_text().strip()

    has_stable_config = _STABLE_CONFIG_PATH.exists()

    execution_lock = {}
    if _EXECUTION_LOCK_PATH.exists():
        try:
            with open(_EXECUTION_LOCK_PATH, "r") as f:
                execution_lock = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    history = _get_rollback_history()

    return {
        "stable_commit": stable_commit,
        "current_commit": _get_current_commit(),
        "has_stable_config": has_stable_config,
        "execution_lock": execution_lock,
        "rollback_count": len(history),
        "recent_rollbacks": history[-5:],
    }


def is_duplicate_execution(trade_id: str) -> bool:
    """
    Check if a trade ID was already executed before rollback.

    Prevents duplicate re-execution after rollback.
    """
    if not _EXECUTION_LOCK_PATH.exists():
        return False

    try:
        with open(_EXECUTION_LOCK_PATH, "r") as f:
            lock = json.load(f)
        previous_ids = lock.get("trade_ids_at_snapshot", [])
        return trade_id in previous_ids
    except (json.JSONDecodeError, IOError):
        return False


def _get_current_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(_BASE_DIR),
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return "unknown"


def _preserve_trade_history() -> bool:
    """Copy trade history files to safe location before rollback."""
    try:
        data_dir = _BASE_DIR / "data"
        backup_dir = _ROLLBACK_DIR / "preserved_data"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Preserve performance ledger
        ledger_src = data_dir / "performance_ledger.json"
        if ledger_src.exists():
            shutil.copy2(str(ledger_src), str(backup_dir / "performance_ledger.json"))

        # Preserve logs
        logs_dir = _BASE_DIR / "logs"
        if logs_dir.exists():
            logs_backup = backup_dir / "logs"
            logs_backup.mkdir(parents=True, exist_ok=True)
            for log_file in logs_dir.glob("*.log"):
                shutil.copy2(str(log_file), str(logs_backup / log_file.name))

        return True
    except Exception as e:
        logger.error(f"Failed to preserve trade history: {e}")
        return False


def _restore_stable_config() -> bool:
    """Restore the last stable config.json."""
    try:
        if not _STABLE_CONFIG_PATH.exists():
            return False

        target = _BASE_DIR / "config.json"
        shutil.copy2(str(_STABLE_CONFIG_PATH), str(target))
        logger.info("Stable config restored")
        return True
    except Exception as e:
        logger.error(f"Failed to restore config: {e}")
        return False


def _set_execution_lock(commit_before: str, commit_after: str):
    """Set lock to prevent duplicate trade execution."""
    lock = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rolled_from": commit_before,
        "rolled_to": commit_after,
        "trade_ids_at_snapshot": _get_recent_trade_ids(),
    }
    try:
        with open(_EXECUTION_LOCK_PATH, "w") as f:
            json.dump(lock, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to set execution lock: {e}")


def _get_recent_trade_ids() -> List[str]:
    """Get recent trade IDs from audit log."""
    try:
        data_dir = _BASE_DIR / "data"
        ledger_path = data_dir / "performance_ledger.json"
        if not ledger_path.exists():
            return []
        with open(ledger_path, "r") as f:
            data = json.load(f)
        trades = data.get("trades", [])
        return [t.get("id", "") for t in trades[-100:] if t.get("id")]
    except Exception:
        return []


def _log_rollback(commit_before: str, commit_after: str):
    """Log rollback event to history."""
    history = _get_rollback_history()
    history.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from_commit": commit_before,
        "to_commit": commit_after,
    })
    # Keep last 50 entries
    history = history[-50:]
    try:
        with open(_ROLLBACK_LOG_PATH, "w") as f:
            json.dump(history, f, indent=2)
    except IOError:
        pass


def _get_rollback_history() -> List[Dict[str, Any]]:
    """Read rollback history."""
    if not _ROLLBACK_LOG_PATH.exists():
        return []
    try:
        with open(_ROLLBACK_LOG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


# CLI entry point
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "--save":
        save_stable_state()
        print("Stable state saved.")
    elif len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        result = rollback(dry_run=True)
        print(f"Dry run: {result.message}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        status = get_rollback_status()
        print(json.dumps(status, indent=2))
    else:
        print("Executing rollback...")
        result = rollback()
        print(f"Result: {result.message}")
        print(f"  Config restored: {result.config_restored}")
        print(f"  History preserved: {result.trade_history_preserved}")
        sys.exit(0 if result.success else 1)
