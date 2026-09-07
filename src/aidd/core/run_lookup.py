from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.run_store import (
    RUN_ATTEMPT_PREFIX,
    load_attempt_artifact_index,
    load_run_manifest,
    run_attempt_root,
    run_attempts_root,
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


class AmbiguousLatestRunError(ValueError):
    """Raised when multiple runs share the latest authoritative timestamp."""


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


def _latest_run_entries(workspace_root: Path, work_item: str) -> list[tuple[Path, datetime]]:
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    if not runs_root.exists():
        return []

    entries: list[tuple[Path, datetime]] = []
    for candidate in runs_root.iterdir():
        if not candidate.is_dir():
            continue

        try:
            payload = load_run_manifest(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=candidate.name,
            )
        except ValueError:
            continue

        if payload is None:
            continue
        timestamp = _parse_utc_timestamp(payload["updated_at_utc"])
        entries.append((candidate, timestamp))
    return entries


def latest_run_path(workspace_root: Path, work_item: str) -> Path | None:
    entries = _latest_run_entries(workspace_root=workspace_root, work_item=work_item)
    if not entries:
        return None

    latest_timestamp = max(timestamp for _, timestamp in entries)
    matching_paths = sorted(
        (path for path, timestamp in entries if timestamp == latest_timestamp),
        key=lambda path: path.name,
    )
    if len(matching_paths) > 1:
        raise AmbiguousLatestRunError(
            "Ambiguous latest run for work item "
            f"'{work_item}': {', '.join(path.name for path in matching_paths)}."
        )
    return matching_paths[0]


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
