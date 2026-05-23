"""Dependency graph builder: constructs a directed graph from parsed module metadata."""

from __future__ import annotations

import networkx as nx

from podifyr.graph.models import NodeAttributes
from podifyr.logging import get_logger
from podifyr.parsing.models import ModuleMetadata
from podifyr.utils.fs import normalize_module_path


logger = get_logger(__name__)


def build_dependency_graph(parsed_modules: list[ModuleMetadata]) -> nx.DiGraph:
    """Build a directed dependency graph from parsed module metadata.

    Nodes represent modules (labeled by dotted module path).
    Directed edges represent import relationships (importer -> imported).
    Only internal (intra-project) dependencies are represented as edges.

    Args:
        parsed_modules: List of parsed module metadata.

    Returns:
        A NetworkX directed graph with module dependencies.
    """
    graph = nx.DiGraph()

    # Register all known module names
    known_modules: dict[str, ModuleMetadata] = {}
    for module in parsed_modules:
        module_name = module.module_name or normalize_module_path(module.file_path)
        known_modules[module_name] = module

        # Add node with rich attributes
        attrs = NodeAttributes(
            file_path=module.file_path,
            module_name=module_name,
            line_count=module.line_count,
            class_count=len(module.classes),
            function_count=len(module.functions),
            import_count=len(module.imports),
            is_package_init=module.file_path.endswith("__init__.py"),
        )
        graph.add_node(module_name, **attrs.model_dump())

    known_set = set(known_modules.keys())

    # Build edges from import statements
    for module in parsed_modules:
        source = module.module_name or normalize_module_path(module.file_path)

        for imp in module.imports:
            # Skip relative imports that can't be resolved
            if imp.is_relative and not imp.module:
                continue

            target = _resolve_import_to_module(imp.full_path, known_set)
            if target is not None and target != source:
                graph.add_edge(source, target, import_path=imp.full_path)

    logger.info(
        "graph_built",
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
    )
    return graph


def _resolve_import_to_module(import_path: str, known_modules: set[str]) -> str | None:
    """Resolve an import path to a known internal module.

    Tries progressively shorter prefixes to find a match.

    Args:
        import_path: Fully qualified import path (e.g., 'podifyr.parsing.engine').
        known_modules: Set of known internal module names.

    Returns:
        Matching module name, or None for external dependencies.
    """
    # Direct match
    if import_path in known_modules:
        return import_path

    # Try progressively shorter prefixes
    parts = import_path.split(".")
    for i in range(len(parts) - 1, 0, -1):
        candidate = ".".join(parts[:i])
        if candidate in known_modules:
            return candidate

    return None
