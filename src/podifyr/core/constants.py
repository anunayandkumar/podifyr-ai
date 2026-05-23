"""Application-wide constants and sentinel values."""

from __future__ import annotations

from typing import Final


# ─── File System ─────────────────────────────────────────────────────────────

IGNORED_DIRECTORIES: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "venv",
        ".venv",
        "env",
        ".env",
        "__pycache__",
        "node_modules",
        ".tox",
        ".nox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".eggs",
        "site-packages",
        ".ipynb_checkpoints",
        "migrations",
    }
)

IGNORED_FILE_PATTERNS: Final[frozenset[str]] = frozenset(
    {
        "setup.py",
        "conftest.py",
    }
)

PYTHON_FILE_EXTENSION: Final[str] = ".py"

# ─── LLM Defaults ───────────────────────────────────────────────────────────

DEFAULT_LLM_MODEL: Final[str] = "gpt-4o-mini"
DEFAULT_LLM_TEMPERATURE: Final[float] = 0.3
DEFAULT_LLM_MAX_TOKENS: Final[int] = 2048
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_BASE_DELAY: Final[float] = 1.0

# ─── Audio Defaults ─────────────────────────────────────────────────────────

DEFAULT_TTS_VOICE: Final[str] = "alloy"
DEFAULT_TTS_MODEL: Final[str] = "tts-1"
DEFAULT_MAX_CONCURRENT_REQUESTS: Final[int] = 5
DEFAULT_TTS_TIMEOUT_SECONDS: Final[int] = 120
AUDIO_CHUNK_PREFIX: Final[str] = "chunk_"
AUDIO_FILE_EXTENSION: Final[str] = ".mp3"
FINAL_OUTPUT_FILENAME: Final[str] = "walkthrough.mp3"

# ─── Cache Defaults ──────────────────────────────────────────────────────────

DEFAULT_CACHE_TTL_SECONDS: Final[int] = 86400  # 24 hours
CACHE_NAMESPACE_PARSE: Final[str] = "parse"
CACHE_NAMESPACE_SCRIPT: Final[str] = "script"
CACHE_NAMESPACE_AUDIO: Final[str] = "audio"

# ─── CLI ─────────────────────────────────────────────────────────────────────

APP_NAME: Final[str] = "podifyr"
OUTPUT_DIR_DEFAULT: Final[str] = "./podifyr_output"
CHUNKS_SUBDIR: Final[str] = "chunks"
SCRIPT_FILENAME: Final[str] = "walkthrough_script.md"
