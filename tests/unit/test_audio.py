"""Unit tests for the audio module."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from podifyr.audio.backends.openai_tts import OpenAITTSBackend
from podifyr.audio.stitcher import _write_concat_list, stitch_audio, verify_ffmpeg_available


class TestOpenAITTSBackend:
    """Tests for the OpenAI TTS backend."""

    def test_backend_name(self) -> None:
        """Should report correct backend name."""
        backend = OpenAITTSBackend(api_key="sk-test")
        assert backend.name == "OpenAI TTS"

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self, tmp_dir: Path) -> None:
        """Should return False for empty text input."""
        backend = OpenAITTSBackend(api_key="sk-test")
        output = tmp_dir / "empty.mp3"

        result = await backend.synthesize("", output, voice="alloy")
        assert result is False

    @pytest.mark.asyncio
    async def test_synthesize_whitespace_text(self, tmp_dir: Path) -> None:
        """Should return False for whitespace-only text."""
        backend = OpenAITTSBackend(api_key="sk-test")
        output = tmp_dir / "whitespace.mp3"

        result = await backend.synthesize("   \n\t  ", output, voice="alloy")
        assert result is False

    @pytest.mark.asyncio
    async def test_close_idempotent(self) -> None:
        """Should handle multiple close() calls safely."""
        backend = OpenAITTSBackend(api_key="sk-test")
        await backend.close()
        await backend.close()  # Should not raise


class TestStitchAudio:
    """Tests for audio stitching."""

    def test_stitch_no_chunks(self, tmp_dir: Path) -> None:
        """Should return False when no chunks exist."""
        result = stitch_audio(tmp_dir, tmp_dir / "output.mp3")
        assert result is False

    def test_stitch_single_chunk(self, tmp_dir: Path) -> None:
        """Should copy single chunk directly."""
        chunk = tmp_dir / "chunk_0000.mp3"
        chunk.write_bytes(b"fake mp3 data")

        output = tmp_dir / "output.mp3"
        result = stitch_audio(tmp_dir, output)

        assert result is True
        assert output.exists()
        assert output.read_bytes() == b"fake mp3 data"

    @patch("podifyr.audio.stitcher.subprocess.run")
    def test_stitch_multiple_chunks_calls_ffmpeg(
        self, mock_run: MagicMock, tmp_dir: Path
    ) -> None:
        """Should call FFmpeg for multiple chunks."""
        # Create fake chunks
        for i in range(3):
            (tmp_dir / f"chunk_{i:04d}.mp3").write_bytes(b"data")

        output = tmp_dir / "output.mp3"
        mock_run.return_value = MagicMock(returncode=0)

        # Create the output file to simulate FFmpeg success
        output.write_bytes(b"merged")
        result = stitch_audio(tmp_dir, output)

        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-y" in cmd
        assert "concat" in cmd

    @patch("podifyr.audio.stitcher.subprocess.run")
    def test_stitch_ffmpeg_failure(self, mock_run: MagicMock, tmp_dir: Path) -> None:
        """Should return False when FFmpeg fails."""
        for i in range(2):
            (tmp_dir / f"chunk_{i:04d}.mp3").write_bytes(b"data")

        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        output = tmp_dir / "output.mp3"

        result = stitch_audio(tmp_dir, output)
        assert result is False

    @patch("podifyr.audio.stitcher.subprocess.run", side_effect=FileNotFoundError)
    def test_stitch_ffmpeg_not_installed(self, mock_run: MagicMock, tmp_dir: Path) -> None:
        """Should handle missing FFmpeg gracefully."""
        for i in range(2):
            (tmp_dir / f"chunk_{i:04d}.mp3").write_bytes(b"data")

        output = tmp_dir / "output.mp3"
        result = stitch_audio(tmp_dir, output)
        assert result is False


class TestWriteConcatList:
    """Tests for concat list file generation."""

    def test_write_concat_list(self, tmp_dir: Path) -> None:
        """Should write properly formatted concat list."""
        chunks = [tmp_dir / "chunk_0000.mp3", tmp_dir / "chunk_0001.mp3"]
        list_path = tmp_dir / "list.txt"

        _write_concat_list(list_path, chunks)

        content = list_path.read_text(encoding="utf-8")
        assert "file '" in content
        assert "chunk_0000.mp3" in content
        assert "chunk_0001.mp3" in content


class TestVerifyFfmpeg:
    """Tests for FFmpeg availability check."""

    @patch("podifyr.audio.stitcher.subprocess.run")
    def test_ffmpeg_available(self, mock_run: MagicMock) -> None:
        """Should return True when FFmpeg is installed."""
        mock_run.return_value = MagicMock(returncode=0)
        assert verify_ffmpeg_available() is True

    @patch("podifyr.audio.stitcher.subprocess.run", side_effect=FileNotFoundError)
    def test_ffmpeg_not_available(self, mock_run: MagicMock) -> None:
        """Should return False when FFmpeg is not found."""
        assert verify_ffmpeg_available() is False
