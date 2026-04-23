from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
)

runner = CliRunner()


def test_run_show_prints_run_and_stage_metadata(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-123",
        run_id="run-123",
        runtime_id="claude-code",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-123",
        run_id="run-123",
        stage="plan",
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-123",
        run_id="run-123",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-123",
        run_id="run-123",
        stage="plan",
        status="executing",
    )

    result = runner.invoke(
        app,
        [
            "run",
            "show",
            "--work-item",
            "WI-123",
            "--root",
            str(workspace_root),
            "--run-id",
            "run-123",
        ],
    )

    assert result.exit_code == 0
    assert "Run metadata: run-123 / WI-123" in result.stdout
    assert "runtime" in result.stdout
    assert "claude-code" in result.stdout
    assert "stage target" in result.stdout
    assert "plan" in result.stdout
    assert "Run stages: run-123" in result.stdout
    assert "executing" in result.stdout
    assert "2" in result.stdout


def test_run_show_rejects_missing_runs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    result = runner.invoke(
        app,
        [
            "run",
            "show",
            "--work-item",
            "WI-404",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code != 0
    assert "No runs found for work item 'WI-404'." in result.output


def test_run_show_rejects_ambiguous_latest_run_selection(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    timestamp = datetime.now(UTC).replace(microsecond=0)

    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-AMB",
        run_id="run-001",
        runtime_id="claude-code",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-AMB",
        run_id="run-002",
        runtime_id="claude-code",
        stage_target="plan",
        config_snapshot={"mode": "test"},
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
            "show",
            "--work-item",
            "WI-AMB",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code != 0
    assert "Ambiguous latest run for work item 'WI-AMB'" in result.output
    assert "run-001" in result.output
    assert "run-002" in result.output


def test_run_without_args_exits_non_zero() -> None:
    result = runner.invoke(app, ["run"])
    assert result.exit_code != 0
    assert (
        "Missing option '--work-item'." in result.output
        or "Usage: root run [OPTIONS] COMMAND [ARGS]..." in result.output
    )
