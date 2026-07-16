from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.core.run_inspection import resolve_run_metadata_summary
from aidd.core.run_lookup import latest_attempt_number
from aidd.core.run_store import load_attempt_artifact_index, run_manifest_path
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
class RunAccountabilityAttempt:
    stage: str
    attempt_number: int
    attempt_mode: str
    prompt_pack_provenance: tuple[RunAccountabilityPrompt, ...]


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
    attempts: tuple[RunAccountabilityAttempt, ...]
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
    warnings: list[str] = []
    attempts: list[RunAccountabilityAttempt] = []
    aggregate_entries: list[RunAccountabilityPrompt] = []
    aggregate_seen: set[tuple[str, str]] = set()
    for stage in STAGES:
        attempt_count = latest_attempt_number(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if attempt_count is None:
            continue
        for attempt_number in range(1, attempt_count + 1):
            load_failed = False
            try:
                index = load_attempt_artifact_index(
                    workspace_root=workspace_root,
                    work_item=work_item,
                    run_id=run_id,
                    stage=stage,
                    attempt_number=attempt_number,
                )
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                index = None
                load_failed = True
                warnings.append(
                    f"Attempt evidence is malformed for {stage} attempt {attempt_number}: "
                    f"{type(exc).__name__}."
                )
            attempt_prompts = tuple(
                RunAccountabilityPrompt(path=entry.path, sha256=entry.sha256)
                for entry in (() if index is None else index.prompt_pack_provenance)
            )
            attempt_mode = (
                "unknown" if index is None or index.attempt_mode is None else index.attempt_mode
            )
            if index is None and not load_failed:
                warnings.append(
                    f"Attempt artifact index is missing for {stage} attempt {attempt_number}."
                )
            elif index is not None and index.attempt_mode is None:
                warnings.append(
                    f"Attempt mode is missing for legacy {stage} attempt {attempt_number}."
                )
            attempts.append(
                RunAccountabilityAttempt(
                    stage=stage,
                    attempt_number=attempt_number,
                    attempt_mode=attempt_mode,
                    prompt_pack_provenance=attempt_prompts,
                )
            )
            for entry in attempt_prompts:
                identity = (entry.path, entry.sha256)
                if identity not in aggregate_seen:
                    aggregate_seen.add(identity)
                    aggregate_entries.append(entry)

    if attempts:
        prompts = tuple(aggregate_entries)
    else:
        prompts = tuple(
            RunAccountabilityPrompt(path=entry.path, sha256=entry.sha256)
            for entry in summary.prompt_pack_provenance
        )
    if not attempts and prompts:
        warnings.append(
            "Attempt-level prompt provenance is unavailable; using run-manifest fallback."
        )
    if attempts and not prompts:
        warnings.append("Attempt-level prompt provenance contains no usable prompt entries.")
    elif not prompts:
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
        attempts=tuple(attempts),
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
    "RunAccountabilityAttempt",
    "RunAccountabilityStage",
    "RunAccountabilityView",
    "resolve_run_accountability",
]
