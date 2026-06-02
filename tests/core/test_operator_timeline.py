from __future__ import annotations

from pathlib import Path

from aidd.core.operator_timeline import resolve_operator_run_timeline
from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_root,
    run_attempt_runtime_log_path,
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
    assert not view.warnings
