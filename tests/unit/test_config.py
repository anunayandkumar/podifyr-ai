"""Unit tests for the configuration module."""

from __future__ import annotations

import os

import pytest

from podifyr.config.settings import Settings, get_settings, reset_settings


class TestSettings:
    """Tests for application settings."""

    def test_default_settings(self) -> None:
        """Should create settings with sensible defaults."""
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )

        assert settings.llm.model == "gpt-4o-mini"
        assert settings.llm.temperature == 0.3
        assert settings.tts.backend == "edge"
        assert settings.tts.voice == "alloy"
        assert settings.cache.enabled is True

    def test_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should load settings from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("PODIFYR_LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("PODIFYR_TTS_VOICE", "nova")

        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )

        assert settings.openai_api_key == "sk-test-key"
        assert settings.llm.model == "gpt-4o"
        assert settings.tts.voice == "nova"

    def test_effective_openai_key_from_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should resolve API key from root-level setting."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-root")

        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )

        assert settings.effective_openai_key == "sk-from-root"

    def test_log_level_normalization(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should normalize log level to uppercase."""
        monkeypatch.setenv("PODIFYR_LOG_LEVEL", "debug")

        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )

        assert settings.logging.level == "DEBUG"

    def test_get_settings_cached(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should cache settings instance."""
        reset_settings()
        monkeypatch.setenv("OPENAI_API_KEY", "sk-cached")

        s1 = get_settings()
        s2 = get_settings()

        assert s1 is s2
        reset_settings()

    def test_reset_settings_clears_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should clear the cached settings on reset."""
        reset_settings()
        monkeypatch.setenv("OPENAI_API_KEY", "sk-first")
        s1 = get_settings()

        reset_settings()
        monkeypatch.setenv("OPENAI_API_KEY", "sk-second")
        s2 = get_settings()

        assert s1 is not s2
        reset_settings()

    def test_azure_settings_defaults(self) -> None:
        """Should have Azure disabled by default."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]

        assert settings.azure.enabled is False
        assert settings.azure.endpoint == ""
        assert settings.azure.api_version == "2024-12-01-preview"
        assert settings.is_azure is False

    def test_azure_enabled_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should configure Azure settings from env vars."""
        monkeypatch.setenv("PODIFYR_AZURE_ENABLED", "true")
        monkeypatch.setenv("PODIFYR_AZURE_ENDPOINT", "https://my-resource.openai.azure.com")
        monkeypatch.setenv("PODIFYR_AZURE_API_KEY", "azure-key-123")
        monkeypatch.setenv("PODIFYR_AZURE_CHAT_DEPLOYMENT", "gpt-4o-mini")

        settings = Settings(_env_file=None)  # type: ignore[call-arg]

        assert settings.azure.enabled is True
        assert settings.azure.endpoint == "https://my-resource.openai.azure.com"
        assert settings.azure.api_key == "azure-key-123"
        assert settings.azure.chat_deployment == "gpt-4o-mini"
        assert settings.is_azure is True

    def test_effective_key_uses_azure_when_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return Azure API key when Azure is enabled."""
        monkeypatch.setenv("PODIFYR_AZURE_ENABLED", "true")
        monkeypatch.setenv("PODIFYR_AZURE_ENDPOINT", "https://x.openai.azure.com")
        monkeypatch.setenv("PODIFYR_AZURE_API_KEY", "azure-key")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

        settings = Settings(_env_file=None)  # type: ignore[call-arg]

        assert settings.effective_openai_key == "azure-key"
