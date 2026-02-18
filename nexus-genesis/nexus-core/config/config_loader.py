"""
NEXUS Configuration Loader — Phase 12 (A + B)
================================================

All configuration loaded from:
    1. .env file (via dotenv or OS env)
    2. config.json (structured settings)
    3. Environment variables (override)

HARDCODED VALUES ARE FORBIDDEN.

Environments:
    - LOCAL_DEV:   Debug logging, paper trading only, verbose Telegram
    - STAGING:     Info logging, paper trading, normal Telegram
    - PRODUCTION:  Warning logging, live trading allowed, minimal Telegram

Production NEVER defaults to aggressive risk.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("nexus.config")

_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONFIG_JSON_PATH = _BASE_DIR / "config.json"
_ENV_FILE_PATH = _BASE_DIR / ".env"


class EnvironmentMode(str, Enum):
    LOCAL_DEV = "LOCAL_DEV"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


# Environment-specific defaults — PRODUCTION is always conservative
_ENV_DEFAULTS: Dict[str, Dict[str, Any]] = {
    EnvironmentMode.LOCAL_DEV: {
        "log_level": "DEBUG",
        "risk_level": "CONSERVATIVE",
        "execution_allowed": False,
        "paper_trading": True,
        "telegram_verbosity": "VERBOSE",
        "max_position_size": 0.01,
        "max_daily_trades": 50,
        "cors_origins": "http://localhost:3000,http://localhost:5173",
    },
    EnvironmentMode.STAGING: {
        "log_level": "INFO",
        "risk_level": "CONSERVATIVE",
        "execution_allowed": False,
        "paper_trading": True,
        "telegram_verbosity": "NORMAL",
        "max_position_size": 0.05,
        "max_daily_trades": 30,
        "cors_origins": "http://localhost:3000,http://localhost:5173",
    },
    EnvironmentMode.PRODUCTION: {
        "log_level": "WARNING",
        "risk_level": "CONSERVATIVE",
        "execution_allowed": True,
        "paper_trading": False,
        "telegram_verbosity": "MINIMAL",
        "max_position_size": 0.1,
        "max_daily_trades": 20,
        "cors_origins": "",
    },
}


@dataclass
class NexusConfig:
    """Immutable configuration snapshot."""

    # Environment
    env_mode: EnvironmentMode = EnvironmentMode.LOCAL_DEV

    # Logging
    log_level: str = "INFO"

    # Risk
    risk_level: str = "CONSERVATIVE"
    max_position_size: float = 0.01
    max_daily_trades: int = 20

    # Execution
    execution_allowed: bool = False
    paper_trading: bool = True

    # Telegram
    telegram_verbosity: str = "NORMAL"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Infrastructure
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    host: str = "0.0.0.0"
    port: int = 8080

    # Google Cloud
    google_cloud_project: str = ""
    google_application_credentials: str = ""

    # Trading Secrets (presence only, never logged)
    has_mt5_credentials: bool = False
    has_binance_credentials: bool = False

    # Deployment
    deployment_lock: bool = False
    backup_enabled: bool = True
    backup_retention_days: int = 30
    resource_monitoring_enabled: bool = True

    # Raw config.json data for extensibility
    _raw_json: Dict[str, Any] = field(default_factory=dict, repr=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value from raw JSON or attributes."""
        if hasattr(self, key):
            return getattr(self, key)
        return self._raw_json.get(key, default)

    def is_production(self) -> bool:
        return self.env_mode == EnvironmentMode.PRODUCTION

    def is_local_dev(self) -> bool:
        return self.env_mode == EnvironmentMode.LOCAL_DEV

    def is_staging(self) -> bool:
        return self.env_mode == EnvironmentMode.STAGING

    def to_safe_dict(self) -> Dict[str, Any]:
        """Return config dict with secrets masked."""
        return {
            "env_mode": self.env_mode.value,
            "log_level": self.log_level,
            "risk_level": self.risk_level,
            "max_position_size": self.max_position_size,
            "max_daily_trades": self.max_daily_trades,
            "execution_allowed": self.execution_allowed,
            "paper_trading": self.paper_trading,
            "telegram_verbosity": self.telegram_verbosity,
            "telegram_configured": bool(self.telegram_bot_token),
            "host": self.host,
            "port": self.port,
            "has_mt5_credentials": self.has_mt5_credentials,
            "has_binance_credentials": self.has_binance_credentials,
            "deployment_lock": self.deployment_lock,
            "backup_enabled": self.backup_enabled,
            "backup_retention_days": self.backup_retention_days,
            "resource_monitoring_enabled": self.resource_monitoring_enabled,
        }


