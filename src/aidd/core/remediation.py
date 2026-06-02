from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidd.core.run_store import run_manifest_path, run_root
from aidd.core.stages import STAGES, stage_index
from aidd.core.workspace import work_item_root

REMEDIATIONS_DIRNAME = "remediations"
REMEDIATION_STATUS_FILENAME = "remediation-status.json"
_REQUEST_PREFIX = "request-"


@dataclass(frozen=True, slots=True)
class RemediationRequest:
    request_id: str
    work_item: str
    run_id: str
    source_stage: str
    source_ids: tuple[str, ...]
    target_stage: str
    operator_note: str
    request_path: Path
    created_at_utc: str


@dataclass(frozen=True, slots=True)
class RemediationStaleStage:
    stage: str
    status: str
    invalidated_by: str
    invalidated_at_utc: str
    reason: str


@dataclass(frozen=True, slots=True)
class RemediationStatus:
    run_id: str
    stale_stages: tuple[RemediationStaleStage, ...]
    requests: tuple[RemediationRequest, ...]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _remediation_root(*, workspace_root: Path, work_item: str, run_id: str) -> Path:
    return work_item_root(root=workspace_root, work_item=work_item) / REMEDIATIONS_DIRNAME / run_id


def _request_number(path: Path) -> int | None:
    if not path.name.startswith(_REQUEST_PREFIX) or path.suffix != ".md":
        return None
    value = path.stem.removeprefix(_REQUEST_PREFIX)
    return int(value) if value.isdigit() else None


def _next_request_id(root: Path) -> str:
    existing = [
        number
        for path in root.glob(f"{_REQUEST_PREFIX}*.md")
        if (number := _request_number(path)) is not None
    ]
    return f"{_REQUEST_PREFIX}{max(existing, default=0) + 1:04d}"


