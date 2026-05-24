"""Analyzer node: produces technical summaries from module metadata."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from podifyr.agents.prompts import ANALYZER_SYSTEM_PROMPT, format_module_for_analysis
from podifyr.agents.state import ScriptState  # noqa: TCH001
from podifyr.llm import build_chat_model
from podifyr.logging import get_logger
from podifyr.parsing.models import ModuleMetadata


logger = get_logger(__name__)


def analyzer_node(state: ScriptState) -> dict[str, str]:
    """LangGraph node: analyze module metadata and produce a technical summary.

    Takes module metadata and graph context from state, invokes the LLM with
    the analyzer prompt, and returns the technical summary.

    Falls back to a basic summary if the LLM call fails.
    """
    module_name = state["module_name"]
    module_data = state["module_metadata"]
    graph_ctx = state["graph_context"]

    formatted_input = format_module_for_analysis(module_data, graph_ctx, module_name)

    try:
        llm = build_chat_model(temperature=0.2)

        messages = [
            SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=formatted_input),
        ]

        response = llm.invoke(messages)
        summary = response.content if isinstance(response.content, str) else str(response.content)

        if not summary.strip():
            raise ValueError("LLM returned empty response")

        logger.info("analyzer_complete", module=module_name, summary_length=len(summary))
        return {"technical_summary": summary}

    except Exception as exc:
        logger.warning("analyzer_failed", module=module_name, error=str(exc))

        # Construct a basic fallback summary from metadata
        metadata = ModuleMetadata.model_validate(module_data)
        fallback = _build_fallback_summary(metadata, graph_ctx)
        return {"technical_summary": fallback}


def _build_fallback_summary(
    metadata: ModuleMetadata,
    graph_ctx: dict[str, object],
) -> str:
    """Build a basic technical summary without LLM when the API is unavailable."""
    parts: list[str] = []

    parts.append(
        f"Module '{metadata.module_name}' ({metadata.line_count} lines) "
        f"contains {len(metadata.classes)} class(es) and {len(metadata.functions)} function(s)."
    )

    if metadata.module_docstring:
        parts.append(f"Purpose: {metadata.module_docstring[:200]}")

    if metadata.classes:
        class_names = [c.name for c in metadata.classes[:5]]
        parts.append(f"Key classes: {', '.join(class_names)}.")

    if metadata.functions:
        func_names = [f.name for f in metadata.functions[:5]]
        parts.append(f"Key functions: {', '.join(func_names)}.")

    deps = graph_ctx.get("dependencies", [])
    if deps:
        parts.append(f"Depends on: {', '.join(deps[:5])}.")  # type: ignore[arg-type]

    return " ".join(parts)
