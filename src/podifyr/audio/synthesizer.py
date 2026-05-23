"""Audio synthesizer: orchestrates concurrent TTS generation across chunks."""

from __future__ import annotations

import asyncio
from pathlib import Path

from podifyr.audio.backends import BaseTTSBackend
from podifyr.audio.backends.openai_tts import OpenAITTSBackend
from podifyr.config import get_settings
from podifyr.core.constants import AUDIO_CHUNK_PREFIX, AUDIO_FILE_EXTENSION
from podifyr.core.exceptions import AudioGenerationError, ConfigurationError
from podifyr.core.types import AudioChunkResult
from podifyr.logging import get_logger


logger = get_logger(__name__)


def _create_backend() -> BaseTTSBackend:
    """Factory: create the appropriate TTS backend based on configuration."""
    settings = get_settings()
    backend_name = settings.tts.backend

    # Azure OpenAI TTS takes priority when Azure is enabled
    if settings.is_azure and backend_name == "openai":
        from podifyr.audio.backends.azure_tts import AzureTTSBackend

        if not settings.azure.api_key:
            raise ConfigurationError(
                field="PODIFYR_AZURE_API_KEY",
                detail="Azure OpenAI API key is required for TTS. Set PODIFYR_AZURE_API_KEY.",
            )
        return AzureTTSBackend(
            endpoint=settings.azure.endpoint,
            api_key=settings.azure.api_key,
            deployment=settings.azure.tts_deployment,
            api_version=settings.azure.api_version,
            timeout=settings.tts.timeout_seconds,
        )

    if backend_name == "openai":
        api_key = settings.effective_openai_key
        if not api_key:
            raise ConfigurationError(
                field="OPENAI_API_KEY",
                detail="OpenAI API key is required for TTS. Set OPENAI_API_KEY environment variable.",
            )
        return OpenAITTSBackend(
            api_key=api_key,
            model=settings.tts.model,
            timeout=settings.tts.timeout_seconds,
        )

    elif backend_name == "edge":
        from podifyr.audio.backends.edge_tts import EdgeTTSBackend

        return EdgeTTSBackend()

    elif backend_name == "elevenlabs":
        api_key = settings.elevenlabs_api_key
        if not api_key:
            raise ConfigurationError(
                field="ELEVENLABS_API_KEY",
                detail="ElevenLabs API key is required. Set ELEVENLABS_API_KEY environment variable.",
            )
        from podifyr.audio.backends.elevenlabs import ElevenLabsTTSBackend

        return ElevenLabsTTSBackend(api_key=api_key)

    else:
        raise ConfigurationError(
            field="PODIFYR_TTS_BACKEND",
            detail=f"Unknown TTS backend: '{backend_name}'. Supported: openai, edge, elevenlabs.",
        )


async def _generate_chunk(
    backend: BaseTTSBackend,
    text: str,
    output_path: Path,
    voice: str,
    index: int,
    semaphore: asyncio.Semaphore,
) -> AudioChunkResult:
    """Generate a single audio chunk with concurrency control.

    Args:
        backend: TTS backend instance.
        text: Text content for this chunk.
        output_path: Where to write the audio file.
        voice: Voice identifier.
        index: Chunk index for ordering.
        semaphore: Concurrency limiter.

    Returns:
        AudioChunkResult with success status and metadata.
    """
    async with semaphore:
        if not text.strip():
            return AudioChunkResult(
                index=index,
                success=False,
                path=None,
                error="Empty text chunk",
                bytes_written=0,
            )

        success = await backend.synthesize(text, output_path, voice=voice)

        if success and output_path.exists():
            bytes_written = output_path.stat().st_size
            return AudioChunkResult(
                index=index,
                success=True,
                path=output_path,
                error=None,
                bytes_written=bytes_written,
            )
        else:
            return AudioChunkResult(
                index=index,
                success=False,
                path=None,
                error="Synthesis returned failure",
                bytes_written=0,
            )


async def _generate_all_chunks(
    script_chunks: list[str],
    output_dir: Path,
    voice: str,
    max_concurrent: int,
) -> list[AudioChunkResult]:
    """Generate all audio chunks concurrently."""
    backend = _create_backend()
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[AudioChunkResult] = []

    try:
        tasks: list[asyncio.Task[AudioChunkResult]] = []

        for idx, chunk_text in enumerate(script_chunks):
            output_path = output_dir / f"{AUDIO_CHUNK_PREFIX}{idx:04d}{AUDIO_FILE_EXTENSION}"
            task = asyncio.create_task(
                _generate_chunk(
                    backend=backend,
                    text=chunk_text,
                    output_path=output_path,
                    voice=voice,
                    index=idx,
                    semaphore=semaphore,
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    finally:
        await backend.close()

    return sorted(results, key=lambda r: r["index"])


def generate_audio_chunks(
    script_chunks: list[str],
    output_dir: Path,
    voice: str | None = None,
    max_concurrent: int | None = None,
) -> list[Path]:
    """Generate audio chunks from script text using the configured TTS backend.

    Orchestrates concurrent API calls with rate limiting and retry logic.

    Args:
        script_chunks: List of text segments to convert to speech.
        output_dir: Directory to write audio chunk files.
        voice: Override voice identifier (uses config default if None).
        max_concurrent: Override max concurrency (uses config default if None).

    Returns:
        List of paths to successfully generated audio files, in order.

    Raises:
        ConfigurationError: If required API keys are missing.
    """
    settings = get_settings()
    voice = voice or settings.tts.voice
    max_concurrent = max_concurrent or settings.tts.max_concurrent_requests

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "audio_generation_started",
        chunks=len(script_chunks),
        backend=settings.tts.backend,
        voice=voice,
        concurrency=max_concurrent,
    )

    results = asyncio.run(
        _generate_all_chunks(
            script_chunks=script_chunks,
            output_dir=output_dir,
            voice=voice,
            max_concurrent=max_concurrent,
        )
    )

    successful_paths: list[Path] = []
    failed_count = 0

    for result in results:
        if result["success"] and result["path"] is not None:
            successful_paths.append(result["path"])
        else:
            failed_count += 1
            logger.warning(
                "audio_chunk_failed",
                index=result["index"],
                error=result["error"],
            )

    logger.info(
        "audio_generation_complete",
        succeeded=len(successful_paths),
        failed=failed_count,
        total=len(script_chunks),
    )

    return successful_paths
