"""Parsing engine: orchestrates file collection, AST parsing, and caching."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from podifyr.logging import get_logger
from podifyr.parsing.models import ModuleMetadata
from podifyr.parsing.visitors import ModuleVisitor
from podifyr.utils.fs import collect_python_files, normalize_module_path


if TYPE_CHECKING:
    from pathlib import Path

    from podifyr.cache import CacheManager


logger = get_logger(__name__)


def parse_file(file_path: Path) -> ModuleMetadata | None:
    """Parse a single Python file into structured metadata.

    Uses the AST module to extract imports, classes, functions, and module-level info.
    Returns None if the file cannot be read or contains invalid syntax.

    Args:
        file_path: Absolute path to a Python source file.

    Returns:
        ModuleMetadata instance, or None on failure.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("file_read_failed", file=str(file_path), error=str(exc))
        return None

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        logger.warning(
            "file_syntax_error",
            file=str(file_path),
            line=exc.lineno,
            detail=str(exc.msg),
        )
        return None

    visitor = ModuleVisitor()
    visitor.visit(tree)

    module_name = normalize_module_path(str(file_path))

    return ModuleMetadata(
        file_path=str(file_path),
        module_name=module_name,
        imports=visitor.imports,
        classes=visitor.classes,
        functions=visitor.functions,
        module_docstring=ast.get_docstring(tree),
        line_count=len(source.splitlines()),
        has_main_guard=visitor.has_main_guard,
        global_constants=visitor.global_constants,
    )


def parse_file_cached(
    file_path: Path,
    cache: CacheManager,
) -> ModuleMetadata | None:
    """Parse a file with cache support — returns cached result if content unchanged.

    Args:
        file_path: Path to the Python file.
        cache: CacheManager instance for read/write.

    Returns:
        ModuleMetadata or None on failure.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("file_read_failed", file=str(file_path), error=str(exc))
        return None

    # Check cache first
    cached = cache.get_parsed_module(str(file_path), source)
    if cached is not None:
        try:
            return ModuleMetadata.model_validate(cached)
        except Exception as exc:
            logger.debug("cache_deserialize_failed", file=str(file_path), error=str(exc))

    # Parse fresh
    result = parse_file(file_path)

    # Store in cache
    if result is not None:
        cache.set_parsed_module(str(file_path), source, result.model_dump())

    return result


def parse_directory(
    target_dir: Path,
    cache: CacheManager | None = None,
) -> list[ModuleMetadata]:
    """Traverse a directory and parse all Python files into structured metadata.

    Skips common non-source directories (.git, venv, __pycache__, etc.).
    Gracefully handles unreadable or unparseable files by logging and continuing.

    Args:
        target_dir: Root directory to analyze.
        cache: Optional CacheManager for caching parse results.

    Returns:
        List of successfully parsed ModuleMetadata objects.
    """
    if not target_dir.is_dir():
        logger.error("directory_not_found", path=str(target_dir))
        return []

    python_files = collect_python_files(target_dir)

    if not python_files:
        logger.warning("no_python_files", path=str(target_dir))
        return []

    logger.info("parsing_started", file_count=len(python_files), root=str(target_dir))

    parsed_modules: list[ModuleMetadata] = []
    parse_errors: int = 0

    for file_path in python_files:
        if cache is not None:
            metadata = parse_file_cached(file_path, cache)
        else:
            metadata = parse_file(file_path)

        if metadata is not None:
            parsed_modules.append(metadata)
        else:
            parse_errors += 1

    logger.info(
        "parsing_complete",
        total_files=len(python_files),
        parsed=len(parsed_modules),
        errors=parse_errors,
    )
    return parsed_modules
