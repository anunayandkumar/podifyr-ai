"""Dialogue node: generates a Host/Expert two-speaker podcast dialogue.

Unlike the monologue scriptwriter (which produces a single-voice narration),
this node produces a JSON array of speaker turns that get synthesized with
two distinct TTS voices for a true podcast feel.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from podifyr.agents.prompts import DIALOGUE_SYSTEM_PROMPT
from podifyr.agents.state import DialogueTurn, ScriptState  # noqa: TC001
from podifyr.llm import build_chat_model
from podifyr.logging import get_logger


logger = get_logger(__name__)


_VALID_SPEAKERS = ("host", "expert")
_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def dialogue_node(state: ScriptState) -> dict[str, Any]:
    """LangGraph node: rewrite a technical summary into a Host/Expert dialogue.

    Falls back to a minimal two-turn dialogue derived from the technical summary
    if the LLM call fails or returns malformed JSON.
    """
    module_name = state["module_name"]
    technical_summary = state.get("technical_summary", "")

    if not technical_summary.strip():
        logger.warning("dialogue_empty_input", module=module_name)
        return {
            "dialogue": [
                {"speaker": "host", "text": f"What's in the {module_name} module?"},
                {"speaker": "expert", "text": f"We don't have details on {module_name} yet."},
            ],
            "error": "Empty technical summary received.",
        }

    try:
        llm = build_chat_model(temperature=0.8)

        messages = [
            SystemMessage(content=DIALOGUE_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Module: {module_name}\n\n"
                    f"Technical Summary:\n{technical_summary}\n\n"
                    "Produce the dialogue now. Return ONLY the JSON array."
                )
            ),
        ]

        response = llm.invoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
        turns = _parse_dialogue(raw)

        if not turns:
            raise ValueError("Parsed dialogue was empty")

        logger.info("dialogue_complete", module=module_name, turn_count=len(turns))
        return {"dialogue": turns}

    except Exception as exc:
        logger.warning("dialogue_failed", module=module_name, error=str(exc))
        return {"dialogue": _fallback_dialogue(module_name, technical_summary)}


def _parse_dialogue(raw: str) -> list[DialogueTurn]:
    """Parse the LLM response into a validated list of dialogue turns.

    Tolerant to common LLM quirks: code fences, leading prose, trailing commas.
    """
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.strip("`")
        # Remove an optional "json" language tag
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    # If there's leading/trailing prose, extract the first JSON array
    match = _JSON_ARRAY_RE.search(text)
    if match:
        text = match.group(0)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in dialogue response: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("Dialogue response is not a JSON array")

    turns: list[DialogueTurn] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        speaker_raw = str(item.get("speaker", "")).strip().lower()
        turn_text = str(item.get("text", "")).strip()
        if not turn_text:
            continue
        speaker = speaker_raw if speaker_raw in _VALID_SPEAKERS else "expert"
        turns.append({"speaker": speaker, "text": turn_text})

    return turns


def _fallback_dialogue(module_name: str, technical_summary: str) -> list[DialogueTurn]:
    """Best-effort two-turn dialogue when the LLM fails."""
    summary = technical_summary.strip() or f"The {module_name} module."
    # Trim very long fallback content to keep the audio reasonable
    if len(summary) > 600:
        summary = summary[:600].rsplit(".", 1)[0] + "."
    return [
        {"speaker": "host", "text": f"Let's talk about the {module_name} module. What's it for?"},
        {"speaker": "expert", "text": summary},
    ]
