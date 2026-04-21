from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from aidd.cli.run_lookup import resolve_cli_run_target
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_attempt_root,
)


def test_resolve_cli_run_target_uses_latest_run_and_attempt(tmp_path: Path) -> None:
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
        status="running",
        changed_at_utc=now + timedelta(minutes=5),
    )

    resolved = resolve_cli_run_target(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    assert resolved.run_id == "run-002"
    assert resolved.attempt_number == 2
    assert resolved.attempt_path == run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
        attempt_number=2,
    )
    assert resolved.documents["stage_brief"].as_posix().endswith(
        "/workitems/WI-001/stages/plan/stage-brief.md"
    )


def test_resolve_cli_run_target_supports_explicit_run_and_attempt(tmp_path: Path) -> None:
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

    resolved = resolve_cli_run_target(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        run_id="run-001",
        attempt_number=1,
    )
    assert resolved.run_id == "run-001"
    assert resolved.attempt_number == 1


def test_resolve_cli_run_target_rejects_closed_runs(tmp_path: Path) -> None:
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
        status="passed",
        changed_at_utc=now + timedelta(minutes=5),
    )

    with pytest.raises(ValueError, match="terminal status"):
        resolve_cli_run_target(
            workspace_root=workspace_root,
            work_item="WI-001",
            stage="plan",
            run_id="run-001",
        )


def test_resolve_cli_run_target_rejects_missing_artifact_index(tmp_path: Path) -> None:
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
        resolve_cli_run_target(
            workspace_root=workspace_root,
            work_item="WI-001",
            stage="plan",
            run_id="run-001",
            attempt_number=1,
        )
