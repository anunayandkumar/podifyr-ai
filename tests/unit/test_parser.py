"""Unit tests for the parsing engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from podifyr.parsing import parse_directory, parse_file
from podifyr.parsing.models import ModuleMetadata


if TYPE_CHECKING:
    from pathlib import Path


class TestParseFile:
    """Tests for single-file parsing."""

    def test_parse_valid_file(self, sample_python_file: Path) -> None:
        """Should successfully parse a valid Python file."""
        result = parse_file(sample_python_file)

        assert result is not None
        assert isinstance(result, ModuleMetadata)
        assert result.file_path == str(sample_python_file)

    def test_parse_extracts_module_docstring(self, sample_python_file: Path) -> None:
        """Should extract the module-level docstring."""
        result = parse_file(sample_python_file)

        assert result is not None
        assert result.module_docstring == "A sample module for testing AST parsing."

    def test_parse_extracts_imports(self, sample_python_file: Path) -> None:
        """Should extract all import statements."""
        result = parse_file(sample_python_file)

        assert result is not None
        import_paths = [imp.full_path for imp in result.imports]
        assert "os" in import_paths
        assert "pathlib.Path" in import_paths
        assert "some_package.module.SomeClass" in import_paths

    def test_parse_extracts_classes(self, sample_python_file: Path) -> None:
        """Should extract class definitions with methods."""
        result = parse_file(sample_python_file)

        assert result is not None
        assert len(result.classes) == 2

        base_proc = next(c for c in result.classes if c.name == "BaseProcessor")
        assert base_proc.docstring == "Base class for all processors."
        assert len(base_proc.methods) == 2
        assert base_proc.methods[0].name == "__init__"

    def test_parse_extracts_functions(self, sample_python_file: Path) -> None:
        """Should extract top-level function definitions."""
        result = parse_file(sample_python_file)

        assert result is not None
        func_names = [f.name for f in result.functions]
        assert "helper_function" in func_names
        assert "async_helper" in func_names

    def test_parse_detects_async_functions(self, sample_python_file: Path) -> None:
        """Should correctly identify async functions."""
        result = parse_file(sample_python_file)

        assert result is not None
        async_helper = next(f for f in result.functions if f.name == "async_helper")
        assert async_helper.is_async is True

        helper = next(f for f in result.functions if f.name == "helper_function")
        assert helper.is_async is False

    def test_parse_detects_main_guard(self, sample_python_file: Path) -> None:
        """Should detect if __name__ == '__main__' guard."""
        result = parse_file(sample_python_file)

        assert result is not None
        assert result.has_main_guard is True

    def test_parse_extracts_constants(self, sample_python_file: Path) -> None:
        """Should extract UPPER_CASE module-level constants."""
        result = parse_file(sample_python_file)

        assert result is not None
        assert "CONSTANT_VALUE" in result.global_constants
        assert "ANOTHER_CONSTANT" in result.global_constants

    def test_parse_counts_lines(self, sample_python_file: Path) -> None:
        """Should count the number of lines in the file."""
        result = parse_file(sample_python_file)

        assert result is not None
        assert result.line_count > 0

    def test_parse_nonexistent_file(self, tmp_dir: Path) -> None:
        """Should return None for non-existent files."""
        result = parse_file(tmp_dir / "does_not_exist.py")
        assert result is None

    def test_parse_syntax_error(self, tmp_dir: Path) -> None:
        """Should return None for files with syntax errors."""
        bad_file = tmp_dir / "bad_syntax.py"
        bad_file.write_text("def broken(\n", encoding="utf-8")

        result = parse_file(bad_file)
        assert result is None

    def test_parse_empty_file(self, tmp_dir: Path) -> None:
        """Should handle empty files gracefully."""
        empty_file = tmp_dir / "empty.py"
        empty_file.write_text("", encoding="utf-8")

        result = parse_file(empty_file)
        assert result is not None
        assert result.classes == []
        assert result.functions == []
        assert result.imports == []

    def test_parse_extracts_function_arguments(self, sample_python_file: Path) -> None:
        """Should extract function arguments with type annotations."""
        result = parse_file(sample_python_file)

        assert result is not None
        helper = next(f for f in result.functions if f.name == "helper_function")
        assert "x: int" in helper.arguments
        assert "y: int" in helper.arguments

    def test_parse_extracts_return_type(self, sample_python_file: Path) -> None:
        """Should extract function return type annotations."""
        result = parse_file(sample_python_file)

        assert result is not None
        helper = next(f for f in result.functions if f.name == "helper_function")
        assert helper.returns == "int"

    def test_parse_extracts_base_classes(self, sample_python_file: Path) -> None:
        """Should extract class inheritance information."""
        result = parse_file(sample_python_file)

        assert result is not None
        async_proc = next(c for c in result.classes if c.name == "AsyncProcessor")
        assert "BaseProcessor" in async_proc.base_classes


class TestParseDirectory:
    """Tests for directory parsing."""

    def test_parse_directory_success(self, sample_repo: Path) -> None:
        """Should parse all Python files in a directory."""
        results = parse_directory(sample_repo)

        assert len(results) > 0
        file_paths = [r.file_path for r in results]
        # Should include engine.py and models.py
        assert any("engine.py" in fp for fp in file_paths)
        assert any("models.py" in fp for fp in file_paths)

    def test_parse_directory_skips_venv(self, sample_repo: Path) -> None:
        """Should skip venv directories."""
        results = parse_directory(sample_repo)

        file_paths = [r.file_path for r in results]
        assert not any("venv" in fp for fp in file_paths)

    def test_parse_directory_nonexistent(self, tmp_dir: Path) -> None:
        """Should return empty list for non-existent directory."""
        results = parse_directory(tmp_dir / "nonexistent")
        assert results == []

    def test_parse_directory_empty(self, tmp_dir: Path) -> None:
        """Should return empty list for directory with no .py files."""
        empty_dir = tmp_dir / "empty_project"
        empty_dir.mkdir()
        (empty_dir / "readme.md").write_text("# Empty", encoding="utf-8")

        results = parse_directory(empty_dir)
        assert results == []


class TestModuleVisitor:
    """Tests for the AST visitor directly."""

    def test_visitor_handles_decorators(self, tmp_dir: Path) -> None:
        """Should extract decorator information."""
        file_path = tmp_dir / "decorated.py"
        file_path.write_text(
            """\
from functools import lru_cache
from dataclasses import dataclass

@dataclass
class Config:
    name: str
    value: int

@lru_cache(maxsize=128)
def cached_func(x: int) -> int:
    return x * 2
""",
            encoding="utf-8",
        )

        result = parse_file(file_path)
        assert result is not None

        config_cls = next(c for c in result.classes if c.name == "Config")
        assert config_cls.is_dataclass is True
        assert "dataclass" in config_cls.decorators

        cached = next(f for f in result.functions if f.name == "cached_func")
        assert any("lru_cache" in d for d in cached.decorators)
