"""Custom exception hierarchy for podifyr.

All exceptions inherit from PodifyrError to allow broad catching at the CLI boundary.
Each module raises specific exceptions to enable granular error handling.
"""

from __future__ import annotations


class PodifyrError(Exception):
    """Base exception for all podifyr errors."""

    def __init__(self, message: str, *, context: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


# ─── Parsing Errors ──────────────────────────────────────────────────────────


class ParsingError(PodifyrError):
    """Raised when file or directory parsing fails unrecoverably."""


class FileSyntaxError(ParsingError):
    """Raised when a Python file contains invalid syntax."""

    def __init__(self, file_path: str, line: int | None = None, detail: str = "") -> None:
        msg = f"Syntax error in {file_path}"
        if line is not None:
            msg += f" at line {line}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg, context={"file_path": file_path, "line": line})
        self.file_path = file_path
        self.line = line


# ─── Graph Errors ────────────────────────────────────────────────────────────


class GraphCycleError(PodifyrError):
    """Raised when the dependency graph contains unresolvable cycles."""

    def __init__(self, cycles: list[list[str]]) -> None:
        cycle_strs = [" -> ".join(c) for c in cycles[:5]]
        msg = f"Dependency graph contains {len(cycles)} cycle(s): {'; '.join(cycle_strs)}"
        super().__init__(msg, context={"cycles": cycles})
        self.cycles = cycles


# ─── LLM / Agent Errors ─────────────────────────────────────────────────────


class LLMError(PodifyrError):
    """Raised when an LLM API call fails after retries."""

    def __init__(self, provider: str, detail: str, *, status_code: int | None = None) -> None:
        msg = f"LLM error ({provider}): {detail}"
        if status_code is not None:
            msg += f" [HTTP {status_code}]"
        super().__init__(msg, context={"provider": provider, "status_code": status_code})
        self.provider = provider
        self.status_code = status_code


class ScriptGenerationError(PodifyrError):
    """Raised when script generation fails for a module."""


# ─── Audio Errors ────────────────────────────────────────────────────────────


class AudioGenerationError(PodifyrError):
    """Raised when TTS audio generation fails."""

    def __init__(self, chunk_index: int, detail: str) -> None:
        msg = f"Audio generation failed for chunk {chunk_index}: {detail}"
        super().__init__(msg, context={"chunk_index": chunk_index})
        self.chunk_index = chunk_index


class AudioStitchingError(PodifyrError):
    """Raised when FFmpeg audio concatenation fails."""

    def __init__(self, detail: str, *, stderr: str = "") -> None:
        msg = f"Audio stitching failed: {detail}"
        super().__init__(msg, context={"stderr": stderr[:500]})
        self.stderr = stderr


# ─── Configuration Errors ────────────────────────────────────────────────────


class ConfigurationError(PodifyrError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, field: str, detail: str) -> None:
        msg = f"Configuration error for '{field}': {detail}"
        super().__init__(msg, context={"field": field})
        self.field = field


# ─── Cache Errors ────────────────────────────────────────────────────────────


class CacheError(PodifyrError):
    """Raised when cache operations fail (non-fatal, logged as warning)."""
