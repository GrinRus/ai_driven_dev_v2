from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskLedger,
    persist_task_ledger,
    task_root,
)
from aidd.core.task_plan import parse_task_plan
from aidd.core.task_read_model import resolve_task_read_model


def _tasklist(*, summary: str = "four dependency-aware tasks") -> str:
    return f"""# Tasklist

## Task summary

{summary}.

## Ordered tasks

### TL-1 — Establish the contract

- Outcome: The contract is explicit.
- Dominant deliverable: `contracts/example.md` is updated.
- In scope: `contracts/example.md` and `tests/test_contract.py`.
- Acceptance criteria:
  - TL-1-AC1: The contract is documented.

### TL-2 — Implement the behavior

- Outcome: The behavior is implemented.
- Dominant deliverable: `src/example.py` contains the behavior.
- In scope: `src/example.py` and `tests/test_example.py`.
- Acceptance criteria:
  - TL-2-AC1: The behavior is covered.

### TL-3 — Add the edge cases

- Outcome: Edge cases are handled.
- Dominant deliverable: `src/edge_cases.py` contains the guards.
- In scope: `src/edge_cases.py` and `tests/test_edge_cases.py`.
- Acceptance criteria:
  - TL-3-AC1: Edge cases are covered.

### TL-4 — Verify the delivery

- Outcome: Delivery is verified.
- Dominant deliverable: `tests/test_delivery.py` verifies the result.
- In scope: `tests/test_delivery.py`.
- Acceptance criteria:
  - TL-4-AC1: The delivery is verified.

## Dependencies

- TL-1: none
- TL-2: TL-1
- TL-3: TL-1
- TL-4: TL-2, TL-3

## Verification notes

- TL-1: `pytest tests/test_contract.py -q`
- TL-2: `pytest tests/test_example.py -q`
- TL-3: `pytest tests/test_edge_cases.py -q`
- TL-4: `pytest tests/test_delivery.py -q`
"""


def _write_tasklist(workspace_root: Path, text: str | None = None) -> None:
    path = (
        workspace_root
        / "workitems"
        / "WI-READ"
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or _tasklist(), encoding="utf-8")


def _ledger(workspace_root: Path, *, run_id: str = "run-1") -> TaskLedger:
    plan = parse_task_plan(_tasklist())
    return TaskLedger.create(plan)


def test_task_workspace_groups_dependency_graph_and_selects_next_ready(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)

    model = cast(
        dict[str, Any],
        resolve_task_read_model(workspace_root=workspace_root, work_item="WI-READ"),
    )

    assert model["groups"] == {
        "Ready": ["TL-1"],
        "Running": [],
        "Blocked": ["TL-2", "TL-3", "TL-4"],
        "Done": [],
    }
    assert model["next_ready_task"] == "TL-1"
    assert model["critical_path"] == ["TL-1", "TL-2", "TL-4"]
    assert model["dependency_graph"]["TL-4"] == {
        "dependencies": ["TL-2", "TL-3"],
        "dependents": [],
        "dependency_eligible": False,
        "status": "pending",
    }
    assert model["status"] == "ready"
    assert model["tasklist"]["matches"] is True


def test_task_workspace_preserves_success_and_projects_partial_progress(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)
    ledger = _ledger(workspace_root)
    ledger = ledger.transition("TL-1", TaskExecutionStatus.EXECUTING)
    ledger = ledger.transition("TL-1", TaskExecutionStatus.SUCCEEDED)
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-READ",
        run_id="run-1",
        ledger=ledger,
    )

    model = cast(dict[str, Any], resolve_task_read_model(
        workspace_root=workspace_root,
        work_item="WI-READ",
        run_id="run-1",
    ))

    assert model["groups"] == {
        "Ready": ["TL-2", "TL-3"],
        "Running": [],
        "Blocked": ["TL-4"],
        "Done": ["TL-1"],
    }
    assert model["next_ready"]["task_id"] == "TL-2"
    assert model["preserved_successes"] == ["TL-1"]
    assert model["finalization_eligibility"] == {
        "eligible": False,
        "reason": "Every task must succeed before finalization.",
    }
    selected = next(task for task in model["tasks"] if task["id"] == "TL-4")
    assert selected["missing_dependencies"] == ["TL-2", "TL-3"]
    assert selected["dependency_state"]["satisfied"] is False


def test_task_workspace_exposes_running_attempt_and_durable_event(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)
    attempt_path = task_root(
        workspace_root=workspace_root,
        work_item="WI-READ",
        run_id="run-1",
        task_id="TL-1",
    ) / "attempts" / "attempt-0001"
    attempt_path.mkdir(parents=True)
    (attempt_path / "attempt-state.json").write_text(
        json.dumps({"status": "executing", "task_id": "TL-1", "attempt_number": 1}),
        encoding="utf-8",
    )
    ledger = _ledger(workspace_root).transition(
        "TL-1",
        TaskExecutionStatus.EXECUTING,
        attempt_number=1,
        latest_attempt_path=attempt_path.relative_to(workspace_root).as_posix(),
    )
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-READ",
        run_id="run-1",
        ledger=ledger,
    )

    model = cast(dict[str, Any], resolve_task_read_model(
        workspace_root=workspace_root,
        work_item="WI-READ",
        run_id="run-1",
    ))
    task = next(item for item in model["tasks"] if item["id"] == "TL-1")

    assert model["groups"]["Running"] == ["TL-1"]
    assert task["attempts"][0]["status"] == "executing"
    assert task["last_durable_event"]["kind"] == "task-ledger"
    assert task["last_durable_event"]["path"] == attempt_path.relative_to(workspace_root).as_posix()


def test_task_workspace_has_no_ready_task_while_current_attempt_runs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)
    ledger = _ledger(workspace_root).transition("TL-1", TaskExecutionStatus.EXECUTING)
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-READ",
        run_id="run-1",
        ledger=ledger,
    )

    model = cast(dict[str, Any], resolve_task_read_model(
        workspace_root=workspace_root,
        work_item="WI-READ",
        run_id="run-1",
    ))

    assert model["next_ready_task"] is None
    assert model["groups"]["Running"] == ["TL-1"]
    assert model["groups"]["Blocked"] == ["TL-2", "TL-3", "TL-4"]


def test_task_workspace_fails_closed_when_published_tasklist_hash_drifts(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist(workspace_root)
    ledger = _ledger(workspace_root).transition("TL-1", TaskExecutionStatus.EXECUTING)
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-READ",
        run_id="run-1",
        ledger=ledger,
    )
    _write_tasklist(workspace_root, _tasklist(summary="published tasklist changed"))

    with pytest.raises(ValueError, match="Published tasklist changed"):
        resolve_task_read_model(
            workspace_root=workspace_root,
            work_item="WI-READ",
            run_id="run-1",
        )
