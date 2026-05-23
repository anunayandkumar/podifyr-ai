"""Application settings with layered resolution: defaults < env < .env file < CLI flags."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureSettings(BaseSettings):
    """Settings for Azure OpenAI deployments."""

    model_config = SettingsConfigDict(
        env_prefix="PODIFYR_AZURE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(default=False, description="Use Azure OpenAI instead of public OpenAI.")
    endpoint: str = Field(default="", description="Azure OpenAI resource endpoint URL.")
    api_key: str = Field(default="", description="Azure OpenAI API key.")
    api_version: str = Field(
        default="2024-12-01-preview", description="Azure OpenAI API version."
    )
    chat_deployment: str = Field(
        default="", description="Azure deployment name for the chat/completion model."
    )
    tts_deployment: str = Field(
        default="tts", description="Azure deployment name for TTS."
    )


class LLMSettings(BaseSettings):
    """Settings for the LLM (Large Language Model) provider."""

    model_config = SettingsConfigDict(
        env_prefix="PODIFYR_LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = Field(default="gpt-4o-mini", description="LLM model identifier.")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Sampling temperature.")
    max_tokens: int = Field(default=2048, ge=128, le=16384, description="Max response tokens.")
    api_key: str = Field(default="", description="OpenAI API key (prefer OPENAI_API_KEY env var).")


class TTSSettings(BaseSettings):
    """Settings for the text-to-speech engine."""

    model_config = SettingsConfigDict(
        env_prefix="PODIFYR_TTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend: Literal["openai", "edge", "elevenlabs"] = Field(
        default="edge", description="TTS backend provider."
    )
    voice: str = Field(default="alloy", description="Voice identifier.")
    model: str = Field(default="tts-1", description="TTS model identifier.")
    max_concurrent_requests: int = Field(
        default=5, ge=1, le=20, description="Max parallel TTS API requests."
    )
    timeout_seconds: int = Field(default=120, ge=10, description="Per-request timeout.")


class CacheSettings(BaseSettings):
    """Settings for the caching layer."""

    model_config = SettingsConfigDict(
        env_prefix="PODIFYR_CACHE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(default=True, description="Enable/disable caching.")
    ttl_seconds: int = Field(default=86400, ge=0, description="Cache time-to-live in seconds.")
    directory: Path | None = Field(default=None, description="Custom cache directory path.")


class LoggingSettings(BaseSettings):
    """Settings for structured logging."""

    model_config = SettingsConfigDict(
        env_prefix="PODIFYR_LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log level."
    )
    format: Literal["console", "json"] = Field(
        default="console", description="Log output format."
    )

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class Settings(BaseSettings):
    """Root application settings, composing all sub-settings."""

    model_config = SettingsConfigDict(
        env_prefix="PODIFYR_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # API keys at root level for convenience
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")

    # Sub-settings
    azure: AzureSettings = Field(default_factory=AzureSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @property
    def effective_openai_key(self) -> str:
        """Resolve the OpenAI API key from available sources."""
        if self.azure.enabled:
            return self.azure.api_key
        return self.openai_api_key or self.llm.api_key

    @property
    def is_azure(self) -> bool:
        """Whether Azure OpenAI is the active provider."""
        return self.azure.enabled and bool(self.azure.endpoint)


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the singleton application settings instance.

    Settings are loaded once and cached. Call this from anywhere in the app.
    Resolution order: defaults < environment variables < .env file.
    """
    return Settings()


def reset_settings() -> None:
    """Clear the cached settings instance (useful for testing)."""
    get_settings.cache_clear()
