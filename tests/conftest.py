"""Test configuration and shared fixtures."""

from __future__ import annotations

import tempfile
from collections.abc import Generator  # noqa: TCH003
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset runtime settings between tests so cases never leak into each other."""
    from podifyr.config import reset_settings

    monkeypatch.chdir(tmp_path)
    reset_settings()
    yield
    reset_settings()


@pytest.fixture()
def tmp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture()
def sample_python_file(tmp_dir: Path) -> Path:
    """Create a sample Python file for parsing tests."""
    file_path = tmp_dir / "sample_module.py"
    file_path.write_text(
        '''\
"""A sample module for testing AST parsing."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from some_package.module import SomeClass


CONSTANT_VALUE: int = 42
ANOTHER_CONSTANT = "hello"


class BaseProcessor:
    """Base class for all processors."""

    def __init__(self, name: str) -> None:
        """Initialize the processor."""
        self.name = name

    def process(self, data: list[str]) -> dict[str, int]:
        """Process input data and return results."""
        result = {}
        for item in data:
            result[item] = len(item)
        return result


class AsyncProcessor(BaseProcessor):
    """Async variant of the processor."""

    async def process_async(self, data: list[str], *, timeout: float = 30.0) -> dict[str, int]:
        """Process data asynchronously."""
        import asyncio
        await asyncio.sleep(0)
        return self.process(data)


def helper_function(x: int, y: int = 10) -> int:
    """A simple helper function."""
    return x + y


async def async_helper(items: list[str]) -> Optional[str]:
    """An async helper function."""
    if not items:
        return None
    return items[0]


if __name__ == "__main__":
    processor = BaseProcessor("test")
    print(processor.process(["hello", "world"]))
''',
        encoding="utf-8",
    )
    return file_path


@pytest.fixture()
def sample_repo(tmp_dir: Path) -> Path:
    """Create a sample repository structure for integration tests."""
    repo_dir = tmp_dir / "sample_repo"
    repo_dir.mkdir()

    # Package init
    (repo_dir / "__init__.py").write_text(
        '"""Sample repository root package."""\n',
        encoding="utf-8",
    )

    # Core module
    core_dir = repo_dir / "core"
    core_dir.mkdir()
    (core_dir / "__init__.py").write_text(
        '"""Core sub-package."""\nfrom sample_repo.core.engine import Engine\n',
        encoding="utf-8",
    )
    (core_dir / "engine.py").write_text(
        '''\
"""The main processing engine."""

from sample_repo.core.models import DataModel


class Engine:
    """Orchestrates data processing."""

    def __init__(self) -> None:
        self.model = DataModel()

    def run(self, input_data: str) -> str:
        """Run the processing pipeline."""
        return self.model.transform(input_data)
''',
        encoding="utf-8",
    )
    (core_dir / "models.py").write_text(
        '''\
"""Data models for the engine."""


class DataModel:
    """Represents processed data."""

    def transform(self, data: str) -> str:
        """Transform input data."""
        return data.upper()
''',
        encoding="utf-8",
    )

    # Utils module
    utils_dir = repo_dir / "utils"
    utils_dir.mkdir()
    (utils_dir / "__init__.py").write_text("", encoding="utf-8")
    (utils_dir / "helpers.py").write_text(
        '''\
"""Utility helpers."""


def format_output(data: str, width: int = 80) -> str:
    """Format output string to given width."""
    return data.center(width)
''',
        encoding="utf-8",
    )

    # Create venv directory that should be skipped
    venv_dir = repo_dir / "venv"
    venv_dir.mkdir()
    (venv_dir / "should_skip.py").write_text("# should be skipped", encoding="utf-8")

    return repo_dir


@pytest.fixture()
def mock_settings() -> None:  # noqa: PT004
    """Install an in-memory settings object with a fake OpenAI API key for tests."""
    from podifyr.config import LLMConfig, Settings, set_settings

    set_settings(
        Settings(
            llm=LLMConfig(provider="openai", api_key="sk-test-fake-key-for-testing"),
        )
    )
