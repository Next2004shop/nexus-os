"""
NEXUS Configuration Management — Phase 12 (A + B)
===================================================

Environment-aware configuration loading from .env, config.json,
and OS environment variables. No hardcoded values permitted.
"""

from config.config_loader import (
    get_config,
    EnvironmentMode,
    NexusConfig,
)

__all__ = [
    "get_config",
    "EnvironmentMode",
    "NexusConfig",
]
