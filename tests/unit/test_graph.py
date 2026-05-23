"""Unit tests for the dependency graph module."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pytest

from podifyr.graph import build_dependency_graph, get_topological_sort
from podifyr.graph.analyzer import compute_graph_metrics, get_module_context
from podifyr.graph.builder import _resolve_import_to_module
from podifyr.parsing.models import ImportInfo, ModuleMetadata


def _make_module(
    name: str,
    file_path: str,
    imports: list[ImportInfo] | None = None,
) -> ModuleMetadata:
    """Helper to create a ModuleMetadata instance for testing."""
    return ModuleMetadata(
        file_path=file_path,
        module_name=name,
        imports=imports or [],
        classes=[],
        functions=[],
    )


class TestBuildDependencyGraph:
    """Tests for graph construction."""

    def test_build_empty_list(self) -> None:
        """Should handle empty module list."""
        graph = build_dependency_graph([])
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_build_single_module_no_deps(self) -> None:
        """Should create a single node with no edges."""
        modules = [_make_module("app.main", "src/app/main.py")]
        graph = build_dependency_graph(modules)

        assert graph.number_of_nodes() == 1
        assert graph.number_of_edges() == 0
        assert "app.main" in graph.nodes

    def test_build_with_internal_dependency(self) -> None:
        """Should create edges for internal imports."""
        modules = [
            _make_module(
                "app.main",
                "src/app/main.py",
                imports=[ImportInfo(module="app.core", name="Engine")],
            ),
            _make_module("app.core", "src/app/core.py"),
        ]

        graph = build_dependency_graph(modules)

        assert graph.number_of_edges() == 1
        assert graph.has_edge("app.main", "app.core")

    def test_build_ignores_external_deps(self) -> None:
        """Should not create edges for external dependencies."""
        modules = [
            _make_module(
                "app.main",
                "src/app/main.py",
                imports=[
                    ImportInfo(module="numpy", name="array"),
                    ImportInfo(module="requests"),
                ],
            ),
        ]

        graph = build_dependency_graph(modules)

        assert graph.number_of_edges() == 0

    def test_build_no_self_loops(self) -> None:
        """Should not create self-referencing edges."""
        modules = [
            _make_module(
                "app.main",
                "src/app/main.py",
                imports=[ImportInfo(module="app.main", name="something")],
            ),
        ]

        graph = build_dependency_graph(modules)
        assert graph.number_of_edges() == 0

    def test_build_multiple_dependencies(self) -> None:
        """Should handle modules with multiple internal dependencies."""
        modules = [
            _make_module(
                "app.cli",
                "src/app/cli.py",
                imports=[
                    ImportInfo(module="app.core", name="Engine"),
                    ImportInfo(module="app.utils", name="format"),
                ],
            ),
            _make_module("app.core", "src/app/core.py"),
            _make_module("app.utils", "src/app/utils.py"),
        ]

        graph = build_dependency_graph(modules)

        assert graph.has_edge("app.cli", "app.core")
        assert graph.has_edge("app.cli", "app.utils")
        assert graph.number_of_edges() == 2


class TestResolveImport:
    """Tests for import resolution."""

    def test_direct_match(self) -> None:
        """Should resolve exact module name matches."""
        known = {"app.core", "app.utils", "app.main"}
        assert _resolve_import_to_module("app.core", known) == "app.core"

    def test_prefix_match(self) -> None:
        """Should resolve imports to their containing module."""
        known = {"app.core", "app.utils"}
        assert _resolve_import_to_module("app.core.Engine", known) == "app.core"

    def test_no_match_returns_none(self) -> None:
        """Should return None for external imports."""
        known = {"app.core"}
        assert _resolve_import_to_module("numpy.array", known) is None

    def test_deepest_prefix_match(self) -> None:
        """Should match the most specific prefix."""
        known = {"app", "app.core", "app.core.engine"}
        assert _resolve_import_to_module("app.core.engine.run", known) == "app.core.engine"


class TestTopologicalSort:
    """Tests for topological sorting."""

    def test_sort_dag(self) -> None:
        """Should return valid topological order for a DAG."""
        graph = nx.DiGraph()
        graph.add_edges_from([("cli", "core"), ("core", "models"), ("cli", "utils")])

        order = get_topological_sort(graph)

        # In a valid topological order, dependencies come before dependents
        assert order.index("models") < order.index("core")
        assert order.index("core") < order.index("cli")

    def test_sort_empty_graph(self) -> None:
        """Should return empty list for empty graph."""
        graph = nx.DiGraph()
        assert get_topological_sort(graph) == []

    def test_sort_single_node(self) -> None:
        """Should return single node for single-node graph."""
        graph = nx.DiGraph()
        graph.add_node("main")

        order = get_topological_sort(graph)
        assert order == ["main"]

    def test_sort_cyclic_graph_falls_back(self) -> None:
        """Should handle cycles gracefully with SCC condensation."""
        graph = nx.DiGraph()
        graph.add_edges_from([("a", "b"), ("b", "c"), ("c", "a"), ("d", "a")])

        order = get_topological_sort(graph)

        # All nodes should be present
        assert set(order) == {"a", "b", "c", "d"}


class TestModuleContext:
    """Tests for module context extraction."""

    def test_context_leaf_module(self) -> None:
        """Should identify leaf modules correctly."""
        graph = nx.DiGraph()
        graph.add_edges_from([("cli", "core"), ("core", "models")])

        ctx = get_module_context(graph, "models")

        assert ctx["is_leaf"] is True
        assert ctx["is_entry_point"] is False
        assert ctx["dependencies"] == []
        assert "core" in ctx["dependents"]

    def test_context_entry_point(self) -> None:
        """Should identify entry points correctly."""
        graph = nx.DiGraph()
        graph.add_edges_from([("cli", "core")])

        ctx = get_module_context(graph, "cli")

        assert ctx["is_entry_point"] is True
        assert ctx["is_leaf"] is False

    def test_context_unknown_module(self) -> None:
        """Should return default context for unknown modules."""
        graph = nx.DiGraph()
        graph.add_node("core")

        ctx = get_module_context(graph, "unknown")

        assert ctx["is_leaf"] is True
        assert ctx["is_entry_point"] is True


class TestGraphMetrics:
    """Tests for graph metrics computation."""

    def test_metrics_empty_graph(self) -> None:
        """Should handle empty graph."""
        graph = nx.DiGraph()
        metrics = compute_graph_metrics(graph)

        assert metrics.node_count == 0
        assert metrics.edge_count == 0

    def test_metrics_dag(self) -> None:
        """Should compute correct metrics for a DAG."""
        graph = nx.DiGraph()
        graph.add_edges_from([("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")])

        metrics = compute_graph_metrics(graph)

        assert metrics.node_count == 4
        assert metrics.edge_count == 4
        assert metrics.has_cycles is False
        assert metrics.longest_path_length == 2

    def test_metrics_cyclic(self) -> None:
        """Should detect cycles."""
        graph = nx.DiGraph()
        graph.add_edges_from([("a", "b"), ("b", "a")])

        metrics = compute_graph_metrics(graph)
        assert metrics.has_cycles is True
