"""Azure OpenAI TTS backend implementation."""

from __future__ import annotations

import asyncio
from pathlib import Path

import aiohttp

from podifyr.audio.backends import BaseTTSBackend
from podifyr.core.constants import DEFAULT_TTS_TIMEOUT_SECONDS, DEFAULT_TTS_VOICE
from podifyr.logging import get_logger
from podifyr.utils.retry import async_retry_with_backoff


logger = get_logger(__name__)


class AzureTTSBackend(BaseTTSBackend):
    """Azure OpenAI TTS API backend for audio synthesis.

    Calls the Azure OpenAI deployments REST endpoint for speech generation.
    Implements retry with exponential backoff for transient failures.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str = "2024-12-01-preview",
        timeout: int = DEFAULT_TTS_TIMEOUT_SECONDS,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._deployment = deployment
        self._api_version = api_version
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    @property
    def name(self) -> str:
        return "Azure OpenAI TTS"

    @property
    def _tts_url(self) -> str:
        """Construct the Azure OpenAI TTS endpoint URL."""
        return (
            f"{self._endpoint}/openai/deployments/{self._deployment}"
            f"/audio/speech?api-version={self._api_version}"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session (lazy initialization)."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={
                    "api-key": self._api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._session

    async def synthesize(
        self, text: str, output_path: Path, *, voice: str = DEFAULT_TTS_VOICE
    ) -> bool:
        """Synthesize text to MP3 using the Azure OpenAI TTS API.

        Args:
            text: Text to convert to speech.
            output_path: Path to write the .mp3 file.
            voice: Voice identifier (alloy, echo, fable, onyx, nova, shimmer).

        Returns:
            True on success, False on failure.
        """
        if not text.strip():
            logger.warning("azure_tts_empty_input", output=str(output_path))
            return False

        try:
            return await self._synthesize_with_retry(text, output_path, voice)
        except Exception as exc:
            logger.error(
                "azure_tts_synthesis_failed",
                output=str(output_path),
                error=str(exc),
            )
            return False

    @async_retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        retryable_exceptions=(aiohttp.ClientError, asyncio.TimeoutError, OSError),
    )
    async def _synthesize_with_retry(
        self,
        text: str,
        output_path: Path,
        voice: str,
    ) -> bool:
        """Internal synthesis with retry logic."""
        session = await self._get_session()

        payload = {
            "model": self._deployment,
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }

        async with session.post(self._tts_url, json=payload) as response:
            if response.status == 429:
                retry_after = response.headers.get("Retry-After", "5")
                logger.warning("azure_tts_rate_limited", retry_after=retry_after)
                await asyncio.sleep(float(retry_after))
                raise aiohttp.ClientError("Rate limited")

            if response.status != 200:
                error_body = await response.text()
                logger.warning(
                    "azure_tts_api_error",
                    status=response.status,
                    body=error_body[:200],
                )
                if response.status >= 500:
                    raise aiohttp.ClientError(f"Server error: {response.status}")
                return False

            content = await response.read()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(content)

            logger.debug(
                "azure_tts_chunk_written",
                path=str(output_path),
                bytes=len(content),
            )
            return True

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
