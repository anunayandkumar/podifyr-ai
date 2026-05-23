"""Orchestrator: compiles and runs the LangGraph workflow for script generation."""

from __future__ import annotations

import hashlib
import json

import networkx as nx
from langgraph.graph import END, StateGraph

from podifyr.agents.nodes.analyzer import analyzer_node
from podifyr.agents.nodes.scriptwriter import scriptwriter_node
from podifyr.agents.state import ScriptState
from podifyr.cache import CacheManager
from podifyr.graph.analyzer import get_module_context
from podifyr.logging import get_logger
from podifyr.parsing.models import ModuleMetadata
from podifyr.utils.fs import normalize_module_path


logger = get_logger(__name__)


def _build_workflow() -> StateGraph:
    """Construct the two-node LangGraph workflow (analyzer -> scriptwriter)."""
    workflow = StateGraph(ScriptState)

    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("scriptwriter", scriptwriter_node)

    workflow.set_entry_point("analyzer")
    workflow.add_edge("analyzer", "scriptwriter")
    workflow.add_edge("scriptwriter", END)

    return workflow


# Compile once at module level for reuse across invocations
_compiled_workflow = _build_workflow().compile()


def generate_script_for_module(
    metadata: ModuleMetadata,
    dep_graph: nx.DiGraph,
    cache: CacheManager | None = None,
) -> str:
    """Run the agent pipeline for a single module and return the conversational script.

    Args:
        metadata: Parsed metadata for the module.
        dep_graph: The full project dependency graph.
        cache: Optional cache manager for script caching.

    Returns:
        A conversational script segment for the module.
    """
    module_name = metadata.module_name or normalize_module_path(metadata.file_path)
    graph_context = get_module_context(dep_graph, module_name)

    # Check cache
    if cache is not None:
        metadata_hash = _compute_metadata_hash(metadata)
        cached_script = cache.get_script(module_name, metadata_hash)
        if cached_script is not None:
            logger.debug("script_cache_hit", module=module_name)
            return cached_script

    # Build initial state
    initial_state: ScriptState = {
        "module_metadata": metadata.model_dump(),
        "graph_context": dict(graph_context),  # TypedDict to regular dict
        "technical_summary": "",
        "conversational_script": "",
        "module_name": module_name,
        "error": "",
    }

    try:
        result = _compiled_workflow.invoke(initial_state)
        script: str = result.get("conversational_script", "")

        if not script:
            logger.warning("empty_script", module=module_name)
            script = f"[Script generation produced no output for {module_name}]"

        # Cache the result
        if cache is not None:
            metadata_hash = _compute_metadata_hash(metadata)
            cache.set_script(module_name, metadata_hash, script)

        return script

    except Exception as exc:
        logger.error("pipeline_failed", module=module_name, error=str(exc))
        return (
            f"[Pipeline failed for {module_name}: {metadata.module_docstring or 'No description'}. "
            f"Contains {len(metadata.classes)} classes and {len(metadata.functions)} functions.]"
        )


def generate_full_script(
    parsed_modules: list[ModuleMetadata],
    dep_graph: nx.DiGraph,
    reading_order: list[str],
    cache: CacheManager | None = None,
) -> list[str]:
    """Generate conversational script segments for all modules in reading order.

    Args:
        parsed_modules: All parsed module metadata.
        dep_graph: The full project dependency graph.
        reading_order: Topologically sorted module names.
        cache: Optional cache manager.

    Returns:
        List of script chunks, one per module, in reading order.
    """
    # Build lookup from module name to metadata
    module_lookup: dict[str, ModuleMetadata] = {}
    for mod in parsed_modules:
        name = mod.module_name or normalize_module_path(mod.file_path)
        module_lookup[name] = mod

    script_chunks: list[str] = []
    generated_count = 0
    error_count = 0

    for module_name in reading_order:
        metadata = module_lookup.get(module_name)
        if metadata is None:
            logger.debug("module_not_in_lookup", module=module_name)
            continue

        logger.info("generating_script", module=module_name)
        chunk = generate_script_for_module(metadata, dep_graph, cache=cache)
        script_chunks.append(chunk)

        if chunk.startswith("["):
            error_count += 1
        else:
            generated_count += 1

    logger.info(
        "script_generation_complete",
        total=len(reading_order),
        generated=generated_count,
        errors=error_count,
    )
    return script_chunks


def _compute_metadata_hash(metadata: ModuleMetadata) -> str:
    """Compute a content hash of module metadata for cache invalidation."""
    content = json.dumps(metadata.model_dump(), sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]
