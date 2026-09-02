from __future__ import annotations

import json
from pathlib import Path

from aidd.harness.task_flow_checkpoint import _tasklist_cards, build_task_flow_checkpoint


def test_tasklist_dependency_parser_ignores_explanatory_rationale() -> None:
    task_ids, dependencies = _tasklist_cards(
        """# Tasklist

### T1 — Runtime normalization
### T2 — Direct regressions
### T3 — Composed regressions

## Dependencies

- T1: none — establishes the runtime behavior required by later tasks.
- T2: T1 — adds direct coverage after the runtime behavior exists.
- T3: T1, T2 — adds composed coverage and preserves the existing error path.
"""
    )

    assert task_ids == ["T1", "T2", "T3"]
    assert dependencies == {"T1": (), "T2": ("T1",), "T3": ("T1", "T2")}


def test_tasklist_dependency_parser_keeps_malformed_machine_clause_fail_closed() -> None:
    _, dependencies = _tasklist_cards(
        """# Tasklist

### T1 — Runtime normalization

## Dependencies

- T1: T99 — references an unknown task id.
"""
    )

    assert dependencies == {"T1": ("T99",)}


def test_tasklist_dependency_parser_normalizes_terminal_punctuation() -> None:
    _, dependencies = _tasklist_cards(
        """# Tasklist

### T1 — Runtime normalization
### T2 — Direct regressions
### T3 — Verification

## Dependencies

- T1: none. — establishes the runtime boundary.
- T2: T1. — adds direct coverage.
- T3: T1, T2.; — runs the focused verification.
"""
    )

    assert dependencies == {"T1": (), "T2": ("T1",), "T3": ("T1", "T2")}


def test_tasklist_dependency_parser_matches_core_for_explanatory_task_ids() -> None:
    task_ids, dependencies = _tasklist_cards(
        """# Tasklist

### TL-1 — First task
### TL-2 — Second task
### TL-3 — Third task
### TL-4 — Fourth task

## Dependencies

- TL-1: none
- TL-2: TL-1
- TL-3: TL-1
- TL-4: TL-2 — same dependency reasoning as TL-3
"""
    )

    assert task_ids == ["TL-1", "TL-2", "TL-3", "TL-4"]
    assert dependencies["TL-4"] == ("TL-2",)


