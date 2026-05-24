"""Shared type aliases and TypedDict definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict


if TYPE_CHECKING:
    from pathlib import Path


class ModuleGraphContext(TypedDict):
    """Graph context for a single module in the dependency graph."""

    dependencies: list[str]
    dependents: list[str]
    depth: int
    is_leaf: bool
    is_entry_point: bool


class ScriptChunk(TypedDict):
    """A single segment of the generated walkthrough script."""

    module_name: str
    content: str
    order_index: int


class PipelineResult(TypedDict):
    """Result of a complete podifyr pipeline run."""

    parsed_count: int
    graph_nodes: int
    graph_edges: int
    script_chunks: list[ScriptChunk]
    audio_paths: list[Path]
    final_audio_path: Path | None
    errors: list[str]


class AudioChunkResult(TypedDict):
    """Result of a single audio chunk generation."""

    index: int
    success: bool
    path: Path | None
    error: str | None
    bytes_written: int
