"""Configuration sub-package.

Settings are populated explicitly by the CLI (no env vars, no .env file).
"""

from podifyr.config.settings import (
    CacheConfig,
    LLMConfig,
    LLMProvider,
    LoggingConfig,
    Settings,
    TTSBackend,
    TTSConfig,
    get_settings,
    reset_settings,
    set_settings,
)


__all__ = [
    "CacheConfig",
    "LLMConfig",
    "LLMProvider",
    "LoggingConfig",
    "Settings",
    "TTSBackend",
    "TTSConfig",
    "get_settings",
    "reset_settings",
    "set_settings",
]
