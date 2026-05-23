"""OpenAI TTS backend implementation."""

from __future__ import annotations

import asyncio
from pathlib import Path

import aiohttp

from podifyr.audio.backends import BaseTTSBackend
from podifyr.core.constants import DEFAULT_TTS_MODEL, DEFAULT_TTS_TIMEOUT_SECONDS, DEFAULT_TTS_VOICE
from podifyr.logging import get_logger
from podifyr.utils.retry import async_retry_with_backoff


logger = get_logger(__name__)

_OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"


class OpenAITTSBackend(BaseTTSBackend):
    """OpenAI TTS API backend for audio synthesis.

    Uses aiohttp for async HTTP requests with connection pooling.
    Implements retry with exponential backoff for transient failures.
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_TTS_MODEL,
        timeout: int = DEFAULT_TTS_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    @property
    def name(self) -> str:
        return "OpenAI TTS"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session (lazy initialization)."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._session

    async def synthesize(
        self, text: str, output_path: Path, *, voice: str = DEFAULT_TTS_VOICE
    ) -> bool:
        """Synthesize text to MP3 using the OpenAI TTS API.

        Args:
            text: Text to convert to speech.
            output_path: Path to write the .mp3 file.
            voice: OpenAI voice identifier (alloy, echo, fable, onyx, nova, shimmer).

        Returns:
            True on success, False on failure.
        """
        if not text.strip():
            logger.warning("tts_empty_input", output=str(output_path))
            return False

        try:
            return await self._synthesize_with_retry(text, output_path, voice)
        except Exception as exc:
            logger.error(
                "tts_synthesis_failed",
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
            "model": self._model,
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }

        async with session.post(_OPENAI_TTS_URL, json=payload) as response:
            if response.status == 429:
                # Rate limited — raise to trigger retry
                retry_after = response.headers.get("Retry-After", "5")
                logger.warning("tts_rate_limited", retry_after=retry_after)
                await asyncio.sleep(float(retry_after))
                raise aiohttp.ClientError("Rate limited")

            if response.status != 200:
                error_body = await response.text()
                logger.warning(
                    "tts_api_error",
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
                "tts_chunk_written",
                path=str(output_path),
                bytes=len(content),
            )
            return True

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
