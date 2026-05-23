"""Audio stitcher: FFmpeg-based concatenation of audio chunks."""

from __future__ import annotations

import subprocess
from pathlib import Path

from podifyr.core.constants import AUDIO_CHUNK_PREFIX, AUDIO_FILE_EXTENSION
from podifyr.logging import get_logger


logger = get_logger(__name__)


def stitch_audio(input_dir: Path, final_output_path: Path) -> bool:
    """Concatenate audio chunks into a single MP3 file using FFmpeg.

    Uses FFmpeg's concat demuxer for lossless concatenation of MP3 files.
    Handles edge cases: single file (copy), missing FFmpeg, timeout.

    Args:
        input_dir: Directory containing ordered audio chunk files.
        final_output_path: Path for the final concatenated output file.

    Returns:
        True if stitching succeeded, False otherwise.
    """
    pattern = f"{AUDIO_CHUNK_PREFIX}*{AUDIO_FILE_EXTENSION}"
    chunk_files = sorted(input_dir.glob(pattern))

    if not chunk_files:
        logger.error("stitch_no_chunks", directory=str(input_dir))
        return False

    logger.info("stitch_started", chunks=len(chunk_files), output=str(final_output_path))

    # Single file: just copy
    if len(chunk_files) == 1:
        return _copy_single_file(chunk_files[0], final_output_path)

    # Multiple files: use FFmpeg concat
    return _ffmpeg_concat(chunk_files, input_dir, final_output_path)


def _copy_single_file(source: Path, destination: Path) -> bool:
    """Copy a single audio file to the output path."""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        logger.info("stitch_single_copy", source=str(source), dest=str(destination))
        return True
    except OSError as exc:
        logger.error("stitch_copy_failed", error=str(exc))
        return False


def _ffmpeg_concat(
    chunk_files: list[Path],
    working_dir: Path,
    output_path: Path,
) -> bool:
    """Concatenate multiple audio files using FFmpeg's concat demuxer."""
    concat_list_path = working_dir / "_concat_list.txt"

    try:
        # Write the concat list file
        _write_concat_list(concat_list_path, chunk_files)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Run FFmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output without asking
            "-f",
            "concat",  # Use concat demuxer
            "-safe",
            "0",  # Allow absolute paths
            "-i",
            str(concat_list_path),
            "-c",
            "copy",  # Stream copy (no re-encoding)
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )

        if result.returncode != 0:
            logger.error(
                "ffmpeg_failed",
                exit_code=result.returncode,
                stderr=result.stderr[:500],
            )
            return False

        file_size = output_path.stat().st_size if output_path.exists() else 0
        logger.info(
            "stitch_complete",
            output=str(output_path),
            chunks=len(chunk_files),
            size_bytes=file_size,
        )
        return True

    except FileNotFoundError:
        logger.error(
            "ffmpeg_not_found",
            message="FFmpeg is not installed or not in PATH. "
            "Install from https://ffmpeg.org/download.html",
        )
        return False

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg_timeout", timeout_seconds=300)
        return False

    except OSError as exc:
        logger.error("ffmpeg_os_error", error=str(exc))
        return False

    finally:
        # Clean up the temporary concat list
        _cleanup_concat_list(concat_list_path)


def _write_concat_list(path: Path, chunk_files: list[Path]) -> None:
    """Write the FFmpeg concat list file."""
    with path.open("w", encoding="utf-8") as f:
        for chunk_path in chunk_files:
            # FFmpeg requires forward slashes; escape single quotes in paths
            safe_path = str(chunk_path.resolve()).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")


def _cleanup_concat_list(path: Path) -> None:
    """Remove the temporary concat list file."""
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass  # Non-critical cleanup failure


def verify_ffmpeg_available() -> bool:
    """Check if FFmpeg is installed and accessible.

    Returns:
        True if FFmpeg is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
