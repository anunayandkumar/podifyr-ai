"""Edge TTS backend implementation (free Microsoft neural voices, no API key required)."""

from __future__ import annotations

from pathlib import Path

import edge_tts

from podifyr.audio.backends import BaseTTSBackend
from podifyr.logging import get_logger


logger = get_logger(__name__)

# Mapping of short voice aliases to full Edge TTS voice names
_VOICE_MAP: dict[str, str] = {
    "alloy": "en-US-AndrewMultilingualNeural",
    "echo": "en-US-BrianMultilingualNeural",
    "fable": "en-GB-RyanNeural",
    "nova": "en-US-AvaMultilingualNeural",
    "onyx": "en-US-SteffanNeural",
    "shimmer": "en-US-EmmaMultilingualNeural",
}


def _resolve_voice(voice: str) -> str:
    """Resolve a short alias to a full Edge TTS voice name."""
    return _VOICE_MAP.get(voice, voice)


class EdgeTTSBackend(BaseTTSBackend):
    """Edge TTS backend using Microsoft's free neural TTS voices.

    No API key or Azure subscription required. Uses the same neural voice
    engine as Microsoft Edge's read-aloud feature.
    """

    @property
    def name(self) -> str:
        return "Edge TTS"

    async def synthesize(self, text: str, output_path: Path, *, voice: str = "alloy") -> bool:
        """Synthesize text to MP3 using Edge TTS.

        Args:
            text: Text to convert to speech.
            output_path: Path to write the .mp3 file.
            voice: Voice identifier (short alias or full Edge TTS voice name).

        Returns:
            True on success, False on failure.
        """
        if not text.strip():
            logger.warning("edge_tts_empty_input", output=str(output_path))
            return False

        resolved_voice = _resolve_voice(voice)

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            communicate = edge_tts.Communicate(text, resolved_voice)
            await communicate.save(str(output_path))

            logger.debug(
                "edge_tts_chunk_written",
                path=str(output_path),
                voice=resolved_voice,
            )
            return True

        except Exception as exc:
            logger.error(
                "edge_tts_synthesis_failed",
                output=str(output_path),
                error=str(exc),
            )
            return False

    async def close(self) -> None:
        """No persistent resources to clean up for Edge TTS."""
