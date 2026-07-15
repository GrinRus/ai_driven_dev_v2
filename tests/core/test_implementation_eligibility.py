from __future__ import annotations

from pathlib import Path

from aidd.core.implementation_eligibility import implementation_finalization_blocker
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    persist_task_ledger,
)
from aidd.core.task_plan import parse_task_plan

_TASKLIST = """# Tasklist

## Task summary

One bounded task.

## Ordered tasks

### TL-1 — Implement behavior

- Outcome: Behavior is implemented.
- Dominant deliverable: `src/app.py`.
- In scope: `src/app.py`.
- Acceptance criteria:
  - TL-1-AC1: Behavior is verified.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: `pytest -q`
"""


def _write_tasklist(workspace_root: Path) -> TaskLedger:
    path = (
        workspace_root
        / "workitems"
        / "WI-1"
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    path.parent.mkdir(parents=True)
    path.write_text(_TASKLIST, encoding="utf-8")
    return TaskLedger.create(parse_task_plan(_TASKLIST))


def test_implementation_finalization_blocker_requires_complete_matching_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    ledger = _write_tasklist(workspace_root)

    assert "ledger is missing" in implementation_finalization_blocker(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
    )

    ledger = ledger.transition("TL-1", TaskExecutionStatus.EXECUTING, attempt_number=1)
    ledger = ledger.transition("TL-1", TaskExecutionStatus.SUCCEEDED)
    ledger = ledger.transition_finalization(
        TaskFinalizationStatus.EXECUTING,
        attempt_number=1,
        latest_attempt_path="reports/runs/WI-1/run-1/finalization-attempt-0001",
    )
    ledger = ledger.transition_finalization(TaskFinalizationStatus.SUCCEEDED)
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        ledger=ledger,
    )
    finalization = workspace_root / str(ledger.finalization.latest_attempt_path)
    finalization.mkdir(parents=True)
    published = (
        workspace_root
        / "workitems"
        / "WI-1"
        / "stages"
        / "implement"
        / "output"
        / "implementation-report.md"
    )
    published.parent.mkdir(parents=True)
    published.write_text("# Implementation Report\n", encoding="utf-8")

    assert implementation_finalization_blocker(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
    ) is None

    tasklist = (
        workspace_root
        / "workitems"
        / "WI-1"
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    tasklist.write_text(_TASKLIST.replace("One bounded task.", "Changed task."), encoding="utf-8")
    assert "source hash" in implementation_finalization_blocker(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
    )
