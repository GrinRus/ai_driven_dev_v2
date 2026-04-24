from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aidd.core.run_store import (
    RUN_ARTIFACT_INDEX_FILENAME,
    RUN_ATTEMPTS_DIRNAME,
    RUN_MANIFEST_FILENAME,
    RUN_RUNTIME_EXIT_METADATA_FILENAME,
    RUN_RUNTIME_LOG_FILENAME,
    RUN_STAGE_METADATA_FILENAME,
    RUN_STAGES_DIRNAME,
    RunStore,
    create_next_attempt_directory,
    create_run_manifest,
    format_attempt_directory_name,
    load_attempt_artifact_index,
    next_attempt_number,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_attempt_root,
    run_attempt_runtime_log_path,
    run_manifest_path,
    run_root,
    run_stage_metadata_path,
    run_stage_root,
    run_stages_root,
    run_store_root,
    work_item_runs_root,
    write_attempt_artifact_index,
)
from aidd.core.workspace import (
    RESERVED_STAGE_FILENAMES,
    WORKSPACE_REPORTS_DIRNAME,
    WORKSPACE_REPORTS_RUNS_DIRNAME,
)


def test_run_store_root_uses_reports_runs_layout(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    assert run_store_root(workspace_root) == (
        workspace_root / WORKSPACE_REPORTS_DIRNAME / WORKSPACE_REPORTS_RUNS_DIRNAME
    )


def test_run_directory_layout_includes_stage_and_attempt_subdirectories(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-001"
    run_id = "run-001"
    stage = "plan"

    expected_work_item_root = run_store_root(workspace_root) / work_item
    expected_run_root = expected_work_item_root / run_id
    expected_stages_root = expected_run_root / RUN_STAGES_DIRNAME
    expected_stage_root = expected_stages_root / stage

    assert work_item_runs_root(workspace_root, work_item) == expected_work_item_root
    assert run_root(workspace_root, work_item, run_id) == expected_run_root
    assert run_stages_root(workspace_root, work_item, run_id) == expected_stages_root
    assert run_stage_root(workspace_root, work_item, run_id, stage) == expected_stage_root
    assert run_attempt_root(workspace_root, work_item, run_id, stage, 3) == (
        expected_stage_root / RUN_ATTEMPTS_DIRNAME / "attempt-0003"
    )


def test_format_attempt_directory_name_rejects_non_positive_numbers() -> None:
    with pytest.raises(ValueError, match=">= 1"):
        format_attempt_directory_name(0)


def test_run_store_dataclass_root_matches_helper(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    store = RunStore(workspace_root=workspace_root, work_item="WI-001", run_id="run-001")

    assert store.root == run_root(workspace_root, "WI-001", "run-001")


def test_create_run_manifest_writes_runtime_stage_and_config_snapshot(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest_path = create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"log_mode": "both"},
        workflow_stage_start="idea",
        workflow_stage_end="plan",
    )

    assert manifest_path.name == RUN_MANIFEST_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-001"
    assert payload["work_item_id"] == "WI-001"
    assert payload["runtime_id"] == "generic-cli"
    assert payload["stage_target"] == "plan"
    assert payload["workflow_bounds"] == {"start": "idea", "end": "plan"}
    assert payload["config_snapshot"] == {"log_mode": "both"}
    assert "repository_git_sha" in payload
    git_sha = payload["repository_git_sha"]
    assert git_sha is None or (isinstance(git_sha, str) and len(git_sha) == 40)

    prompt_pack_provenance = payload["prompt_pack_provenance"]
    assert isinstance(prompt_pack_provenance, list)
    assert prompt_pack_provenance
    system_prompt = next(
        entry
        for entry in prompt_pack_provenance
        if entry["path"] == "prompt-packs/stages/plan/system.md"
    )
    expected_hash = hashlib.sha256(
        Path(system_prompt["path"]).read_bytes()
    ).hexdigest()
    assert system_prompt["sha256"] == expected_hash
    assert payload["schema_version"] == 1


def test_next_attempt_number_starts_from_one_when_attempts_missing(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    assert next_attempt_number(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    ) == 1


def test_create_next_attempt_directory_uses_monotonic_numbering(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_attempts_root = (
        run_stage_root(workspace_root, "WI-001", "run-001", "plan") / RUN_ATTEMPTS_DIRNAME
    )
    (stage_attempts_root / "attempt-0001").mkdir(parents=True)
    (stage_attempts_root / "attempt-0003").mkdir(parents=True)
    (stage_attempts_root / "misc-dir").mkdir(parents=True)

    created = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert created.name == "attempt-0004"
    artifact_index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=4,
    )
    assert artifact_index_path.exists()

    payload = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    assert payload["attempt_number"] == 4
    assert payload["logs"]["runtime_log"] == (
        run_attempt_runtime_log_path(workspace_root, "WI-001", "run-001", "plan", 4)
        .relative_to(workspace_root)
        .as_posix()
    )


def test_attempt_artifact_index_records_canonical_stage_document_paths(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    created = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert created.name == "attempt-0001"
    artifact_index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    )
    assert artifact_index_path.name == RUN_ARTIFACT_INDEX_FILENAME

    payload = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    expected_doc_keys = {
        name.removesuffix(".md").replace("-", "_")
        for name in RESERVED_STAGE_FILENAMES
    }
    assert set(payload["documents"]) == expected_doc_keys

    for filename in RESERVED_STAGE_FILENAMES:
        key = filename.removesuffix(".md").replace("-", "_")
        expected_path = (
            workspace_root / "workitems" / "WI-001" / "stages" / "plan" / filename
        ).relative_to(workspace_root)
        assert payload["documents"][key] == expected_path.as_posix()

    assert payload["logs"] == {
        "runtime_log": (
            workspace_root
            / "reports"
            / "runs"
            / "WI-001"
            / "run-001"
            / "stages"
            / "plan"
            / "attempts"
            / "attempt-0001"
            / RUN_RUNTIME_LOG_FILENAME
        )
        .relative_to(workspace_root)
        .as_posix()
    }
    prompt_pack_provenance = payload["prompt_pack_provenance"]
    assert isinstance(prompt_pack_provenance, list)
    assert prompt_pack_provenance
    system_prompt = next(
        entry
        for entry in prompt_pack_provenance
        if entry["path"] == "prompt-packs/stages/plan/system.md"
    )
    expected_hash = hashlib.sha256(Path(system_prompt["path"]).read_bytes()).hexdigest()
    assert system_prompt["sha256"] == expected_hash


def test_load_attempt_artifact_index_supports_legacy_payload_without_prompt_provenance(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    artifact_index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    )
    payload = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    payload.pop("prompt_pack_provenance", None)
    artifact_index_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    loaded = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    )

    assert loaded is not None
    assert loaded.prompt_pack_provenance == ()


def test_run_store_fresh_run_creates_manifest_attempt_and_stage_metadata(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    store = RunStore(workspace_root=workspace_root, work_item="WI-001", run_id="run-001")

    manifest_path = store.create_manifest(
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    attempt_path = store.create_next_attempt("plan")
    stage_metadata_path = store.persist_stage_status(
        stage="plan",
        status="running",
        changed_at_utc=datetime(2026, 4, 21, 11, 0, tzinfo=UTC),
    )

    assert manifest_path.exists()
    assert attempt_path.name == "attempt-0001"
    assert store.attempt_artifact_index_path("plan", 1).exists()
    stage_metadata = json.loads(stage_metadata_path.read_text(encoding="utf-8"))
    assert stage_metadata["status"] == "running"
    assert stage_metadata["updated_at_utc"] == "2026-04-21T11:00:00Z"


def test_run_store_repeated_attempts_keep_distinct_artifact_indexes(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    store = RunStore(workspace_root=workspace_root, work_item="WI-001", run_id="run-001")

    first_attempt = store.create_next_attempt("plan")
    second_attempt = store.create_next_attempt("plan")

    assert first_attempt.name == "attempt-0001"
    assert second_attempt.name == "attempt-0002"

    first_index = json.loads(
        store.attempt_artifact_index_path("plan", 1).read_text(encoding="utf-8")
    )
    second_index = json.loads(
        store.attempt_artifact_index_path("plan", 2).read_text(encoding="utf-8")
    )

    assert first_index["attempt_number"] == 1
    assert second_index["attempt_number"] == 2
    assert first_index["logs"]["runtime_log"].endswith("/attempt-0001/runtime.log")
    assert second_index["logs"]["runtime_log"].endswith("/attempt-0002/runtime.log")


def test_attempt_artifact_index_records_runtime_exit_metadata_when_present(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    attempt_path = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    (attempt_path / RUN_RUNTIME_LOG_FILENAME).write_text("runtime-log\n", encoding="utf-8")
    (attempt_path / RUN_RUNTIME_EXIT_METADATA_FILENAME).write_text("{}", encoding="utf-8")

    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    )
    payload = json.loads(
        run_attempt_artifact_index_path(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            attempt_number=1,
        ).read_text(encoding="utf-8")
    )

    assert payload["logs"]["runtime_log"].endswith("/attempt-0001/runtime.log")
    assert payload["logs"]["runtime_exit_metadata"].endswith(
        "/attempt-0001/runtime-exit.json"
    )


def test_stage_metadata_write_is_atomic_on_interrupted_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        changed_at_utc=datetime(2026, 4, 21, 12, 0, tzinfo=UTC),
    )
    metadata_path = run_stage_metadata_path(workspace_root, "WI-001", "run-001", "plan")
    original_payload = metadata_path.read_text(encoding="utf-8")
    original_replace = Path.replace

    def _failing_replace(path_obj: Path, target: Path) -> Path:
        if Path(target).name == RUN_STAGE_METADATA_FILENAME:
            raise OSError("simulated interrupted write")
        return original_replace(path_obj, target)

    monkeypatch.setattr(Path, "replace", _failing_replace)

    with pytest.raises(OSError, match="simulated interrupted write"):
        persist_stage_status(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            status="failed",
            changed_at_utc=datetime(2026, 4, 21, 12, 5, tzinfo=UTC),
        )

    assert metadata_path.read_text(encoding="utf-8") == original_payload
    assert (metadata_path.parent / f".{RUN_STAGE_METADATA_FILENAME}.tmp").exists() is False


def test_artifact_index_write_is_atomic_on_interrupted_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    store = RunStore(workspace_root=workspace_root, work_item="WI-001", run_id="run-001")
    store.create_next_attempt("plan")
    artifact_index_path = store.attempt_artifact_index_path("plan", 1)
    original_payload = artifact_index_path.read_text(encoding="utf-8")
    original_replace = Path.replace

    def _failing_replace(path_obj: Path, target: Path) -> Path:
        if Path(target).name == RUN_ARTIFACT_INDEX_FILENAME:
            raise OSError("simulated interrupted write")
        return original_replace(path_obj, target)

    monkeypatch.setattr(Path, "replace", _failing_replace)

    with pytest.raises(OSError, match="simulated interrupted write"):
        store.write_attempt_artifact_index(
            stage="plan",
            attempt_number=1,
            changed_at_utc=datetime(2026, 4, 21, 12, 10, tzinfo=UTC),
        )

    assert artifact_index_path.read_text(encoding="utf-8") == original_payload
    assert (artifact_index_path.parent / f".{RUN_ARTIFACT_INDEX_FILENAME}.tmp").exists() is False


def test_persist_stage_status_creates_stage_metadata_and_touches_manifest(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-001"
    run_id = "run-001"
    stage = "plan"
    changed_at = datetime(2026, 4, 21, 10, 0, tzinfo=UTC)

    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target=stage,
        config_snapshot={"mode": "test"},
    )
    metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status="running",
        changed_at_utc=changed_at,
    )

    assert metadata_path == run_stage_metadata_path(workspace_root, work_item, run_id, stage)
    assert metadata_path.name == RUN_STAGE_METADATA_FILENAME

    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata_payload["run_id"] == run_id
    assert metadata_payload["work_item_id"] == work_item
    assert metadata_payload["stage"] == stage
    assert metadata_payload["status"] == "running"
    assert metadata_payload["created_at_utc"] == "2026-04-21T10:00:00Z"
    assert metadata_payload["updated_at_utc"] == "2026-04-21T10:00:00Z"
    assert metadata_payload["status_history"] == [
        {"status": "running", "changed_at_utc": "2026-04-21T10:00:00Z"}
    ]

    manifest_payload = json.loads(
        run_manifest_path(workspace_root, work_item, run_id).read_text(encoding="utf-8")
    )
    assert manifest_payload["updated_at_utc"] == "2026-04-21T10:00:00Z"


def test_persist_stage_status_is_history_aware_across_status_transitions(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-001"
    run_id = "run-001"
    stage = "plan"

    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target=stage,
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status="running",
        changed_at_utc=datetime(2026, 4, 21, 10, 0, tzinfo=UTC),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status="running",
        changed_at_utc=datetime(2026, 4, 21, 10, 5, tzinfo=UTC),
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status="passed",
        changed_at_utc=datetime(2026, 4, 21, 10, 8, tzinfo=UTC),
    )

    metadata_path = run_stage_metadata_path(workspace_root, work_item, run_id, stage)
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["created_at_utc"] == "2026-04-21T10:00:00Z"
    assert payload["updated_at_utc"] == "2026-04-21T10:08:00Z"
    assert payload["status_history"] == [
        {"status": "running", "changed_at_utc": "2026-04-21T10:00:00Z"},
        {"status": "passed", "changed_at_utc": "2026-04-21T10:08:00Z"},
    ]
