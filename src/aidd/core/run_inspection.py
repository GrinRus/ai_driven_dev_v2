from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.core.run_archive import resolve_run_archive_decision
from aidd.core.run_lookup import (
    latest_attempt_number,
    latest_run_id,
    resolve_attempt_artifact_paths,
)
from aidd.core.run_store import (
    load_run_manifest,
    load_stage_metadata,
)
from aidd.core.run_store import run_stages_root as run_stage_roots_path
from aidd.core.workspace import work_item_metadata_path
from aidd.validators.protocol import parse_validator_report


@dataclass(frozen=True, slots=True)
class StageResultSummary:
    run_id: str
    stage: str
    runtime_id: str
    final_state: str
    attempt_count: int
    validator_pass_count: int
    validator_fail_count: int
    validator_report_path: str
    log_artifact_paths: tuple[str, ...]
    document_artifact_paths: tuple[str, ...]
    repair_output_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RunStageMetadataSummary:
    stage: str
    status: str
    updated_at_utc: str
    attempt_count: int


@dataclass(frozen=True, slots=True)
class PromptPackProvenance:
    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class ChildWorkItemCandidateSummary:
    work_item_id: str
    label: str | None
    relationship: str | None
    source_run_id: str | None


@dataclass(frozen=True, slots=True)
class RunLineageSummary:
    source_run_id: str | None
    source_work_item_id: str | None
    baseline_id: str | None
    baseline_label: str | None
    child_work_item_candidates: tuple[ChildWorkItemCandidateSummary, ...]


@dataclass(frozen=True, slots=True)
class RunArchiveSummary:
    archived: bool
    archived_at_utc: str | None
    reason: str | None
    source: str | None


@dataclass(frozen=True, slots=True)
class RunMetadataSummary:
    run_id: str
    work_item: str
    runtime_id: str
    adapter_id: str | None
    stage_target: str
    workflow_stage_start: str | None
    workflow_stage_end: str | None
    repository_git_sha: str | None
    resource_revision: str | None
    prompt_pack_provenance: tuple[PromptPackProvenance, ...]
    lineage: RunLineageSummary
    archive: RunArchiveSummary
    created_at_utc: str
    updated_at_utc: str
    stages: tuple[RunStageMetadataSummary, ...]
    runtime_permission_policy: str | None = None


@dataclass(frozen=True, slots=True)
class RunLogSummary:
    run_id: str
    stage: str
    attempt_number: int
    runtime_log_path: Path


@dataclass(frozen=True, slots=True)
class RunArtifactsSummary:
    run_id: str
    stage: str
    attempt_number: int
    documents: dict[str, str]
    logs: dict[str, str]


