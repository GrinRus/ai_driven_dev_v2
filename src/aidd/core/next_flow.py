from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.core.run_inspection import RunMetadataSummary, resolve_run_metadata_summary
from aidd.core.run_store import run_manifest_path
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    StageManifestLoadError,
    load_all_stage_manifests,
)
from aidd.core.workspace import (
    WorkItemContextSeedResult,
    init_workspace,
    seed_work_item_context,
    work_item_context_root,
    work_item_metadata_path,
)
from aidd.runtime_catalog import get_runtime_definition

_CLONE_FLOW_DRAFT_FILENAME = "clone-flow-draft.md"
_FOLLOW_UP_REQUEST_FILENAME = "follow-up-request.md"
_SUPPORTED_FOLLOW_UP_SOURCE_KINDS = frozenset(
    {
        "qa-finding",
        "review-note",
        "failed-evidence",
        "manual-request",
    }
)


@dataclass(frozen=True, slots=True)
class FollowUpSourceSelection:
    kind: str
    title: str
    source_path: str | None = None
    stage: str | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class FollowUpDraftRequest:
    workspace_root: Path
    source_work_item: str
    source_run_id: str
    new_work_item: str
    title: str
    selections: tuple[FollowUpSourceSelection, ...]
    project_root: Path | None = None


@dataclass(frozen=True, slots=True)
class FollowUpDraftResult:
    work_item: str
    request_path: Path
    context_seed: WorkItemContextSeedResult
    source_artifact_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClonePromptPackReference:
    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class CloneFlowDraftConfig:
    runtime_id: str
    adapter_id: str | None
    stage_target: str
    workflow_stage_start: str | None
    workflow_stage_end: str | None
    resource_root: str | None
    repository_git_sha: str | None
    resource_revision: str | None
    baseline_id: str
    baseline_label: str
    prompt_pack_provenance: tuple[ClonePromptPackReference, ...]


@dataclass(frozen=True, slots=True)
class CloneFlowDraftRequest:
    workspace_root: Path
    source_work_item: str
    source_run_id: str
    new_work_item: str
    title: str
    project_root: Path | None = None


@dataclass(frozen=True, slots=True)
class CloneFlowDraftResult:
    work_item: str
    draft_path: Path
    context_seed: WorkItemContextSeedResult
    config: CloneFlowDraftConfig


@dataclass(frozen=True, slots=True)
class NextFlowLaunchPreflightRequest:
    workspace_root: Path
    source_work_item: str
    source_run_id: str
    runtime_id: str
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT
    baseline_id: str | None = None


@dataclass(frozen=True, slots=True)
class NextFlowLaunchPreflightCheck:
    code: str
    severity: str
    message: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class NextFlowLaunchPreflightResult:
    status: str
    can_launch: bool
    checks: tuple[NextFlowLaunchPreflightCheck, ...]
    blocking_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    resolved_baseline_id: str | None
    error_payload: dict[str, Any]


def create_follow_up_work_item_draft(request: FollowUpDraftRequest) -> FollowUpDraftResult:
    if not request.selections:
        raise ValueError("At least one follow-up source selection is required.")
    normalized_title = _required_text(request.title, field_name="title")
    normalized_source_work_item = _required_text(
        request.source_work_item,
        field_name="source_work_item",
    )
    normalized_source_run = _required_text(request.source_run_id, field_name="source_run_id")
    normalized_new_work_item = _required_text(request.new_work_item, field_name="new_work_item")
    normalized_selections = tuple(
        _normalize_selection(
            workspace_root=request.workspace_root,
            selection=selection,
        )
        for selection in request.selections
    )

    init_workspace(root=request.workspace_root, work_item=normalized_new_work_item)
    context_seed = seed_work_item_context(
        root=request.workspace_root,
        work_item=normalized_new_work_item,
        request_text=_follow_up_user_request_text(
            title=normalized_title,
            source_work_item=normalized_source_work_item,
            source_run_id=normalized_source_run,
        ),
        project_root=request.project_root,
    )

    context_root = work_item_context_root(
        root=request.workspace_root,
        work_item=normalized_new_work_item,
    )
    request_path = context_root / _FOLLOW_UP_REQUEST_FILENAME
    request_path.write_text(
        _render_follow_up_request_markdown(
            title=normalized_title,
            source_work_item=normalized_source_work_item,
            source_run_id=normalized_source_run,
            selections=normalized_selections,
        ),
        encoding="utf-8",
    )
    _persist_follow_up_lineage(
        workspace_root=request.workspace_root,
        new_work_item=normalized_new_work_item,
        source_work_item=normalized_source_work_item,
        source_run_id=normalized_source_run,
    )
    return FollowUpDraftResult(
        work_item=normalized_new_work_item,
        request_path=request_path,
        context_seed=context_seed,
        source_artifact_paths=tuple(
            selection.source_path
            for selection in normalized_selections
            if selection.source_path
        ),
    )


