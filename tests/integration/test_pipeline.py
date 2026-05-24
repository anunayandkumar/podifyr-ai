"""Integration tests for the full pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from podifyr.graph import build_dependency_graph, get_topological_sort
from podifyr.parsing import parse_directory


if TYPE_CHECKING:
    from pathlib import Path


class TestFullParsePipeline:
    """Integration tests for parsing + graph building."""

    def test_parse_and_build_graph(self, sample_repo: Path) -> None:
        """Should parse a repo and build a valid dependency graph."""
        modules = parse_directory(sample_repo)
        assert len(modules) > 0

        graph = build_dependency_graph(modules)
        assert graph.number_of_nodes() > 0

    def test_topological_sort_of_real_repo(self, sample_repo: Path) -> None:
        """Should produce a valid reading order for a real repo."""
        modules = parse_directory(sample_repo)
        graph = build_dependency_graph(modules)
        order = get_topological_sort(graph)

        # All nodes should be in the order
        assert set(order) == set(graph.nodes())

    def test_pipeline_handles_empty_init_files(self, sample_repo: Path) -> None:
        """Should handle empty __init__.py files gracefully."""
        modules = parse_directory(sample_repo)

        # Should have parsed the utils __init__.py (empty) without error
        init_modules = [m for m in modules if m.file_path.endswith("__init__.py")]
        assert len(init_modules) > 0
