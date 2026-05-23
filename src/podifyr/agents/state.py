"""LangGraph state definition for the script generation workflow."""

from __future__ import annotations

from typing import Any, TypedDict


class ScriptState(TypedDict):
    """State passed through the LangGraph analyzer -> scriptwriter pipeline.

    Attributes:
        module_metadata: Serialized ModuleMetadata dict.
        graph_context: Dependency context (dependencies, dependents, depth).
        technical_summary: Output from the analyzer node.
        conversational_script: Output from the scriptwriter node.
        module_name: Dotted module path name.
        error: Error message if pipeline fails at any node.
    """

    module_metadata: dict[str, Any]
    graph_context: dict[str, Any]
    technical_summary: str
    conversational_script: str
    module_name: str
    error: str
