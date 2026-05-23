"""Graph analyzer: topological sorting, metrics, and context extraction."""

from __future__ import annotations

import networkx as nx

from podifyr.core.types import ModuleGraphContext
from podifyr.graph.models import GraphMetrics
from podifyr.logging import get_logger


logger = get_logger(__name__)


def get_topological_sort(graph: nx.DiGraph) -> list[str]:
    """Return a topological ordering of the dependency graph.

    Provides the optimal logical reading order: dependencies before dependents.
    Falls back to SCC-condensation ordering if the graph contains cycles.

    Args:
        graph: Directed dependency graph.

    Returns:
        List of module names in reading order.
    """
    if graph.number_of_nodes() == 0:
        return []

    try:
        return list(reversed(list(nx.topological_sort(graph))))
    except nx.NetworkXUnfeasible:
        logger.warning("graph_has_cycles", message="Falling back to SCC-aware ordering.")
        return _condensation_order(graph)


def _condensation_order(graph: nx.DiGraph) -> list[str]:
    """Compute reading order for a cyclic graph using SCC condensation.

    Condenses strongly connected components into single nodes, sorts the DAG
    of SCCs topologically, then expands back to individual modules.
    """
    try:
        condensed = nx.condensation(graph)
        scc_order = list(nx.topological_sort(condensed))
        result: list[str] = []
        for scc_id in scc_order:
            members = sorted(condensed.nodes[scc_id]["members"])
            result.extend(members)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("condensation_failed", error=str(exc))
        return sorted(graph.nodes())


def get_module_context(graph: nx.DiGraph, module_name: str) -> ModuleGraphContext:
    """Extract rich dependency context for a single module.

    Args:
        graph: The dependency graph.
        module_name: The module to get context for.

    Returns:
        ModuleGraphContext with dependency info, depth, and role indicators.
    """
    if module_name not in graph:
        return ModuleGraphContext(
            dependencies=[],
            dependents=[],
            depth=0,
            is_leaf=True,
            is_entry_point=True,
        )

    dependencies = sorted(graph.successors(module_name))
    dependents = sorted(graph.predecessors(module_name))

    # Calculate depth (longest path from a root to this node)
    depth = _compute_depth(graph, module_name)

    is_leaf = len(dependencies) == 0
    is_entry_point = len(dependents) == 0

    return ModuleGraphContext(
        dependencies=dependencies,
        dependents=dependents,
        depth=depth,
        is_leaf=is_leaf,
        is_entry_point=is_entry_point,
    )


def _compute_depth(graph: nx.DiGraph, node: str) -> int:
    """Compute the depth of a node (longest path from any root)."""
    try:
        # Find all roots (nodes with no predecessors/dependents)
        roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        if not roots:
            return 0

        max_depth = 0
        for root in roots:
            try:
                path_length = nx.shortest_path_length(graph, root, node)
                max_depth = max(max_depth, path_length)
            except nx.NetworkXNoPath:
                continue

        return max_depth
    except Exception:  # noqa: BLE001
        return 0


def compute_graph_metrics(graph: nx.DiGraph) -> GraphMetrics:
    """Compute summary metrics for the dependency graph.

    Args:
        graph: The dependency graph.

    Returns:
        GraphMetrics with density, connectivity, and centrality info.
    """
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()

    if node_count == 0:
        return GraphMetrics(node_count=0, edge_count=0)

    density = nx.density(graph)
    has_cycles = not nx.is_directed_acyclic_graph(graph)

    # Connected components (treating as undirected for connectivity)
    undirected = graph.to_undirected()
    connected_components = nx.number_connected_components(undirected)

    # Most depended-on modules (highest in-degree)
    in_degrees = sorted(graph.in_degree(), key=lambda x: x[1], reverse=True)
    most_depended_on = [name for name, deg in in_degrees[:5] if deg > 0]

    # Modules with most dependencies (highest out-degree)
    out_degrees = sorted(graph.out_degree(), key=lambda x: x[1], reverse=True)
    most_dependencies = [name for name, deg in out_degrees[:5] if deg > 0]

    # Longest path (only for DAGs)
    longest_path_length = 0
    if not has_cycles:
        try:
            longest_path_length = nx.dag_longest_path_length(graph)
        except Exception:  # noqa: BLE001
            pass

    return GraphMetrics(
        node_count=node_count,
        edge_count=edge_count,
        density=density,
        connected_components=connected_components,
        has_cycles=has_cycles,
        longest_path_length=longest_path_length,
        most_depended_on=most_depended_on,
        most_dependencies=most_dependencies,
    )
