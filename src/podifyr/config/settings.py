"""Runtime configuration objects, populated explicitly by the CLI.

No environment variables, no .env files. All values come from CLI flags
(or in-process callers using `set_settings`).
"""

from __future__ import annotations

from pathlib import Path  # noqa: TCH003
from typing import Literal

from pydantic import BaseModel, Field, field_validator


LLMProvider = Literal["openai", "azure", "ollama"]
TTSBackend = Literal["edge", "openai", "elevenlabs"]


class LLMConfig(BaseModel):
    """Configuration for the chat LLM provider."""

    provider: LLMProvider = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=128, le=16384)
    api_key: str = ""

    # Azure-specific
    azure_endpoint: str = ""
    azure_deployment: str = ""
    azure_api_version: str = "2024-12-01-preview"

    # Ollama-specific
    ollama_base_url: str = "http://localhost:11434"


class TTSConfig(BaseModel):
    """Configuration for text-to-speech synthesis."""

    backend: TTSBackend = "edge"
    voice: str = "alloy"
    model: str = "tts-1"
    max_concurrent_requests: int = Field(default=5, ge=1, le=20)
    timeout_seconds: int = Field(default=120, ge=10)

    # OpenAI / ElevenLabs key (independent of the LLM key)
    api_key: str = ""

    # When LLM provider is "azure" and backend is "openai", these are used.
    azure_deployment: str = "tts"


class CacheConfig(BaseModel):
    """Configuration for the disk cache."""

    enabled: bool = True
    ttl_seconds: int = Field(default=86400, ge=0)
    directory: Path | None = None


class LoggingConfig(BaseModel):
    """Configuration for structured logging."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["console", "json"] = "console"

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class Settings(BaseModel):
    """Root application settings, composing all sub-configs."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the current runtime settings (defaults if none were set)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def set_settings(settings: Settings) -> None:
    """Install a new runtime settings instance (called by the CLI at startup)."""
    global _settings
    _settings = settings


def reset_settings() -> None:
    """Clear the current settings (useful for tests)."""
    global _settings
    _settings = None
