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


def stage_graph() -> tuple[str, ...]:
    return STAGES


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
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> str | None:
    for stage in stage_graph():
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
