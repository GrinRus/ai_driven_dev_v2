from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from aidd.core.run_lookup import (
    latest_attempt_number,
    latest_attempt_path,
    latest_attempt_path_for_work_item,
    latest_run_id,
    latest_run_path,
)
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_root,
    run_root,
)


def test_latest_run_path_returns_none_when_work_item_has_no_runs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    assert latest_run_path(workspace_root=workspace_root, work_item="WI-001") is None
    assert latest_run_id(workspace_root=workspace_root, work_item="WI-001") is None


def test_latest_run_path_uses_manifest_updated_timestamp(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-001"
    now = datetime.now(UTC).replace(microsecond=0)

    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
        stage="plan",
        status="running",
        changed_at_utc=now + timedelta(minutes=1),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        stage="plan",
        status="running",
        changed_at_utc=now + timedelta(minutes=2),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
        stage="plan",
        status="passed",
        changed_at_utc=now + timedelta(minutes=3),
    )

    assert latest_run_id(workspace_root=workspace_root, work_item=work_item) == "run-001"
    assert latest_run_path(workspace_root=workspace_root, work_item=work_item) == run_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
    )


def test_latest_attempt_number_resolves_highest_attempt(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-001"
    run_id = "run-001"
    stage = "plan"

    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )

    assert latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    ) == 2
    assert latest_attempt_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    ) == run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=2,
    )


def test_latest_attempt_path_for_work_item_uses_latest_run(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-001"
    stage = "plan"
    now = datetime.now(UTC).replace(microsecond=0)

    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target=stage,
        config_snapshot={"mode": "test"},
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        runtime_id="generic-cli",
        stage_target=stage,
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
        stage=stage,
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        stage=stage,
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        stage=stage,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        stage=stage,
        status="running",
        changed_at_utc=now + timedelta(minutes=5),
    )

    assert latest_attempt_path_for_work_item(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    ) == run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        stage=stage,
        attempt_number=2,
    )
