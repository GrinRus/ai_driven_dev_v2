from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aidd.core.identifiers import contained_component_path
from aidd.core.run_lookup import latest_run_id
from aidd.core.run_store import load_stage_metadata, run_manifest_path
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    resolve_expected_output_documents,
)
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.state_machine import StageState
from aidd.core.workspace import stage_root as workspace_stage_root

OPERATOR_REQUESTS_DIRNAME = "operator-requests"
OPERATOR_REQUEST_PREFIX = "request-"
OPERATOR_REQUEST_SUFFIX = ".md"

_REQUEST_ID_PATTERN = re.compile(r"^request-(\d{4,})$")
_CONTROL_DOCUMENTS_BLOCKED_AS_TARGETS = frozenset({"repair-brief.md", "stage-brief.md"})


@dataclass(frozen=True, slots=True)
class OperatorInterventionRequest:
    work_item: str
    stage: str
    request_id: str
    request_path: Path
    request_markdown: str
    request_text: str
    target_documents: tuple[str, ...]
    created_at_utc: str
    created_by: str


def _write_text_atomic(path: Path, content: str) -> None:
    staging_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        staging_path.write_text(content, encoding="utf-8")
        staging_path.replace(path)
    finally:
        staging_path.unlink(missing_ok=True)


def _utc_timestamp(moment: datetime | None = None) -> str:
    return (moment or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def _validate_stage(stage: str) -> None:
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}.")


def operator_requests_root(*, workspace_root: Path, work_item: str, stage: str) -> Path:
    _validate_stage(stage)
    return contained_component_path(
        workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage),
        OPERATOR_REQUESTS_DIRNAME,
        boundary_root=workspace_root,
        label="operator requests directory",
    )


def _request_number(path: Path) -> int | None:
    if path.suffix != OPERATOR_REQUEST_SUFFIX:
        return None
    match = _REQUEST_ID_PATTERN.match(path.stem)
    if match is None:
        return None
    return int(match.group(1))


def next_operator_request_id(*, workspace_root: Path, work_item: str, stage: str) -> str:
    root = operator_requests_root(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    next_number = 1
    if root.exists():
        existing_numbers = [
            number
            for path in root.iterdir()
            if path.is_file() and (number := _request_number(path)) is not None
        ]
        if existing_numbers:
            next_number = max(existing_numbers) + 1
    return f"{OPERATOR_REQUEST_PREFIX}{next_number:04d}"


def _stage_scope_target_documents(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[Path, ...]:
    expected_outputs = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    return tuple(
        path
        for path in expected_outputs
        if path.suffix.lower() == ".md"
        and path.name not in _CONTROL_DOCUMENTS_BLOCKED_AS_TARGETS
    )


def validate_operator_target_documents(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    target_documents: tuple[str, ...] = (),
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[str, ...]:
    _validate_stage(stage)
    if not target_documents:
        return ()

    stage_root = workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage)
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_stage_root = stage_root.resolve(strict=False)
    allowed_paths = {
        path.resolve(strict=False)
        for path in _stage_scope_target_documents(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            contracts_root=contracts_root,
        )
    }
    normalized: list[str] = []
    seen: set[str] = set()

    for raw_target in target_documents:
        target = raw_target.strip()
        if not target:
            continue
        relative = Path(target)
        if relative.is_absolute():
            raise ValueError("Target document must be workspace-relative or stage-relative.")
        base = workspace_root if relative.parts and relative.parts[0] == "workitems" else stage_root
        resolved = (base / relative).resolve(strict=False)
        if not resolved.is_relative_to(resolved_workspace):
            raise ValueError(f"Target document escapes workspace root: {target}")
        if not resolved.is_relative_to(resolved_stage_root):
            raise ValueError(
                f"Target document is outside current stage scope '{stage}': {target}"
            )
        if resolved.suffix.lower() != ".md":
            raise ValueError(f"Target document must be Markdown: {target}")
        if resolved.name in _CONTROL_DOCUMENTS_BLOCKED_AS_TARGETS:
            raise ValueError(f"Target document is AIDD-owned and cannot be targeted: {target}")
        if resolved not in allowed_paths:
            allowed = ", ".join(
                workspace_relative_path(workspace_root, path)
                for path in sorted(allowed_paths, key=lambda item: item.as_posix())
            )
            raise ValueError(
                f"Target document is not writable by stage '{stage}': {target}. "
                f"Allowed documents: {allowed or 'none'}."
            )
        relative_workspace = workspace_relative_path(workspace_root, resolved)
        if relative_workspace not in seen:
            normalized.append(relative_workspace)
            seen.add(relative_workspace)

    return tuple(normalized)


def render_operator_request_markdown(
    *,
    stage: str,
    request_text: str,
    target_documents: tuple[str, ...] = (),
    constraints: tuple[str, ...] = (),
    created_by: str = "operator",
    created_at_utc: str | None = None,
) -> str:
    normalized_request = request_text.strip()
    if not normalized_request:
        raise ValueError("Operator request must not be empty.")

    timestamp = created_at_utc or _utc_timestamp()
    lines = [
        "# Operator Request",
        "",
        "## Request",
        "",
        normalized_request,
        "",
        "## Target stage",
        "",
        f"- `{stage}`",
        "",
        "## Target documents",
        "",
    ]
    if target_documents:
        lines.extend(f"- `{path}`" for path in target_documents)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Constraints",
            "",
        ]
    )
    if constraints:
        lines.extend(f"- {constraint}" for constraint in constraints)
    else:
        lines.extend(
            [
                "- Keep changes within the selected stage scope.",
                "- Preserve valid existing sections unless the request requires a narrow change.",
            ]
        )
    lines.extend(
        [
            "",
            "## Created by",
            "",
            f"- Operator: `{created_by}`",
            f"- Created at UTC: `{timestamp}`",
            "",
        ]
    )
    return "\n".join(lines)


