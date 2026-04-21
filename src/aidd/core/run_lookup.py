from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.run_store import (
    RUN_ATTEMPT_PREFIX,
    load_attempt_artifact_index,
    run_attempt_artifact_index_path,
    run_attempt_root,
    run_attempts_root,
    run_manifest_path,
    work_item_runs_root,
)

_MIN_TIMESTAMP = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class AttemptArtifactPaths:
    run_id: str
    stage: str
    attempt_number: int
    documents: dict[str, Path]
    logs: dict[str, Path]


def _parse_utc_timestamp(timestamp: str | None) -> datetime:
    if not timestamp:
        return _MIN_TIMESTAMP
    normalized = timestamp.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).astimezone(UTC)
    except ValueError:
        return _MIN_TIMESTAMP


def _resolve_workspace_relative_path(workspace_root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute():
        raise ValueError(f"Artifact path must be workspace-relative: {relative_path}")

    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = (workspace_root / relative).resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_workspace):
        raise ValueError(f"Artifact path escapes workspace root: {relative_path}")
    return resolved_path


def latest_run_path(workspace_root: Path, work_item: str) -> Path | None:
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    if not runs_root.exists():
        return None

    latest_path: Path | None = None
    latest_timestamp = _MIN_TIMESTAMP
    latest_run_id = ""

    for candidate in runs_root.iterdir():
        if not candidate.is_dir():
            continue

        manifest_path = run_manifest_path(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=candidate.name,
        )
        if not manifest_path.exists():
            continue

        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        timestamp = _parse_utc_timestamp(
            str(payload.get("updated_at_utc", payload.get("created_at_utc")))
        )
        if timestamp > latest_timestamp or (
            timestamp == latest_timestamp and candidate.name > latest_run_id
        ):
            latest_timestamp = timestamp
            latest_run_id = candidate.name
            latest_path = candidate

    return latest_path


def latest_run_id(workspace_root: Path, work_item: str) -> str | None:
    resolved = latest_run_path(workspace_root=workspace_root, work_item=work_item)
    if resolved is None:
        return None
    return resolved.name


def latest_attempt_number(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> int | None:
    attempts_root = run_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if not attempts_root.exists():
        return None

    latest_attempt: int | None = None
    for candidate in attempts_root.iterdir():
        if not candidate.is_dir():
            continue
        if not candidate.name.startswith(RUN_ATTEMPT_PREFIX):
            continue

        suffix = candidate.name.removeprefix(RUN_ATTEMPT_PREFIX)
        if not suffix.isdigit():
            continue

        parsed_attempt = int(suffix)
        latest_attempt = (
            parsed_attempt if latest_attempt is None else max(latest_attempt, parsed_attempt)
        )

    return latest_attempt


def latest_attempt_path(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> Path | None:
    attempt_number = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_number is None:
        return None
    return run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )


def latest_attempt_path_for_work_item(
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> Path | None:
    run_id = latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if run_id is None:
        return None
    return latest_attempt_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )


def attempt_artifact_index_path(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> Path:
    return run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )


def resolve_attempt_artifact_paths(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> AttemptArtifactPaths | None:
    artifact_index = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    if artifact_index is None:
        return None

    return AttemptArtifactPaths(
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        documents={
            name: _resolve_workspace_relative_path(
                workspace_root=workspace_root,
                relative_path=relative_path,
            )
            for name, relative_path in artifact_index.documents.items()
        },
        logs={
            name: _resolve_workspace_relative_path(
                workspace_root=workspace_root,
                relative_path=relative_path,
            )
            for name, relative_path in artifact_index.logs.items()
        },
    )


def resolve_latest_attempt_artifact_paths(
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> AttemptArtifactPaths | None:
    run_id = latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if run_id is None:
        return None

    attempt_number = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_number is None:
        return None

    return resolve_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