def create_clone_flow_draft(request: CloneFlowDraftRequest) -> CloneFlowDraftResult:
    normalized_source_work_item = _required_text(
        request.source_work_item,
        field_name="source_work_item",
    )
    normalized_source_run = _required_text(request.source_run_id, field_name="source_run_id")
    normalized_new_work_item = _required_text(request.new_work_item, field_name="new_work_item")
    normalized_title = _required_text(request.title, field_name="title")
    metadata = resolve_run_metadata_summary(
        workspace_root=request.workspace_root,
        work_item=normalized_source_work_item,
        run_id=normalized_source_run,
    )
    manifest_payload = _load_source_run_manifest(
        workspace_root=request.workspace_root,
        work_item=normalized_source_work_item,
        run_id=normalized_source_run,
    )
    config = _clone_flow_config(metadata=metadata, manifest_payload=manifest_payload)

    init_workspace(root=request.workspace_root, work_item=normalized_new_work_item)
    context_seed = seed_work_item_context(
        root=request.workspace_root,
        work_item=normalized_new_work_item,
        request_text=_clone_flow_user_request_text(
            title=normalized_title,
            source_work_item=normalized_source_work_item,
            source_run_id=normalized_source_run,
        ),
        project_root=request.project_root,
    )

    context_root = work_item_context_root(
        root=request.workspace_root,
        work_item=normalized_new_work_item,
    )
    draft_path = context_root / _CLONE_FLOW_DRAFT_FILENAME
    draft_path.write_text(
        _render_clone_flow_draft_markdown(
            title=normalized_title,
            source_work_item=normalized_source_work_item,
            source_run_id=normalized_source_run,
            config=config,
        ),
        encoding="utf-8",
    )
    _persist_clone_lineage(
        workspace_root=request.workspace_root,
        new_work_item=normalized_new_work_item,
        source_work_item=normalized_source_work_item,
        source_run_id=normalized_source_run,
        baseline_id=config.baseline_id,
        baseline_label=config.baseline_label,
    )
    return CloneFlowDraftResult(
        work_item=normalized_new_work_item,
        draft_path=draft_path,
        context_seed=context_seed,
        config=config,
    )


