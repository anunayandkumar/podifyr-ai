"""Unit tests for the agents module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from podifyr.agents.nodes.analyzer import _build_fallback_summary, analyzer_node
from podifyr.agents.nodes.scriptwriter import scriptwriter_node
from podifyr.agents.prompts import format_module_for_analysis
from podifyr.agents.state import ScriptState
from podifyr.parsing.models import ClassMetadata, FunctionMetadata, ModuleMetadata


def _make_test_state(module_name: str = "test.module") -> ScriptState:
    """Create a test ScriptState for agent node testing."""
    metadata = ModuleMetadata(
        file_path="src/test/module.py",
        module_name=module_name,
        imports=[],
        classes=[
            ClassMetadata(
                name="TestClass",
                docstring="A test class.",
                methods=[
                    FunctionMetadata(name="do_thing", arguments=["self", "x: int"], returns="str"),
                ],
                base_classes=["BaseClass"],
            ),
        ],
        functions=[
            FunctionMetadata(
                name="helper",
                arguments=["data: list[str]"],
                returns="dict[str, int]",
                docstring="Helper function.",
            ),
        ],
        module_docstring="Test module for agents.",
        line_count=50,
    )

    return ScriptState(
        module_metadata=metadata.model_dump(),
        graph_context={
            "dependencies": ["test.utils"],
            "dependents": ["test.cli"],
            "depth": 2,
            "is_leaf": False,
            "is_entry_point": False,
        },
        technical_summary="",
        conversational_script="",
        module_name=module_name,
        error="",
    )


class TestFormatModuleForAnalysis:
    """Tests for prompt formatting."""

    def test_format_includes_module_name(self) -> None:
        """Should include the module name in output."""
        state = _make_test_state()
        result = format_module_for_analysis(
            state["module_metadata"], state["graph_context"], state["module_name"]
        )

        assert "test.module" in result

    def test_format_includes_classes(self) -> None:
        """Should include class information."""
        state = _make_test_state()
        result = format_module_for_analysis(
            state["module_metadata"], state["graph_context"], state["module_name"]
        )

        assert "TestClass" in result
        assert "BaseClass" in result

    def test_format_includes_functions(self) -> None:
        """Should include function information."""
        state = _make_test_state()
        result = format_module_for_analysis(
            state["module_metadata"], state["graph_context"], state["module_name"]
        )

        assert "helper" in result
        assert "dict[str, int]" in result

    def test_format_includes_graph_context(self) -> None:
        """Should include dependency information."""
        state = _make_test_state()
        result = format_module_for_analysis(
            state["module_metadata"], state["graph_context"], state["module_name"]
        )

        assert "test.utils" in result
        assert "test.cli" in result


class TestAnalyzerNode:
    """Tests for the analyzer agent node."""

    @patch("podifyr.agents.nodes.analyzer.ChatOpenAI")
    def test_analyzer_success(self, mock_llm_class: MagicMock, mock_settings: None) -> None:
        """Should return technical summary from LLM."""
        mock_response = MagicMock()
        mock_response.content = "This module handles data processing."
        mock_llm_class.return_value.invoke.return_value = mock_response

        state = _make_test_state()
        result = analyzer_node(state)

        assert "technical_summary" in result
        assert result["technical_summary"] == "This module handles data processing."

    @patch("podifyr.agents.nodes.analyzer.ChatOpenAI")
    def test_analyzer_fallback_on_error(self, mock_llm_class: MagicMock, mock_settings: None) -> None:
        """Should fall back to basic summary if LLM fails."""
        mock_llm_class.return_value.invoke.side_effect = Exception("API Error")

        state = _make_test_state()
        result = analyzer_node(state)

        assert "technical_summary" in result
        # Fallback should contain module info
        assert "test.module" in result["technical_summary"]

    def test_fallback_summary_content(self) -> None:
        """Should build informative fallback summary from metadata."""
        metadata = ModuleMetadata(
            file_path="src/test/module.py",
            module_name="test.module",
            imports=[],
            classes=[ClassMetadata(name="MyClass", methods=[])],
            functions=[FunctionMetadata(name="my_func", arguments=[])],
            module_docstring="Does important things.",
            line_count=100,
        )

        result = _build_fallback_summary(metadata, {"dependencies": ["test.dep"]})

        assert "test.module" in result
        assert "1 class" in result
        assert "1 function" in result
        assert "Does important things" in result


class TestScriptwriterNode:
    """Tests for the scriptwriter agent node."""

    @patch("podifyr.agents.nodes.scriptwriter.ChatOpenAI")
    def test_scriptwriter_success(self, mock_llm_class: MagicMock, mock_settings: None) -> None:
        """Should return conversational script from LLM."""
        mock_response = MagicMock()
        mock_response.content = "So this module is really the heart of the system..."
        mock_llm_class.return_value.invoke.return_value = mock_response

        state = _make_test_state()
        state["technical_summary"] = "Module handles core data processing."

        result = scriptwriter_node(state)

        assert "conversational_script" in result
        assert "heart of the system" in result["conversational_script"]

    @patch("podifyr.agents.nodes.scriptwriter.ChatOpenAI")
    def test_scriptwriter_fallback_on_error(self, mock_llm_class: MagicMock, mock_settings: None) -> None:
        """Should fall back to technical summary if LLM fails."""
        mock_llm_class.return_value.invoke.side_effect = Exception("API Error")

        state = _make_test_state()
        state["technical_summary"] = "Technical summary content."

        result = scriptwriter_node(state)

        # Should return the technical summary as fallback
        assert result["conversational_script"] == "Technical summary content."

    @patch("podifyr.agents.nodes.scriptwriter.ChatOpenAI")
    def test_scriptwriter_empty_input(self, mock_llm_class: MagicMock, mock_settings: None) -> None:
        """Should handle empty technical summary."""
        state = _make_test_state()
        state["technical_summary"] = ""

        result = scriptwriter_node(state)

        assert "No content available" in result["conversational_script"]
