from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.core.implementation_finalization import (
    complete_task_finalization,
    prepare_task_finalization,
    render_aggregate_implementation_report,
)
from aidd.core.task_ledger import TaskExecutionStatus, TaskLedger
from aidd.core.task_plan import parse_task_plan


def _plan():  # type: ignore[no-untyped-def]
    return parse_task_plan(
        """# Tasklist

## Task summary

One task supplies aggregate finalization evidence.

## Ordered tasks

### TL-1 — Add evidence

- Outcome: Evidence is available.
- Dominant deliverable: `src/example.py` contains evidence.
- In scope: `src/example.py`.
- Acceptance criteria:
  - TL-1-AC1: Evidence exists.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: `pytest -q`
"""
    )


def _successful_ledger(workspace_root: Path) -> TaskLedger:
    plan = _plan()
    attempt = workspace_root / "task-attempt"
    attempt.mkdir(parents=True)
    (attempt / "implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n- `src/example.py`\n\n"
        "## Verification notes\n\n- `pytest -q` -> pass.\n\n"
        "## Follow-up notes\n\n- none\n",
        encoding="utf-8",
    )
    ledger = TaskLedger.create(plan).transition(
        "TL-1",
        TaskExecutionStatus.EXECUTING,
        attempt_number=1,
        latest_attempt_path="task-attempt",
    )
    return ledger.transition("TL-1", TaskExecutionStatus.SUCCEEDED)


def test_finalization_attempts_are_monotonic_after_interruption(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    first = prepare_task_finalization(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        ledger=_successful_ledger(workspace_root),
    )

    second = prepare_task_finalization(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        ledger=first.ledger,
    )

    assert first.attempt_number == 1
    assert second.attempt_number == 2
    assert second.attempt_path.name == "attempt-0002"


def test_finalization_terminal_state_preserves_schema_and_blocker(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    context = prepare_task_finalization(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        ledger=_successful_ledger(workspace_root),
    )

    ledger = complete_task_finalization(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        succeeded=False,
        blocker="publication failed",
    )

    payload = json.loads(
        (context.attempt_path / "finalization-state.json").read_text(encoding="utf-8")
    )
    assert ledger.finalization.status.value == "failed"
    assert payload == {
        "schema_version": 1,
        "attempt_number": 1,
        "status": "failed",
        "blocker": "publication failed",
    }


def test_aggregate_report_requires_complete_task_evidence(tmp_path: Path) -> None:
    plan = _plan()
    incomplete = TaskLedger.create(plan)

    with pytest.raises(ValueError, match="before every task succeeds"):
        render_aggregate_implementation_report(
            plan=plan,
            ledger=incomplete,
            workspace_root=tmp_path,
        )

    report = render_aggregate_implementation_report(
        plan=plan,
        ledger=_successful_ledger(tmp_path),
        workspace_root=tmp_path,
    )
    assert "`TL-1`" in report
    assert "`TL-1-AC1`" in report
    assert "`src/example.py`" in report