def validate_next_flow_launch_preflight(
    request: NextFlowLaunchPreflightRequest,
) -> NextFlowLaunchPreflightResult:
    normalized_source_work_item = _required_preflight_text(
        request.source_work_item,
        field_name="source_work_item",
    )
    normalized_source_run = _required_preflight_text(
        request.source_run_id,
        field_name="source_run_id",
    )
    normalized_runtime = _required_preflight_text(
        request.runtime_id,
        field_name="runtime_id",
    )
    normalized_baseline = request.baseline_id.strip() or None if request.baseline_id else None

    checks: list[NextFlowLaunchPreflightCheck] = []
    checks.append(_workspace_writable_check(request.workspace_root))
    checks.append(_runtime_selection_check(normalized_runtime))
    checks.append(_contract_availability_check(request.contracts_root))

    source_metadata: RunMetadataSummary | None = None
    try:
        source_metadata = resolve_run_metadata_summary(
            workspace_root=request.workspace_root,
            work_item=normalized_source_work_item,
            run_id=normalized_source_run,
        )
    except ValueError as exc:
        checks.append(
            NextFlowLaunchPreflightCheck(
                code="source-run-missing",
                severity="blocking",
                message="Source run must exist before launching a next flow.",
                detail=str(exc),
            )
        )
    else:
        checks.append(
            NextFlowLaunchPreflightCheck(
                code="source-run-exists",
                severity="pass",
                message="Source run exists and can be used for launch lineage.",
                detail=f"{normalized_source_work_item}/{source_metadata.run_id}",
            )
        )

    resolved_baseline_id: str | None = None
    if source_metadata is not None:
        baseline_check, resolved_baseline_id = _baseline_availability_check(
            workspace_root=request.workspace_root,
            source_work_item=normalized_source_work_item,
            source_run_id=normalized_source_run,
            metadata=source_metadata,
            requested_baseline_id=normalized_baseline,
        )
        checks.append(baseline_check)

    return _next_flow_preflight_result(
        checks=tuple(checks),
        resolved_baseline_id=resolved_baseline_id,
    )


def _required_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"Follow-up draft {field_name} is required.")
    return normalized


def _required_preflight_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"Next-flow launch preflight {field_name} is required.")
    return normalized


def _workspace_writable_check(workspace_root: Path) -> NextFlowLaunchPreflightCheck:
    resolved = workspace_root.resolve(strict=False)
    if not resolved.exists():
        return NextFlowLaunchPreflightCheck(
            code="workspace-missing",
            severity="blocking",
            message="Workspace root must exist before launching a next flow.",
            detail=resolved.as_posix(),
        )
    if not resolved.is_dir():
        return NextFlowLaunchPreflightCheck(
            code="workspace-not-directory",
            severity="blocking",
            message="Workspace root must be a directory.",
            detail=resolved.as_posix(),
        )
    if not os.access(resolved, os.W_OK):
        return NextFlowLaunchPreflightCheck(
            code="workspace-not-writable",
            severity="blocking",
            message="Workspace root must be writable before launch.",
            detail=resolved.as_posix(),
        )
    return NextFlowLaunchPreflightCheck(
        code="workspace-writable",
        severity="pass",
        message="Workspace root exists and is writable.",
        detail=resolved.as_posix(),
    )


def _runtime_selection_check(runtime_id: str) -> NextFlowLaunchPreflightCheck:
    try:
        definition = get_runtime_definition(runtime_id)
    except ValueError as exc:
        return NextFlowLaunchPreflightCheck(
            code="unsupported-runtime",
            severity="blocking",
            message="Runtime id must be one of the maintained runtime catalog entries.",
            detail=str(exc),
        )
    return NextFlowLaunchPreflightCheck(
        code="runtime-supported",
        severity="pass",
        message="Runtime id is supported by the runtime catalog.",
        detail=f"{definition.runtime_id} ({definition.support_tier})",
    )


def _contract_availability_check(contracts_root: Path) -> NextFlowLaunchPreflightCheck:
    resolved = contracts_root.resolve(strict=False)
    if not resolved.exists():
        return NextFlowLaunchPreflightCheck(
            code="contracts-missing",
            severity="blocking",
            message="Stage contracts root must exist before launch.",
            detail=resolved.as_posix(),
        )
    try:
        load_all_stage_manifests(contracts_root=resolved)
    except (OSError, StageManifestLoadError, ValueError) as exc:
        return NextFlowLaunchPreflightCheck(
            code="contracts-unavailable",
            severity="blocking",
            message="Stage contracts must be loadable before launch.",
            detail=str(exc),
        )
    return NextFlowLaunchPreflightCheck(
        code="contracts-available",
        severity="pass",
        message="Stage contracts and referenced prompt packs are available.",
        detail=resolved.as_posix(),
    )


