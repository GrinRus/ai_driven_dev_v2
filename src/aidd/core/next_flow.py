from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from aidd.core.workspace import (
    WorkItemContextSeedResult,
    init_workspace,
    seed_work_item_context,
    work_item_context_root,
    work_item_metadata_path,
)

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
    source_path: str
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
        source_artifact_paths=tuple(selection.source_path for selection in normalized_selections),
    )


def _required_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"Follow-up draft {field_name} is required.")
    return normalized


def _normalize_selection(
    *,
    workspace_root: Path,
    selection: FollowUpSourceSelection,
) -> FollowUpSourceSelection:
    kind = _required_text(selection.kind, field_name="selection kind")
    if kind not in _SUPPORTED_FOLLOW_UP_SOURCE_KINDS:
        supported = ", ".join(sorted(_SUPPORTED_FOLLOW_UP_SOURCE_KINDS))
        raise ValueError(f"Unsupported follow-up source kind '{kind}'. Supported: {supported}.")
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


def _workspace_relative_source_path(*, workspace_root: Path, source_path: str) -> str:
    relative_path = Path(_required_text(source_path, field_name="selection source_path"))
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
                f"- Source artifact: `{selection.source_path}`",
            ]
        )
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


__all__ = [
    "FollowUpDraftRequest",
    "FollowUpDraftResult",
    "FollowUpSourceSelection",
    "create_follow_up_work_item_draft",
]
