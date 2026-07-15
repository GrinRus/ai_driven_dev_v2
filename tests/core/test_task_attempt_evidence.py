from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.core.implementation_service import (
    ImplementationExecutionRequest,
    _record_global_attempt_references,
)
from aidd.core.run_store import run_attempt_root
from aidd.core.task_attempt_evidence import (
    TASK_ATTEMPT_REFERENCES_FILENAME,
    load_task_attempt_references,
    resolve_task_attempt_evidence,
    write_task_attempt_references,
)
from aidd.core.task_attempt_lifecycle import TaskExecutionContext
from aidd.core.task_ledger import TaskLedger
from aidd.core.task_plan import TaskPlan, parse_task_plan
from aidd.core.task_read_model import _attempts


def _plan() -> TaskPlan:
    return parse_task_plan(
        """# Tasklist

## Task summary

One bounded task.

## Ordered tasks

### TL-1 — Add evidence

- Outcome: Evidence is durable.
- Dominant deliverable: `src/evidence.py` records evidence.
- In scope: `src/evidence.py`.
- Acceptance criteria:
  - TL-1-AC1: Evidence exists.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: `pytest -q`
"""
    )


def _global_attempt(workspace_root: Path, number: int) -> Path:
    path = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        stage="implement",
        attempt_number=number,
    )
    path.mkdir(parents=True)
    return path


def _task_attempt(workspace_root: Path, number: int = 1) -> Path:
    path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-1"
        / "run-1"
        / "stages"
        / "implement"
        / "tasks"
        / "TL-1"
        / "attempts"
        / f"attempt-{number:04d}"
    )
    path.mkdir(parents=True)
    return path


