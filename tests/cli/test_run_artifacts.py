from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.core.run_store import (
    RUN_RUNTIME_EXIT_METADATA_FILENAME,
    RUN_RUNTIME_LOG_FILENAME,
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    write_attempt_artifact_index,
)

runner = CliRunner()


def test_run_artifacts_lists_document_and_log_paths(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-777",
        run_id="run-777",
        runtime_id="claude-code",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-777",
        run_id="run-777",
        stage="plan",
    )

    result = runner.invoke(
        app,
        [
            "run",
            "artifacts",
            "--work-item",
            "WI-777",
            "--stage",
            "plan",
            "--root",
            str(workspace_root),
            "--run-id",
            "run-777",
            "--attempt",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert "Run artifacts: run_id=run-777 stage=plan attempt=1" in result.stdout
    assert "Document artifacts:" in result.stdout
    assert "Log artifacts:" in result.stdout
    assert "stage_result" in result.stdout
    assert "runtime_log" in result.stdout
    assert "workitems/WI-777/stages/plan/stage-result.md" in result.stdout
    assert (
        "reports/runs/WI-777/run-777/stages/plan/attempts/attempt-0001/runtime.log"
        in result.stdout
    )


def test_run_artifacts_rejects_missing_runs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    result = runner.invoke(
        app,
        [
            "run",
            "artifacts",
            "--work-item",
            "WI-404",
            "--stage",
            "plan",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code != 0
    assert "No runs found for work item 'WI-404'." in result.output


def test_run_artifacts_lists_runtime_exit_metadata_when_present(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-778",
        run_id="run-778",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    attempt_path = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-778",
        run_id="run-778",
        stage="plan",
    )
    (attempt_path / RUN_RUNTIME_LOG_FILENAME).write_text("runtime\n", encoding="utf-8")
    (attempt_path / RUN_RUNTIME_EXIT_METADATA_FILENAME).write_text("{}", encoding="utf-8")
    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item="WI-778",
        run_id="run-778",
        stage="plan",
        attempt_number=1,
    )

    result = runner.invoke(
        app,
        [
            "run",
            "artifacts",
            "--work-item",
            "WI-778",
            "--stage",
            "plan",
            "--root",
            str(workspace_root),
            "--run-id",
            "run-778",
            "--attempt",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert "runtime_exit_metadata" in result.stdout
    assert "reports/runs/WI-778/run-778/stages/plan/attempts/attempt-0001/runtime-exit.json" in (
        result.stdout
    )


def test_run_artifacts_rejects_ambiguous_latest_run_selection(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    timestamp = datetime.now(UTC).replace(microsecond=0)

    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-AMB",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-AMB",
        run_id="run-002",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-AMB",
        run_id="run-001",
        stage="plan",
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-AMB",
        run_id="run-002",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-AMB",
        run_id="run-001",
        stage="plan",
        status="running",
        changed_at_utc=timestamp,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-AMB",
        run_id="run-002",
        stage="plan",
        status="running",
        changed_at_utc=timestamp,
    )

    result = runner.invoke(
        app,
        [
            "run",
            "artifacts",
            "--work-item",
            "WI-AMB",
            "--stage",
            "plan",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code != 0
    assert "Ambiguous latest run for work item 'WI-AMB'" in result.output
    assert "run-001" in result.output
    assert "run-002" in result.output
