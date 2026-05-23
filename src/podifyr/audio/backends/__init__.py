"""Abstract base for TTS backend implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseTTSBackend(ABC):
    """Abstract base class for text-to-speech backends.

    All TTS backend implementations must inherit from this class
    and implement the synthesize() and close() methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the backend."""

    @abstractmethod
    async def synthesize(self, text: str, output_path: Path, *, voice: str) -> bool:
        """Synthesize text to an audio file.

        Args:
            text: The text to convert to speech.
            output_path: Path to write the audio file.
            voice: Voice identifier specific to the backend.

        Returns:
            True if synthesis succeeded, False otherwise.
        """

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources (connection pools, sessions, etc.)."""

    async def __aenter__(self) -> "BaseTTSBackend":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
