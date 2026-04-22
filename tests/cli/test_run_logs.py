from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_runtime_log_path,
)

runner = CliRunner()


def _prepare_run_with_log(*, workspace_root: Path) -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-321",
        run_id="run-321",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-321",
        run_id="run-321",
        stage="plan",
    )
    runtime_log_path = run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-321",
        run_id="run-321",
        stage="plan",
        attempt_number=1,
    )
    runtime_log_path.write_text("line-1\nline-2\nline-3\n", encoding="utf-8")


def test_run_logs_prints_full_runtime_log(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run_with_log(workspace_root=workspace_root)

    result = runner.invoke(
        app,
        [
            "run",
            "logs",
            "--work-item",
            "WI-321",
            "--stage",
            "plan",
            "--root",
            str(workspace_root),
            "--run-id",
            "run-321",
            "--attempt",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert "Run log: run_id=run-321 stage=plan attempt=1" in result.stdout
    assert "line-1" in result.stdout
    assert "line-2" in result.stdout
    assert "line-3" in result.stdout


def test_run_logs_supports_tail_mode(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run_with_log(workspace_root=workspace_root)

    result = runner.invoke(
        app,
        [
            "run",
            "logs",
            "--work-item",
            "WI-321",
            "--stage",
            "plan",
            "--root",
            str(workspace_root),
            "--run-id",
            "run-321",
            "--attempt",
            "1",
            "--tail",
            "--lines",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "line-1" not in result.stdout
    assert "line-2" in result.stdout
    assert "line-3" in result.stdout


def test_run_logs_rejects_missing_runs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    result = runner.invoke(
        app,
        [
            "run",
            "logs",
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


def test_run_logs_rejects_ambiguous_latest_run_selection(tmp_path: Path) -> None:
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
            "logs",
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
