"""File filtering logic for the parsing engine."""

from __future__ import annotations

from pathlib import Path

from podifyr.core.constants import IGNORED_FILE_PATTERNS
from podifyr.logging import get_logger


logger = get_logger(__name__)


def should_include_file(file_path: Path) -> bool:
    """Determine whether a Python file should be included in parsing.

    Excludes test files, setup scripts, and other non-architectural files
    that don't contribute to understanding the system architecture.

    Args:
        file_path: Path to evaluate.

    Returns:
        True if the file should be parsed.
    """
    file_name = file_path.name

    # Exclude known non-architectural files
    if file_name in IGNORED_FILE_PATTERNS:
        return False

    # Exclude test files (they describe tests, not architecture)
    if file_name.startswith("test_") or file_name.endswith("_test.py"):
        return False

    # Exclude migration files
    parts = file_path.parts
    if "migrations" in parts or "alembic" in parts:
        return False

    return True


def estimate_file_importance(file_path: Path, line_count: int) -> float:
    """Estimate the architectural importance of a file for prioritization.

    Higher scores indicate files that are more likely to be architecturally significant.

    Args:
        file_path: Path to the file.
        line_count: Number of lines in the file.

    Returns:
        Importance score between 0.0 and 1.0.
    """
    score = 0.5  # Base score

    file_name = file_path.stem

    # Boost for files with architecturally significant names
    significant_names = {
        "app", "main", "core", "base", "engine", "manager",
        "service", "handler", "router", "middleware", "models",
        "schema", "config", "settings", "factory", "registry",
    }
    if file_name in significant_names:
        score += 0.2

    # Boost for __init__.py (package definition)
    if file_name == "__init__" and line_count > 5:
        score += 0.1

    # Penalize very short files (likely empty or trivial)
    if line_count < 10:
        score -= 0.2

    # Boost for substantial files
    if line_count > 100:
        score += 0.1
    if line_count > 300:
        score += 0.1

    return max(0.0, min(1.0, score))