def _baseline_availability_check(
    *,
    workspace_root: Path,
    source_work_item: str,
    source_run_id: str,
    metadata: RunMetadataSummary,
    requested_baseline_id: str | None,
) -> tuple[NextFlowLaunchPreflightCheck, str]:
    if requested_baseline_id is None and metadata.lineage.baseline_id is None:
        return (
            NextFlowLaunchPreflightCheck(
                code="baseline-fallback-source-run",
                severity="warning",
                message="No explicit baseline is recorded; source run will be used as baseline.",
                detail=source_run_id,
            ),
            source_run_id,
        )

    baseline_id = requested_baseline_id or metadata.lineage.baseline_id or source_run_id
    baseline_manifest = run_manifest_path(
        workspace_root=workspace_root,
        work_item=source_work_item,
        run_id=baseline_id,
    )
    if not baseline_manifest.exists():
        return (
            NextFlowLaunchPreflightCheck(
                code="baseline-missing",
                severity="blocking",
                message="Baseline run manifest must exist before launch.",
                detail=baseline_manifest.as_posix(),
            ),
            baseline_id,
        )
    return (
        NextFlowLaunchPreflightCheck(
            code="baseline-available",
            severity="pass",
            message="Baseline run manifest is available.",
            detail=baseline_id,
        ),
        baseline_id,
    )


def _next_flow_preflight_result(
    *,
    checks: tuple[NextFlowLaunchPreflightCheck, ...],
    resolved_baseline_id: str | None,
) -> NextFlowLaunchPreflightResult:
    blocking_codes = tuple(check.code for check in checks if check.severity == "blocking")
    warning_codes = tuple(check.code for check in checks if check.severity == "warning")
    if blocking_codes:
        status = "blocked"
    elif warning_codes:
        status = "warning"
    else:
        status = "pass"
    return NextFlowLaunchPreflightResult(
        status=status,
        can_launch=status != "blocked",
        checks=checks,
        blocking_codes=blocking_codes,
        warning_codes=warning_codes,
        resolved_baseline_id=resolved_baseline_id,
        error_payload=(
            _next_flow_preflight_error_payload(
                checks=checks,
                blocking_codes=blocking_codes,
                warning_codes=warning_codes,
            )
            if blocking_codes
            else {}
        ),
    )


def _next_flow_preflight_error_payload(
    *,
    checks: tuple[NextFlowLaunchPreflightCheck, ...],
    blocking_codes: tuple[str, ...],
    warning_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "error": "next-flow launch preflight blocked",
        "status": "blocked",
        "blocking_codes": list(blocking_codes),
        "warning_codes": list(warning_codes),
        "checks": [
            {
                "code": check.code,
                "severity": check.severity,
                "message": check.message,
                "detail": check.detail,
            }
            for check in checks
        ],
    }


