"""Protocol definitions (structural typing) for pluggable components."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class TTSBackend(Protocol):
    """Protocol for text-to-speech backend implementations.

    Any class implementing this protocol can be used as an audio backend.
    """

    @property
    def name(self) -> str:
        """Human-readable name of the backend."""
        ...

    async def synthesize(self, text: str, output_path: Path, *, voice: str) -> bool:
        """Synthesize text to an audio file.

        Args:
            text: The text to convert to speech.
            output_path: Path to write the audio file.
            voice: Voice identifier specific to the backend.

        Returns:
            True if synthesis succeeded, False otherwise.
        """
        ...

    async def close(self) -> None:
        """Clean up any resources (connection pools, sessions, etc.)."""
        ...


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol for cache backend implementations."""

    def get(self, key: str) -> bytes | None:
        """Retrieve cached value by key. Returns None on miss."""
        ...

    def set(self, key: str, value: bytes, *, ttl: int | None = None) -> None:
        """Store a value in the cache with optional TTL."""
        ...

    def invalidate(self, key: str) -> None:
        """Remove a specific key from the cache."""
        ...

    def clear(self) -> None:
        """Clear all cached entries."""
        ...