def _validate_run_exists(*, workspace_root: Path, work_item: str, run_id: str) -> None:
    path = run_manifest_path(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    if not path.exists():
        raise ValueError(f"Run '{run_id}' does not exist for work item '{work_item}'.")


def _validate_remediation_request(
    *,
    source_stage: str,
    source_ids: tuple[str, ...],
    target_stage: str,
    operator_note: str,
) -> None:
    if source_stage not in {"review", "qa"}:
        raise ValueError("source_stage must be review or qa.")
    if target_stage != "implement":
        raise ValueError("target_stage must be implement.")
    if not source_ids:
        raise ValueError("At least one source id is required.")
    for source_id in source_ids:
        if not source_id.strip():
            raise ValueError("source_ids must not contain empty entries.")
        if "/" in source_id or "\\" in source_id or source_id in {".", ".."}:
            raise ValueError("source_ids must be plain identifiers.")
    if not operator_note.strip():
        raise ValueError("operator_note is required.")


def _render_request_markdown(request: RemediationRequest) -> str:
    source_ids = "\n".join(f"- `{source_id}`" for source_id in request.source_ids)
    return "\n".join(
        (
            "# Remediation Request",
            "",
            "## Metadata",
            "",
            f"- Request id: `{request.request_id}`",
            f"- Work item: `{request.work_item}`",
            f"- Run id: `{request.run_id}`",
            f"- Source stage: `{request.source_stage}`",
            f"- Target stage: `{request.target_stage}`",
            f"- Created at: `{request.created_at_utc}`",
            "",
            "## Source ids",
            "",
            source_ids,
            "",
            "## Operator note",
            "",
            request.operator_note.strip(),
            "",
            "## Runtime instruction",
            "",
            "Use this request as remediation input for a new `implement` attempt. "
            "Fix only the selected findings or risks, preserve unrelated source-run artifacts, "
            "and record verification evidence in `implementation-report.md`.",
            "",
        )
    )


def create_remediation_request(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    source_stage: str,
    source_ids: tuple[str, ...],
    operator_note: str,
    target_stage: str = "implement",
) -> RemediationRequest:
    _validate_run_exists(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    normalized_source_ids = tuple(
        source_id.strip() for source_id in source_ids if source_id.strip()
    )
    _validate_remediation_request(
        source_stage=source_stage,
        source_ids=normalized_source_ids,
        target_stage=target_stage,
        operator_note=operator_note,
    )
    root = _remediation_root(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    root.mkdir(parents=True, exist_ok=True)
    request_id = _next_request_id(root)
    request = RemediationRequest(
        request_id=request_id,
        work_item=work_item,
        run_id=run_id,
        source_stage=source_stage,
        source_ids=normalized_source_ids,
        target_stage=target_stage,
        operator_note=operator_note.strip(),
        request_path=root / f"{request_id}.md",
        created_at_utc=_utc_now(),
    )
    request.request_path.write_text(_render_request_markdown(request), encoding="utf-8")
    return request


def _metadata_value(text: str, label: str) -> str | None:
    matched = re.search(rf"{re.escape(label)}\s*:\s*`([^`]+)`", text, flags=re.IGNORECASE)
    return matched.group(1).strip() if matched else None


def _parse_request(
    path: Path,
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> RemediationRequest:
    text = path.read_text(encoding="utf-8", errors="replace")
    source_ids_section = False
    source_ids: list[str] = []
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.+)$", line)
        if heading:
            source_ids_section = heading.group(1).strip().lower() == "source ids"
            continue
        if source_ids_section:
            matched = re.search(r"`([^`]+)`", line)
            if matched:
                source_ids.append(matched.group(1))
    note = text.split("## Operator note", 1)[-1].split("## Runtime instruction", 1)[0].strip()
    return RemediationRequest(
        request_id=_metadata_value(text, "Request id") or path.stem,
        work_item=_metadata_value(text, "Work item") or work_item,
        run_id=_metadata_value(text, "Run id") or run_id,
        source_stage=_metadata_value(text, "Source stage") or "review",
        source_ids=tuple(source_ids),
        target_stage=_metadata_value(text, "Target stage") or "implement",
        operator_note=note,
        request_path=path,
        created_at_utc=_metadata_value(text, "Created at") or "",
    )


def list_remediation_requests(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> tuple[RemediationRequest, ...]:
    root = _remediation_root(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    if not root.is_dir():
        return ()
    paths = sorted(
        (path for path in root.glob(f"{_REQUEST_PREFIX}*.md") if _request_number(path) is not None),
        key=lambda path: _request_number(path) or 0,
    )
    return tuple(
        _parse_request(path, workspace_root=workspace_root, work_item=work_item, run_id=run_id)
        for path in paths
    )


def latest_remediation_input_documents(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    target_stage: str,
) -> tuple[Path, ...]:
    if target_stage != "implement":
        return ()
    requests = list_remediation_requests(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not requests:
        return ()
    return (requests[-1].request_path,)


def _status_path(*, workspace_root: Path, work_item: str, run_id: str) -> Path:
    return run_root(workspace_root=workspace_root, work_item=work_item, run_id=run_id) / (
        REMEDIATION_STATUS_FILENAME
    )


def _stale_from_payload(payload: dict[str, Any]) -> RemediationStaleStage:
    return RemediationStaleStage(
        stage=str(payload["stage"]),
        status=str(payload.get("status", "stale")),
        invalidated_by=str(payload["invalidated_by"]),
        invalidated_at_utc=str(payload["invalidated_at_utc"]),
        reason=str(payload["reason"]),
    )


def load_remediation_status(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> RemediationStatus:
    requests = list_remediation_requests(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    path = _status_path(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    if not path.exists():
        return RemediationStatus(run_id=run_id, stale_stages=(), requests=requests)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return RemediationStatus(
        run_id=run_id,
        stale_stages=tuple(
            _stale_from_payload(item) for item in payload.get("stale_stages", [])
        ),
        requests=requests,
    )


def mark_downstream_stale(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    invalidated_by: str,
    target_stage: str = "implement",
) -> RemediationStatus:
    if target_stage not in STAGES:
        raise ValueError(f"Unknown target_stage '{target_stage}'.")
    timestamp = _utc_now()
    downstream = STAGES[stage_index(target_stage) + 1 :]
    stale_entries = tuple(
        RemediationStaleStage(
            stage=stage,
            status="stale",
            invalidated_by=invalidated_by,
            invalidated_at_utc=timestamp,
            reason=f"New {target_stage} remediation attempt invalidated downstream {stage}.",
        )
        for stage in downstream
    )
    path = _status_path(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "stale_stages": [
            {
                "stage": item.stage,
                "status": item.status,
                "invalidated_by": item.invalidated_by,
                "invalidated_at_utc": item.invalidated_at_utc,
                "reason": item.reason,
            }
            for item in stale_entries
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return load_remediation_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )


def clear_stale_stages(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stages: tuple[str, ...],
) -> RemediationStatus:
    current = load_remediation_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    cleared = set(stages)
    remaining = tuple(item for item in current.stale_stages if item.stage not in cleared)
    path = _status_path(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": run_id,
                "stale_stages": [
                    {
                        "stage": item.stage,
                        "status": item.status,
                        "invalidated_by": item.invalidated_by,
                        "invalidated_at_utc": item.invalidated_at_utc,
                        "reason": item.reason,
                    }
                    for item in remaining
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return load_remediation_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )


__all__ = [
    "REMEDIATION_STATUS_FILENAME",
    "REMEDIATIONS_DIRNAME",
    "RemediationRequest",
    "RemediationStaleStage",
    "RemediationStatus",
    "clear_stale_stages",
    "create_remediation_request",
    "latest_remediation_input_documents",
    "list_remediation_requests",
    "load_remediation_status",
    "mark_downstream_stale",
]
