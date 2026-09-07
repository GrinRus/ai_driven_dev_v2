from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.application.implementation import aggregate_finalization_port
from aidd.core.implementation_finalization import (
    OUTSIDE_PROJECT_SET_EVIDENCE_FILENAME,
    TaskFinalizationContext,
    aggregate_execution_mode,
    complete_task_finalization,
    outside_project_set_changes,
    prepare_task_finalization,
    render_aggregate_implementation_report,
)
from aidd.core.run_store import create_run_manifest, load_stage_metadata, persist_stage_status
from aidd.core.task_ledger import TaskExecutionStatus, TaskLedger
from aidd.core.task_plan import TaskExecutionMode, parse_task_plan
from aidd.validators.semantic_rules.evidence import has_implementation_command_evidence


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
        "## Verification\n\n- `pytest -q` -> pass.\n\n"
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
    assert first.lineage is not None
    assert first.lineage.scope.value == "finalization"
    assert first.lineage.attempt_kind.value == "finalization"
    assert first.lineage.attempt_number == 1


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
    assert payload["schema_version"] == 1
    assert payload["attempt_number"] == 1
    assert payload["status"] == "failed"
    assert payload["blocker"] == "publication failed"
    assert payload["lineage"]["scope"] == "finalization"
    assert payload["lineage"]["attempt_kind"] == "finalization"
    assert payload["lineage"]["attempt_number"] == 1
    assert payload["created_at_utc"]
    assert payload["updated_at_utc"]
    assert payload["created_at_utc"] <= payload["updated_at_utc"]


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
    assert "- `TL-1` `pytest -q` -> pass." in report


def test_aggregate_report_preserves_wrapped_verification_evidence(tmp_path: Path) -> None:
    plan = _plan()
    attempt = tmp_path / "task-attempt"
    attempt.mkdir()
    (attempt / "implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n- `src/example.py`\n\n"
        "## Verification\n\n"
        "- Authored test suite:\n"
        "  `uv run --frozen pytest -q tests/test_example.py`\n"
        "  -> pass (12 passed).\n"
        "  - nested detail remains part of the same item\n"
        "- Lint check: `uv run --frozen ruff check src/example.py` -> pass.\n\n"
        "## Follow-up notes\n\n- none\n",
        encoding="utf-8",
    )
    ledger = TaskLedger.create(plan).transition(
        "TL-1",
        TaskExecutionStatus.EXECUTING,
        attempt_number=1,
        latest_attempt_path="task-attempt",
    ).transition("TL-1", TaskExecutionStatus.SUCCEEDED)

    report = render_aggregate_implementation_report(
        plan=plan,
        ledger=ledger,
        workspace_root=tmp_path,
    )

    verification = report.split("## Verification notes", 1)[1].split(
        "## Follow-up notes", 1
    )[0]
    assert "`uv run --frozen pytest -q tests/test_example.py` -> pass (12 passed)." in report
    assert "nested detail remains part of the same item" in report
    assert has_implementation_command_evidence(
        "Authored test suite: `uv run --frozen pytest -q tests/test_example.py`"
        " -> pass (12 passed)."
    )
    assert verification.count("Authored test suite:") == 1
    assert verification.count("Lint check:") == 1


def test_mixed_mode_aggregate_omits_verification_only_none_entry(tmp_path: Path) -> None:
    plan = parse_task_plan(
        """# Tasklist

## Task summary

One task changes the repository and one verifies the aggregate result.

## Ordered tasks

### T1 — Change the repository

- Outcome: The repository change exists.
- Dominant deliverable: `src/example.py` contains the change.
- In scope: `src/example.py`.
- Acceptance criteria:
  - T1-AC1: The change exists.

### T2 — Verify the repository

- Outcome: The completed repository change is verified.
- Dominant deliverable: verification evidence.
- In scope: `src/example.py`.
- Execution mode: verification-only
- Acceptance criteria:
  - T2-AC1: The verification passes.

## Dependencies

- T1: none
- T2: T1

## Verification notes

- T1: `pytest -q`
- T2: `pytest -q`
"""
    )
    reports = {
        "T1": (
            "# Implementation Report\n\n## Touched files\n\n"
            "- `src/example.py` - implement the change.\n\n"
            "## Verification notes\n\n- `pytest -q` -> pass.\n\n"
            "## Follow-up notes\n\n- none\n"
        ),
        "T2": (
            "# Implementation Report\n\n## Touched files\n\n- none\n\n"
            "## Verification notes\n\n- `pytest -q` -> pass.\n\n"
            "## Follow-up notes\n\n- none\n"
        ),
    }
    ledger = TaskLedger.create(plan)
    for attempt_number, task_id in enumerate(("T1", "T2"), start=1):
        attempt = tmp_path / task_id
        attempt.mkdir()
        (attempt / "implementation-report.md").write_text(
            reports[task_id], encoding="utf-8"
        )
        ledger = ledger.transition(
            task_id,
            TaskExecutionStatus.EXECUTING,
            attempt_number=attempt_number,
            latest_attempt_path=task_id,
        ).transition(task_id, TaskExecutionStatus.SUCCEEDED)

    report = render_aggregate_implementation_report(
        plan=plan,
        ledger=ledger,
        workspace_root=tmp_path,
    )

    touched_section = report.split("## Touched files", 1)[1].split(
        "## Verification notes", 1
    )[0]
    assert "`src/example.py`" in touched_section
    assert "- none" not in touched_section
    assert "- `T1` `pytest -q` -> pass." in report
    assert "- `T2` `pytest -q` -> pass." in report
    assert aggregate_execution_mode(plan) is TaskExecutionMode.REPOSITORY_CHANGE


