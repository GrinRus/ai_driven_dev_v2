from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from pathlib import Path

import pytest

from aidd.cli.run import run_workflow
from aidd.cli.stage_run import run_stage_command, run_stage_interact_command
from aidd.cli.ui import OperatorUiService


@dataclass(frozen=True, slots=True)
class EntrypointConformanceCase:
    entrypoint: str
    source: str
    owner: str
    required_calls: tuple[str, ...]


ENTRYPOINT_CONFORMANCE = (
    EntrypointConformanceCase(
        "workflow",
        "src/aidd/cli/run.py",
        "_run_stage_from_workflow",
        ("execute_all_tasks",),
    ),
    EntrypointConformanceCase(
        "stage-run",
        "src/aidd/cli/stage_run.py",
        "run_stage_command",
        ("execute_all_tasks",),
    ),
    EntrypointConformanceCase(
        "stage-interact",
        "src/aidd/cli/stage_run.py",
        "run_stage_interact_command",
        ("interact_with_implementation",),
    ),
    EntrypointConformanceCase(
        "task-run",
        "src/aidd/cli/task.py",
        "execute_task_by_id",
        ("_implementation_service", "run_task"),
    ),
    EntrypointConformanceCase(
        "task-finalize",
        "src/aidd/cli/task.py",
        "finalize_implementation",
        ("_implementation_service", "finalize"),
    ),
    EntrypointConformanceCase(
        "ui-task-run",
        "src/aidd/cli/ui.py",
        "_start_task_job",
        ("_implementation_service", "run_task"),
    ),
    EntrypointConformanceCase(
        "ui-task-finalize",
        "src/aidd/cli/ui.py",
        "_start_task_finalize_job",
        ("_implementation_service", "finalize"),
    ),
    EntrypointConformanceCase(
        "ui-remediation",
        "src/aidd/cli/ui.py",
        "_launch_remediation",
        (
            "reopen_for_remediation",
            "implementation_finalization_blocker",
            "mark_downstream_stale",
        ),
    ),
)


def _function_calls(path: Path, owner: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definition = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == owner
    )
    calls: set[str] = set()
    for node in ast.walk(definition):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            calls.add(node.func.attr)
    return calls


@pytest.mark.parametrize(
    "case",
    ENTRYPOINT_CONFORMANCE,
    ids=lambda case: case.entrypoint,
)
def test_implementation_entrypoint_routes_through_task_aware_boundary(
    case: EntrypointConformanceCase,
) -> None:
    calls = _function_calls(Path(case.source), case.owner)

    assert set(case.required_calls) <= calls


def test_conformance_matrix_covers_every_architecture_entrypoint_family() -> None:
    assert {case.entrypoint for case in ENTRYPOINT_CONFORMANCE} == {
        "workflow",
        "stage-run",
        "stage-interact",
        "task-run",
        "task-finalize",
        "ui-task-run",
        "ui-task-finalize",
        "ui-remediation",
    }


def test_ui_stage_workflow_and_interact_defaults_use_public_task_aware_entrypoints() -> None:
    parameters = inspect.signature(OperatorUiService.__init__).parameters

    assert parameters["workflow_runner"].default is run_workflow
    assert parameters["stage_runner"].default is run_stage_command
    assert parameters["stage_interact_runner"].default is run_stage_interact_command
