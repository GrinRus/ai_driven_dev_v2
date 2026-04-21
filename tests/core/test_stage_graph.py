from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aidd.core.run_store import create_run_manifest, persist_stage_status
from aidd.core.stage_graph import (
    StageAdvancementSummary,
    StageDependencyResolutionError,
    evaluate_stage_eligibility,
    resolve_stage_dependencies,
    resolve_stage_dependency_graph,
    select_next_runnable_stage,
    summarize_workflow_advancement,
)
from aidd.core.stages import STAGES, stage_index
from aidd.core.state_machine import StageState


def _copy_contract_workspace(tmp_path: Path) -> Path:
    shutil.copytree(Path("contracts"), tmp_path / "contracts")
    shutil.copytree(Path("prompt-packs"), tmp_path / "prompt-packs")
    return tmp_path / "contracts" / "stages"


def _summary_by_stage(
    workflow_summaries: tuple[StageAdvancementSummary, ...],
) -> dict[str, StageAdvancementSummary]:
    return {summary.stage: summary for summary in workflow_summaries}


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


def test_select_next_runnable_stage_returns_first_stage_for_new_run(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )

    assert (
        select_next_runnable_stage(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
        )
        == "idea"
    )


def test_select_next_runnable_stage_skips_completed_stages(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="idea",
        status=StageState.SUCCEEDED.value,
    )

    assert (
        select_next_runnable_stage(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
        )
        == "research"
    )


def test_select_next_runnable_stage_prefers_repair_needed_stage(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
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
        status=StageState.REPAIR_NEEDED.value,
    )

    assert (
        select_next_runnable_stage(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
        )
        == "research"
    )


def test_select_next_runnable_stage_returns_none_when_upstream_is_blocked(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="idea",
        status=StageState.BLOCKED.value,
    )

    assert (
        select_next_runnable_stage(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
        )
        is None
    )


def test_select_next_runnable_stage_returns_none_when_upstream_failed(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="idea",
        status=StageState.FAILED.value,
    )

    assert (
        select_next_runnable_stage(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
        )
        is None
    )


def test_summarize_workflow_advancement_explains_runnable_and_missing_cases(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )

    summaries = summarize_workflow_advancement(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
    )
    by_stage = _summary_by_stage(summaries)

    assert by_stage["idea"].can_run is True
    assert by_stage["idea"].reason == "next runnable stage"
    assert by_stage["research"].can_run is False
    assert by_stage["research"].reason == "missing prerequisites: idea"


def test_summarize_workflow_advancement_explains_blocked_and_blocked_upstream(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="idea",
        status=StageState.BLOCKED.value,
    )

    summaries = summarize_workflow_advancement(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
    )
    by_stage = _summary_by_stage(summaries)

    assert by_stage["idea"].reason == "stage is blocked"
    assert by_stage["research"].reason == "blocked upstream stages: idea"


def test_summarize_workflow_advancement_explains_failed_and_failed_upstream(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
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
        status=StageState.FAILED.value,
    )

    summaries = summarize_workflow_advancement(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
    )
    by_stage = _summary_by_stage(summaries)

    assert by_stage["research"].reason == "stage has failed"
    assert by_stage["plan"].reason == "failed upstream stages: research"


def test_evaluate_stage_eligibility_handles_branching_dependencies(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="idea",
        status=StageState.SUCCEEDED.value,
    )

    eligibility = evaluate_stage_eligibility(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert eligibility.dependencies == ("idea", "research")
    assert eligibility.missing_prerequisites == ("research",)
    assert eligibility.blocked_upstream_stages == ()
    assert eligibility.failed_upstream_stages == ()
    assert eligibility.is_eligible is False


def test_select_next_runnable_stage_skips_completed_chain(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )
    for stage in ("idea", "research"):
        persist_stage_status(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage=stage,
            status=StageState.SUCCEEDED.value,
        )

    assert (
        select_next_runnable_stage(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
        )
        == "plan"
    )


def test_summarize_workflow_advancement_keeps_blocked_upstream_reason_for_downstream(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="idea",
        status=StageState.BLOCKED.value,
    )

    summaries = summarize_workflow_advancement(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
    )
    by_stage = _summary_by_stage(summaries)

    assert by_stage["plan"].blocked_upstream_stages == ("idea",)
    assert by_stage["plan"].reason == (
        "missing prerequisites: research; blocked upstream stages: idea"
    )
