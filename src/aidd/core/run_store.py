from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_RUNS_DIRNAME

RUN_STAGES_DIRNAME = "stages"
RUN_ATTEMPTS_DIRNAME = "attempts"
RUN_ATTEMPT_PREFIX = "attempt-"
RUN_MANIFEST_FILENAME = "run-manifest.json"


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


def run_manifest_path(workspace_root: Path, work_item: str, run_id: str) -> Path:
    return run_root(workspace_root=workspace_root, work_item=work_item, run_id=run_id) / (
        RUN_MANIFEST_FILENAME
    )


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

    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
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
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
