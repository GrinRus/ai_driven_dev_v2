from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.core.run_inspection import resolve_run_metadata_summary
from aidd.core.run_store import run_manifest_path
from aidd.core.stages import STAGES


@dataclass(frozen=True, slots=True)
class RunAccountabilityPrompt:
    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class RunAccountabilityStage:
    stage: str
    status: str
    attempt_count: int
    updated_at_utc: str


@dataclass(frozen=True, slots=True)
class RunAccountabilityView:
    run_id: str
    work_item: str
    runtime_id: str
    adapter_id: str | None
    stage_target: str
    workflow_stage_start: str | None
    workflow_stage_end: str | None
    repository_git_sha: str | None
    resource_source: str | None
    resource_revision: str | None
    resource_root: str | None
    config_snapshot: dict[str, Any]
    prompt_pack_provenance: tuple[RunAccountabilityPrompt, ...]
    stage_graph: tuple[str, ...]
    stages: tuple[RunAccountabilityStage, ...]
    warnings: tuple[str, ...]


def _load_manifest(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> dict[str, Any]:
    path = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not path.exists():
        raise ValueError(f"Run manifest does not exist for run '{run_id}'.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Run manifest must be a JSON object for run '{run_id}'.")
    return payload


def resolve_run_accountability(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> RunAccountabilityView:
    manifest = _load_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    summary = resolve_run_metadata_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    raw_config = manifest.get("config_snapshot", {})
    config_snapshot = raw_config if isinstance(raw_config, dict) else {}
    prompts = tuple(
        RunAccountabilityPrompt(path=entry.path, sha256=entry.sha256)
        for entry in summary.prompt_pack_provenance
    )
    warnings: list[str] = []
    if not prompts:
        warnings.append(
            "Run manifest has no prompt-pack provenance; it may predate provenance capture."
        )
    if not summary.repository_git_sha:
        warnings.append("Run manifest does not record a repository Git SHA.")
    if not manifest.get("resource_root"):
        warnings.append("Run manifest does not record a resource root.")
    return RunAccountabilityView(
        run_id=summary.run_id,
        work_item=summary.work_item,
        runtime_id=summary.runtime_id,
        adapter_id=summary.adapter_id,
        stage_target=summary.stage_target,
        workflow_stage_start=summary.workflow_stage_start,
        workflow_stage_end=summary.workflow_stage_end,
        repository_git_sha=summary.repository_git_sha,
        resource_source=str(manifest.get("resource_source", "")).strip() or None,
        resource_revision=summary.resource_revision,
        resource_root=str(manifest.get("resource_root", "")).strip() or None,
        config_snapshot=config_snapshot,
        prompt_pack_provenance=prompts,
        stage_graph=STAGES,
        stages=tuple(
            RunAccountabilityStage(
                stage=stage.stage,
                status=stage.status,
                attempt_count=stage.attempt_count,
                updated_at_utc=stage.updated_at_utc,
            )
            for stage in summary.stages
        ),
        warnings=tuple(warnings),
    )


__all__ = [
    "RunAccountabilityPrompt",
    "RunAccountabilityStage",
    "RunAccountabilityView",
    "resolve_run_accountability",
]
