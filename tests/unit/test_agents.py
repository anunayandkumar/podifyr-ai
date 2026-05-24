"""Unit tests for the agents module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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
        state = _make_test_state()
        result = format_module_for_analysis(
            state["module_metadata"], state["graph_context"], state["module_name"]
        )
        assert "test.module" in result

    def test_format_includes_classes(self) -> None:
        state = _make_test_state()
        result = format_module_for_analysis(
            state["module_metadata"], state["graph_context"], state["module_name"]
        )
        assert "TestClass" in result
        assert "BaseClass" in result

    def test_format_includes_functions(self) -> None:
        state = _make_test_state()
        result = format_module_for_analysis(
            state["module_metadata"], state["graph_context"], state["module_name"]
        )
        assert "helper" in result
        assert "dict[str, int]" in result

    def test_format_includes_graph_context(self) -> None:
        state = _make_test_state()
        result = format_module_for_analysis(
            state["module_metadata"], state["graph_context"], state["module_name"]
        )
        assert "test.utils" in result
        assert "test.cli" in result


class TestAnalyzerNode:
    """Tests for the analyzer agent node."""

    @patch("podifyr.agents.nodes.analyzer.build_chat_model")
    def test_analyzer_success(self, mock_builder: MagicMock, mock_settings: None) -> None:
        mock_response = MagicMock()
        mock_response.content = "This module handles data processing."
        mock_builder.return_value.invoke.return_value = mock_response

        state = _make_test_state()
        result = analyzer_node(state)

        assert "technical_summary" in result
        assert result["technical_summary"] == "This module handles data processing."

    @patch("podifyr.agents.nodes.analyzer.build_chat_model")
    def test_analyzer_fallback_on_error(self, mock_builder: MagicMock, mock_settings: None) -> None:
        mock_builder.return_value.invoke.side_effect = Exception("API Error")

        state = _make_test_state()
        result = analyzer_node(state)

        assert "technical_summary" in result
        assert "test.module" in result["technical_summary"]

    def test_fallback_summary_content(self) -> None:
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

    @patch("podifyr.agents.nodes.scriptwriter.build_chat_model")
    def test_scriptwriter_success(self, mock_builder: MagicMock, mock_settings: None) -> None:
        mock_response = MagicMock()
        mock_response.content = "So this module is really the heart of the system..."
        mock_builder.return_value.invoke.return_value = mock_response

        state = _make_test_state()
        state["technical_summary"] = "Module handles core data processing."

        result = scriptwriter_node(state)

        assert "conversational_script" in result
        assert "heart of the system" in result["conversational_script"]

    @patch("podifyr.agents.nodes.scriptwriter.build_chat_model")
    def test_scriptwriter_fallback_on_error(
        self, mock_builder: MagicMock, mock_settings: None
    ) -> None:
        mock_builder.return_value.invoke.side_effect = Exception("API Error")

        state = _make_test_state()
        state["technical_summary"] = "Technical summary content."

        result = scriptwriter_node(state)

        assert result["conversational_script"] == "Technical summary content."

    @patch("podifyr.agents.nodes.scriptwriter.build_chat_model")
    def test_scriptwriter_empty_input(self, mock_builder: MagicMock, mock_settings: None) -> None:
        state = _make_test_state()
        state["technical_summary"] = ""

        result = scriptwriter_node(state)

        assert "No content available" in result["conversational_script"]


class TestDialogueNode:
    """Tests for the multi-speaker dialogue agent node."""

    @patch("podifyr.agents.nodes.dialogue.build_chat_model")
    def test_dialogue_parses_valid_json(self, mock_builder: MagicMock, mock_settings: None) -> None:
        from podifyr.agents.nodes.dialogue import dialogue_node

        mock_response = MagicMock()
        mock_response.content = (
            '[{"speaker":"host","text":"What is this module?"},'
            '{"speaker":"expert","text":"It builds the dependency graph."}]'
        )
        mock_builder.return_value.invoke.return_value = mock_response

        state = _make_test_state()
        state["technical_summary"] = "Module builds the dependency graph."

        result = dialogue_node(state)

        assert "dialogue" in result
        turns = result["dialogue"]
        assert len(turns) == 2
        assert turns[0]["speaker"] == "host"
        assert turns[1]["speaker"] == "expert"
        assert "dependency graph" in turns[1]["text"]

    @patch("podifyr.agents.nodes.dialogue.build_chat_model")
    def test_dialogue_handles_code_fences(
        self, mock_builder: MagicMock, mock_settings: None
    ) -> None:
        from podifyr.agents.nodes.dialogue import dialogue_node

        mock_response = MagicMock()
        mock_response.content = (
            '```json\n[{"speaker":"host","text":"Hi"},{"speaker":"expert","text":"Hello"}]\n```'
        )
        mock_builder.return_value.invoke.return_value = mock_response

        state = _make_test_state()
        state["technical_summary"] = "Anything."

        result = dialogue_node(state)
        assert len(result["dialogue"]) == 2

    @patch("podifyr.agents.nodes.dialogue.build_chat_model")
    def test_dialogue_normalizes_unknown_speaker(
        self, mock_builder: MagicMock, mock_settings: None
    ) -> None:
        from podifyr.agents.nodes.dialogue import dialogue_node

        mock_response = MagicMock()
        mock_response.content = (
            '[{"speaker":"narrator","text":"Some line"},{"speaker":"HOST","text":"Question?"}]'
        )
        mock_builder.return_value.invoke.return_value = mock_response

        state = _make_test_state()
        state["technical_summary"] = "Anything."

        result = dialogue_node(state)
        turns = result["dialogue"]
        # Unknown speakers fall back to "expert"; case is normalized
        assert turns[0]["speaker"] == "expert"
        assert turns[1]["speaker"] == "host"

    @patch("podifyr.agents.nodes.dialogue.build_chat_model")
    def test_dialogue_fallback_on_invalid_json(
        self, mock_builder: MagicMock, mock_settings: None
    ) -> None:
        from podifyr.agents.nodes.dialogue import dialogue_node

        mock_response = MagicMock()
        mock_response.content = "not even close to JSON"
        mock_builder.return_value.invoke.return_value = mock_response

        state = _make_test_state()
        state["technical_summary"] = "Some technical content here."

        result = dialogue_node(state)
        turns = result["dialogue"]
        assert len(turns) == 2
        assert turns[0]["speaker"] == "host"
        assert turns[1]["speaker"] == "expert"

    @patch("podifyr.agents.nodes.dialogue.build_chat_model")
    def test_dialogue_fallback_on_llm_error(
        self, mock_builder: MagicMock, mock_settings: None
    ) -> None:
        from podifyr.agents.nodes.dialogue import dialogue_node

        mock_builder.return_value.invoke.side_effect = Exception("API down")

        state = _make_test_state()
        state["technical_summary"] = "Technical content."

        result = dialogue_node(state)
        assert len(result["dialogue"]) == 2

    def test_dialogue_empty_input(self, mock_settings: None) -> None:
        from podifyr.agents.nodes.dialogue import dialogue_node

        state = _make_test_state()
        state["technical_summary"] = ""

        result = dialogue_node(state)
        turns = result["dialogue"]
        assert len(turns) == 2
        assert "error" in result
