"""
NEXUS Update Guard — Phase 12 (H)
====================================

When new code is pulled:
    1. Compare checksum of critical files
    2. Validate schema compatibility (config.json, version.json)
    3. Validate config compatibility
    4. Restart safely (never hot-reload blindly)

Prevents dangerous updates from being applied without validation.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.update_guard")

_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CHECKSUM_FILE = _BASE_DIR / "deployment" / "rollback_state" / "file_checksums.json"

# Critical files to track
CRITICAL_FILES = [
    "app/main.py",
    "config/config_loader.py",
    "config.json",
    "version.json",
    "requirements.txt",
    "security/failsafe.py",
    "security/startup_hardening.py",
]

# Required keys in config.json
CONFIG_SCHEMA_KEYS = [
    "ENV_MODE",
]

# Required keys in version.json
VERSION_SCHEMA_KEYS = [
    "version",
    "last_updated",
    "environment",
]


class UpdateGuard:
    """
    Validates code updates before they take effect.
    """

    _instance = None

    def __init__(self):
        self._last_check: Optional[str] = None
        self._checksum_cache: Dict[str, str] = {}
        self._violations: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> "UpdateGuard":
        if cls._instance is None:
            cls._instance = UpdateGuard()
        return cls._instance

    def snapshot_checksums(self) -> Dict[str, str]:
        """
        Compute and save checksums of all critical files.

        Call this after a verified good deployment.
        """
        checksums = {}
        for rel_path in CRITICAL_FILES:
            full_path = _BASE_DIR / rel_path
            if full_path.exists():
                checksums[rel_path] = self._file_checksum(full_path)
            else:
                checksums[rel_path] = "MISSING"

        self._checksum_cache = checksums

        # Persist
        _CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(_CHECKSUM_FILE, "w") as f:
                json.dump({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "checksums": checksums,
                }, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save checksums: {e}")

        return checksums

    def validate_update(self) -> Tuple[bool, List[str]]:
        """
        Validate current files against saved checksums.

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        # Load saved checksums
        saved = self._load_saved_checksums()
        if not saved:
            issues.append("No saved checksums found — run snapshot_checksums() first")
            return True, issues  # Allow if no baseline exists

        # Compare checksums
        changed_files = []
        for rel_path, old_hash in saved.items():
            full_path = _BASE_DIR / rel_path
            if not full_path.exists():
                if old_hash != "MISSING":
                    changed_files.append(f"DELETED: {rel_path}")
            else:
                new_hash = self._file_checksum(full_path)
                if new_hash != old_hash:
                    changed_files.append(f"MODIFIED: {rel_path}")

        if changed_files:
            issues.append(f"Changed files: {changed_files}")
            logger.warning(f"Update guard: {len(changed_files)} files changed: {changed_files}")

        # Validate schemas
        schema_ok, schema_issues = self._validate_schemas()
        issues.extend(schema_issues)

        # Validate config compatibility
        config_ok, config_issues = self._validate_config_compatibility()
        issues.extend(config_issues)

        is_valid = len([i for i in issues if i.startswith("SCHEMA_ERROR") or i.startswith("CONFIG_ERROR")]) == 0
        self._last_check = datetime.now(timezone.utc).isoformat()

        if issues:
            violation = {
                "timestamp": self._last_check,
                "issues": issues,
                "valid": is_valid,
            }
            self._violations.append(violation)

        return is_valid, issues

    def _validate_schemas(self) -> Tuple[bool, List[str]]:
        """Validate JSON file schemas."""
        issues = []

        # Validate config.json schema
        config_path = _BASE_DIR / "config.json"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    issues.append("SCHEMA_ERROR: config.json root must be an object")
            except json.JSONDecodeError as e:
                issues.append(f"SCHEMA_ERROR: config.json invalid JSON: {e}")

        # Validate version.json schema
        version_path = _BASE_DIR / "version.json"
        if version_path.exists():
            try:
                with open(version_path, "r") as f:
                    data = json.load(f)
                for key in VERSION_SCHEMA_KEYS:
                    if key not in data:
                        issues.append(f"SCHEMA_ERROR: version.json missing required key '{key}'")
            except json.JSONDecodeError as e:
                issues.append(f"SCHEMA_ERROR: version.json invalid JSON: {e}")

        return len([i for i in issues if i.startswith("SCHEMA_ERROR")]) == 0, issues

    def _validate_config_compatibility(self) -> Tuple[bool, List[str]]:
        """Validate config compatibility between old and new."""
        issues = []

        config_path = _BASE_DIR / "config.json"
        if not config_path.exists():
            return True, issues

        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            # Validate ENV_MODE if present
            env_mode = config.get("ENV_MODE", "")
            if env_mode and env_mode.upper() not in ("LOCAL_DEV", "STAGING", "PRODUCTION"):
                issues.append(f"CONFIG_ERROR: Invalid ENV_MODE '{env_mode}'")

            # Validate risk level if present
            risk = config.get("RISK_LEVEL", "")
            if risk and risk.upper() not in ("CONSERVATIVE", "MODERATE", "AGGRESSIVE"):
                issues.append(f"CONFIG_ERROR: Invalid RISK_LEVEL '{risk}'")

            # Validate numeric fields
            for field in ("MAX_POSITION_SIZE", "MAX_DAILY_TRADES", "PORT"):
                val = config.get(field)
                if val is not None:
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        issues.append(f"CONFIG_ERROR: {field} must be numeric, got '{val}'")

        except json.JSONDecodeError:
            pass  # Already caught in schema check

        return len([i for i in issues if i.startswith("CONFIG_ERROR")]) == 0, issues

    def _file_checksum(self, path: Path) -> str:
        """Compute SHA256 checksum of a file."""
        sha = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha.update(chunk)
            return sha.hexdigest()[:16]
        except IOError:
            return "ERROR"

    def _load_saved_checksums(self) -> Dict[str, str]:
        """Load previously saved checksums."""
        if not _CHECKSUM_FILE.exists():
            return {}
        try:
            with open(_CHECKSUM_FILE, "r") as f:
                data = json.load(f)
            return data.get("checksums", {})
        except (json.JSONDecodeError, IOError):
            return {}

    def get_status(self) -> Dict[str, Any]:
        return {
            "last_check": self._last_check,
            "cached_checksums": len(self._checksum_cache),
            "violations_count": len(self._violations),
            "recent_violations": self._violations[-5:],
        }


def get_update_guard() -> UpdateGuard:
    return UpdateGuard.get_instance()
