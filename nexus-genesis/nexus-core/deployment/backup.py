"""
NEXUS Automated Backup — Phase 12 (F)
========================================

Every 24 hours, backup:
    - Trade history (performance_ledger.json)
    - Performance ledger
    - State snapshot (market_regime.json)
    - Security logs

Store in: /backups/yyyy-mm-dd/
Auto-prune: keep last 30 days.
"""

import asyncio
import json
import logging
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.backup")

_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BACKUPS_DIR = _BASE_DIR / "backups"
_DATA_DIR = _BASE_DIR / "data"
_LOGS_DIR = _BASE_DIR / "logs"
_STATE_DIR = _BASE_DIR / "state"

BACKUP_INTERVAL_SECONDS = 86400  # 24 hours
DEFAULT_RETENTION_DAYS = 30


class BackupManager:
    """
    Automated backup system with periodic execution and pruning.
    """

    _instance = None

    def __init__(self):
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._last_backup: Optional[str] = None
        self._backup_count: int = 0
        self._retention_days: int = DEFAULT_RETENTION_DAYS
        self._errors: List[str] = []

    @classmethod
    def get_instance(cls) -> "BackupManager":
        if cls._instance is None:
            cls._instance = BackupManager()
        return cls._instance

    def configure(self, retention_days: int = DEFAULT_RETENTION_DAYS):
        """Configure backup retention."""
        self._retention_days = max(1, retention_days)

    def run_backup_now(self) -> Dict[str, Any]:
        """
        Run a backup immediately.

        Backs up:
            1. Trade history / performance ledger
            2. State snapshots
            3. Security logs

        Returns dict with backup details.
        """
        timestamp = datetime.now(timezone.utc)
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H%M%S")
        backup_dir = _BACKUPS_DIR / date_str / time_str

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = f"Cannot create backup directory: {e}"
            logger.error(msg)
            self._errors.append(msg)
            return {"success": False, "error": msg}

        files_backed_up = []
        errors = []

        # 1. Trade history / performance ledger
        ledger_src = _DATA_DIR / "performance_ledger.json"
        if ledger_src.exists():
            try:
                shutil.copy2(str(ledger_src), str(backup_dir / "performance_ledger.json"))
                files_backed_up.append("performance_ledger.json")
            except Exception as e:
                errors.append(f"performance_ledger.json: {e}")

        # 2. State snapshots
        if _STATE_DIR.exists():
            state_backup = backup_dir / "state"
            state_backup.mkdir(exist_ok=True)
            for state_file in _STATE_DIR.glob("*.json"):
                try:
                    shutil.copy2(str(state_file), str(state_backup / state_file.name))
                    files_backed_up.append(f"state/{state_file.name}")
                except Exception as e:
                    errors.append(f"state/{state_file.name}: {e}")

        # 3. Security logs
        if _LOGS_DIR.exists():
            logs_backup = backup_dir / "logs"
            logs_backup.mkdir(exist_ok=True)
            for log_file in _LOGS_DIR.glob("*.log"):
                try:
                    shutil.copy2(str(log_file), str(logs_backup / log_file.name))
                    files_backed_up.append(f"logs/{log_file.name}")
                except Exception as e:
                    errors.append(f"logs/{log_file.name}: {e}")

        # 4. Config snapshot
        config_src = _BASE_DIR / "config.json"
        if config_src.exists():
            try:
                shutil.copy2(str(config_src), str(backup_dir / "config.json"))
                files_backed_up.append("config.json")
            except Exception as e:
                errors.append(f"config.json: {e}")

        # 5. Version snapshot
        version_src = _BASE_DIR / "version.json"
        if version_src.exists():
            try:
                shutil.copy2(str(version_src), str(backup_dir / "version.json"))
                files_backed_up.append("version.json")
            except Exception as e:
                errors.append(f"version.json: {e}")

        # Write backup manifest
        manifest = {
            "timestamp": timestamp.isoformat(),
            "files": files_backed_up,
            "errors": errors,
            "backup_path": str(backup_dir),
        }
        try:
            with open(backup_dir / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
        except IOError:
            pass

        self._last_backup = timestamp.isoformat()
        self._backup_count += 1
        self._errors.extend(errors)

        if errors:
            logger.warning(f"Backup completed with {len(errors)} errors: {errors}")
        else:
            logger.info(f"Backup completed: {len(files_backed_up)} files to {backup_dir}")

        # Auto-prune old backups
        pruned = self._prune_old_backups()

        return {
            "success": len(errors) == 0,
            "timestamp": timestamp.isoformat(),
            "backup_path": str(backup_dir),
            "files_backed_up": files_backed_up,
            "errors": errors,
            "pruned_count": pruned,
        }

    def _prune_old_backups(self) -> int:
        """Remove backups older than retention_days."""
        if not _BACKUPS_DIR.exists():
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        pruned = 0

        for entry in sorted(_BACKUPS_DIR.iterdir()):
            if not entry.is_dir():
                continue
            # Directory name is YYYY-MM-DD
            dir_name = entry.name
            if len(dir_name) == 10 and dir_name < cutoff_str:
                try:
                    shutil.rmtree(str(entry))
                    pruned += 1
                    logger.info(f"Pruned old backup: {dir_name}")
                except Exception as e:
                    logger.error(f"Failed to prune {dir_name}: {e}")

        return pruned

    def get_last_backup_date(self) -> Optional[str]:
        """Get the most recent backup date."""
        if self._last_backup:
            return self._last_backup

        if not _BACKUPS_DIR.exists():
            return None

        dates = sorted(
            [d.name for d in _BACKUPS_DIR.iterdir() if d.is_dir() and len(d.name) == 10],
            reverse=True,
        )
        return dates[0] if dates else None

    async def start(self):
        """Start the automated backup loop (24h cycle)."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._backup_loop())
        logger.info("Automated backup system started")

    async def stop(self):
        """Stop the backup loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Automated backup system stopped")

    async def _backup_loop(self):
        """Periodic backup loop."""
        # Run initial backup after 60 seconds
        await asyncio.sleep(60)

        while self._running:
            try:
                self.run_backup_now()
            except Exception as e:
                logger.error(f"Backup cycle error: {e}")
            await asyncio.sleep(BACKUP_INTERVAL_SECONDS)

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "last_backup": self._last_backup,
            "backup_count": self._backup_count,
            "retention_days": self._retention_days,
            "recent_errors": self._errors[-5:],
            "backups_dir": str(_BACKUPS_DIR),
        }


def get_backup_manager() -> BackupManager:
    return BackupManager.get_instance()
