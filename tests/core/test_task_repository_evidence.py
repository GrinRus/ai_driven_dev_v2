from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.core.implementation_service import (
    ImplementationExecutionRequest,
    _complete_task_execution,
    _prepare_task_execution,
)
from aidd.core.task_attempt_lifecycle import TaskExecutionContext
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskLedger,
)
from aidd.core.task_plan import parse_task_plan
from aidd.core.task_repository_evidence import task_diff_evidence


def _tasklist(*, second_dependency: str = "TL-1") -> str:
    return f"""# Tasklist

## Task summary

Two bounded tasks with complete dependency and verification evidence.

## Ordered tasks

### TL-1 — Add the contract

- Outcome: The contract is explicit.
- Dominant deliverable: `contracts/example.md` is updated.
- In scope: `contracts/example.md` and `tests/test_contract.py`.
- Acceptance criteria:
  - TL-1-AC1: The required field is documented.

### TL-2 — Add enforcement

- Outcome: Invalid content is rejected.
- Dominant deliverable: `src/example.py` validates the field.
- In scope: `src/example.py` and `tests/test_validator.py`.
- Acceptance criteria:
  - TL-2-AC1: Missing content produces a stable finding.

## Dependencies

- TL-1: none
- TL-2: {second_dependency}

## Verification notes

- TL-1: `pytest tests/test_contract.py -q`
- TL-2: `pytest tests/test_validator.py -q`
"""



def prepare_task_execution(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_id: str,
    project_root: Path,
) -> TaskExecutionContext:
    return _prepare_task_execution(
        request=ImplementationExecutionRequest(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            project_root=project_root,
        ),
        task_id=task_id,
    )


def complete_task_execution(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    project_root: Path,
    succeeded: bool,
    blocker: str | None = None,
) -> TaskLedger:
    return _complete_task_execution(
        context=context,
        request=ImplementationExecutionRequest(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            project_root=project_root,
        ),
        succeeded=succeeded,
        blocker=blocker,
    )

def test_task_diff_uses_canonical_scope_component_boundary_and_malformed_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    project_root = tmp_path / "project"
    project_root.mkdir()
    plan = parse_task_plan(
        _tasklist().replace(
            "`contracts/example.md` and `tests/test_contract.py`.",
            "`src`.",
        )
    )
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    (attempt / "repository-baseline.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "TL-1",
                "status": [],
                "files": {},
            }
        ),
        encoding="utf-8",
    )
    context = TaskExecutionContext(
        plan=plan,
        ledger=TaskLedger.create(plan),
        task=plan.tasks[0],
        global_attempt_start=1,
        task_attempt_path=attempt,
    )
    monkeypatch.setattr(
        "aidd.core.task_repository_evidence.repository_file_snapshot",
        lambda _: {"src2/app.py": "changed"},
    )
    scope_path = workspace_root / "workitems" / "WI-1" / "context" / "allowed-write-scope.md"
    scope_path.parent.mkdir(parents=True)
    scope_path.write_text("# Allowed Write Scope\n\n- `src`\n", encoding="utf-8")

    _, issues = task_diff_evidence(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        project_root=project_root,
        report="## Touched files\n\n- `src2/app.py`\n",
    )
    assert any("outside allowed write scope" in issue for issue in issues)

    scope_path.write_text("# Allowed Write Scope\n\n- `../escape`\n", encoding="utf-8")
    _, malformed_issues = task_diff_evidence(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        project_root=project_root,
        report="## Touched files\n\n- `src2/app.py`\n",
    )
    assert any("Allowed write scope" in issue for issue in malformed_issues)

def test_task_attempt_records_diff_relative_to_its_own_baseline(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    tasklist_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)
    tasklist_path.write_text(_tasklist(), encoding="utf-8")
    source_path = tmp_path / "contracts" / "example.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("before\n", encoding="utf-8")

    context = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )
    source_path.write_text("after\n", encoding="utf-8")
    report_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "implement" / "implementation-report.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `contracts/example.md` - updated contract.\n",
        encoding="utf-8",
    )

    ledger = complete_task_execution(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        project_root=tmp_path,
        succeeded=True,
    )

    assert ledger.entry("TL-1").status is TaskExecutionStatus.SUCCEEDED
    diff_payload = (context.task_attempt_path / "task-diff.json").read_text(encoding="utf-8")
    assert '"observed_touched_paths": [\n    "contracts/example.md"' in diff_payload
    assert '"issues": []' in diff_payload

def test_task_attempt_fails_when_reported_paths_do_not_match_local_diff(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    tasklist_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "tasklist" / "output" / "tasklist.md"
    )
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)
    tasklist_path.write_text(_tasklist(), encoding="utf-8")
    source_path = tmp_path / "contracts" / "example.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("before\n", encoding="utf-8")
    context = prepare_task_execution(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        project_root=tmp_path,
    )
    source_path.write_text("after\n", encoding="utf-8")
    report_path = (
        workspace_root / "workitems" / "WI-1" / "stages" / "implement" / "implementation-report.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# Implementation Report\n\n## Touched files\n\n- `src/other.py` - claimed change.\n",
        encoding="utf-8",
    )

    ledger = complete_task_execution(
        context=context,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        project_root=tmp_path,
        succeeded=True,
    )

    entry = ledger.entry("TL-1")
    assert entry.status is TaskExecutionStatus.FAILED
    assert entry.blocker is not None
    assert "contracts/example.md" in entry.blocker
    assert "src/other.py" in entry.blocker
