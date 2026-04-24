from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.core.run_store import load_stage_metadata
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT, load_all_stage_manifests
from aidd.core.stages import STAGES, is_valid_stage, stage_index
from aidd.core.state_machine import StageState


class StageDependencyResolutionError(ValueError):
    """Raised when a stage declares an invalid upstream dependency."""


_RUNNABLE_STAGE_STATUSES = frozenset({StageState.PENDING.value, StageState.REPAIR_NEEDED.value})


@dataclass(frozen=True, slots=True)
class StageEligibility:
    stage: str
    dependencies: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    blocked_upstream_stages: tuple[str, ...]
    failed_upstream_stages: tuple[str, ...]

    @property
    def is_eligible(self) -> bool:
        return not (
            self.missing_prerequisites
            or self.blocked_upstream_stages
            or self.failed_upstream_stages
        )


@dataclass(frozen=True, slots=True)
class StageAdvancementSummary:
    stage: str
    current_status: str | None
    can_run: bool
    reason: str
    dependencies: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    blocked_upstream_stages: tuple[str, ...]
    failed_upstream_stages: tuple[str, ...]


def stage_graph() -> tuple[str, ...]:
    return STAGES


def _normalize_stage_bounds(
    *,
    stage_start: str | None,
    stage_end: str | None,
) -> tuple[int, int]:
    normalized_start = stage_start or STAGES[0]
    normalized_end = stage_end or STAGES[-1]
    if normalized_start not in STAGES:
        raise ValueError(f"Unknown stage_start '{normalized_start}'.")
    if normalized_end not in STAGES:
        raise ValueError(f"Unknown stage_end '{normalized_end}'.")
    start_index = stage_index(normalized_start)
    end_index = stage_index(normalized_end)
    if start_index > end_index:
        raise ValueError(
            f"stage_start '{normalized_start}' must not come after stage_end '{normalized_end}'."
        )
    return start_index, end_index


def bounded_stage_graph(
    *,
    stage_start: str | None = None,
    stage_end: str | None = None,
) -> tuple[str, ...]:
    start_index, end_index = _normalize_stage_bounds(
        stage_start=stage_start,
        stage_end=stage_end,
    )
    return STAGES[start_index : end_index + 1]


def _extract_upstream_stage(declaration_path: str) -> str | None:
    parts = Path(declaration_path).parts
    if len(parts) < 3:
        return None
    if parts[0] != ".." or parts[2] != "output":
        return None
    return parts[1]


