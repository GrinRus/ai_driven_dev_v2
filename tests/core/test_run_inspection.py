from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from aidd.core.run_inspection import resolve_run_artifacts_summary
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_attempt_root,
)


def test_resolve_run_artifacts_summary_uses_latest_run_and_attempt(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    now = datetime.now(UTC).replace(microsecond=0)

    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
        status="executing",
        changed_at_utc=now + timedelta(minutes=5),
    )

    resolved = resolve_run_artifacts_summary(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    assert resolved.run_id == "run-002"
    assert resolved.attempt_number == 2
    assert (
        resolved.logs["runtime_log"]
        == (run_attempt_root(workspace_root, "WI-001", "run-002", "plan", 2) / "runtime.log")
        .relative_to(workspace_root)
        .as_posix()
    )
    assert resolved.documents["stage_brief"] == "workitems/WI-001/stages/plan/stage-brief.md"


def test_resolve_run_artifacts_summary_supports_explicit_run_and_attempt(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    resolved = resolve_run_artifacts_summary(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        run_id="run-001",
        attempt_number=1,
    )
    assert resolved.run_id == "run-001"
    assert resolved.attempt_number == 1


def test_resolve_run_artifacts_summary_keeps_terminal_runs_readable(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    now = datetime.now(UTC).replace(microsecond=0)

    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status="succeeded",
        changed_at_utc=now + timedelta(minutes=5),
    )

    resolved = resolve_run_artifacts_summary(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        run_id="run-001",
    )
    assert resolved.run_id == "run-001"
    assert resolved.attempt_number == 1
    assert "runtime_log" in resolved.logs


def test_resolve_run_artifacts_summary_rejects_missing_artifact_index(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    ).unlink()

    with pytest.raises(ValueError, match="Artifact index is missing"):
        resolve_run_artifacts_summary(
            workspace_root=workspace_root,
            work_item="WI-001",
            stage="plan",
            run_id="run-001",
            attempt_number=1,
        )


def test_resolve_run_artifacts_summary_rejects_ambiguous_latest_run(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    now = datetime.now(UTC).replace(microsecond=0)

    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status="executing",
        changed_at_utc=now + timedelta(minutes=5),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
        status="executing",
        changed_at_utc=now + timedelta(minutes=5),
    )

    with pytest.raises(ValueError, match="Ambiguous latest run"):
        resolve_run_artifacts_summary(
            workspace_root=workspace_root,
            work_item="WI-001",
            stage="plan",
        )
