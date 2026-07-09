from __future__ import annotations

from pathlib import Path

from aidd.harness.eval_preparation import select_authored_task
from aidd.harness.live_workspace_bootstrap import bootstrap_live_work_item
from aidd.harness.scenarios import (
    Scenario,
    ScenarioAuthoredTask,
    ScenarioCommandSteps,
    ScenarioFeatureSource,
    ScenarioLiveFlowConfig,
    ScenarioRepoSource,
    ScenarioRunConfig,
    load_scenario,
)


def _scenario(selected_task: ScenarioAuthoredTask) -> Scenario:
    return Scenario(
        scenario_id="AIDD-LIVE-BOOTSTRAP",
        scenario_class="live-full-flow",
        feature_size="medium",
        live_matrix_role="product-evaluation",
        automation_lane="manual",
        canonical_runtime="codex",
        task="exercise live workspace bootstrap",
        repo=ScenarioRepoSource(
            url="https://example.invalid/repo.git",
            default_branch=None,
            revision="abc123",
        ),
        setup=ScenarioCommandSteps(commands=tuple()),
        run=ScenarioRunConfig(
            stage_start="idea",
            stage_end="qa",
            runtime_targets=("codex",),
            patch_budget_files=None,
            timeout_minutes=240,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=("pytest -q",)),
        feature_source=ScenarioFeatureSource(
            mode="authored-task-pool",
            selection_policy="first-listed",
            tasks=(selected_task,),
            fixture_path=None,
            seed_id=None,
            summary=None,
        ),
        live_flow=ScenarioLiveFlowConfig(
            driver="stepwise-black-box",
            checkpoint_policy="after-each-step",
            answer_policy="agent-decides",
            frontend_checkpoints=True,
        ),
        runtime_targets=("codex",),
        is_live=True,
        raw={},
    )


def test_bootstrap_selected_task_preserves_authored_constraints_with_visible_request(
    tmp_path: Path,
) -> None:
    selected_task = ScenarioAuthoredTask(
        task_id="TASK-LIVE-001",
        title="preserve target semantics",
        summary="Keep scenario-authored semantics visible to downstream stages.",
        intent="Ensure model-authored stages can see the scenario's intended behavior.",
        target_change="Normalize non-Error thrown values at the error boundary.",
        expected_scope="Runtime boundary plus focused tests.",
        acceptance_criteria=("The target change is represented in context.",),
        verification=("pytest -q",),
        quality_bar="The implementation follows the authored semantic target.",
        size_rationale="Medium because the semantic target constrains implementation.",
        interview=tuple(),
        visible_request="Please route non-Error thrown values through configured onError.",
    )
    working_copy = tmp_path / "target"
    work_item_root = working_copy / ".aidd" / "workitems" / "WI-LIVE"
    work_item_root.mkdir(parents=True)

    bootstrap_live_work_item(
        working_copy_path=working_copy,
        scenario=_scenario(selected_task),
        work_item="WI-LIVE",
        selected_task=selected_task,
        resolved_revision="abc123",
    )

    selected_task_text = (
        work_item_root / "context" / "selected-task.md"
    ).read_text(encoding="utf-8")
    user_request_text = (
        work_item_root / "context" / "user-request.md"
    ).read_text(encoding="utf-8")

    assert "## Visible Product Request" in selected_task_text
    assert "Please route non-Error thrown values through configured onError." in (
        selected_task_text
    )
    assert "## Authored Task Constraints" in selected_task_text
    assert "Normalize non-Error thrown values at the error boundary." in (
        selected_task_text
    )
    assert "The implementation follows the authored semantic target." in (
        selected_task_text
    )
    assert "Runtime boundary plus focused tests." in selected_task_text
    assert "## Authored Task Constraints" not in user_request_text
    assert "Please route non-Error thrown values through configured onError." in (
        user_request_text
    )


def test_bootstrap_hono_live_task_exposes_target_change_before_stage_run(
    tmp_path: Path,
) -> None:
    scenario = load_scenario(
        Path("harness/scenarios/live/hono-non-error-throw-handling.yaml")
    )
    selected_task = select_authored_task(scenario)
    assert selected_task is not None
    working_copy = tmp_path / "target"
    work_item_root = (
        working_copy / ".aidd" / "workitems" / "WI-LIVE-HONO-SMOKE"
    )
    work_item_root.mkdir(parents=True)

    bootstrap_live_work_item(
        working_copy_path=working_copy,
        scenario=scenario,
        work_item="WI-LIVE-HONO-SMOKE",
        selected_task=selected_task,
        resolved_revision=scenario.repo.revision,
    )

    selected_task_text = (
        work_item_root / "context" / "selected-task.md"
    ).read_text(encoding="utf-8")
    user_request_text = (
        work_item_root / "context" / "user-request.md"
    ).read_text(encoding="utf-8")

    assert "## Visible Product Request" in selected_task_text
    assert "## Authored Task Constraints" in selected_task_text
    assert (
        "Normalize non-Error thrown values at the error boundary"
        in selected_task_text
    )
    assert (
        "preserves the existing public error type contracts"
        in selected_task_text
    )
    assert "Hono should route thrown non-Error values" in user_request_text
    assert "## Authored Task Constraints" not in user_request_text
