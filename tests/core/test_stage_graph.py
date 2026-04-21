from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aidd.core.run_store import create_run_manifest, persist_stage_status
from aidd.core.stage_graph import (
    StageDependencyResolutionError,
    evaluate_stage_eligibility,
    resolve_stage_dependencies,
    resolve_stage_dependency_graph,
)
from aidd.core.stages import STAGES, stage_index
from aidd.core.state_machine import StageState


def _copy_contract_workspace(tmp_path: Path) -> Path:
    shutil.copytree(Path("contracts"), tmp_path / "contracts")
    shutil.copytree(Path("prompt-packs"), tmp_path / "prompt-packs")
    return tmp_path / "contracts" / "stages"


def test_resolve_stage_dependencies_uses_manifest_declared_upstream_stages() -> None:
    assert resolve_stage_dependencies("idea") == ()
    assert resolve_stage_dependencies("plan") == ("idea", "research")
    assert resolve_stage_dependencies("review-spec") == ("plan",)
    assert resolve_stage_dependencies("implement") == ("tasklist",)


def test_resolve_stage_dependency_graph_returns_all_stage_dependency_entries() -> None:
    graph = resolve_stage_dependency_graph()

    assert tuple(graph) == STAGES
    for stage, dependencies in graph.items():
        for dependency in dependencies:
            assert stage_index(dependency) < stage_index(stage)


def test_resolve_stage_dependencies_rejects_unknown_upstream_stage(tmp_path: Path) -> None:
    contracts_root = _copy_contract_workspace(tmp_path)
    plan_contract = contracts_root / "plan.md"
    plan_contract.write_text(
        plan_contract.read_text(encoding="utf-8").replace(
            "../research/output/research-notes.md",
            "../unknown/output/research-notes.md",
        ),
        encoding="utf-8",
    )

    with pytest.raises(StageDependencyResolutionError, match="Unknown upstream stage"):
        resolve_stage_dependencies("plan", contracts_root=contracts_root)


def test_evaluate_stage_eligibility_reports_missing_prerequisites(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    eligibility = evaluate_stage_eligibility(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert eligibility.dependencies == ("idea", "research")
    assert eligibility.missing_prerequisites == ("idea", "research")
    assert eligibility.blocked_upstream_stages == ()
    assert eligibility.failed_upstream_stages == ()
    assert eligibility.is_eligible is False


def test_evaluate_stage_eligibility_reports_blocked_and_failed_upstream(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="idea",
        status=StageState.BLOCKED.value,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="research",
        status=StageState.FAILED.value,
    )

    eligibility = evaluate_stage_eligibility(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert eligibility.missing_prerequisites == ()
    assert eligibility.blocked_upstream_stages == ("idea",)
    assert eligibility.failed_upstream_stages == ("research",)
    assert eligibility.is_eligible is False


def test_evaluate_stage_eligibility_accepts_satisfied_dependencies(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="idea",
        status=StageState.SUCCEEDED.value,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="research",
        status=StageState.SUCCEEDED.value,
    )

    eligibility = evaluate_stage_eligibility(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert eligibility.missing_prerequisites == ()
    assert eligibility.blocked_upstream_stages == ()
    assert eligibility.failed_upstream_stages == ()
    assert eligibility.is_eligible is True
