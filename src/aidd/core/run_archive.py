from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from aidd.core.identifiers import contained_component_path
from aidd.core.run_store import run_manifest_path, write_json_payload
from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME

_OPERATOR_OVERLAYS_DIRNAME = "operator-overlays"
_RUN_ARCHIVE_DIRNAME = "run-archive"
_DECISION_PREFIX = "decision-"
_DECISION_FILENAME = "archive-decision.json"
_DECISION_PATTERN = re.compile(r"^decision-(\d{4})$")


class RunArchiveProtocolError(ValueError):
    """Raised when an archive overlay is incomplete or malformed."""


@dataclass(frozen=True, slots=True)
class RunArchiveDecision:
    work_item_id: str
    run_id: str
    decision_number: int
    archived_at_utc: str
    reason: str | None
    source: str
    schema_version: int = 1

    @property
    def archived(self) -> bool:
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "work_item_id": self.work_item_id,
            "run_id": self.run_id,
            "decision_number": self.decision_number,
            "archived": True,
            "archived_at_utc": self.archived_at_utc,
            "reason": self.reason,
            "source": self.source,
        }

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "archived": True,
            "archived_at_utc": self.archived_at_utc,
            "reason": self.reason,
            "source": self.source,
        }


def _format_utc_timestamp(timestamp: datetime | None = None) -> str:
    from datetime import UTC

    moment = (timestamp or datetime.now(UTC)).astimezone(UTC)
    return moment.isoformat().replace("+00:00", "Z")


def run_archive_decisions_root(*, workspace_root: Path, work_item: str, run_id: str) -> Path:
    reports_root = contained_component_path(
        workspace_root,
        WORKSPACE_REPORTS_DIRNAME,
        boundary_root=workspace_root,
        label="reports directory",
    )
    overlays_root = contained_component_path(
        reports_root,
        _OPERATOR_OVERLAYS_DIRNAME,
        boundary_root=workspace_root,
        label="operator overlays directory",
    )
    work_item_root = contained_component_path(
        overlays_root,
        work_item,
        boundary_root=workspace_root,
        label="work item id",
    )
    archive_root = contained_component_path(
        work_item_root,
        _RUN_ARCHIVE_DIRNAME,
        boundary_root=workspace_root,
        label="run archive directory",
    )
    return contained_component_path(
        archive_root,
        run_id,
        boundary_root=workspace_root,
        label="run id",
    )


