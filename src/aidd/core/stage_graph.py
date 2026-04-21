from __future__ import annotations

from pathlib import Path

from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT, load_all_stage_manifests
from aidd.core.stages import STAGES, is_valid_stage, stage_index


class StageDependencyResolutionError(ValueError):
    """Raised when a stage declares an invalid upstream dependency."""


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
