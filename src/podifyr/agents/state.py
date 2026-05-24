"""LangGraph state definition for the script generation workflow."""

from __future__ import annotations

from typing import Any, TypedDict


class DialogueTurn(TypedDict):
    """A single spoken turn in a multi-speaker podcast dialogue."""

    speaker: str  # "host" | "expert"
    text: str


class ScriptState(TypedDict, total=False):
    """State passed through the LangGraph analyzer -> scriptwriter/dialogue pipeline.

    Attributes:
        module_metadata: Serialized ModuleMetadata dict.
        graph_context: Dependency context (dependencies, dependents, depth).
        technical_summary: Output from the analyzer node.
        conversational_script: Output from the monologue scriptwriter node.
        dialogue: Output from the dialogue node (list of speaker turns).
        module_name: Dotted module path name.
        error: Error message if pipeline fails at any node.
    """

    module_metadata: dict[str, Any]
    graph_context: dict[str, Any]
    technical_summary: str
    conversational_script: str
    dialogue: list[DialogueTurn]
    module_name: str
    error: str
