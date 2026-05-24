"""LLM provider factory: build a LangChain chat model for the active provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

from podifyr.config import get_settings
from podifyr.core.exceptions import ConfigurationError


if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


def build_chat_model(temperature: float) -> BaseChatModel:
    """Build a chat model for the configured LLM provider.

    Supported providers: ``openai``, ``azure``, ``ollama``.
    Reads :class:`podifyr.config.settings.LLMConfig` from the active settings.
    """
    cfg = get_settings().llm

    if cfg.provider == "azure":
        if not cfg.azure_endpoint:
            raise ConfigurationError(
                field="--azure-endpoint",
                detail="Azure endpoint is required when --provider=azure.",
            )
        if not cfg.azure_deployment:
            raise ConfigurationError(
                field="--azure-deployment",
                detail="Azure deployment name is required when --provider=azure.",
            )
        if not cfg.api_key:
            raise ConfigurationError(
                field="--api-key",
                detail="Azure API key is required when --provider=azure.",
            )
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_endpoint=cfg.azure_endpoint,
            azure_deployment=cfg.azure_deployment,
            openai_api_version=cfg.azure_api_version,
            api_key=cfg.api_key,
            temperature=temperature,
            max_tokens=cfg.max_tokens,
        )

    if cfg.provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover - import-time guard
            raise ConfigurationError(
                field="--provider",
                detail=(
                    "Ollama provider requires the 'langchain-ollama' package. "
                    "Install it with: pip install langchain-ollama"
                ),
            ) from exc

        return ChatOllama(
            model=cfg.model,
            base_url=cfg.ollama_base_url,
            temperature=temperature,
            num_predict=cfg.max_tokens,
        )

    # OpenAI provider (default)
    if not cfg.api_key:
        raise ConfigurationError(
            field="--api-key",
            detail="OpenAI API key is required when --provider=openai.",
        )
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=cfg.model,
        temperature=temperature,
        max_tokens=cfg.max_tokens,
        api_key=cfg.api_key,
    )


__all__ = ["build_chat_model"]
