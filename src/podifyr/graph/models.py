"""Graph models for dependency representation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NodeAttributes(BaseModel):
    """Attributes stored on each graph node."""

    file_path: str
    module_name: str
    line_count: int = 0
    class_count: int = 0
    function_count: int = 0
    import_count: int = 0
    is_package_init: bool = False


class GraphMetrics(BaseModel):
    """Summary metrics for the dependency graph."""

    node_count: int
    edge_count: int
    density: float = 0.0
    connected_components: int = 0
    has_cycles: bool = False
    longest_path_length: int = 0
    most_depended_on: list[str] = Field(default_factory=list)
    most_dependencies: list[str] = Field(default_factory=list)
