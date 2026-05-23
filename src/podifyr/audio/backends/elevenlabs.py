"""ElevenLabs TTS backend implementation (optional dependency)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import aiohttp

from podifyr.audio.backends import BaseTTSBackend
from podifyr.core.constants import DEFAULT_TTS_TIMEOUT_SECONDS
from podifyr.logging import get_logger
from podifyr.utils.retry import async_retry_with_backoff


logger = get_logger(__name__)

_ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Default voice IDs for ElevenLabs
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" - default


class ElevenLabsTTSBackend(BaseTTSBackend):
    """ElevenLabs TTS API backend for high-quality audio synthesis.

    Requires the 'elevenlabs' extra: pip install podifyr-ai[elevenlabs]
    """

    def __init__(
        self,
        api_key: str,
        model_id: str = "eleven_monolingual_v1",
        timeout: int = DEFAULT_TTS_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._model_id = model_id
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    @property
    def name(self) -> str:
        return "ElevenLabs"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={
                    "xi-api-key": self._api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
            )
        return self._session

    async def synthesize(
        self, text: str, output_path: Path, *, voice: str = _DEFAULT_VOICE_ID
    ) -> bool:
        """Synthesize text to MP3 using the ElevenLabs API.

        Args:
            text: Text to synthesize.
            output_path: Path to write the audio file.
            voice: ElevenLabs voice ID.

        Returns:
            True on success, False on failure.
        """
        if not text.strip():
            logger.warning("elevenlabs_empty_input", output=str(output_path))
            return False

        try:
            return await self._synthesize_with_retry(text, output_path, voice)
        except Exception as exc:
            logger.error(
                "elevenlabs_synthesis_failed",
                output=str(output_path),
                error=str(exc),
            )
            return False

    @async_retry_with_backoff(
        max_retries=3,
        base_delay=1.5,
        retryable_exceptions=(aiohttp.ClientError, asyncio.TimeoutError, OSError),
    )
    async def _synthesize_with_retry(
        self,
        text: str,
        output_path: Path,
        voice: str,
    ) -> bool:
        """Internal synthesis with retry."""
        session = await self._get_session()
        url = f"{_ELEVENLABS_TTS_URL}/{voice}"

        payload = {
            "text": text,
            "model_id": self._model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with session.post(url, json=payload) as response:
            if response.status == 429:
                retry_after = response.headers.get("Retry-After", "10")
                logger.warning("elevenlabs_rate_limited", retry_after=retry_after)
                await asyncio.sleep(float(retry_after))
                raise aiohttp.ClientError("Rate limited")

            if response.status != 200:
                error_body = await response.text()
                logger.warning(
                    "elevenlabs_api_error",
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
                "elevenlabs_chunk_written",
                path=str(output_path),
                bytes=len(content),
            )
            return True

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
