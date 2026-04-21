from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from aidd.core.run_lookup import (
    ClosedRunError,
    CorruptedRunError,
    attempt_artifact_index_path,
    guard_latest_run_resume,
    guard_run_resume,
    latest_attempt_number,
    latest_attempt_path,
    latest_attempt_path_for_work_item,
    latest_run_id,
    latest_run_path,
    resolve_attempt_artifact_paths,
    resolve_latest_attempt_artifact_paths,
)
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_root,
    run_manifest_path,
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


def test_attempt_artifact_index_path_matches_attempt_layout(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    ) == (
        workspace_root
        / "reports"
        / "runs"
        / "WI-001"
        / "run-001"
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
        / "artifact-index.json"
    )


def test_resolve_attempt_artifact_paths_returns_absolute_document_and_log_paths(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    resolved = resolve_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    )

    assert resolved is not None
    assert resolved.run_id == "run-001"
    assert resolved.stage == "plan"
    assert resolved.attempt_number == 1
    assert resolved.documents["stage_brief"] == (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "stage-brief.md"
    )
    assert resolved.logs["runtime_log"] == (
        workspace_root
        / "reports"
        / "runs"
        / "WI-001"
        / "run-001"
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
        / "runtime.log"
    )


def test_resolve_attempt_artifact_paths_returns_none_when_index_missing(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    index_path = attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    )
    index_path.unlink()

    assert (
        resolve_attempt_artifact_paths(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            attempt_number=1,
        )
        is None
    )


def test_resolve_latest_attempt_artifact_paths_uses_latest_run_and_attempt(
    tmp_path: Path,
) -> None:
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
        changed_at_utc=now + timedelta(minutes=10),
    )

    resolved = resolve_latest_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    assert resolved is not None
    assert resolved.run_id == "run-002"
    assert resolved.attempt_number == 2
    assert resolved.logs["runtime_log"].as_posix().endswith(
        "/run-002/stages/plan/attempts/attempt-0002/runtime.log"
    )


def test_guard_run_resume_allows_non_terminal_stage_status(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status="running",
        changed_at_utc=datetime.now(UTC).replace(microsecond=0) + timedelta(minutes=1),
    )

    guard_run_resume(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )


def test_guard_run_resume_rejects_terminal_stage_status(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status="passed",
        changed_at_utc=datetime.now(UTC).replace(microsecond=0) + timedelta(minutes=2),
    )

    with pytest.raises(ClosedRunError, match="terminal status"):
        guard_run_resume(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
        )


def test_guard_run_resume_rejects_missing_or_corrupted_manifest(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    with pytest.raises(CorruptedRunError, match="manifest is missing"):
        guard_run_resume(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
        )

    broken_manifest = run_manifest_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
    )
    broken_manifest.parent.mkdir(parents=True, exist_ok=True)
    broken_manifest.write_text("{not-json", encoding="utf-8")

    with pytest.raises(CorruptedRunError, match="not valid JSON"):
        guard_run_resume(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-002",
            stage="plan",
        )


def test_guard_latest_run_resume_returns_latest_run_id(tmp_path: Path) -> None:
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
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
        status="running",
        changed_at_utc=now + timedelta(minutes=10),
    )

    assert (
        guard_latest_run_resume(
            workspace_root=workspace_root,
            work_item="WI-001",
            stage="plan",
        )
        == "run-002"
    )


def test_guard_latest_run_resume_rejects_ambiguous_latest_runs(tmp_path: Path) -> None:
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
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status="running",
        changed_at_utc=now + timedelta(minutes=10),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
        status="running",
        changed_at_utc=now + timedelta(minutes=10),
    )

    with pytest.raises(CorruptedRunError, match="Ambiguous latest run"):
        guard_latest_run_resume(
            workspace_root=workspace_root,
            work_item="WI-001",
            stage="plan",
        )
