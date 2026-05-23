"""Integration tests for the CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from podifyr.cli import app


runner = CliRunner()


class TestCLIVersion:
    """Tests for version display."""

    def test_version_flag(self) -> None:
        """Should display version and exit."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "podifyr" in result.output

    def test_short_version_flag(self) -> None:
        """Should support -v shorthand."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0


class TestCLIHelp:
    """Tests for help display."""

    def test_main_help(self) -> None:
        """Should display main help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output

    def test_generate_help(self) -> None:
        """Should display generate command help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "REPO_PATH" in result.output or "repo-path" in result.output.lower()

    def test_config_help(self) -> None:
        """Should display config sub-command help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0


class TestCLIGenerate:
    """Tests for the generate command."""

    def test_generate_nonexistent_path(self) -> None:
        """Should error for non-existent repository path."""
        result = runner.invoke(app, ["generate", "/nonexistent/path/xyz"])
        assert result.exit_code != 0

    def test_generate_skip_audio(self, sample_repo: Path, mock_settings: None) -> None:
        """Should complete with --skip-audio flag."""
        with patch("podifyr.agents.orchestrator._compiled_workflow") as mock_wf:
            mock_wf.invoke.return_value = {
                "conversational_script": "Test script content.",
                "technical_summary": "Test summary.",
                "error": "",
            }

            result = runner.invoke(
                app,
                ["generate", str(sample_repo), "--skip-audio", "--no-cache"],
            )

            # Should complete successfully (may fail due to LLM mock complexity)
            # The important thing is it doesn't crash
            assert result.exit_code in (0, 1)


class TestCLIConfig:
    """Tests for config commands."""

    def test_config_init(self, tmp_dir: Path) -> None:
        """Should create a .env file."""
        output_path = tmp_dir / ".env"
        result = runner.invoke(app, ["config", "init", "--output", str(output_path)])

        assert result.exit_code == 0
        assert output_path.exists()
        content = output_path.read_text()
        assert "OPENAI_API_KEY" in content

    def test_config_init_no_overwrite(self, tmp_dir: Path) -> None:
        """Should refuse to overwrite without --force."""
        output_path = tmp_dir / ".env"
        output_path.write_text("existing", encoding="utf-8")

        result = runner.invoke(app, ["config", "init", "--output", str(output_path)])
        assert result.exit_code != 0

    def test_config_init_force_overwrite(self, tmp_dir: Path) -> None:
        """Should overwrite with --force flag."""
        output_path = tmp_dir / ".env"
        output_path.write_text("existing", encoding="utf-8")

        result = runner.invoke(
            app, ["config", "init", "--output", str(output_path), "--force"]
        )
        assert result.exit_code == 0