def _load_manifest_payload(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> dict[str, Any]:
    payload = load_run_manifest(workspace_root, work_item, run_id)
    if payload is None:
        raise ValueError(f"Run manifest is missing for work item '{work_item}', run '{run_id}'.")
    return payload


def _load_work_item_payload(
    *,
    workspace_root: Path,
    work_item: str,
) -> dict[str, Any]:
    metadata_path = work_item_metadata_path(root=workspace_root, work_item=work_item)
    if not metadata_path.exists():
        return {}
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_selected_run_id(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str | None,
) -> str:
    if run_id is not None:
        return run_id

    selected = latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")
    return selected


def _optional_lineage_value(payload: dict[str, Any], key: str) -> str | None:
    normalized = str(payload.get(key, "")).strip()
    return normalized or None


def _lineage_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    lineage = payload.get("lineage")
    return lineage if isinstance(lineage, dict) else {}


def _child_work_item_candidates(
    payload: dict[str, Any],
) -> tuple[ChildWorkItemCandidateSummary, ...]:
    raw_candidates = payload.get("child_work_item_candidates")
    if not isinstance(raw_candidates, list):
        return ()

    candidates: list[ChildWorkItemCandidateSummary] = []
    for candidate in raw_candidates:
        if not isinstance(candidate, dict):
            continue
        work_item_id = _optional_lineage_value(candidate, "work_item_id")
        if work_item_id is None:
            continue
        candidates.append(
            ChildWorkItemCandidateSummary(
                work_item_id=work_item_id,
                label=_optional_lineage_value(candidate, "label"),
                relationship=_optional_lineage_value(candidate, "relationship"),
                source_run_id=_optional_lineage_value(candidate, "source_run_id"),
            )
        )
    return tuple(candidates)


def _lineage_summary(
    *,
    manifest_payload: dict[str, Any],
    work_item_payload: dict[str, Any],
) -> RunLineageSummary:
    manifest_lineage = _lineage_mapping(manifest_payload)
    work_item_lineage = _lineage_mapping(work_item_payload)
    child_work_item_candidates = _child_work_item_candidates(manifest_lineage)
    if not child_work_item_candidates:
        child_work_item_candidates = _child_work_item_candidates(work_item_lineage)
    return RunLineageSummary(
        source_run_id=(
            _optional_lineage_value(manifest_lineage, "source_run_id")
            or _optional_lineage_value(work_item_lineage, "source_run_id")
        ),
        source_work_item_id=(
            _optional_lineage_value(manifest_lineage, "source_work_item_id")
            or _optional_lineage_value(work_item_lineage, "source_work_item_id")
        ),
        baseline_id=(
            _optional_lineage_value(manifest_lineage, "baseline_id")
            or _optional_lineage_value(work_item_lineage, "baseline_id")
        ),
        baseline_label=(
            _optional_lineage_value(manifest_lineage, "baseline_label")
            or _optional_lineage_value(work_item_lineage, "baseline_label")
        ),
        child_work_item_candidates=child_work_item_candidates,
    )


def _archive_summary(
    *, workspace_root: Path, work_item: str, run_id: str, manifest_payload: dict[str, Any]
) -> RunArchiveSummary:
    archive = resolve_run_archive_decision(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        manifest_payload=manifest_payload,
    )
    if archive is None:
        return RunArchiveSummary(
            archived=False,
            archived_at_utc=None,
            reason=None,
            source=None,
        )
    return RunArchiveSummary(
        archived=True,
        archived_at_utc=archive.archived_at_utc,
        reason=archive.reason,
        source=archive.source,
    )


def resolve_run_metadata_summary(
    workspace_root: Path,
    work_item: str,
    *,
    run_id: str | None = None,
) -> RunMetadataSummary:
    selected_run_id = _resolve_selected_run_id(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )

    manifest_payload = _load_manifest_payload(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
    )
    work_item_payload = _load_work_item_payload(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    runtime_id = str(manifest_payload["runtime_id"]).strip()
    stage_target = str(manifest_payload["stage_target"]).strip()
    workflow_bounds = manifest_payload["workflow_bounds"]
    workflow_stage_start = workflow_bounds["start"]
    workflow_stage_end = workflow_bounds["end"]
    repository_git_sha = manifest_payload["repository_git_sha"]
    adapter_id = str(manifest_payload["adapter_id"]).strip()
    resource_revision = manifest_payload["resource_revision"]
    config_snapshot = manifest_payload.get("config_snapshot")
    raw_runtime_permission_policy = (
        config_snapshot.get("runtime_permission_policy")
        if isinstance(config_snapshot, dict)
        else None
    )
    runtime_permission_policy = (
        raw_runtime_permission_policy.strip()
        if isinstance(raw_runtime_permission_policy, str) and raw_runtime_permission_policy.strip()
        else None
    )
    prompt_pack_provenance = [
        PromptPackProvenance(path=entry["path"], sha256=entry["sha256"])
        for entry in manifest_payload["prompt_pack_provenance"]
    ]
    created_at_utc = str(manifest_payload["created_at_utc"]).strip()
    updated_at_utc = str(manifest_payload["updated_at_utc"]).strip()

    stage_roots = run_stage_roots_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
    )
    stage_summaries: list[RunStageMetadataSummary] = []
    if stage_roots.exists():
        for child in sorted(stage_roots.iterdir(), key=lambda path: path.name):
            if not child.is_dir():
                continue
            stage_name = child.name
            stage_metadata = load_stage_metadata(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=selected_run_id,
                stage=stage_name,
            )
            if stage_metadata is None:
                continue
            attempts = latest_attempt_number(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=selected_run_id,
                stage=stage_name,
            )
            stage_summaries.append(
                RunStageMetadataSummary(
                    stage=stage_name,
                    status=stage_metadata.status,
                    updated_at_utc=stage_metadata.updated_at_utc,
                    attempt_count=attempts or 0,
                )
            )

    return RunMetadataSummary(
        run_id=selected_run_id,
        work_item=work_item,
        runtime_id=runtime_id,
        adapter_id=adapter_id,
        stage_target=stage_target,
        workflow_stage_start=workflow_stage_start,
        workflow_stage_end=workflow_stage_end,
        repository_git_sha=repository_git_sha,
        resource_revision=resource_revision,
        prompt_pack_provenance=tuple(prompt_pack_provenance),
        lineage=_lineage_summary(
            manifest_payload=manifest_payload,
            work_item_payload=work_item_payload,
        ),
        archive=_archive_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=selected_run_id,
            manifest_payload=manifest_payload,
        ),
        created_at_utc=created_at_utc,
        updated_at_utc=updated_at_utc,
        stages=tuple(stage_summaries),
        runtime_permission_policy=runtime_permission_policy,
    )


