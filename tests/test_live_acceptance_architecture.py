from __future__ import annotations

import ast
from pathlib import Path

_RUNTIME_PRODUCT_ROOTS = (
    Path("src/aidd/core"),
    Path("src/aidd/adapters"),
    Path("src/aidd/validators"),
    Path("src/aidd/cli"),
)
_FORBIDDEN_LITERALS = (
    "AIDD-LIVE-",
    "TASK-LIVE-HONO",
    "hono-non-error-throw-handling",
    "cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba",
)
_PRODUCT_TEXT_ROOTS = (Path("prompt-packs"), Path("contracts"))


def _product_python_files() -> tuple[Path, ...]:
    return tuple(
        path
        for root in _RUNTIME_PRODUCT_ROOTS
        for path in sorted(root.rglob("*.py"))
        if path != Path("src/aidd/cli/eval.py")
    )


def test_runtime_product_surface_has_no_live_scenario_literals() -> None:
    violations = {
        path.as_posix(): literal
        for path in _product_python_files()
        for literal in _FORBIDDEN_LITERALS
        if literal in path.read_text(encoding="utf-8")
    }

    assert violations == {}


def test_product_contracts_and_prompts_have_no_live_scenario_literals() -> None:
    product_files = tuple(
        path
        for root in _PRODUCT_TEXT_ROOTS
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )
    violations = {
        path.as_posix(): literal
        for path in product_files
        for literal in _FORBIDDEN_LITERALS
        if literal in path.read_text(encoding="utf-8")
    }

    assert violations == {}


def test_only_explicit_eval_facade_imports_harness_from_product_cli() -> None:
    violations: list[str] = []
    for path in _product_python_files():
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("aidd.harness"):
                violations.append(path.as_posix())
            if isinstance(node, ast.Import):
                if any(alias.name.startswith("aidd.harness") for alias in node.names):
                    violations.append(path.as_posix())

    assert violations == []
