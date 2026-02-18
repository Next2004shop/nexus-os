"""
NEXUS Version Control Tagging — Phase 12 (C)
===============================================

At startup:
    - Print version number
    - Print Git commit hash
    - Log deployment timestamp

Reads from /version.json and Git state.
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("nexus.version")

_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_VERSION_FILE = _BASE_DIR / "version.json"


def _read_version_json() -> Dict[str, Any]:
    """Read version.json."""
    if not _VERSION_FILE.exists():
        return {"version": "0.0.0", "last_updated": "", "environment": ""}
    try:
        with open(_VERSION_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"version": "0.0.0", "last_updated": "", "environment": ""}


def _write_version_json(data: Dict[str, Any]):
    """Write version.json."""
    try:
        with open(_VERSION_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        logger.error(f"Failed to write version.json: {e}")


def get_git_commit_hash() -> str:
    """Get current Git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(_BASE_DIR),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return "unknown"


def get_git_branch() -> str:
    """Get current Git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(_BASE_DIR),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return "unknown"


def get_version_info() -> Dict[str, Any]:
    """Get complete version information."""
    version_data = _read_version_json()
    return {
        "version": version_data.get("version", "0.0.0"),
        "phase": version_data.get("phase", ""),
        "git_commit": get_git_commit_hash(),
        "git_branch": get_git_branch(),
        "last_updated": version_data.get("last_updated", ""),
        "environment": version_data.get("environment", ""),
    }


def stamp_deployment(env_mode: str):
    """
    Stamp version.json with current deployment info.

    Called at startup to record when and where deployment happened.
    """
    version_data = _read_version_json()
    version_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    version_data["environment"] = env_mode
    _write_version_json(version_data)

    info = get_version_info()

    logger.info("=" * 50)
    logger.info(f"  NEXUS v{info['version']}")
    logger.info(f"  Commit:      {info['git_commit']}")
    logger.info(f"  Branch:      {info['git_branch']}")
    logger.info(f"  Environment: {env_mode}")
    logger.info(f"  Deployed:    {version_data['last_updated']}")
    logger.info("=" * 50)

    # Also print to stdout for container logs
    print(f"\n{'=' * 50}")
    print(f"  NEXUS v{info['version']}  |  {info['git_commit']}  |  {env_mode}")
    print(f"  Deployed: {version_data['last_updated']}")
    print(f"{'=' * 50}\n")

    return info
