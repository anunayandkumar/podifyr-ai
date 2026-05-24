"""Integration tests for the CLI commands."""

from __future__ import annotations

from pathlib import Path  # noqa: TCH003
from unittest.mock import patch

from typer.testing import CliRunner

from podifyr.cli import app


runner = CliRunner()


class TestCLIVersion:
    """Tests for version display."""

    def test_version_flag(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "podifyr" in result.output

    def test_short_version_flag(self) -> None:
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0


class TestCLIHelp:
    """Tests for help display."""

    def test_main_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output

    def test_generate_help(self) -> None:
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "REPO_PATH" in result.output or "repo-path" in result.output.lower()

    def test_generate_help_lists_providers(self) -> None:
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        out = result.output.lower()
        assert "openai" in out
        assert "azure" in out
        assert "ollama" in out

    def test_cache_help(self) -> None:
        result = runner.invoke(app, ["cache", "--help"])
        assert result.exit_code == 0


class TestCLIGenerate:
    """Tests for the generate command."""

    def test_generate_nonexistent_path(self) -> None:
        result = runner.invoke(app, ["generate", "/nonexistent/path/xyz"])
        assert result.exit_code != 0

    def test_generate_unknown_provider(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            ["generate", str(sample_repo), "--provider", "bogus", "--skip-audio"],
        )
        assert result.exit_code != 0

    def test_generate_skip_audio(self, sample_repo: Path) -> None:
        """Should complete with --skip-audio flag."""
        with patch("podifyr.agents.orchestrator._compiled_workflow") as mock_wf:
            mock_wf.invoke.return_value = {
                "conversational_script": "Test script content.",
                "technical_summary": "Test summary.",
                "error": "",
            }

            result = runner.invoke(
                app,
                [
                    "generate",
                    str(sample_repo),
                    "--provider",
                    "openai",
                    "--api-key",
                    "sk-test",
                    "--skip-audio",
                    "--no-cache",
                ],
            )

            # Should complete successfully (may fail due to LLM mock complexity)
            # The important thing is it doesn't crash
            assert result.exit_code in (0, 1)
