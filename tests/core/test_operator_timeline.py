from __future__ import annotations

import json
from pathlib import Path

from aidd.core.operator_timeline import (
    resolve_operator_run_history,
    resolve_operator_run_timeline,
)
from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_root,
    run_attempt_runtime_log_path,
    run_stage_root,
)


def test_operator_run_timeline_uses_existing_metadata_and_artifacts(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="generic-cli",
        stage_target="implement",
        config_snapshot={"mode": "timeline-test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="implement",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="implement",
        status="executing",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="implement",
        status="succeeded",
    )
    run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="implement",
        attempt_number=1,
    ).write_text("runtime output\n", encoding="utf-8")
    run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="implement",
        attempt_number=1,
    ).joinpath(RUN_EVENTS_JSONL_FILENAME).write_text(
        '{"timestamp":"2026-06-02T00:00:00Z","event":"validator.started","status":"running"}\n',
        encoding="utf-8",
    )
    questions_path = (
        workspace_root
        / "workitems"
        / "WI-UI"
        / "stages"
        / "implement"
        / "questions.md"
    )
    questions_path.parent.mkdir(parents=True, exist_ok=True)
    questions_path.write_text("# Questions\n\n- `Q1` Need detail.\n", encoding="utf-8")

    view = resolve_operator_run_timeline(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="implement",
    )

    kinds = [event.kind for event in view.events]
    assert "stage-status" in kinds
    assert "attempt" in kinds
    assert "runtime-log" in kinds
    assert "runtime-event" in kinds
    assert "questions" in kinds
    assert any(event.message == "validator.started" for event in view.events)
    stage_frames = [frame for frame in view.frames if frame.kind == "stage-attempt"]
    assert [frame.identity for frame in stage_frames] == [
        "stage:implement:attempt:0001"
    ]
    assert "reports/runs/WI-UI/run-ui/stages/implement/attempts/attempt-0001/runtime.log" in (
        stage_frames[0].evidence_refs
    )
    assert any(frame.kind == "event-marker" for frame in view.frames)
    assert not view.warnings


def test_operator_timeline_projects_task_and_finalization_frames(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="generic-cli",
        stage_target="implement",
        config_snapshot={"mode": "timeline-test"},
    )
    implement_root = run_stage_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="implement",
    )
    task_attempt = implement_root / "tasks" / "TL-2" / "attempts" / "attempt-0002"
    task_attempt.mkdir(parents=True)
    task_attempt.joinpath("attempt-state.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "attempt_number": 2,
                "status": "failed",
                "updated_at_utc": "2026-06-03T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    task_attempt.joinpath("task-diff.json").write_text("{}\n", encoding="utf-8")
    finalization = implement_root / "finalization" / "attempts" / "attempt-0001"
    finalization.mkdir(parents=True)
    finalization.joinpath("finalization-state.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "attempt_number": 1,
                "status": "failed",
                "updated_at_utc": "2026-06-03T00:01:00Z",
            }
        ),
        encoding="utf-8",
    )

    view = resolve_operator_run_timeline(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
    )

    task_frame = next(frame for frame in view.frames if frame.kind == "task-attempt")
    finalization_frame = next(
        frame for frame in view.frames if frame.kind == "finalization-attempt"
    )
    assert task_frame.identity == "task:TL-2:attempt:0002"
    assert task_frame.task_id == "TL-2"
    assert task_frame.status == "failed"
    assert task_frame.evidence_refs == (
        "reports/runs/WI-UI/run-ui/stages/implement/tasks/TL-2/attempts/attempt-0002/attempt-state.json",
        "reports/runs/WI-UI/run-ui/stages/implement/tasks/TL-2/attempts/attempt-0002/task-diff.json",
    )
    assert finalization_frame.identity == "finalization:implement:attempt:0001"
    assert finalization_frame.status == "failed"


def test_operator_timeline_retains_attempt_metadata_and_hashes(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
        run_id="run-history",
        runtime_id="generic-cli",
        stage_target="implement",
        config_snapshot={"mode": "history-test"},
    )
    attempt_root = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
        run_id="run-history",
        stage="implement",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
        run_id="run-history",
        stage="implement",
        status="succeeded",
    )
    attempt_root.joinpath("attempt-state.json").write_text(
        json.dumps(
            {
                "status": "succeeded",
                "started_at_utc": "2026-06-04T00:00:00Z",
                "updated_at_utc": "2026-06-04T00:00:12Z",
                "validator_outcome": "passed",
                "copy_id": "copy-001",
            }
        ),
        encoding="utf-8",
    )
    attempt_root.joinpath("runtime-exit.json").write_text(
        json.dumps({"exit_classification": "success"}), encoding="utf-8"
    )
    attempt_root.joinpath("input-bundle.md").write_text("input\n", encoding="utf-8")
    output_path = workspace_root / "workitems" / "WI-HISTORY" / "stages" / "implement" / "output.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("output\n", encoding="utf-8")
    attempt_root.joinpath("artifact-index.json").write_text(
        json.dumps(
            {
                "attempt_mode": "initial",
                "documents": {"output": "workitems/WI-HISTORY/stages/implement/output.md"},
                "logs": {},
            }
        ),
        encoding="utf-8",
    )

    view = resolve_operator_run_timeline(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
        run_id="run-history",
        stage="implement",
    )

    frame = next(frame for frame in view.frames if frame.kind == "stage-attempt")
    assert frame.attempt_mode == "initial"
    assert frame.runtime_id == "generic-cli"
    assert frame.started_at_utc == "2026-06-04T00:00:00Z"
    assert frame.duration_seconds == 12.0
    assert frame.validator_outcome == "passed"
    assert frame.input_hash
    assert frame.output_hash
    assert frame.copy_id == "copy-001"
    assert frame.retained is True
    assert frame.first_decisive_failure is None
    assert frame.primary_artifact == "workitems/WI-HISTORY/stages/implement/output.md"


def test_operator_run_history_lists_filters_and_selection(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    for run_id, status in (("run-old", "failed"), ("run-new", "succeeded")):
        create_run_manifest(
            workspace_root=workspace_root,
            work_item="WI-HISTORY",
            run_id=run_id,
            runtime_id="generic-cli",
            stage_target="implement",
            config_snapshot={"mode": "history-test"},
        )
        create_next_attempt_directory(
            workspace_root=workspace_root,
            work_item="WI-HISTORY",
            run_id=run_id,
            stage="implement",
        )
        persist_stage_status(
            workspace_root=workspace_root,
            work_item="WI-HISTORY",
            run_id=run_id,
            stage="implement",
            status=status,
        )

    history = resolve_operator_run_history(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
        run_id="run-old",
    )
    assert [entry.run_id for entry in history.runs] == ["run-new", "run-old"]
    assert history.selected_run_id == "run-old"
    assert history.runs[0].status == "completed"
    assert history.runs[1].status == "failed"
    assert history.runs[0].retained_attempt_count == 1

    failed = resolve_operator_run_history(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
        status="failed",
    )
    assert [entry.run_id for entry in failed.runs] == ["run-old"]