def _resolve_manifest_dependencies(stage: str, required_inputs: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    dependencies: list[str] = []

    for declaration in required_inputs:
        upstream_stage = _extract_upstream_stage(declaration)
        if upstream_stage is None:
            continue
        if not is_valid_stage(upstream_stage):
            raise StageDependencyResolutionError(
                f"Unknown upstream stage '{upstream_stage}' declared by '{stage}'."
            )
        if upstream_stage == stage:
            raise StageDependencyResolutionError(
                f"Stage '{stage}' cannot declare itself as an upstream dependency."
            )
        if stage_index(upstream_stage) >= stage_index(stage):
            raise StageDependencyResolutionError(
                f"Stage '{stage}' has non-upstream dependency '{upstream_stage}'."
            )
        if upstream_stage not in seen:
            seen.add(upstream_stage)
            dependencies.append(upstream_stage)

    return tuple(dependencies)


def resolve_stage_dependencies(
    stage: str,
    *,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[str, ...]:
    manifests = load_all_stage_manifests(contracts_root=contracts_root)
    if stage not in manifests:
        raise StageDependencyResolutionError(f"Unknown stage: {stage}")
    return _resolve_manifest_dependencies(stage, manifests[stage].required_input_paths)


def resolve_stage_dependency_graph(
    *,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> dict[str, tuple[str, ...]]:
    manifests = load_all_stage_manifests(contracts_root=contracts_root)
    return {
        stage: _resolve_manifest_dependencies(stage, manifest.required_input_paths)
        for stage, manifest in manifests.items()
    }


def evaluate_stage_eligibility(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> StageEligibility:
    dependencies = resolve_stage_dependencies(stage, contracts_root=contracts_root)
    missing: list[str] = []
    blocked: list[str] = []
    failed: list[str] = []

    for dependency in dependencies:
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=dependency,
        )
        if metadata is None:
            missing.append(dependency)
            continue

        normalized_status = metadata.status.strip().lower()
        if normalized_status == StageState.SUCCEEDED.value:
            continue
        if normalized_status == StageState.BLOCKED.value:
            blocked.append(dependency)
            continue
        if normalized_status == StageState.FAILED.value:
            failed.append(dependency)
            continue
        missing.append(dependency)

    return StageEligibility(
        stage=stage,
        dependencies=dependencies,
        missing_prerequisites=tuple(missing),
        blocked_upstream_stages=tuple(blocked),
        failed_upstream_stages=tuple(failed),
    )


def _can_attempt_stage(status: str | None) -> bool:
    if status is None:
        return True
    normalized = status.strip().lower()
    if normalized == StageState.SUCCEEDED.value:
        return False
    return normalized in _RUNNABLE_STAGE_STATUSES


def select_next_runnable_stage(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage_start: str | None = None,
    stage_end: str | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> str | None:
    for stage in bounded_stage_graph(stage_start=stage_start, stage_end=stage_end):
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if not _can_attempt_stage(metadata.status if metadata else None):
            continue

        eligibility = evaluate_stage_eligibility(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            contracts_root=contracts_root,
        )
        if eligibility.is_eligible:
            return stage

    return None


def _summarize_eligibility_blockers(eligibility: StageEligibility) -> str:
    reasons: list[str] = []
    if eligibility.missing_prerequisites:
        reasons.append(
            "missing prerequisites: " + ", ".join(eligibility.missing_prerequisites)
        )
    if eligibility.blocked_upstream_stages:
        reasons.append(
            "blocked upstream stages: " + ", ".join(eligibility.blocked_upstream_stages)
        )
    if eligibility.failed_upstream_stages:
        reasons.append(
            "failed upstream stages: " + ", ".join(eligibility.failed_upstream_stages)
        )
    return "; ".join(reasons)


def summarize_workflow_advancement(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage_start: str | None = None,
    stage_end: str | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[StageAdvancementSummary, ...]:
    next_runnable = select_next_runnable_stage(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage_start=stage_start,
        stage_end=stage_end,
        contracts_root=contracts_root,
    )
    summaries: list[StageAdvancementSummary] = []

    for stage in bounded_stage_graph(stage_start=stage_start, stage_end=stage_end):
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        current_status = metadata.status.strip().lower() if metadata is not None else None
        eligibility = evaluate_stage_eligibility(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            contracts_root=contracts_root,
        )

        can_run = False
        reason = "not runnable"
        if current_status == StageState.SUCCEEDED.value:
            reason = "already completed"
        elif current_status == StageState.BLOCKED.value:
            reason = "stage is blocked"
        elif current_status == StageState.FAILED.value:
            reason = "stage has failed"
        elif not eligibility.is_eligible:
            reason = _summarize_eligibility_blockers(eligibility)
        elif next_runnable == stage:
            can_run = True
            reason = "next runnable stage"
        elif next_runnable is None:
            reason = "no runnable stage available"
        else:
            reason = f"waiting for earlier runnable stage '{next_runnable}'"

        summaries.append(
            StageAdvancementSummary(
                stage=stage,
                current_status=current_status,
                can_run=can_run,
                reason=reason,
                dependencies=eligibility.dependencies,
                missing_prerequisites=eligibility.missing_prerequisites,
                blocked_upstream_stages=eligibility.blocked_upstream_stages,
                failed_upstream_stages=eligibility.failed_upstream_stages,
            )
        )

    return tuple(summaries)
