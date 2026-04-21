from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidd.core.models.run import StageRunMetadata
from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_RUNS_DIRNAME

RUN_STAGES_DIRNAME = "stages"
RUN_ATTEMPTS_DIRNAME = "attempts"
RUN_ATTEMPT_PREFIX = "attempt-"
RUN_MANIFEST_FILENAME = "run-manifest.json"
RUN_STAGE_METADATA_FILENAME = "stage-metadata.json"


def _format_utc_timestamp(timestamp: datetime | None = None) -> str:
    moment = (timestamp or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    return moment.isoformat().replace("+00:00", "Z")


def run_store_root(workspace_root: Path) -> Path:
    return workspace_root / WORKSPACE_REPORTS_DIRNAME / WORKSPACE_REPORTS_RUNS_DIRNAME


def work_item_runs_root(workspace_root: Path, work_item: str) -> Path:
    return run_store_root(workspace_root=workspace_root) / work_item


def run_root(workspace_root: Path, work_item: str, run_id: str) -> Path:
    return work_item_runs_root(workspace_root=workspace_root, work_item=work_item) / run_id


def run_stages_root(workspace_root: Path, work_item: str, run_id: str) -> Path:
    return (
        run_root(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
        / RUN_STAGES_DIRNAME
    )


def run_stage_root(workspace_root: Path, work_item: str, run_id: str, stage: str) -> Path:
    return run_stages_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    ) / stage


def format_attempt_directory_name(attempt_number: int) -> str:
    if attempt_number < 1:
        raise ValueError("Attempt number must be >= 1.")
    return f"{RUN_ATTEMPT_PREFIX}{attempt_number:04d}"


def run_attempts_root(workspace_root: Path, work_item: str, run_id: str, stage: str) -> Path:
    return (
        run_stage_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        / RUN_ATTEMPTS_DIRNAME
    )


def run_attempt_root(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> Path:
    attempt_dir = format_attempt_directory_name(attempt_number)
    return (
        run_attempts_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        / attempt_dir
    )


def _parse_attempt_directory_name(name: str) -> int | None:
    if not name.startswith(RUN_ATTEMPT_PREFIX):
        return None

    suffix = name.removeprefix(RUN_ATTEMPT_PREFIX)
    if not suffix.isdigit():
        return None
    return int(suffix)


def next_attempt_number(workspace_root: Path, work_item: str, run_id: str, stage: str) -> int:
    attempts_root = run_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if not attempts_root.exists():
        return 1

    existing_numbers = [
        number
        for child in attempts_root.iterdir()
        if child.is_dir() and (number := _parse_attempt_directory_name(child.name)) is not None
    ]
    return max(existing_numbers, default=0) + 1


def create_next_attempt_directory(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> Path:
    attempts_root = run_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    attempts_root.mkdir(parents=True, exist_ok=True)

    attempt_number = next_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    attempt_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    attempt_path.mkdir(parents=False, exist_ok=False)
    return attempt_path


def run_manifest_path(workspace_root: Path, work_item: str, run_id: str) -> Path:
    return run_root(workspace_root=workspace_root, work_item=work_item, run_id=run_id) / (
        RUN_MANIFEST_FILENAME
    )


def run_stage_metadata_path(workspace_root: Path, work_item: str, run_id: str, stage: str) -> Path:
    return run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    ) / RUN_STAGE_METADATA_FILENAME


def load_stage_metadata(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> StageRunMetadata | None:
    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if not metadata_path.exists():
        return None
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return StageRunMetadata.from_dict(payload)


def _write_json_payload(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _touch_manifest_timestamp(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    updated_at_utc: str,
) -> None:
    manifest_path = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not manifest_path.exists():
        return

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["updated_at_utc"] = updated_at_utc
    _write_json_payload(manifest_path, payload)


def persist_stage_status(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    status: str,
    *,
    changed_at_utc: datetime | None = None,
) -> Path:
    if not status.strip():
        raise ValueError("Status must be a non-empty string.")

    timestamp = _format_utc_timestamp(changed_at_utc)
    stage_root = run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    stage_root.mkdir(parents=True, exist_ok=True)
    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )

    existing = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if existing is None:
        metadata = StageRunMetadata.create(
            run_id=run_id,
            work_item_id=work_item,
            stage=stage,
            status=status,
            changed_at_utc=timestamp,
        )
    else:
        metadata = existing.with_status(status=status, changed_at_utc=timestamp)

    _write_json_payload(metadata_path, metadata.to_dict())
    _touch_manifest_timestamp(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        updated_at_utc=timestamp,
    )
    return metadata_path


def create_run_manifest(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    runtime_id: str,
    stage_target: str,
    config_snapshot: dict[str, Any],
) -> Path:
    manifest_path = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if manifest_path.exists():
        return manifest_path

    run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage_target,
    ).mkdir(parents=True, exist_ok=True)

    now = _format_utc_timestamp()
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "work_item_id": work_item,
        "runtime_id": runtime_id,
        "stage_target": stage_target,
        "config_snapshot": config_snapshot,
        "created_at_utc": now,
        "updated_at_utc": now,
    }
    _write_json_payload(manifest_path, payload)
    return manifest_path


@dataclass(frozen=True)
class RunStore:
    workspace_root: Path
    work_item: str
    run_id: str

    @property
    def root(self) -> Path:
        return run_root(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
        )

    def manifest_path(self) -> Path:
        return run_manifest_path(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
        )

    def create_manifest(
        self,
        runtime_id: str,
        stage_target: str,
        config_snapshot: dict[str, Any],
    ) -> Path:
        return create_run_manifest(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            runtime_id=runtime_id,
            stage_target=stage_target,
            config_snapshot=config_snapshot,
        )

    def create_next_attempt(self, stage: str) -> Path:
        return create_next_attempt_directory(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            stage=stage,
        )

    def stage_metadata_path(self, stage: str) -> Path:
        return run_stage_metadata_path(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            stage=stage,
        )

    def persist_stage_status(
        self,
        stage: str,
        status: str,
        *,
        changed_at_utc: datetime | None = None,
    ) -> Path:
        return persist_stage_status(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            stage=stage,
            status=status,
            changed_at_utc=changed_at_utc,
        )