def _load_env_file() -> Dict[str, str]:
    """Load .env file if present (simple parser, no external dependency)."""
    env_vars: Dict[str, str] = {}
    if not _ENV_FILE_PATH.exists():
        return env_vars

    with open(_ENV_FILE_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
    return env_vars


def _load_config_json() -> Dict[str, Any]:
    """Load config.json if present."""
    if not _CONFIG_JSON_PATH.exists():
        return {}
    try:
        with open(_CONFIG_JSON_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load config.json: {e}")
        return {}


def _resolve_value(key: str, env_vars: Dict[str, str], json_config: Dict[str, Any], default: Any = None) -> Any:
    """
    Resolution order:
        1. OS environment variable (highest priority)
        2. .env file
        3. config.json
        4. default
    """
    # OS env overrides everything
    os_val = os.environ.get(key)
    if os_val is not None:
        return os_val

    # .env file
    if key in env_vars:
        return env_vars[key]

    # config.json (supports nested via dot notation not needed here)
    if key in json_config:
        return json_config[key]

    return default


def load_config() -> NexusConfig:
    """
    Load and merge configuration from all sources.

    Priority: OS env > .env file > config.json > environment defaults.
    """
    env_vars = _load_env_file()
    json_config = _load_config_json()

    # Determine environment mode
    env_mode_str = _resolve_value("ENV_MODE", env_vars, json_config, "LOCAL_DEV")
    try:
        env_mode = EnvironmentMode(env_mode_str.upper())
    except ValueError:
        logger.warning(f"Invalid ENV_MODE '{env_mode_str}', defaulting to LOCAL_DEV")
        env_mode = EnvironmentMode.LOCAL_DEV

    # Get environment defaults
    defaults = _ENV_DEFAULTS[env_mode]

    # Build config
    config = NexusConfig(
        env_mode=env_mode,
        log_level=str(_resolve_value("LOG_LEVEL", env_vars, json_config, defaults["log_level"])).upper(),
        risk_level=str(_resolve_value("RISK_LEVEL", env_vars, json_config, defaults["risk_level"])).upper(),
        max_position_size=float(_resolve_value("MAX_POSITION_SIZE", env_vars, json_config, defaults["max_position_size"])),
        max_daily_trades=int(_resolve_value("MAX_DAILY_TRADES", env_vars, json_config, defaults["max_daily_trades"])),
        execution_allowed=_to_bool(_resolve_value("EXECUTION_ALLOWED", env_vars, json_config, defaults["execution_allowed"])),
        paper_trading=_to_bool(_resolve_value("PAPER_TRADING", env_vars, json_config, defaults["paper_trading"])),
        telegram_verbosity=str(_resolve_value("TELEGRAM_VERBOSITY", env_vars, json_config, defaults["telegram_verbosity"])).upper(),
        telegram_bot_token=str(_resolve_value("TELEGRAM_BOT_TOKEN", env_vars, json_config, "") or ""),
        telegram_chat_id=str(_resolve_value("TELEGRAM_CHAT_ID", env_vars, json_config, "") or ""),
        cors_origins=str(_resolve_value("ALLOWED_ORIGINS", env_vars, json_config, defaults["cors_origins"])),
        host=str(_resolve_value("HOST", env_vars, json_config, "0.0.0.0")),
        port=int(_resolve_value("PORT", env_vars, json_config, 8080)),
        google_cloud_project=str(_resolve_value("GOOGLE_CLOUD_PROJECT", env_vars, json_config, "") or ""),
        google_application_credentials=str(_resolve_value("GOOGLE_APPLICATION_CREDENTIALS", env_vars, json_config, "") or ""),
        has_mt5_credentials=bool(_resolve_value("MT5_LOGIN", env_vars, json_config)),
        has_binance_credentials=bool(_resolve_value("BINANCE_API_KEY", env_vars, json_config)),
        deployment_lock=_to_bool(_resolve_value("DEPLOYMENT_LOCK", env_vars, json_config, False)),
        backup_enabled=_to_bool(_resolve_value("BACKUP_ENABLED", env_vars, json_config, True)),
        backup_retention_days=int(_resolve_value("BACKUP_RETENTION_DAYS", env_vars, json_config, 30)),
        resource_monitoring_enabled=_to_bool(_resolve_value("RESOURCE_MONITORING_ENABLED", env_vars, json_config, True)),
        _raw_json=json_config,
    )

    # SAFETY: Production can never default to aggressive risk
    if config.is_production() and config.risk_level == "AGGRESSIVE":
        logger.critical("PRODUCTION environment cannot use AGGRESSIVE risk — forcing CONSERVATIVE")
        config.risk_level = "CONSERVATIVE"

    logger.info(f"Configuration loaded: env={config.env_mode.value}, risk={config.risk_level}, "
                f"execution={'LIVE' if config.execution_allowed else 'PAPER'}")
    return config


def _to_bool(value: Any) -> bool:
    """Convert various representations to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


# Singleton
_config: Optional[NexusConfig] = None


def get_config() -> NexusConfig:
    """Get the global configuration singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> NexusConfig:
    """Force reload configuration from all sources."""
    global _config
    _config = load_config()
    return _config