def test_all_verification_only_aggregate_preserves_verification_mode() -> None:
    plan = parse_task_plan(
        """# Tasklist

## Task summary

One task verifies existing repository state.

## Ordered tasks

### T1 — Verify the repository

- Outcome: The repository is verified.
- Dominant deliverable: verification evidence.
- In scope: `src/example.py`.
- Execution mode: verification-only
- Acceptance criteria:
  - T1-AC1: The verification passes.

## Dependencies

- T1: none

## Verification notes

- T1: `pytest -q`
"""
    )

    assert aggregate_execution_mode(plan) is TaskExecutionMode.VERIFICATION_ONLY


def _write_project_set_context(workspace_root: Path, work_item: str = "WI-1") -> None:
    context = workspace_root / "workitems" / work_item / "context" / "project-set.md"
    context.parent.mkdir(parents=True, exist_ok=True)
    context.write_text(
        "# Project set\n\n"
        "## Projects\n\n"
        "| Project id | Root | Role |\n"
        "| --- | --- | --- |\n"
        "| `api` | `services/api` | `primary` |\n"
        "| `web` | `apps/web` | `secondary` |\n",
        encoding="utf-8",
    )


def test_outside_project_set_changes_preserve_exact_paths_and_task_ids(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    ledger = _successful_ledger(workspace_root)
    _write_project_set_context(workspace_root)
    (workspace_root / "task-attempt" / "task-diff.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "TL-1",
                "observed_touched_paths": [
                    "services/api/src/example.py",
                    "README.md",
                    "docs/notes.md",
                ],
            }
        ),
        encoding="utf-8",
    )

    assert outside_project_set_changes(
        workspace_root=workspace_root,
        work_item="WI-1",
        ledger=ledger,
    ) == (
        ("README.md", ("TL-1",)),
        ("docs/notes.md", ("TL-1",)),
    )


def test_aggregate_finalization_blocks_outside_project_set_and_persists_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item, run_id = "WI-1", "run-1"
    ledger = _successful_ledger(workspace_root)
    _write_project_set_context(workspace_root, work_item)
    (workspace_root / "task-attempt" / "task-diff.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "TL-1",
                "observed_touched_paths": ["outside.py"],
            }
        ),
        encoding="utf-8",
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target="implement",
        config_snapshot={},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
        status="executing",
    )
    finalization_attempt = (
        workspace_root
        / "reports"
        / "runs"
        / work_item
        / run_id
        / "stages"
        / "implement"
        / "finalization"
        / "attempts"
        / "attempt-0001"
    )
    finalization_attempt.mkdir(parents=True)
    context = TaskFinalizationContext(
        ledger=ledger,
        attempt_path=finalization_attempt,
        attempt_number=1,
    )

    with pytest.raises(ValueError, match="outside declared project-set paths"):
        aggregate_finalization_port(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )(context)

    evidence = finalization_attempt / OUTSIDE_PROJECT_SET_EVIDENCE_FILENAME
    assert evidence.is_file()
    assert "`outside.py`" in evidence.read_text(encoding="utf-8")
    diagnostics = json.loads(
        (finalization_attempt / "publication-diagnostics.json").read_text(encoding="utf-8")
    )
    assert diagnostics["status"] == "failed"
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
    )
    assert metadata is not None
    assert metadata.status == "failed"