def _write_workspace(tmp_path: Path, *, finalization: str = "pending") -> tuple[Path, Path]:
    workspace = tmp_path / ".aidd"
    work_item = "WI-CHECKPOINT"
    tasklist = (
        workspace
        / "workitems"
        / work_item
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    tasklist.parent.mkdir(parents=True)
    tasklist.write_text(
        """# Tasklist

## Ordered tasks

### TL-1 — First task

### TL-2 — Second task

## Dependencies

- TL-1: none
- TL-2: TL-1
""",
        encoding="utf-8",
    )
    run_root = workspace / "reports" / "runs" / work_item / "run-1" / "stages" / "implement"
    run_root.mkdir(parents=True)
    ledger = {
        "schema_version": 2,
        "source_tasklist_sha256": "placeholder",
        "tasks": [],
        "finalization": {
            "status": finalization,
            "attempt_count": 1 if finalization == "succeeded" else 0,
            "latest_attempt_path": (
                "reports/runs/WI-CHECKPOINT/run-1/stages/implement/finalization/attempts/attempt-0001"
                if finalization == "succeeded"
                else None
            ),
        },
    }
    ledger_path = run_root / "task-ledger.json"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    if finalization == "succeeded":
        attempt = run_root / "finalization" / "attempts" / "attempt-0001"
        attempt.mkdir(parents=True)
        (attempt / "finalization-state.json").write_text(
            '{"status":"succeeded"}\n',
            encoding="utf-8",
        )
    return workspace, tasklist


def _model(*, tasklist_hash: str, finalization: str = "pending") -> dict[str, object]:
    succeeded = finalization == "succeeded"
    tasks = [
        {
            "id": "TL-1",
            "status": "succeeded" if succeeded else "pending",
            "dependencies": [],
            "ready": not succeeded,
            "attempt_count": 1 if succeeded else 0,
            "evidence_links": (
                [
                    "reports/runs/WI-CHECKPOINT/run-1/stages/implement/tasks/"
                    "TL-1/attempts/attempt-0001/implementation-report.md"
                ]
                if succeeded
                else []
            ),
        },
        {
            "id": "TL-2",
            "status": "succeeded" if succeeded else "blocked",
            "dependencies": ["TL-1"],
            "ready": False,
            "attempt_count": 1 if succeeded else 0,
            "evidence_links": (
                [
                    "reports/runs/WI-CHECKPOINT/run-1/stages/implement/tasks/"
                    "TL-2/attempts/attempt-0001/implementation-report.md"
                ]
                if succeeded
                else []
            ),
        },
    ]
    return {
        "schema_version": 1,
        "run_id": "run-1",
        "tasks": tasks,
        "tasklist": {
            "published_sha256": tasklist_hash,
            "ledger_sha256": tasklist_hash,
        },
        "next_ready_task": None if succeeded else "TL-1",
        "all_succeeded": succeeded,
        "finalization": {
            "status": finalization,
            "attempt_count": 1 if succeeded else 0,
            "latest_attempt_path": (
                "reports/runs/WI-CHECKPOINT/run-1/stages/implement/finalization/attempts/attempt-0001"
                if succeeded
                else None
            ),
        },
        "review_eligible": succeeded,
        "review_eligibility": {"eligible": succeeded, "reason": None if succeeded else "pending"},
    }


def test_checkpoint_passes_tasklist_snapshot_and_writes_both_projections(tmp_path: Path) -> None:
    workspace, tasklist = _write_workspace(tmp_path)
    import hashlib

    tasklist_hash = hashlib.sha256(tasklist.read_bytes()).hexdigest()
    ledger_path = (
        workspace
        / "reports"
        / "runs"
        / "WI-CHECKPOINT"
        / "run-1"
        / "stages"
        / "implement"
        / "task-ledger.json"
    )
    ledger_path.write_text(
        ledger_path.read_text(encoding="utf-8").replace("placeholder", tasklist_hash),
        encoding="utf-8",
    )
    result = build_task_flow_checkpoint(
        scenario_id="AIDD-DETERMINISTIC-004",
        work_item="WI-CHECKPOINT",
        run_id="run-1",
        runtime_id="generic-cli",
        aidd_revision="aidd-rev",
        target_revision="target-rev",
        stage="tasklist",
        workspace_root=workspace,
        output_root=tmp_path / "bundle",
        task_view=_model(tasklist_hash=tasklist_hash),
    )

    assert result.classification == "pass"
    assert result.json_path.exists()
    assert result.markdown_path.exists()
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["next_ready_task"] == "TL-1"
    assert "Task-Flow Checkpoint" in result.markdown_path.read_text(encoding="utf-8")


def test_checkpoint_fails_closed_on_hash_drift_and_missing_terminal_evidence(
    tmp_path: Path,
) -> None:
    workspace, _ = _write_workspace(tmp_path, finalization="succeeded")
    result = build_task_flow_checkpoint(
        scenario_id="AIDD-DETERMINISTIC-004",
        work_item="WI-CHECKPOINT",
        run_id="run-1",
        runtime_id="generic-cli",
        aidd_revision="aidd-rev",
        target_revision="target-rev",
        stage="implement",
        workspace_root=workspace,
        output_root=tmp_path / "bundle",
        task_view=_model(tasklist_hash="wrong", finalization="succeeded"),
    )

    assert result.classification == "fail"
    assert "public-tasklist-hash-mismatch" in result.payload["findings"]
    assert "missing-terminal-task-evidence:TL-1" in result.payload["findings"]
    assert "missing-terminal-task-evidence:TL-2" in result.payload["findings"]


def test_checkpoint_fails_closed_on_invalid_next_ready_selection(tmp_path: Path) -> None:
    workspace, tasklist = _write_workspace(tmp_path)
    import hashlib

    tasklist_hash = hashlib.sha256(tasklist.read_bytes()).hexdigest()
    model = _model(tasklist_hash=tasklist_hash)
    model["next_ready_task"] = "TL-2"
    result = build_task_flow_checkpoint(
        scenario_id="AIDD-DETERMINISTIC-004",
        work_item="WI-CHECKPOINT",
        run_id="run-1",
        runtime_id="generic-cli",
        aidd_revision=None,
        target_revision=None,
        stage="tasklist",
        workspace_root=workspace,
        output_root=tmp_path / "bundle",
        task_view=model,
    )

    assert result.classification == "fail"
    assert "invalid-core-next-ready-selection" in result.payload["findings"]


def test_implement_checkpoint_catches_failed_task_marked_blocked_stage(tmp_path: Path) -> None:
    workspace, tasklist = _write_workspace(tmp_path)
    import hashlib

    tasklist_hash = hashlib.sha256(tasklist.read_bytes()).hexdigest()
    metadata_path = (
        workspace
        / "reports"
        / "runs"
        / "WI-CHECKPOINT"
        / "run-1"
        / "stages"
        / "implement"
        / "stage-metadata.json"
    )
    metadata_path.write_text(
        json.dumps({"status": "blocked"}),
        encoding="utf-8",
    )
    stage_documents_root = (
        workspace
        / "workitems"
        / "WI-CHECKPOINT"
        / "stages"
        / "implement"
    )
    stage_documents_root.mkdir(parents=True, exist_ok=True)
    validator_report_path = stage_documents_root / "validator-report.md"
    validator_report_path.write_text(
        "# Validator Report\n\n## Result\n\n- Verdict: `fail`\n",
        encoding="utf-8",
    )
    stage_result_path = stage_documents_root / "stage-result.md"
    stage_result_path.write_text(
        "# Stage result\n\n## Status\n\n- Status: `blocked`\n",
        encoding="utf-8",
    )
    model = _model(tasklist_hash=tasklist_hash)
    model_tasks = model["tasks"]
    assert isinstance(model_tasks, list)
    model_tasks[0]["status"] = "failed"
    model_tasks[0]["ready"] = True
    model["next_ready_task"] = "TL-1"
    result = build_task_flow_checkpoint(
        scenario_id="AIDD-DETERMINISTIC-004",
        work_item="WI-CHECKPOINT",
        run_id="run-1",
        runtime_id="generic-cli",
        aidd_revision="aidd-rev",
        target_revision="target-rev",
        stage="implement",
        workspace_root=workspace,
        output_root=tmp_path / "bundle",
        task_view=model,
    )

    assert result.classification == "fail"
    assert (
        "implementation-status-drift:failed-task-stage-blocked:TL-1"
        in result.payload["findings"]
    )
    assert "implementation-status-drift:validator-fail-stage-blocked" in result.payload["findings"]
    assert result.payload["stage_lifecycle"] == {
        "path": metadata_path.as_posix(),
        "status": "blocked",
        "validator_report_path": validator_report_path.as_posix(),
        "validator_verdict": "fail",
        "stage_result_path": stage_result_path.as_posix(),
        "stage_result_status": "blocked",
        "failed_task_ids": ["TL-1"],
    }


def test_checkpoint_passes_after_aggregate_finalization_with_retained_task_evidence(
    tmp_path: Path,
) -> None:
    workspace, tasklist = _write_workspace(tmp_path, finalization="succeeded")
    import hashlib

    tasklist_hash = hashlib.sha256(tasklist.read_bytes()).hexdigest()
    ledger_path = (
        workspace
        / "reports"
        / "runs"
        / "WI-CHECKPOINT"
        / "run-1"
        / "stages"
        / "implement"
        / "task-ledger.json"
    )
    ledger_path.write_text(
        ledger_path.read_text(encoding="utf-8").replace("placeholder", tasklist_hash),
        encoding="utf-8",
    )
    for task_id in ("TL-1", "TL-2"):
        evidence = (
            workspace
            / "reports"
            / "runs"
            / "WI-CHECKPOINT"
            / "run-1"
            / "stages"
            / "implement"
            / "tasks"
            / task_id
            / "attempts"
            / "attempt-0001"
            / "implementation-report.md"
        )
        evidence.parent.mkdir(parents=True)
        evidence.write_text(f"# {task_id}\n", encoding="utf-8")

    result = build_task_flow_checkpoint(
        scenario_id="AIDD-DETERMINISTIC-004",
        work_item="WI-CHECKPOINT",
        run_id="run-1",
        runtime_id="generic-cli",
        aidd_revision="aidd-rev",
        target_revision="target-rev",
        stage="implement",
        workspace_root=workspace,
        output_root=tmp_path / "bundle",
        task_view=_model(tasklist_hash=tasklist_hash, finalization="succeeded"),
    )

    assert result.classification == "pass"
    assert result.payload["finalization"]["evidence"].endswith("finalization-state.json")  # type: ignore[union-attr]
