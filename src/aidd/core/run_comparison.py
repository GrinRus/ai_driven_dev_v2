from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from aidd.core.run_inspection import RunMetadataSummary, resolve_run_metadata_summary
from aidd.core.run_lookup import latest_attempt_number
from aidd.core.run_store import load_attempt_artifact_index, load_stage_metadata
from aidd.core.stages import STAGES

_MAX_COMPARISON_ARTIFACT_BYTES = 512 * 1024
_VALIDATOR_VERDICT_PATTERN = re.compile(
    r"(?im)^\s*-\s*Verdict:\s*`?([a-z][a-z0-9_-]*)`?"
)


@dataclass(frozen=True, slots=True)
class RunComparisonIdentity:
    run_id: str
    work_item: str
    runtime_id: str
    stage_target: str
    repository_git_sha: str | None
    resource_revision: str | None
    created_at_utc: str
    updated_at_utc: str


@dataclass(frozen=True, slots=True)
class RunComparisonPromptDelta:
    path: str
    baseline_sha256: str | None
    target_sha256: str | None
    status: str


@dataclass(frozen=True, slots=True)
class RunComparisonStageDelta:
    stage: str
    baseline_status: str | None
    target_status: str | None
    baseline_attempt_count: int | None
    target_attempt_count: int | None
    status: str


@dataclass(frozen=True, slots=True)
class RunComparisonArtifactDelta:
    stage: str
    kind: str
    key: str
    baseline_path: str | None
    target_path: str | None
    baseline_sha256: str | None
    target_sha256: str | None
    baseline_byte_size: int | None
    target_byte_size: int | None
    baseline_truncated: bool
    target_truncated: bool
    status: str


@dataclass(frozen=True, slots=True)
class RunComparisonValidatorDelta:
    stage: str
    baseline_verdict: str | None
    target_verdict: str | None
    baseline_path: str | None
    target_path: str | None
    status: str


