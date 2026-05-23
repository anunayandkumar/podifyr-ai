"""AST visitors for extracting structural metadata from Python source."""

from __future__ import annotations

import ast
from typing import Any

from podifyr.parsing.models import ClassMetadata, FunctionMetadata, ImportInfo


class ModuleVisitor(ast.NodeVisitor):
    """AST visitor that extracts top-level structural information from a module.

    Collects imports, class definitions, function definitions, and module-level constants.
    Does NOT descend into function bodies — only captures signatures and docstrings.
    """

    def __init__(self) -> None:
        self.imports: list[ImportInfo] = []
        self.classes: list[ClassMetadata] = []
        self.functions: list[FunctionMetadata] = []
        self.global_constants: list[str] = []
        self.has_main_guard: bool = False

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        """Extract standard import statements."""
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    module=alias.name,
                    alias=alias.asname,
                    is_relative=False,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        """Extract from-import statements."""
        module_name = node.module or ""
        level = node.level or 0

        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    module=module_name,
                    name=alias.name,
                    alias=alias.asname,
                    is_relative=level > 0,
                    level=level,
                )
            )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        """Extract class definitions with methods."""
        methods = self._extract_methods(node)
        base_classes = self._extract_bases(node)
        decorators = self._extract_decorators(node)

        is_dataclass = any("dataclass" in d for d in decorators)
        is_abstract = any(
            base in ("ABC", "ABCMeta", "abc.ABC") for base in base_classes
        )

        self.classes.append(
            ClassMetadata(
                name=node.name,
                docstring=ast.get_docstring(node),
                methods=methods,
                base_classes=base_classes,
                decorators=decorators,
                line_number=node.lineno,
                is_dataclass=is_dataclass,
                is_abstract=is_abstract,
            )
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        """Extract top-level function definitions."""
        self.functions.append(self._build_function_metadata(node, is_async=False))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        """Extract top-level async function definitions."""
        self.functions.append(self._build_function_metadata(node, is_async=True))

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        """Detect module-level constant assignments (UPPER_CASE names)."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                self.global_constants.append(target.id)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
        """Detect module-level annotated constant assignments (UPPER_CASE names)."""
        if isinstance(node.target, ast.Name) and node.target.id.isupper():
            self.global_constants.append(node.target.id)

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        """Detect if __name__ == '__main__' guard."""
        if self._is_main_guard(node):
            self.has_main_guard = True
        self.generic_visit(node)

    def _build_function_metadata(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        *,
        is_async: bool,
    ) -> FunctionMetadata:
        """Extract metadata from a function/method node."""
        arguments = self._extract_arguments(node.args)
        returns = ast.unparse(node.returns) if node.returns else None
        decorators = self._extract_decorators(node)
        complexity = self._estimate_complexity(node)

        return FunctionMetadata(
            name=node.name,
            arguments=arguments,
            returns=returns,
            docstring=ast.get_docstring(node),
            is_async=is_async,
            decorators=decorators,
            line_number=node.lineno,
            complexity_hint=complexity,
        )

    @staticmethod
    def _extract_arguments(args: ast.arguments) -> list[str]:
        """Extract function arguments with type annotations."""
        result: list[str] = []

        all_args = args.posonlyargs + args.args + args.kwonlyargs
        for arg in all_args:
            repr_str = arg.arg
            if arg.annotation is not None:
                try:
                    repr_str += f": {ast.unparse(arg.annotation)}"
                except Exception:  # noqa: BLE001
                    repr_str += ": <unparseable>"
            result.append(repr_str)

        if args.vararg:
            result.append(f"*{args.vararg.arg}")
        if args.kwarg:
            result.append(f"**{args.kwarg.arg}")

        return result

    @staticmethod
    def _extract_bases(node: ast.ClassDef) -> list[str]:
        """Extract base class names."""
        bases: list[str] = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except Exception:  # noqa: BLE001
                bases.append("<unknown>")
        return bases

    @staticmethod
    def _extract_decorators(
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> list[str]:
        """Extract decorator names."""
        decorators: list[str] = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except Exception:  # noqa: BLE001
                decorators.append("<unknown>")
        return decorators

    @staticmethod
    def _extract_methods(node: ast.ClassDef) -> list[FunctionMetadata]:
        """Extract method definitions from a class body."""
        methods: list[FunctionMetadata] = []

        for item in ast.iter_child_nodes(node):
            if isinstance(item, ast.FunctionDef):
                arguments = ModuleVisitor._extract_arguments(item.args)
                decorators = ModuleVisitor._extract_decorators(item)
                methods.append(
                    FunctionMetadata(
                        name=item.name,
                        arguments=arguments,
                        returns=ast.unparse(item.returns) if item.returns else None,
                        docstring=ast.get_docstring(item),
                        is_async=False,
                        decorators=decorators,
                        line_number=item.lineno,
                    )
                )
            elif isinstance(item, ast.AsyncFunctionDef):
                arguments = ModuleVisitor._extract_arguments(item.args)
                decorators = ModuleVisitor._extract_decorators(item)
                methods.append(
                    FunctionMetadata(
                        name=item.name,
                        arguments=arguments,
                        returns=ast.unparse(item.returns) if item.returns else None,
                        docstring=ast.get_docstring(item),
                        is_async=True,
                        decorators=decorators,
                        line_number=item.lineno,
                    )
                )

        return methods

    @staticmethod
    def _estimate_complexity(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """Estimate cyclomatic complexity by counting branch points."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    @staticmethod
    def _is_main_guard(node: ast.If) -> bool:
        """Check if an If node is `if __name__ == '__main__':`."""
        if not isinstance(node.test, ast.Compare):
            return False
        if not isinstance(node.test.left, ast.Name):
            return False
        if node.test.left.id != "__name__":
            return False
        if len(node.test.comparators) != 1:
            return False
        comp = node.test.comparators[0]
        if isinstance(comp, ast.Constant) and comp.value == "__main__":
            return True
        return False
