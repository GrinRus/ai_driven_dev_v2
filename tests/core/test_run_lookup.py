from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from aidd.core.run_inspection import resolve_run_artifacts_summary
from aidd.core.run_lookup import (
    AmbiguousLatestRunError,
    latest_attempt_number,
    latest_attempt_path,
    latest_run_id,
    latest_run_path,
    resolve_attempt_artifact_paths,
)
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    load_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
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
        status="executing",
        changed_at_utc=now + timedelta(minutes=1),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        stage="plan",
        status="executing",
        changed_at_utc=now + timedelta(minutes=2),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
        stage="plan",
        status="succeeded",
        changed_at_utc=now + timedelta(minutes=3),
    )

    assert latest_run_id(workspace_root=workspace_root, work_item=work_item) == "run-001"
    assert latest_run_path(workspace_root=workspace_root, work_item=work_item) == run_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
    )


def test_latest_run_resolver_preserves_sub_second_identity(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SUBSECOND"
    same_second = datetime(2026, 7, 16, 10, 30, 0, tzinfo=UTC)

    for run_id in ("run-001", "run-002"):
        create_run_manifest(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            runtime_id="generic-cli",
            stage_target="plan",
            config_snapshot={"mode": "test"},
        )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-001",
        stage="plan",
        status="executing",
        changed_at_utc=same_second.replace(microsecond=100_000),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-002",
        stage="plan",
        status="executing",
        changed_at_utc=same_second.replace(microsecond=900_000),
    )

    first_payload = json.loads(
        run_manifest_path(workspace_root, work_item, "run-001").read_text(encoding="utf-8")
    )
    second_payload = json.loads(
        run_manifest_path(workspace_root, work_item, "run-002").read_text(encoding="utf-8")
    )
    assert first_payload["updated_at_utc"] == "2026-07-16T10:30:00.100000Z"
    assert second_payload["updated_at_utc"] == "2026-07-16T10:30:00.900000Z"
    assert latest_run_id(workspace_root=workspace_root, work_item=work_item) == "run-002"


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


def test_latest_run_and_attempt_selection_use_latest_timestamp(tmp_path: Path) -> None:
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
        status="executing",
        changed_at_utc=now + timedelta(minutes=5),
    )

    selected_run = latest_run_id(workspace_root, work_item)
    assert selected_run == "run-002"
    assert latest_attempt_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run,
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

    assert run_attempt_artifact_index_path(
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
    assert "input_bundle" not in resolved.documents
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
    index_path = run_attempt_artifact_index_path(
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


def test_resolve_run_artifacts_summary_uses_latest_run_and_attempt(
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
        status="executing",
        changed_at_utc=now + timedelta(minutes=10),
    )

    resolved = resolve_run_artifacts_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    assert resolved is not None
    assert resolved.run_id == "run-002"
    assert resolved.attempt_number == 2
    assert resolved.logs["runtime_log"].endswith(
        "/run-002/stages/plan/attempts/attempt-0002/runtime.log"
    )


def test_manifest_reader_preserves_absence_and_rejects_corrupt_json(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    assert load_run_manifest(workspace_root, "WI-001", "run-001") is None
    broken_manifest = run_manifest_path(workspace_root, "WI-001", "run-002")
    broken_manifest.parent.mkdir(parents=True)
    broken_manifest.write_text("{not-json", encoding="utf-8")
    before = broken_manifest.read_bytes()
    with pytest.raises(ValueError, match="not valid JSON"):
        load_run_manifest(workspace_root, "WI-001", "run-002")
    assert latest_run_id(workspace_root, "WI-001") is None
    assert broken_manifest.read_bytes() == before


def test_latest_run_id_uses_current_metadata_timestamp(tmp_path: Path) -> None:
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
        status="executing",
        changed_at_utc=now + timedelta(minutes=10),
    )

    assert (
        latest_run_id(workspace_root=workspace_root, work_item="WI-001")
        == "run-002"
    )


def test_latest_run_id_rejects_ambiguous_timestamps(tmp_path: Path) -> None:
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
        status="executing",
        changed_at_utc=now + timedelta(minutes=10),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-002",
        stage="plan",
        status="executing",
        changed_at_utc=now + timedelta(minutes=10),
    )

    with pytest.raises(AmbiguousLatestRunError, match="Ambiguous latest run"):
        latest_run_id(workspace_root=workspace_root, work_item="WI-001")