@dataclass(frozen=True, slots=True)
class RunComparisonView:
    baseline: RunComparisonIdentity
    target: RunComparisonIdentity
    prompt_hash_deltas: tuple[RunComparisonPromptDelta, ...]
    stage_status_deltas: tuple[RunComparisonStageDelta, ...]
    artifact_hash_deltas: tuple[RunComparisonArtifactDelta, ...]
    validator_outcome_deltas: tuple[RunComparisonValidatorDelta, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ArtifactSnapshot:
    stage: str
    kind: str
    key: str
    path: str
    sha256: str | None
    byte_size: int | None
    truncated: bool
    validator_verdict: str | None = None


def _identity(summary: RunMetadataSummary) -> RunComparisonIdentity:
    return RunComparisonIdentity(
        run_id=summary.run_id,
        work_item=summary.work_item,
        runtime_id=summary.runtime_id,
        stage_target=summary.stage_target,
        repository_git_sha=summary.repository_git_sha,
        resource_revision=summary.resource_revision,
        created_at_utc=summary.created_at_utc,
        updated_at_utc=summary.updated_at_utc,
    )


def _delta_status(baseline: object | None, target: object | None) -> str:
    if baseline is None and target is None:
        return "same"
    if baseline is None:
        return "added"
    if target is None:
        return "removed"
    if baseline == target:
        return "same"
    return "changed"


def _append_warning(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def _prompt_deltas(
    baseline: RunMetadataSummary,
    target: RunMetadataSummary,
    warnings: list[str],
) -> tuple[RunComparisonPromptDelta, ...]:
    if not baseline.prompt_pack_provenance:
        _append_warning(
            warnings,
            f"Run '{baseline.run_id}' has no prompt-pack provenance; "
            "prompt deltas may be incomplete.",
        )
    if not target.prompt_pack_provenance:
        _append_warning(
            warnings,
            f"Run '{target.run_id}' has no prompt-pack provenance; "
            "prompt deltas may be incomplete.",
        )
    baseline_prompts = {
        entry.path: entry.sha256 for entry in baseline.prompt_pack_provenance
    }
    target_prompts = {entry.path: entry.sha256 for entry in target.prompt_pack_provenance}
    deltas: list[RunComparisonPromptDelta] = []
    for path in sorted(set(baseline_prompts) | set(target_prompts)):
        baseline_hash = baseline_prompts.get(path)
        target_hash = target_prompts.get(path)
        deltas.append(
            RunComparisonPromptDelta(
                path=path,
                baseline_sha256=baseline_hash,
                target_sha256=target_hash,
                status=_delta_status(baseline_hash, target_hash),
            )
        )
    return tuple(deltas)


def _stage_deltas(
    baseline: RunMetadataSummary,
    target: RunMetadataSummary,
) -> tuple[RunComparisonStageDelta, ...]:
    baseline_stages = {stage.stage: stage for stage in baseline.stages}
    target_stages = {stage.stage: stage for stage in target.stages}
    ordered_stages = [
        stage for stage in STAGES if stage in baseline_stages or stage in target_stages
    ]
    extra_stages = sorted((set(baseline_stages) | set(target_stages)) - set(STAGES))
    deltas: list[RunComparisonStageDelta] = []
    for stage in (*ordered_stages, *extra_stages):
        baseline_stage = baseline_stages.get(stage)
        target_stage = target_stages.get(stage)
        baseline_status = baseline_stage.status if baseline_stage is not None else None
        target_status = target_stage.status if target_stage is not None else None
        deltas.append(
            RunComparisonStageDelta(
                stage=stage,
                baseline_status=baseline_status,
                target_status=target_status,
                baseline_attempt_count=(
                    baseline_stage.attempt_count if baseline_stage is not None else None
                ),
                target_attempt_count=(
                    target_stage.attempt_count if target_stage is not None else None
                ),
                status=_delta_status(baseline_status, target_status),
            )
        )
    return tuple(deltas)


def _safe_workspace_file(
    *,
    workspace_root: Path,
    run_id: str,
    stage: str,
    key: str,
    relative_path: str,
    warnings: list[str],
) -> Path | None:
    normalized = Path(relative_path)
    if normalized.is_absolute() or ".." in normalized.parts:
        _append_warning(
            warnings,
            f"Run '{run_id}' artifact '{stage}:{key}' has an unsafe path and was skipped.",
        )
        return None
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved = (workspace_root / normalized).resolve(strict=False)
    if not resolved.is_relative_to(resolved_workspace):
        _append_warning(
            warnings,
            f"Run '{run_id}' artifact '{stage}:{key}' escapes the workspace and was skipped.",
        )
        return None
    return resolved


def _hash_workspace_artifact(
    *,
    workspace_root: Path,
    run_id: str,
    stage: str,
    key: str,
    relative_path: str,
    warnings: list[str],
) -> tuple[str | None, int | None, bool, str | None]:
    path = _safe_workspace_file(
        workspace_root=workspace_root,
        run_id=run_id,
        stage=stage,
        key=key,
        relative_path=relative_path,
        warnings=warnings,
    )
    if path is None:
        return None, None, False, None
    if not path.is_file():
        _append_warning(
            warnings,
            f"Run '{run_id}' artifact '{stage}:{key}' is missing at '{relative_path}'.",
        )
        return None, None, False, None
    byte_size = path.stat().st_size
    truncated = byte_size > _MAX_COMPARISON_ARTIFACT_BYTES
    with path.open("rb") as handle:
        data = handle.read(_MAX_COMPARISON_ARTIFACT_BYTES + 1)
    if truncated:
        data = data[:_MAX_COMPARISON_ARTIFACT_BYTES]
        _append_warning(
            warnings,
            f"Run '{run_id}' artifact '{stage}:{key}' was hashed with a bounded prefix.",
        )
    digest = hashlib.sha256(data).hexdigest()
    verdict: str | None = None
    if key == "validator_report":
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            _append_warning(
                warnings,
                f"Run '{run_id}' validator report for stage '{stage}' is not UTF-8.",
            )
        else:
            match = _VALIDATOR_VERDICT_PATTERN.search(text)
            if match is not None:
                verdict = match.group(1).lower()
    return digest, byte_size, truncated, verdict


def _missing_repair_brief_is_expected_without_repair_history(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    relative_path: str,
) -> bool:
    normalized = Path(relative_path)
    if normalized.is_absolute() or ".." in normalized.parts:
        return False
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved = (workspace_root / normalized).resolve(strict=False)
    if not resolved.is_relative_to(resolved_workspace) or resolved.is_file():
        return False
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    return metadata is not None and not metadata.repair_history


def _artifact_snapshots(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    warnings: list[str],
) -> dict[str, _ArtifactSnapshot]:
    snapshots: dict[str, _ArtifactSnapshot] = {}
    for stage in STAGES:
        attempt_number = latest_attempt_number(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if attempt_number is None:
            continue
        artifact_index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
        if artifact_index is None:
            _append_warning(
                warnings,
                f"Run '{run_id}' stage '{stage}' has no artifact index; "
                "artifact deltas may be incomplete.",
            )
            continue
        for kind, entries in (
            ("document", artifact_index.documents),
            ("log", artifact_index.logs),
        ):
            for key, relative_path in sorted(entries.items()):
                if (
                    key == "repair_brief"
                    and _missing_repair_brief_is_expected_without_repair_history(
                        workspace_root=workspace_root,
                        work_item=work_item,
                        run_id=run_id,
                        stage=stage,
                        relative_path=relative_path,
                    )
                ):
                    continue
                digest, byte_size, truncated, verdict = _hash_workspace_artifact(
                    workspace_root=workspace_root,
                    run_id=run_id,
                    stage=stage,
                    key=key,
                    relative_path=relative_path,
                    warnings=warnings,
                )
                snapshot_key = f"{stage}:{kind}:{key}"
                snapshots[snapshot_key] = _ArtifactSnapshot(
                    stage=stage,
                    kind=kind,
                    key=key,
                    path=relative_path,
                    sha256=digest,
                    byte_size=byte_size,
                    truncated=truncated,
                    validator_verdict=verdict if kind == "document" else None,
                )
    return snapshots


def _artifact_deltas(
    baseline: dict[str, _ArtifactSnapshot],
    target: dict[str, _ArtifactSnapshot],
) -> tuple[RunComparisonArtifactDelta, ...]:
    deltas: list[RunComparisonArtifactDelta] = []
    for key in sorted(set(baseline) | set(target)):
        baseline_snapshot = baseline.get(key)
        target_snapshot = target.get(key)
        identity = target_snapshot or baseline_snapshot
        assert identity is not None
        baseline_hash = baseline_snapshot.sha256 if baseline_snapshot is not None else None
        target_hash = target_snapshot.sha256 if target_snapshot is not None else None
        hash_status = _delta_status(baseline_hash, target_hash)
        path_status = _delta_status(
            baseline_snapshot.path if baseline_snapshot is not None else None,
            target_snapshot.path if target_snapshot is not None else None,
        )
        deltas.append(
            RunComparisonArtifactDelta(
                stage=identity.stage,
                kind=identity.kind,
                key=identity.key,
                baseline_path=baseline_snapshot.path if baseline_snapshot is not None else None,
                target_path=target_snapshot.path if target_snapshot is not None else None,
                baseline_sha256=baseline_hash,
                target_sha256=target_hash,
                baseline_byte_size=(
                    baseline_snapshot.byte_size if baseline_snapshot is not None else None
                ),
                target_byte_size=(
                    target_snapshot.byte_size if target_snapshot is not None else None
                ),
                baseline_truncated=(
                    baseline_snapshot.truncated if baseline_snapshot is not None else False
                ),
                target_truncated=(
                    target_snapshot.truncated if target_snapshot is not None else False
                ),
                status="changed" if path_status == "changed" else hash_status,
            )
        )
    return tuple(deltas)


def _validator_deltas(
    baseline: dict[str, _ArtifactSnapshot],
    target: dict[str, _ArtifactSnapshot],
) -> tuple[RunComparisonValidatorDelta, ...]:
    baseline_validators = {
        snapshot.stage: snapshot
        for snapshot in baseline.values()
        if snapshot.kind == "document" and snapshot.key == "validator_report"
    }
    target_validators = {
        snapshot.stage: snapshot
        for snapshot in target.values()
        if snapshot.kind == "document" and snapshot.key == "validator_report"
    }
    ordered_stages = [
        stage
        for stage in STAGES
        if stage in baseline_validators or stage in target_validators
    ]
    extra_stages = sorted(
        (set(baseline_validators) | set(target_validators)) - set(STAGES)
    )
    deltas: list[RunComparisonValidatorDelta] = []
    for stage in (*ordered_stages, *extra_stages):
        baseline_snapshot = baseline_validators.get(stage)
        target_snapshot = target_validators.get(stage)
        baseline_verdict = (
            baseline_snapshot.validator_verdict if baseline_snapshot is not None else None
        )
        target_verdict = (
            target_snapshot.validator_verdict if target_snapshot is not None else None
        )
        deltas.append(
            RunComparisonValidatorDelta(
                stage=stage,
                baseline_verdict=baseline_verdict,
                target_verdict=target_verdict,
                baseline_path=(
                    baseline_snapshot.path if baseline_snapshot is not None else None
                ),
                target_path=target_snapshot.path if target_snapshot is not None else None,
                status=_delta_status(baseline_verdict, target_verdict),
            )
        )
    return tuple(deltas)


def resolve_run_comparison(
    *,
    workspace_root: Path,
    work_item: str,
    baseline_run_id: str,
    target_run_id: str,
) -> RunComparisonView:
    baseline = resolve_run_metadata_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=baseline_run_id,
    )
    target = resolve_run_metadata_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=target_run_id,
    )
    warnings: list[str] = []
    if baseline.run_id == target.run_id:
        _append_warning(
            warnings,
            "Baseline and target run ids are identical; deltas should be all unchanged.",
        )

    prompt_deltas = _prompt_deltas(baseline, target, warnings)
    baseline_artifacts = _artifact_snapshots(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=baseline.run_id,
        warnings=warnings,
    )
    target_artifacts = _artifact_snapshots(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=target.run_id,
        warnings=warnings,
    )
    return RunComparisonView(
        baseline=_identity(baseline),
        target=_identity(target),
        prompt_hash_deltas=prompt_deltas,
        stage_status_deltas=_stage_deltas(baseline, target),
        artifact_hash_deltas=_artifact_deltas(baseline_artifacts, target_artifacts),
        validator_outcome_deltas=_validator_deltas(baseline_artifacts, target_artifacts),
        warnings=tuple(warnings),
    )


__all__ = [
    "RunComparisonArtifactDelta",
    "RunComparisonIdentity",
    "RunComparisonPromptDelta",
    "RunComparisonStageDelta",
    "RunComparisonValidatorDelta",
    "RunComparisonView",
    "resolve_run_comparison",
]