def resolve_run_log_summary(
    workspace_root: Path,
    work_item: str,
    stage: str,
    *,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunLogSummary:
    selected_run_id = _resolve_selected_run_id(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )

    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )

    artifact_paths = resolve_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_paths is None:
        raise ValueError(
            f"Artifact index is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    runtime_log_path = artifact_paths.logs.get("runtime_log")
    if runtime_log_path is None:
        raise ValueError(
            "Runtime log path is missing in artifact index for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}', attempt {selected_attempt}."
        )
    if not runtime_log_path.exists():
        raise ValueError(f"Runtime log file does not exist: {runtime_log_path.as_posix()}.")

    return RunLogSummary(
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        runtime_log_path=runtime_log_path,
    )


def resolve_run_artifacts_summary(
    workspace_root: Path,
    work_item: str,
    stage: str,
    *,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunArtifactsSummary:
    selected_run_id = _resolve_selected_run_id(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )

    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )

    artifact_paths = resolve_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_paths is None:
        raise ValueError(
            f"Artifact index is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    return RunArtifactsSummary(
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        documents={
            key: _workspace_relative_path(workspace_root, path)
            for key, path in sorted(artifact_paths.documents.items())
        },
        logs={
            key: _workspace_relative_path(workspace_root, path)
            for key, path in sorted(artifact_paths.logs.items())
        },
    )


def _workspace_relative_path(workspace_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _validator_counts_from_history(*, outcomes: tuple[str, ...]) -> tuple[int, int]:
    pass_count = 0
    fail_count = 0
    for outcome in outcomes:
        normalized = outcome.strip().lower()
        if "fail" in normalized:
            fail_count += 1
            continue
        if "pass" in normalized or "succeed" in normalized:
            pass_count += 1
    return pass_count, fail_count


def _validator_verdict_from_report(report_path: Path) -> str | None:
    if not report_path.exists():
        return None
    return parse_validator_report(report_path.read_text(encoding="utf-8")).verdict


def _normalize_repair_output_paths(
    *,
    workspace_root: Path,
    repair_history_paths: tuple[str, ...],
    stage_root: Path,
) -> tuple[str, ...]:
    collected = {path.strip() for path in repair_history_paths if path.strip()}
    repair_brief = stage_root / "repair-brief.md"
    if repair_brief.exists():
        collected.add(_workspace_relative_path(workspace_root, repair_brief))
    return tuple(sorted(collected))


def resolve_stage_result_summary(
    workspace_root: Path,
    work_item: str,
    stage: str,
    *,
    run_id: str | None = None,
) -> StageResultSummary:
    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")

    stage_metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if stage_metadata is None:
        raise ValueError(
            f"Stage metadata is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}'."
        )

    attempts = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if attempts is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )

    stage_root = workspace_root / "workitems" / work_item / "stages" / stage
    validator_report = stage_root / "validator-report.md"
    verdict = _validator_verdict_from_report(validator_report)
    if verdict == "pass":
        pass_count = 1
        fail_count = 0
    elif verdict == "fail":
        pass_count = 0
        fail_count = 1
    else:
        pass_count, fail_count = _validator_counts_from_history(
            outcomes=tuple(entry.outcome for entry in stage_metadata.repair_history)
        )

    artifact_paths = resolve_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=attempts,
    )
    log_artifact_paths = (
        tuple(
            sorted(
                _workspace_relative_path(workspace_root, path)
                for path in artifact_paths.logs.values()
            )
        )
        if artifact_paths is not None
        else ()
    )
    document_artifact_paths = (
        tuple(
            sorted(
                _workspace_relative_path(workspace_root, path)
                for path in artifact_paths.documents.values()
            )
        )
        if artifact_paths is not None
        else ()
    )
    repair_output_paths = _normalize_repair_output_paths(
        workspace_root=workspace_root,
        repair_history_paths=tuple(
            entry.repair_brief_path or "" for entry in stage_metadata.repair_history
        ),
        stage_root=stage_root,
    )

    return StageResultSummary(
        run_id=selected_run_id,
        stage=stage,
        runtime_id=_load_manifest_payload(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=selected_run_id,
        )["runtime_id"],
        final_state=stage_metadata.status,
        attempt_count=attempts,
        validator_pass_count=pass_count,
        validator_fail_count=fail_count,
        validator_report_path=_workspace_relative_path(workspace_root, validator_report),
        log_artifact_paths=log_artifact_paths,
        document_artifact_paths=document_artifact_paths,
        repair_output_paths=repair_output_paths,
    )
