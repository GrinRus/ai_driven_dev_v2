from __future__ import annotations

import ast
from pathlib import Path

import pytest

CORE_TASK_SEMANTICS = {
    "RepositorySnapshot",
    "TaskExecutionContext",
    "TaskFinalizationContext",
    "complete_task_attempt",
    "complete_task_finalization",
    "prepare_task_attempt",
    "prepare_task_finalization",
    "render_aggregate_implementation_report",
    "task_diff_evidence",
}


@pytest.mark.parametrize("path", [Path("src/aidd/cli/task.py"), Path("src/aidd/cli/ui.py")])
def test_cli_and_ui_do_not_own_or_reexport_core_task_semantics(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definitions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    exported: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            continue
        if isinstance(node.value, (ast.List, ast.Tuple)):
            exported.update(
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )

    assert definitions.isdisjoint(CORE_TASK_SEMANTICS)
    assert exported.isdisjoint(CORE_TASK_SEMANTICS)


def test_task_execution_hotspot_has_no_compatibility_facade() -> None:
    assert not Path("src/aidd/core/task_execution.py").exists()
