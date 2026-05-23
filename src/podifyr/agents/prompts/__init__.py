"""Prompt templates for the multi-agent script generation pipeline."""

from __future__ import annotations

from typing import Final


ANALYZER_SYSTEM_PROMPT: Final[str] = """You are a senior software architect performing a \
detailed architectural review of a Python module. You receive structured metadata about the \
module including its classes, functions, imports, and position within the dependency graph.

Your task is to produce a precise technical summary covering:
1. The module's primary responsibility (one sentence).
2. Key classes: their roles, design patterns used, and inheritance hierarchy.
3. Key functions: what they accomplish, their signatures, and algorithmic approach.
4. Architectural significance: how this module fits into the larger system.
5. Dependency relationships: what it depends on and what depends on it.

Guidelines:
- Be concise but technically rigorous.
- Identify design patterns (Factory, Strategy, Observer, etc.) when present.
- Note any async patterns, protocol usage, or metaprogramming.
- Do NOT include implementation details like loop bodies or variable assignments.
- Focus on architectural intent and public API surface."""

SCRIPTWRITER_SYSTEM_PROMPT: Final[str] = """You are a charismatic Senior Engineer giving a \
whiteboard walkthrough to a new team member on their first day. Your job is to take a \
technical summary and rewrite it as a conversational, engaging segment for a podcast episode \
about this codebase.

Guidelines:
- Use natural spoken language, as if talking to a colleague over coffee.
- Use transitions like "So what this module does is...", "The clever bit here is...", \
"Think of this as the..."
- Explain WHY architectural decisions were made, not just WHAT they are.
- Use analogies where appropriate to make complex concepts accessible.
- Keep it informative but approachable — no jargon walls.
- Target 4-6 sentences per module segment.
- Do NOT use bullet points, markdown, or code formatting. Write flowing prose.
- End each segment with a natural transition to keep the listener engaged."""


def format_module_for_analysis(
    module_data: dict[str, object],
    graph_context: dict[str, object],
    module_name: str,
) -> str:
    """Format module metadata and graph context into a prompt-ready string.

    Args:
        module_data: Serialized ModuleMetadata dict.
        graph_context: Dependency context dict.
        module_name: The dotted module name.

    Returns:
        Formatted string suitable for the analyzer prompt.
    """
    lines: list[str] = [
        f"Module: {module_name}",
        f"File: {module_data.get('file_path', 'unknown')}",
        f"Lines: {module_data.get('line_count', 0)}",
        f"Module Docstring: {module_data.get('module_docstring') or 'None'}",
        "",
    ]

    # Imports
    imports = module_data.get("imports", [])
    if imports:
        lines.append("Imports:")
        for imp in imports[:25]:  # Cap to avoid token overflow
            if isinstance(imp, dict):
                full_path = imp.get("module", "")
                if imp.get("name"):
                    full_path += f".{imp['name']}"
                lines.append(f"  - {full_path}")
            else:
                lines.append(f"  - {imp}")
        if len(imports) > 25:
            lines.append(f"  ... and {len(imports) - 25} more")
        lines.append("")

    # Classes
    classes = module_data.get("classes", [])
    if classes:
        lines.append("Classes:")
        for cls in classes:
            if isinstance(cls, dict):
                bases = ", ".join(cls.get("base_classes", [])) or "None"
                lines.append(f"  - {cls['name']} (bases: {bases})")
                if cls.get("docstring"):
                    lines.append(f"    Docstring: {cls['docstring'][:200]}")
                if cls.get("is_abstract"):
                    lines.append("    [Abstract class]")
                if cls.get("is_dataclass"):
                    lines.append("    [Dataclass]")
                for method in cls.get("methods", [])[:8]:
                    if isinstance(method, dict):
                        args = ", ".join(method.get("arguments", [])[:4])
                        ret = f" -> {method['returns']}" if method.get("returns") else ""
                        prefix = "async " if method.get("is_async") else ""
                        lines.append(f"    {prefix}def {method['name']}({args}){ret}")
        lines.append("")

    # Functions
    functions = module_data.get("functions", [])
    if functions:
        lines.append("Top-level Functions:")
        for func in functions:
            if isinstance(func, dict):
                args = ", ".join(func.get("arguments", [])[:5])
                ret = f" -> {func['returns']}" if func.get("returns") else ""
                prefix = "async " if func.get("is_async") else ""
                lines.append(f"  - {prefix}{func['name']}({args}){ret}")
                if func.get("docstring"):
                    lines.append(f"    Docstring: {func['docstring'][:150]}")
        lines.append("")

    # Graph context
    lines.append("Dependency Context:")
    deps = graph_context.get("dependencies", [])
    dependents = graph_context.get("dependents", [])
    depth = graph_context.get("depth", 0)
    lines.append(f"  Graph depth: {depth}")
    lines.append(f"  Depends on: {', '.join(deps) if deps else 'None (leaf module)'}")
    lines.append(f"  Used by: {', '.join(dependents) if dependents else 'None (entry point)'}")

    if graph_context.get("is_leaf"):
        lines.append("  Role: Foundational leaf module (no internal dependencies)")
    if graph_context.get("is_entry_point"):
        lines.append("  Role: Entry point (nothing depends on this)")

    return "\n".join(lines)
