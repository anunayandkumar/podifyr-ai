"""Scriptwriter node: rewrites technical summaries into conversational podcast segments."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from podifyr.agents.prompts import SCRIPTWRITER_SYSTEM_PROMPT
from podifyr.agents.state import ScriptState  # noqa: TCH001
from podifyr.llm import build_chat_model
from podifyr.logging import get_logger


logger = get_logger(__name__)


def scriptwriter_node(state: ScriptState) -> dict[str, str]:
    """LangGraph node: rewrite a technical summary into conversational podcast script.

    Takes the technical summary from the analyzer node and produces an engaging,
    spoken-language segment suitable for audio narration.

    Falls back to the raw technical summary if the LLM call fails.
    """
    module_name = state["module_name"]
    technical_summary = state["technical_summary"]

    if not technical_summary.strip():
        logger.warning("scriptwriter_empty_input", module=module_name)
        return {
            "conversational_script": f"[No content available for {module_name}]",
            "error": "Empty technical summary received.",
        }

    try:
        llm = build_chat_model(temperature=0.7)

        messages = [
            SystemMessage(content=SCRIPTWRITER_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Module: {module_name}\n\n"
                    f"Technical Summary:\n{technical_summary}\n\n"
                    "Rewrite this as a conversational podcast segment. "
                    "Speak naturally as if explaining to a new team member."
                )
            ),
        ]

        response = llm.invoke(messages)
        script = response.content if isinstance(response.content, str) else str(response.content)

        if not script.strip():
            raise ValueError("LLM returned empty response")

        logger.info("scriptwriter_complete", module=module_name, script_length=len(script))
        return {"conversational_script": script}

    except Exception as exc:
        logger.warning("scriptwriter_failed", module=module_name, error=str(exc))
        # Fall back to the technical summary itself
        return {"conversational_script": technical_summary}
