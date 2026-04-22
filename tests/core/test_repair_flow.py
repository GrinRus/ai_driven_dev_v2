from __future__ import annotations

from pathlib import Path

from aidd.core.repair import RepairBudgetPolicy, persist_repair_history_snapshot
from aidd.core.run_store import create_run_manifest, load_stage_metadata, persist_stage_status
from aidd.core.stage_runner import (
    PostValidationAction,
    ValidationVerdict,
    decide_post_validation_transition,
    persist_execution_state,
    persist_validation_state_with_repair_budget,
)
from aidd.core.state_machine import StageState


def _bootstrap_run(tmp_path: Path, *, stage_target: str = "plan") -> Path:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target=stage_target,
        config_snapshot={"mode": "test"},
    )
    return workspace_root


def _start_attempt(workspace_root: Path, *, stage: str = "plan") -> int:
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage=stage,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage=stage,
        status=StageState.VALIDATING.value,
    )
    return execution_state.attempt_number


def test_one_shot_repair_success_flow(tmp_path: Path) -> None:
    workspace_root = _bootstrap_run(tmp_path)
    policy = RepairBudgetPolicy(default_max_repair_attempts=2)

    attempt_number = _start_attempt(workspace_root)
    first_transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.REPAIR,
        repair_policy=policy,
    )
    assert first_transition.resolved_verdict is ValidationVerdict.REPAIR
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=attempt_number,
        trigger="initial",
        outcome="failed validation",
        stage_status="repair-needed",
    )

    attempt_number = _start_attempt(workspace_root)
    second_transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.PASS,
        repair_policy=policy,
    )
    assert second_transition.resolved_verdict is ValidationVerdict.PASS
    result = persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=attempt_number,
        trigger="repair",
        outcome="succeeded",
        stage_status="succeeded",
    )

    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert metadata is not None
    assert [entry.trigger for entry in metadata.repair_history] == ["initial", "repair"]

    stage_result_text = result.stage_result_path.read_text(encoding="utf-8")
    assert "- Attempt `1` (`initial`) -> failed validation." in stage_result_text
    assert "- Attempt `2` (`repair`) -> succeeded." in stage_result_text
    assert "## Status" in stage_result_text
    assert "- `succeeded`" in stage_result_text


def test_repeated_repair_failure_flow_records_attempt_history(tmp_path: Path) -> None:
    workspace_root = _bootstrap_run(tmp_path)
    policy = RepairBudgetPolicy(default_max_repair_attempts=2)

    for attempt_number, trigger in ((1, "initial"), (2, "repair"), (3, "repair")):
        current_attempt = _start_attempt(workspace_root)
        assert current_attempt == attempt_number
        transition = persist_validation_state_with_repair_budget(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            verdict=ValidationVerdict.REPAIR,
            repair_policy=policy,
        )
        if attempt_number < 3:
            assert transition.resolved_verdict is ValidationVerdict.REPAIR
            stage_status = "repair-needed"
        else:
            assert transition.resolved_verdict is ValidationVerdict.FAIL
            assert transition.budget_exhausted is True
            stage_status = "failed"

        persist_repair_history_snapshot(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            attempt_number=current_attempt,
            trigger=trigger,
            outcome="failed validation",
            stage_status=stage_status,
        )

    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert metadata is not None
    assert len(metadata.repair_history) == 3
    assert [entry.attempt_number for entry in metadata.repair_history] == [1, 2, 3]


def test_exhausted_budget_forces_terminal_stop_transition(tmp_path: Path) -> None:
    workspace_root = _bootstrap_run(tmp_path)
    policy = RepairBudgetPolicy(default_max_repair_attempts=1)

    _start_attempt(workspace_root)
    persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.REPAIR,
        repair_policy=policy,
    )
    _start_attempt(workspace_root)
    transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.REPAIR,
        repair_policy=policy,
    )

    assert transition.resolved_verdict is ValidationVerdict.FAIL
    assert transition.budget_exhausted is True
    post_transition = decide_post_validation_transition(transition.validation_state)
    assert post_transition.action is PostValidationAction.STOP
    assert post_transition.is_terminal is True


def test_implement_repair_loop_integration_scenario(tmp_path: Path) -> None:
    workspace_root = _bootstrap_run(tmp_path, stage_target="implement")
    policy = RepairBudgetPolicy(default_max_repair_attempts=2)

    attempt_number = _start_attempt(workspace_root, stage="implement")
    first_transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="implement",
        verdict=ValidationVerdict.REPAIR,
        repair_policy=policy,
    )
    assert first_transition.resolved_verdict is ValidationVerdict.REPAIR
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="implement",
        attempt_number=attempt_number,
        trigger="initial",
        outcome="failed validation",
        stage_status="repair-needed",
    )

    attempt_number = _start_attempt(workspace_root, stage="implement")
    second_transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="implement",
        verdict=ValidationVerdict.PASS,
        repair_policy=policy,
    )
    assert second_transition.resolved_verdict is ValidationVerdict.PASS
    result = persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="implement",
        attempt_number=attempt_number,
        trigger="repair",
        outcome="succeeded",
        stage_status="succeeded",
    )

    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="implement",
    )
    assert metadata is not None
    assert [entry.trigger for entry in metadata.repair_history] == ["initial", "repair"]

    stage_result_text = result.stage_result_path.read_text(encoding="utf-8")
    assert "# Stage" in stage_result_text
    assert "implement" in stage_result_text
    assert "- Attempt `1` (`initial`) -> failed validation." in stage_result_text
    assert "- Attempt `2` (`repair`) -> succeeded." in stage_result_text
    assert "## Status" in stage_result_text
    assert "- `succeeded`" in stage_result_text