def _load_source_run_manifest(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> dict[str, object]:
    manifest_path = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not manifest_path.exists():
        raise ValueError(f"Source run manifest does not exist: {manifest_path.as_posix()}.")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Source run manifest must be a JSON object: {manifest_path.as_posix()}.")
    return payload


def _clone_flow_config(
    *,
    metadata: RunMetadataSummary,
    manifest_payload: dict[str, object],
) -> CloneFlowDraftConfig:
    baseline_id = metadata.lineage.baseline_id or metadata.run_id
    baseline_label = metadata.lineage.baseline_label or f"source run {metadata.run_id}"
    return CloneFlowDraftConfig(
        runtime_id=metadata.runtime_id,
        adapter_id=metadata.adapter_id,
        stage_target=metadata.stage_target,
        workflow_stage_start=metadata.workflow_stage_start,
        workflow_stage_end=metadata.workflow_stage_end,
        resource_root=_optional_payload_text(manifest_payload, "resource_root"),
        repository_git_sha=metadata.repository_git_sha,
        resource_revision=metadata.resource_revision,
        baseline_id=baseline_id,
        baseline_label=baseline_label,
        prompt_pack_provenance=tuple(
            ClonePromptPackReference(path=entry.path, sha256=entry.sha256)
            for entry in metadata.prompt_pack_provenance
        ),
    )


def _optional_payload_text(payload: dict[str, object], key: str) -> str | None:
    normalized = str(payload.get(key, "")).strip()
    return normalized or None


def _normalize_selection(
    *,
    workspace_root: Path,
    selection: FollowUpSourceSelection,
) -> FollowUpSourceSelection:
    kind = _required_text(selection.kind, field_name="selection kind")
    if kind not in _SUPPORTED_FOLLOW_UP_SOURCE_KINDS:
        supported = ", ".join(sorted(_SUPPORTED_FOLLOW_UP_SOURCE_KINDS))
        raise ValueError(f"Unsupported follow-up source kind '{kind}'. Supported: {supported}.")
    if kind == "manual-request" and not str(selection.source_path or "").strip():
        source_path = None
    else:
        source_path = _workspace_relative_source_path(
            workspace_root=workspace_root,
            source_path=selection.source_path,
        )
    return FollowUpSourceSelection(
        kind=kind,
        title=_required_text(selection.title, field_name="selection title"),
        source_path=source_path,
        stage=selection.stage.strip() or None if selection.stage is not None else None,
        note=selection.note.strip() or None if selection.note is not None else None,
    )


def _workspace_relative_source_path(*, workspace_root: Path, source_path: str | None) -> str:
    relative_path = Path(_required_text(source_path or "", field_name="selection source_path"))
    if relative_path.is_absolute():
        raise ValueError("Follow-up source artifact path must be workspace-relative.")
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_source = (workspace_root / relative_path).resolve(strict=False)
    if not resolved_source.is_relative_to(resolved_workspace):
        raise ValueError(f"Follow-up source artifact escapes workspace root: {source_path}.")
    if not resolved_source.exists():
        raise ValueError(f"Follow-up source artifact does not exist: {source_path}.")
    return resolved_source.relative_to(resolved_workspace).as_posix()


def _follow_up_user_request_text(
    *,
    title: str,
    source_work_item: str,
    source_run_id: str,
) -> str:
    return (
        f"Create follow-up work for {title}.\n\n"
        f"Source work item: `{source_work_item}`.\n"
        f"Source run: `{source_run_id}`.\n"
        f"Detailed selected evidence is recorded in `context/{_FOLLOW_UP_REQUEST_FILENAME}`."
    )


def _clone_flow_user_request_text(
    *,
    title: str,
    source_work_item: str,
    source_run_id: str,
) -> str:
    return (
        f"Clone the completed flow for {title}.\n\n"
        f"Source work item: `{source_work_item}`.\n"
        f"Source run: `{source_run_id}`.\n"
        f"Editable clone configuration is recorded in `context/{_CLONE_FLOW_DRAFT_FILENAME}`."
    )


def _render_follow_up_request_markdown(
    *,
    title: str,
    source_work_item: str,
    source_run_id: str,
    selections: tuple[FollowUpSourceSelection, ...],
) -> str:
    lines = [
        "# Follow-up work item request",
        "",
        "## Source",
        "",
        f"- Source work item: `{source_work_item}`",
        f"- Source run: `{source_run_id}`",
        "- Source artifacts are references and must not be rewritten in the completed run.",
        "",
        "## Requested work",
        "",
        f"- {title}",
        "",
        "## Selected source findings",
        "",
    ]
    for index, selection in enumerate(selections, 1):
        lines.extend(
            [
                f"### FUP-{index}: {selection.title}",
                "",
                f"- Kind: `{selection.kind}`",
            ]
        )
        if selection.source_path:
            lines.append(f"- Source artifact: `{selection.source_path}`")
        else:
            lines.append("- Source artifact: manual operator request only")
        if selection.stage is not None:
            lines.append(f"- Stage: `{selection.stage}`")
        if selection.note is not None:
            lines.append(f"- Note: {selection.note}")
        lines.append("")
    lines.extend(
        [
            "## Launch notes",
            "",
            "- Create a new work item and run identity before runtime execution.",
            "- Preserve source-run references as lineage metadata.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_clone_flow_draft_markdown(
    *,
    title: str,
    source_work_item: str,
    source_run_id: str,
    config: CloneFlowDraftConfig,
) -> str:
    lines = [
        "# Clone flow draft",
        "",
        "## Source",
        "",
        f"- Source work item: `{source_work_item}`",
        f"- Source run: `{source_run_id}`",
        "",
        "## Requested work",
        "",
        f"- {title}",
        "",
        "## Editable configuration",
        "",
        f"- Runtime id: `{config.runtime_id}`",
        f"- Adapter id: `{config.adapter_id or config.runtime_id}`",
        f"- Stage target: `{config.stage_target}`",
        f"- Workflow start: `{config.workflow_stage_start or 'default'}`",
        f"- Workflow end: `{config.workflow_stage_end or config.stage_target}`",
        f"- Resource/contracts root: `{config.resource_root or 'not recorded'}`",
        f"- Repository commit: `{config.repository_git_sha or 'not recorded'}`",
        f"- Resource revision: `{config.resource_revision or 'not recorded'}`",
        "",
        "## Baseline",
        "",
        f"- Baseline id: `{config.baseline_id}`",
        f"- Baseline label: {config.baseline_label}",
        "",
        "## Prompt pack provenance",
        "",
    ]
    if config.prompt_pack_provenance:
        for entry in config.prompt_pack_provenance:
            lines.append(f"- `{entry.path}` sha256 `{entry.sha256}`")
    else:
        lines.append("- No prompt pack provenance recorded.")
    lines.extend(
        [
            "",
            "## Launch notes",
            "",
            "- Review and edit this configuration before launch.",
            "- Launch must allocate a new run identity; do not resume the source run.",
            "",
        ]
    )
    return "\n".join(lines)


def _persist_follow_up_lineage(
    *,
    workspace_root: Path,
    new_work_item: str,
    source_work_item: str,
    source_run_id: str,
) -> None:
    metadata_path = work_item_metadata_path(root=workspace_root, work_item=new_work_item)
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Work item metadata must be a JSON object: {metadata_path.as_posix()}.")
    lineage = payload.get("lineage")
    if not isinstance(lineage, dict):
        lineage = {}
    lineage.update(
        {
            "source_work_item_id": source_work_item,
            "source_run_id": source_run_id,
        }
    )
    payload["lineage"] = lineage
    metadata_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _persist_clone_lineage(
    *,
    workspace_root: Path,
    new_work_item: str,
    source_work_item: str,
    source_run_id: str,
    baseline_id: str,
    baseline_label: str,
) -> None:
    metadata_path = work_item_metadata_path(root=workspace_root, work_item=new_work_item)
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Work item metadata must be a JSON object: {metadata_path.as_posix()}.")
    lineage = payload.get("lineage")
    if not isinstance(lineage, dict):
        lineage = {}
    lineage.update(
        {
            "source_work_item_id": source_work_item,
            "source_run_id": source_run_id,
            "baseline_id": baseline_id,
            "baseline_label": baseline_label,
        }
    )
    payload["lineage"] = lineage
    metadata_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "CloneFlowDraftConfig",
    "CloneFlowDraftRequest",
    "CloneFlowDraftResult",
    "ClonePromptPackReference",
    "FollowUpDraftRequest",
    "FollowUpDraftResult",
    "FollowUpSourceSelection",
    "NextFlowLaunchPreflightCheck",
    "NextFlowLaunchPreflightRequest",
    "NextFlowLaunchPreflightResult",
    "create_clone_flow_draft",
    "create_follow_up_work_item_draft",
    "validate_next_flow_launch_preflight",
]
