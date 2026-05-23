"""Filesystem utilities for directory traversal and path normalization."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from podifyr.core.constants import IGNORED_DIRECTORIES, PYTHON_FILE_EXTENSION
from podifyr.logging import get_logger


logger = get_logger(__name__)


def should_skip_directory(dir_name: str) -> bool:
    """Determine if a directory should be skipped during traversal.

    Checks against known non-source directories and hidden directory patterns.
    """
    if dir_name in IGNORED_DIRECTORIES:
        return True
    if dir_name.startswith("."):
        return True
    if dir_name.endswith(".egg-info"):
        return True
    return False


def collect_python_files(target_dir: Path) -> list[Path]:
    """Recursively collect all Python files in a directory, respecting ignore rules.

    Args:
        target_dir: Root directory to traverse.

    Returns:
        Sorted list of Python file paths.
    """
    if not target_dir.is_dir():
        logger.error("target_not_found", path=str(target_dir))
        return []

    python_files: list[Path] = []

    for path in target_dir.rglob(f"*{PYTHON_FILE_EXTENSION}"):
        skip = False
        try:
            relative = path.relative_to(target_dir)
        except ValueError:
            continue

        for parent in relative.parents:
            if parent.name and should_skip_directory(parent.name):
                skip = True
                break

        if not skip:
            python_files.append(path)

    python_files.sort()
    logger.info("files_collected", count=len(python_files), root=str(target_dir))
    return python_files


def normalize_module_path(file_path: str, strip_src: bool = True) -> str:
    """Convert a file path to a dotted module name suitable for graph labeling.

    Args:
        file_path: The file path to normalize (can use either / or \\).
        strip_src: Whether to strip a leading 'src/' prefix.

    Returns:
        A dotted module path string (e.g., 'podifyr.parsing.engine').
    """
    posix_path = file_path.replace("\\", "/")
    parts = list(PurePosixPath(posix_path).parts)

    # Strip common prefixes
    if strip_src and parts and parts[0] == "src":
        parts = parts[1:]

    # Remove .py extension from the last part
    if parts and parts[-1].endswith(PYTHON_FILE_EXTENSION):
        parts[-1] = parts[-1][: -len(PYTHON_FILE_EXTENSION)]

    # Remove __init__ as it represents the package itself
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)