def _parse_decision(
    *, path: Path, work_item: str, run_id: str, decision_number: int
) -> RunArchiveDecision:
    if path.is_symlink():
        raise RunArchiveProtocolError(f"Archive decision must not be a symlink: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunArchiveProtocolError(f"Archive decision is unreadable: {path}") from exc
    if not isinstance(payload, dict):
        raise RunArchiveProtocolError(f"Archive decision must be an object: {path}")
    if payload.get("schema_version") != 1:
        raise RunArchiveProtocolError(f"Archive decision schema is unsupported: {path}")
    if (
        payload.get("work_item_id") != work_item
        or payload.get("run_id") != run_id
        or payload.get("decision_number") != decision_number
        or payload.get("archived") is not True
    ):
        raise RunArchiveProtocolError(f"Archive decision identity is invalid: {path}")
    archived_at = str(payload.get("archived_at_utc", "")).strip()
    source = str(payload.get("source", "")).strip()
    raw_reason = payload.get("reason")
    if (
        not archived_at
        or not source
        or (raw_reason is not None and not isinstance(raw_reason, str))
    ):
        raise RunArchiveProtocolError(f"Archive decision fields are invalid: {path}")
    reason = raw_reason.strip() if isinstance(raw_reason, str) and raw_reason.strip() else None
    return RunArchiveDecision(
        work_item_id=work_item,
        run_id=run_id,
        decision_number=decision_number,
        archived_at_utc=archived_at,
        reason=reason,
        source=source,
    )


def load_run_archive_decisions(
    *, workspace_root: Path, work_item: str, run_id: str
) -> tuple[RunArchiveDecision, ...]:
    root = run_archive_decisions_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not root.exists():
        return ()
    if not root.is_dir():
        raise RunArchiveProtocolError(f"Archive overlay is not a directory: {root}")

    numbered_paths: list[tuple[int, Path]] = []
    for child in root.iterdir():
        match = _DECISION_PATTERN.fullmatch(child.name)
        if match is None or child.is_symlink() or not child.is_dir():
            raise RunArchiveProtocolError(f"Archive overlay contains an invalid entry: {child}")
        numbered_paths.append((int(match.group(1)), child))
    if not numbered_paths:
        raise RunArchiveProtocolError(f"Archive overlay contains no decisions: {root}")

    decisions: list[RunArchiveDecision] = []
    for expected_number, (number, directory) in enumerate(sorted(numbered_paths), start=1):
        if number != expected_number:
            raise RunArchiveProtocolError(f"Archive decision sequence is not contiguous: {root}")
        decisions.append(
            _parse_decision(
                path=directory / _DECISION_FILENAME,
                work_item=work_item,
                run_id=run_id,
                decision_number=number,
            )
        )
    return tuple(decisions)


def persist_run_archive_decision(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    reason: str | None = None,
    source: str = "ui",
    changed_at_utc: datetime | None = None,
) -> dict[str, Any]:
    manifest = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not manifest.is_file():
        raise ValueError(f"Run manifest is missing for work item '{work_item}', run '{run_id}'.")

    root = run_archive_decisions_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    root_existed = root.exists()
    root.mkdir(parents=True, exist_ok=True)
    decision_number = 1
    while True:
        decision_dir = contained_component_path(
            root,
            f"{_DECISION_PREFIX}{decision_number:04d}",
            boundary_root=workspace_root,
            label="archive decision id",
        )
        try:
            decision_dir.mkdir(parents=False, exist_ok=False)
            break
        except FileExistsError:
            decision_number += 1

    decision = RunArchiveDecision(
        work_item_id=work_item,
        run_id=run_id,
        decision_number=decision_number,
        archived_at_utc=_format_utc_timestamp(changed_at_utc),
        reason=reason.strip() if isinstance(reason, str) and reason.strip() else None,
        source=source.strip() or "ui",
    )
    try:
        write_json_payload(decision_dir / _DECISION_FILENAME, decision.to_dict())
    except Exception:
        if decision_dir.exists() and not tuple(decision_dir.iterdir()):
            decision_dir.rmdir()
        if not root_existed:
            reports_root = workspace_root / WORKSPACE_REPORTS_DIRNAME
            cleanup = root
            while cleanup != reports_root and cleanup.exists() and not tuple(cleanup.iterdir()):
                cleanup.rmdir()
                cleanup = cleanup.parent
        raise
    return decision.to_api_dict()


def resolve_run_archive_decision(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    manifest_payload: dict[str, Any],
) -> RunArchiveDecision | None:
    decisions = load_run_archive_decisions(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if decisions:
        return decisions[-1]

    legacy = manifest_payload.get("operator_archive")
    if not isinstance(legacy, dict) or legacy.get("archived") is not True:
        return None
    archived_at = str(legacy.get("archived_at_utc", "")).strip()
    source = str(legacy.get("source", "")).strip()
    raw_reason = legacy.get("reason")
    if (
        not archived_at
        or not source
        or (raw_reason is not None and not isinstance(raw_reason, str))
    ):
        raise RunArchiveProtocolError("Legacy archive state in run manifest is malformed.")
    return RunArchiveDecision(
        work_item_id=work_item,
        run_id=run_id,
        decision_number=0,
        archived_at_utc=archived_at,
        reason=raw_reason.strip() if isinstance(raw_reason, str) and raw_reason.strip() else None,
        source=source,
    )


__all__ = [
    "RunArchiveDecision",
    "RunArchiveProtocolError",
    "load_run_archive_decisions",
    "persist_run_archive_decision",
    "resolve_run_archive_decision",
    "run_archive_decisions_root",
]