def persist_operator_intervention_request(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    request_text: str,
    target_documents: tuple[str, ...] = (),
    created_by: str = "operator",
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    created_at_utc: datetime | None = None,
) -> OperatorInterventionRequest:
    _validate_stage(stage)
    normalized_request = request_text.strip()
    if not normalized_request:
        raise ValueError("Operator request must not be empty.")

    normalized_targets = validate_operator_target_documents(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        target_documents=target_documents,
        contracts_root=contracts_root,
    )
    request_root = operator_requests_root(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    request_root.mkdir(parents=True, exist_ok=True)
    request_id = next_operator_request_id(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    timestamp = _utc_timestamp(created_at_utc)
    markdown = render_operator_request_markdown(
        stage=stage,
        request_text=normalized_request,
        target_documents=normalized_targets,
        created_by=created_by,
        created_at_utc=timestamp,
    )
    request_path = request_root / f"{request_id}{OPERATOR_REQUEST_SUFFIX}"
    _write_text_atomic(request_path, markdown)
    return OperatorInterventionRequest(
        work_item=work_item,
        stage=stage,
        request_id=request_id,
        request_path=request_path,
        request_markdown=markdown,
        request_text=normalized_request,
        target_documents=normalized_targets,
        created_at_utc=timestamp,
        created_by=created_by,
    )


def _extract_section(markdown: str, heading: str) -> str:
    lines = markdown.splitlines()
    heading_line = f"## {heading}"
    in_section = False
    collected: list[str] = []
    for line in lines:
        if line.strip() == heading_line:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            collected.append(line)
    return "\n".join(collected).strip()


def _parse_target_documents(markdown: str) -> tuple[str, ...]:
    section = _extract_section(markdown, "Target documents")
    targets: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        value = stripped[2:].strip()
        if value == "none":
            continue
        targets.append(value.strip("`"))
    return tuple(targets)


def _parse_created_at(markdown: str) -> str:
    section = _extract_section(markdown, "Created by")
    for line in section.splitlines():
        if "Created at UTC:" not in line:
            continue
        return line.split("Created at UTC:", 1)[1].strip().strip("`")
    return ""


def _parse_created_by(markdown: str) -> str:
    section = _extract_section(markdown, "Created by")
    for line in section.splitlines():
        if "Operator:" not in line:
            continue
        return line.split("Operator:", 1)[1].strip().strip("`")
    return "operator"


def _request_from_path(*, work_item: str, stage: str, path: Path) -> OperatorInterventionRequest:
    markdown = path.read_text(encoding="utf-8")
    return OperatorInterventionRequest(
        work_item=work_item,
        stage=stage,
        request_id=path.stem,
        request_path=path,
        request_markdown=markdown,
        request_text=_extract_section(markdown, "Request"),
        target_documents=_parse_target_documents(markdown),
        created_at_utc=_parse_created_at(markdown),
        created_by=_parse_created_by(markdown),
    )


def list_operator_intervention_requests(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> tuple[OperatorInterventionRequest, ...]:
    root = operator_requests_root(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    if not root.exists():
        return ()
    paths = sorted(
        (
            path
            for path in root.iterdir()
            if path.is_file() and _request_number(path) is not None
        ),
        key=lambda path: _request_number(path) or 0,
    )
    return tuple(_request_from_path(work_item=work_item, stage=stage, path=path) for path in paths)


def latest_operator_intervention_request(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> OperatorInterventionRequest | None:
    requests = list_operator_intervention_requests(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    return requests[-1] if requests else None


def resolve_intervention_run_id(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str | None = None,
) -> str:
    if run_id is not None and run_id.strip():
        selected = run_id.strip()
    else:
        selected = latest_run_id(workspace_root=workspace_root, work_item=work_item) or ""
    if not selected:
        raise ValueError(f"No run found for work item '{work_item}'.")
    manifest_path = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected,
    )
    if not manifest_path.exists():
        raise ValueError(f"Run '{selected}' does not exist for work item '{work_item}'.")
    return selected


def ensure_intervention_allowed_for_downstream(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> None:
    _validate_stage(stage)
    stage_index = STAGES.index(stage)
    succeeded_downstream: list[str] = []
    for downstream_stage in STAGES[stage_index + 1 :]:
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=downstream_stage,
        )
        if metadata is not None and metadata.status == StageState.SUCCEEDED.value:
            succeeded_downstream.append(downstream_stage)
    if succeeded_downstream:
        raise ValueError(
            "Operator intervention is blocked because downstream stages already succeeded "
            f"in run '{run_id}': {', '.join(succeeded_downstream)}. "
            "Rerun downstream policy is not available in this slice."
        )


__all__ = [
    "OPERATOR_REQUESTS_DIRNAME",
    "OperatorInterventionRequest",
    "ensure_intervention_allowed_for_downstream",
    "latest_operator_intervention_request",
    "list_operator_intervention_requests",
    "next_operator_request_id",
    "operator_requests_root",
    "persist_operator_intervention_request",
    "render_operator_request_markdown",
    "resolve_intervention_run_id",
    "validate_operator_target_documents",
]
