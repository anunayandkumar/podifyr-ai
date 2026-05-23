"""Pydantic models for parsed Python module metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FunctionMetadata(BaseModel):
    """Metadata extracted from a single function or method definition."""

    name: str
    arguments: list[str] = Field(default_factory=list)
    returns: str | None = None
    docstring: str | None = None
    is_async: bool = False
    decorators: list[str] = Field(default_factory=list)
    line_number: int = 0
    complexity_hint: int = Field(
        default=1,
        description="Rough cyclomatic complexity based on branch count.",
    )


class ClassMetadata(BaseModel):
    """Metadata extracted from a single class definition."""

    name: str
    docstring: str | None = None
    methods: list[FunctionMetadata] = Field(default_factory=list)
    base_classes: list[str] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)
    line_number: int = 0
    is_dataclass: bool = False
    is_abstract: bool = False


class ImportInfo(BaseModel):
    """Structured import information."""

    module: str
    name: str | None = None
    alias: str | None = None
    is_relative: bool = False
    level: int = 0

    @property
    def full_path(self) -> str:
        """Return the fully qualified import path."""
        if self.name:
            return f"{self.module}.{self.name}"
        return self.module


class ModuleMetadata(BaseModel):
    """Complete structural metadata for a single Python module."""

    file_path: str
    module_name: str = ""
    imports: list[ImportInfo] = Field(default_factory=list)
    classes: list[ClassMetadata] = Field(default_factory=list)
    functions: list[FunctionMetadata] = Field(default_factory=list)
    module_docstring: str | None = None
    line_count: int = 0
    has_main_guard: bool = False
    global_constants: list[str] = Field(default_factory=list)

    @property
    def import_names(self) -> list[str]:
        """Return flat list of import paths for backward compatibility."""
        return [imp.full_path for imp in self.imports]