def test_reference_manifest_rejects_dangling_and_identity_mismatch(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    task_attempt = _task_attempt(workspace_root)
    global_attempt = _global_attempt(workspace_root, 1)
    manifest_path = write_task_attempt_references(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        task_attempt_number=1,
        task_attempt_path=task_attempt,
        stage_attempt_numbers=(1,),
    )

    manifest = load_task_attempt_references(
        path=manifest_path,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        task_attempt_number=1,
    )
    assert [reference.attempt_number for reference in manifest.stage_attempts] == [1]

    global_attempt.rmdir()
    with pytest.raises(ValueError, match="does not exist"):
        load_task_attempt_references(
            path=manifest_path,
            workspace_root=workspace_root,
            work_item="WI-1",
            run_id="run-1",
            task_id="TL-1",
            task_attempt_number=1,
        )

    global_attempt.mkdir()
    (global_attempt / "artifact-index.json").write_text(
        json.dumps(
            {
                "work_item_id": "WI-OTHER",
                "run_id": "run-1",
                "stage": "implement",
                "attempt_number": 1,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="identity"):
        load_task_attempt_references(
            path=manifest_path,
            workspace_root=workspace_root,
            work_item="WI-1",
            run_id="run-1",
            task_id="TL-1",
            task_attempt_number=1,
        )


def test_reference_manifest_atomic_write_cleans_staging_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    task_attempt = _task_attempt(workspace_root)
    _global_attempt(workspace_root, 1)
    original_replace = Path.replace

    def fail_manifest_replace(path: Path, target: Path) -> Path:
        if path.name == f".{TASK_ATTEMPT_REFERENCES_FILENAME}.tmp":
            raise OSError("interrupted manifest commit")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_manifest_replace)
    with pytest.raises(OSError, match="interrupted"):
        write_task_attempt_references(
            workspace_root=workspace_root,
            work_item="WI-1",
            run_id="run-1",
            task_id="TL-1",
            task_attempt_number=1,
            task_attempt_path=task_attempt,
            stage_attempt_numbers=(1,),
        )

    assert not (task_attempt / TASK_ATTEMPT_REFERENCES_FILENAME).exists()
    assert not (task_attempt / f".{TASK_ATTEMPT_REFERENCES_FILENAME}.tmp").exists()


def test_reference_manifest_rejects_symlink_escape(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    task_attempt = _task_attempt(workspace_root)
    expected = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        stage="implement",
        attempt_number=1,
    )
    expected.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside-attempt"
    outside.mkdir()
    expected.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="resolve directly|escapes workspace"):
        write_task_attempt_references(
            workspace_root=workspace_root,
            work_item="WI-1",
            run_id="run-1",
            task_id="TL-1",
            task_attempt_number=1,
            task_attempt_path=task_attempt,
            stage_attempt_numbers=(1,),
        )


def test_materialization_references_only_current_attempt_range_without_payload_copies(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    task_attempt = _task_attempt(workspace_root, number=2)
    for number in range(1, 5):
        global_attempt = _global_attempt(workspace_root, number)
        (global_attempt / "runtime.log").write_bytes(b"x" * 256_000)
        (global_attempt / "input-bundle.md").write_text("# Input\n", encoding="utf-8")
        if number == 4:
            (global_attempt / "repair-context.md").write_text("# Repair\n", encoding="utf-8")
    plan = _plan()
    context = TaskExecutionContext(
        plan=plan,
        ledger=TaskLedger.create(plan),
        task=plan.tasks[0],
        global_attempt_start=3,
        task_attempt_number=2,
        task_attempt_path=task_attempt,
    )
    _record_global_attempt_references(
        context=context,
        request=ImplementationExecutionRequest(
            workspace_root=workspace_root,
            work_item="WI-1",
            run_id="run-1",
            project_root=tmp_path,
        ),
    )

    manifest_path = task_attempt / TASK_ATTEMPT_REFERENCES_FILENAME
    manifest = load_task_attempt_references(
        path=manifest_path,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        task_attempt_number=2,
    )
    assert [reference.attempt_number for reference in manifest.stage_attempts] == [3, 4]
    assert manifest_path.stat().st_size < 2_048
    assert not tuple(task_attempt.glob("stage-attempt-[0-9][0-9][0-9][0-9]"))
    assert not (task_attempt / "runtime.log").exists()
    assert not (task_attempt / "input-bundle.md").exists()
    assert not (task_attempt / "repair-context.md").exists()


def test_read_model_resolves_new_references_and_legacy_embedded_attempts(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    referenced_attempt = _global_attempt(workspace_root, 1)
    referenced_attempt.joinpath("runtime.log").write_text("runtime\n", encoding="utf-8")
    new_attempt = _task_attempt(workspace_root, number=1)
    new_attempt.joinpath("attempt-state.json").write_text(
        '{"status": "succeeded"}', encoding="utf-8"
    )
    write_task_attempt_references(
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        task_attempt_number=1,
        task_attempt_path=new_attempt,
        stage_attempt_numbers=(1,),
    )
    legacy_attempt = _task_attempt(workspace_root, number=2)
    legacy_attempt.joinpath("attempt-state.json").write_text(
        '{"status": "failed"}', encoding="utf-8"
    )
    legacy_attempt.joinpath("stage-attempt-0002").mkdir()
    legacy_attempt.joinpath("runtime.log").write_text("legacy\n", encoding="utf-8")

    items = _attempts(
        new_attempt.parent,
        workspace_root=workspace_root,
        task_evidence_identity=("WI-1", "run-1", "TL-1"),
    )

    assert items[0]["runtime_evidence"] == {
        "layout": "references",
        "stage_attempts": [
            {
                "attempt_number": 1,
                "path": referenced_attempt.relative_to(workspace_root).as_posix(),
            }
        ],
    }
    assert items[1]["runtime_evidence"] == {
        "layout": "legacy",
        "stage_attempts": [
            {
                "attempt_number": 2,
                "path": legacy_attempt.joinpath("stage-attempt-0002")
                .relative_to(workspace_root)
                .as_posix(),
            }
        ],
    }
    legacy = resolve_task_attempt_evidence(
        task_attempt_path=legacy_attempt,
        workspace_root=workspace_root,
        work_item="WI-1",
        run_id="run-1",
        task_id="TL-1",
        task_attempt_number=2,
    )
    assert legacy.layout == "legacy"
