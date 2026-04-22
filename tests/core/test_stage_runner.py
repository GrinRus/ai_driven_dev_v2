from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aidd.core.repair import RepairBudgetPolicy
from aidd.core.run_store import (
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_stage_metadata_path,
)
from aidd.core.stage_runner import (
    ATTEMPT_INPUT_BUNDLE_FILENAME,
    PostValidationAction,
    RepairBudgetValidationTransition,
    StageExecutionState,
    StageInterviewRouting,
    StageOutputDiscovery,
    StageResumeResult,
    StageStructuralValidationResult,
    StageValidationState,
    ValidationVerdict,
    decide_post_validation_transition,
    discover_stage_markdown_outputs,
    persist_execution_state,
    persist_validation_state,
    persist_validation_state_with_repair_budget,
    prepare_adapter_invocation,
    prepare_stage_bundle,
    prepare_stage_resume_after_answers,
    route_stage_questions_to_interview,
    run_structural_validation_after_output_discovery,
    update_stage_unblock_state,
)
from aidd.core.state_machine import StageState, is_terminal_state, transition_stage_state


def _materialize_expected_inputs(paths: tuple[Path, ...]) -> None:
    for index, path in enumerate(paths, start=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# Input {index}\n\nPrepared input for `{path.name}`.\n",
            encoding="utf-8",
        )


def test_prepare_stage_bundle_resolves_expected_inputs_and_outputs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="implement",
    )

    assert bundle.stage == "implement"
    assert bundle.work_item == "WI-001"
    assert bundle.expected_input_bundle == (
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md",
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "tasklist"
        / "output"
        / "stage-result.md",
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "tasklist"
        / "output"
        / "validator-report.md",
        workspace_root / "workitems" / "WI-001" / "context" / "repository-state.md",
        workspace_root / "workitems" / "WI-001" / "context" / "task-selection.md",
        workspace_root / "workitems" / "WI-001" / "context" / "allowed-write-scope.md",
    )
    assert bundle.expected_output_documents == (
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "implement"
        / "implementation-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "stage-result.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "validator-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "repair-brief.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "questions.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "answers.md",
    )


def test_prepare_stage_bundle_renders_stage_brief_with_relative_paths(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    content = bundle.stage_brief_markdown

    assert "# Stage" in content
    assert "\nplan\n" in content
    assert "# Expected input bundle" in content
    assert "`workitems/WI-001/stages/research/output/research-notes.md`" in content
    assert "# Expected output documents" in content
    assert "`workitems/WI-001/stages/plan/plan.md`" in content


def test_persist_execution_state_creates_attempt_and_sets_executing_status(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )

    assert execution_state.attempt_number == 1
    assert execution_state.attempt_path.name == "attempt-0001"
    assert run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    ).exists()
    stage_metadata_payload = json.loads(
        execution_state.stage_metadata_path.read_text(encoding="utf-8")
    )
    assert stage_metadata_payload["status"] == "executing"
    assert stage_metadata_payload["updated_at_utc"] == "2026-04-22T10:00:00Z"


def test_persist_execution_state_uses_monotonic_attempt_numbers(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    first = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    second = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert first.attempt_number == 1
    assert second.attempt_number == 2


def test_prepare_adapter_invocation_initial_attempt_has_no_repair_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )

    assert invocation.attempt_number == 1
    assert invocation.repair_mode is False
    assert invocation.repair_context_markdown is None
    assert invocation.repair_brief_path is None
    assert invocation.input_bundle_path == (
        execution_state.attempt_path / ATTEMPT_INPUT_BUNDLE_FILENAME
    )
    assert invocation.input_bundle_path.exists()
    assert invocation.input_bundle_markdown == invocation.input_bundle_path.read_text(
        encoding="utf-8"
    )
    assert "# Input bundle" in invocation.input_bundle_markdown
    assert invocation.stage_brief_markdown == preparation_bundle.stage_brief_markdown


def test_prepare_adapter_invocation_repair_attempt_injects_repair_context(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    second_attempt = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    repair_brief_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "repair-brief.md"
    )
    repair_brief_path.parent.mkdir(parents=True, exist_ok=True)
    repair_brief_path.write_text(
        (
            "# Failed checks\n\n"
            "- `STRUCT-MISSING-REQUIRED-SECTION` `high` in "
            "`workitems/WI-001/stages/plan/plan.md`\n"
        ),
        encoding="utf-8",
    )

    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=second_attempt,
    )

    assert invocation.attempt_number == 2
    assert invocation.repair_mode is True
    assert invocation.repair_brief_path == repair_brief_path
    assert invocation.repair_context_markdown is not None
    assert "Mode: `repair`" in invocation.repair_context_markdown
    assert "Attempt number: `2`" in invocation.repair_context_markdown
    assert "repair-brief.md" in invocation.repair_context_markdown
    assert "STRUCT-MISSING-REQUIRED-SECTION" in invocation.repair_context_markdown
    assert invocation.input_bundle_path == (
        second_attempt.attempt_path / ATTEMPT_INPUT_BUNDLE_FILENAME
    )
    assert invocation.input_bundle_path.exists()


def test_prepare_adapter_invocation_requires_existing_input_documents(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    with pytest.raises(FileNotFoundError, match="Input bundle preparation requires an existing"):
        prepare_adapter_invocation(
            workspace_root=workspace_root,
            preparation_bundle=preparation_bundle,
            execution_state=execution_state,
        )


def test_discover_stage_markdown_outputs_returns_discovered_and_missing_documents(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    for output_path in preparation_bundle.expected_output_documents[:2]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("# Output\n\nPresent.\n", encoding="utf-8")

    invocation_with_non_markdown_output = replace(
        invocation,
        expected_output_documents=(
            *invocation.expected_output_documents,
            execution_state.attempt_path / "runtime.log",
        ),
    )
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation_with_non_markdown_output,
    )

    assert isinstance(discovery, StageOutputDiscovery)
    assert discovery.stage == "plan"
    assert discovery.attempt_number == 1
    assert all(path.suffix.lower() == ".md" for path in discovery.expected_markdown_documents)
    assert execution_state.attempt_path / "runtime.log" not in discovery.expected_markdown_documents
    assert discovery.discovered_markdown_documents == (
        preparation_bundle.expected_output_documents[:2]
    )
    assert discovery.missing_markdown_documents == preparation_bundle.expected_output_documents[2:]


def test_discover_stage_markdown_outputs_rejects_mismatched_execution_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )

    with pytest.raises(ValueError, match="does not match adapter invocation stage"):
        discover_stage_markdown_outputs(
            execution_state=StageExecutionState(
                stage="qa",
                work_item=execution_state.work_item,
                run_id=execution_state.run_id,
                attempt_number=execution_state.attempt_number,
                attempt_path=execution_state.attempt_path,
                stage_metadata_path=execution_state.stage_metadata_path,
            ),
            invocation_bundle=invocation,
        )


def test_run_structural_validation_after_output_discovery_writes_report_path(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    plan_output_path = preparation_bundle.expected_output_documents[0]
    plan_output_path.parent.mkdir(parents=True, exist_ok=True)
    plan_output_path.write_text("# Plan\n\nPartial output.\n", encoding="utf-8")
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )

    structural_validation = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
    )

    assert isinstance(structural_validation, StageStructuralValidationResult)
    assert structural_validation.stage == "plan"
    assert structural_validation.run_id == "run-001"
    assert structural_validation.attempt_number == 1
    assert structural_validation.validator_report_path == (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "validator-report.md"
    )
    assert structural_validation.validator_report_path.exists()
    assert any(
        finding.code == "STRUCT-MISSING-REQUIRED-DOCUMENT"
        for finding in structural_validation.findings
    )
    report_text = structural_validation.validator_report_path.read_text(encoding="utf-8")
    assert "`STRUCT-MISSING-REQUIRED-DOCUMENT`" in report_text


def test_route_stage_questions_to_interview_detects_unresolved_blocking_questions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        (
            "# Questions\n\n"
            "## Questions\n\n"
            "- `Q1` `[blocking]` Confirm scope.\n"
            "- `Q2` `[non-blocking]` Optional context.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        (
            "# Answers\n\n"
            "## Answers\n\n"
            "- `Q2` `[resolved]` Added optional context.\n"
        ),
        encoding="utf-8",
    )

    routing = route_stage_questions_to_interview(
        workspace_root=workspace_root,
        discovery=discovery,
    )

    assert isinstance(routing, StageInterviewRouting)
    assert routing.requires_interview is True
    assert routing.unresolved_blocking_question_ids == ("Q1",)
    assert routing.questions_path == stage_root / "questions.md"
    assert routing.answers_path == stage_root / "answers.md"


def test_route_stage_questions_to_interview_skips_when_blocking_questions_resolved(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        (
            "# Questions\n\n"
            "## Questions\n\n"
            "- `Q1` `[blocking]` Confirm scope.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        (
            "# Answers\n\n"
            "## Answers\n\n"
            "- `Q1` `[resolved]` Scope confirmed.\n"
        ),
        encoding="utf-8",
    )

    routing = route_stage_questions_to_interview(
        workspace_root=workspace_root,
        discovery=discovery,
    )

    assert routing.requires_interview is False
    assert routing.unresolved_blocking_question_ids == ()


def test_prepare_adapter_invocation_repair_attempt_requires_repair_brief(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    second_attempt = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    with pytest.raises(FileNotFoundError, match="Repair rerun requires an existing repair brief"):
        prepare_adapter_invocation(
            workspace_root=workspace_root,
            preparation_bundle=preparation_bundle,
            execution_state=second_attempt,
        )


@pytest.mark.parametrize(
    ("verdict", "expected_state"),
    (
        (ValidationVerdict.PASS, StageState.SUCCEEDED),
        (ValidationVerdict.REPAIR, StageState.REPAIR_NEEDED),
        (ValidationVerdict.BLOCKED, StageState.BLOCKED),
        (ValidationVerdict.FAIL, StageState.FAILED),
    ),
)
def test_persist_validation_state_persists_verdict_transition(
    tmp_path: Path,
    verdict: ValidationVerdict,
    expected_state: StageState,
) -> None:
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
        stage="plan",
        status=StageState.VALIDATING.value,
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=verdict,
        changed_at_utc=datetime(2026, 4, 22, 10, 5, tzinfo=UTC),
    )

    assert validation_state.verdict is verdict
    assert validation_state.next_state == expected_state
    stage_metadata_payload = json.loads(
        validation_state.stage_metadata_path.read_text(encoding="utf-8")
    )
    assert stage_metadata_payload["status"] == expected_state.value
    assert stage_metadata_payload["updated_at_utc"] == "2026-04-22T10:05:00Z"
    assert [entry["status"] for entry in stage_metadata_payload["status_history"]] == [
        "validating",
        expected_state.value,
    ]


def test_persist_validation_state_rejects_illegal_transition(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    with pytest.raises(ValueError, match="Illegal stage transition"):
        persist_validation_state(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            verdict=ValidationVerdict.PASS,
            from_state=StageState.PENDING,
        )

    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert not metadata_path.exists()


def test_persist_validation_state_with_repair_budget_keeps_repair_when_budget_remains(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )

    transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.REPAIR,
        repair_policy=RepairBudgetPolicy(default_max_repair_attempts=2),
    )

    assert isinstance(transition, RepairBudgetValidationTransition)
    assert transition.requested_verdict is ValidationVerdict.REPAIR
    assert transition.resolved_verdict is ValidationVerdict.REPAIR
    assert transition.budget_exhausted is False
    assert transition.remaining_repair_attempts == 2
    assert transition.validation_state.next_state is StageState.REPAIR_NEEDED


def test_persist_validation_state_with_repair_budget_forces_fail_when_exhausted(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )

    transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.REPAIR,
        repair_policy=RepairBudgetPolicy(default_max_repair_attempts=2),
    )

    assert transition.requested_verdict is ValidationVerdict.REPAIR
    assert transition.resolved_verdict is ValidationVerdict.FAIL
    assert transition.budget_exhausted is True
    assert transition.remaining_repair_attempts == 0
    assert transition.validation_state.next_state is StageState.FAILED


@pytest.mark.parametrize(
    ("verdict", "expected_state", "expected_action", "expected_terminal"),
    (
        (
            ValidationVerdict.PASS,
            StageState.SUCCEEDED,
            PostValidationAction.ADVANCE,
            True,
        ),
        (
            ValidationVerdict.REPAIR,
            StageState.REPAIR_NEEDED,
            PostValidationAction.REPAIR,
            False,
        ),
        (
            ValidationVerdict.BLOCKED,
            StageState.BLOCKED,
            PostValidationAction.WAIT,
            False,
        ),
        (
            ValidationVerdict.FAIL,
            StageState.FAILED,
            PostValidationAction.STOP,
            True,
        ),
    ),
)
def test_decide_post_validation_transition_maps_supported_outcomes(
    tmp_path: Path,
    verdict: ValidationVerdict,
    expected_state: StageState,
    expected_action: PostValidationAction,
    expected_terminal: bool,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=verdict,
    )

    transition = decide_post_validation_transition(validation_state)

    assert transition.next_state == expected_state
    assert transition.action == expected_action
    assert transition.is_terminal is expected_terminal
    assert transition.stage_metadata_path == validation_state.stage_metadata_path


def test_decide_post_validation_transition_rejects_unsupported_state() -> None:
    with pytest.raises(ValueError, match="Unsupported post-validation state"):
        decide_post_validation_transition(
            StageValidationState(
                stage="plan",
                work_item="WI-001",
                run_id="run-001",
                verdict=ValidationVerdict.PASS,
                next_state=StageState.VALIDATING,
                stage_metadata_path=Path("/tmp/stage-metadata.json"),
            )
        )


@pytest.mark.parametrize(
    ("verdict", "expected_state", "expected_action", "expected_terminal"),
    (
        (
            ValidationVerdict.PASS,
            StageState.SUCCEEDED,
            PostValidationAction.ADVANCE,
            True,
        ),
        (
            ValidationVerdict.REPAIR,
            StageState.REPAIR_NEEDED,
            PostValidationAction.REPAIR,
            False,
        ),
        (
            ValidationVerdict.BLOCKED,
            StageState.BLOCKED,
            PostValidationAction.WAIT,
            False,
        ),
    ),
)
def test_stage_transition_flow_covers_happy_validator_failure_and_blocked_paths(
    tmp_path: Path,
    verdict: ValidationVerdict,
    expected_state: StageState,
    expected_action: PostValidationAction,
    expected_terminal: bool,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )
    transition_stage_state(StageState.EXECUTING, StageState.VALIDATING)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
        changed_at_utc=datetime(2026, 4, 22, 10, 1, tzinfo=UTC),
    )
    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=verdict,
        changed_at_utc=datetime(2026, 4, 22, 10, 2, tzinfo=UTC),
    )

    transition = decide_post_validation_transition(validation_state)

    assert transition.next_state == expected_state
    assert transition.action == expected_action
    assert transition.is_terminal is expected_terminal
    payload = json.loads(validation_state.stage_metadata_path.read_text(encoding="utf-8"))
    assert [entry["status"] for entry in payload["status_history"]] == [
        StageState.EXECUTING.value,
        StageState.VALIDATING.value,
        expected_state.value,
    ]


def test_stage_transition_flow_covers_adapter_failure_path(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )
    transition_stage_state(StageState.EXECUTING, StageState.FAILED)
    metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.FAILED.value,
        changed_at_utc=datetime(2026, 4, 22, 10, 1, tzinfo=UTC),
    )

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.FAILED.value
    assert [entry["status"] for entry in payload["status_history"]] == [
        StageState.EXECUTING.value,
        StageState.FAILED.value,
    ]
    assert is_terminal_state(StageState.FAILED) is True


def test_decide_post_validation_transition_blocks_success_with_unresolved_questions(
    tmp_path: Path,
) -> None:
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
        stage="plan",
        status=StageState.VALIDATING.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.PASS,
    )

    transition = decide_post_validation_transition(
        validation_state,
        workspace_root=workspace_root,
    )

    assert transition.next_state == StageState.BLOCKED
    assert transition.action == PostValidationAction.WAIT
    assert transition.is_terminal is False
    payload = json.loads(transition.stage_metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.BLOCKED.value
    assert [entry["status"] for entry in payload["status_history"]] == [
        StageState.VALIDATING.value,
        StageState.SUCCEEDED.value,
        StageState.BLOCKED.value,
    ]


def test_decide_post_validation_transition_allows_success_when_questions_resolved(
    tmp_path: Path,
) -> None:
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
        stage="plan",
        status=StageState.VALIDATING.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [resolved] Release owner approval is recorded.\n",
        encoding="utf-8",
    )

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.PASS,
    )

    transition = decide_post_validation_transition(
        validation_state,
        workspace_root=workspace_root,
    )

    assert transition.next_state == StageState.SUCCEEDED
    assert transition.action == PostValidationAction.ADVANCE
    assert transition.is_terminal is True


def test_update_stage_unblock_state_keeps_stage_blocked_when_answers_missing(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )

    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert unblock_state.was_blocked is True
    assert unblock_state.unblocked is False
    assert unblock_state.next_state == StageState.BLOCKED
    assert unblock_state.stage_metadata_path is not None
    payload = json.loads(unblock_state.stage_metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.BLOCKED.value
    assert unblock_state.next_state == StageState.BLOCKED
    assert unblock_state.stage_metadata_path == metadata_path
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.BLOCKED.value


def test_update_stage_unblock_state_moves_stage_to_preparing_when_answers_ready(
    tmp_path: Path,
) -> None:
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
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [resolved] Release owner approval is recorded.\n",
        encoding="utf-8",
    )

    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert unblock_state.was_blocked is True
    assert unblock_state.unblocked is True
    assert unblock_state.next_state == StageState.PREPARING
    assert unblock_state.stage_metadata_path is not None
    payload = json.loads(unblock_state.stage_metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.PREPARING.value
    assert [entry["status"] for entry in payload["status_history"]] == [
        StageState.BLOCKED.value,
        StageState.PREPARING.value,
    ]


def test_update_stage_unblock_state_keeps_stage_blocked_with_partial_answer(
    tmp_path: Path,
) -> None:
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
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [partial] Approval requested; final sign-off pending.\n",
        encoding="utf-8",
    )

    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert unblock_state.was_blocked is True
    assert unblock_state.unblocked is False


def test_prepare_stage_resume_after_answers_keeps_stage_blocked_without_resolved_answers(
    tmp_path: Path,
) -> None:
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
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )

    resume_result = prepare_stage_resume_after_answers(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert isinstance(resume_result, StageResumeResult)
    assert resume_result.unblock_state.unblocked is False
    assert resume_result.preparation_bundle is None
    assert resume_result.execution_state is None
    assert resume_result.adapter_invocation is None


def test_prepare_stage_resume_after_answers_creates_new_attempt_and_invocation(
    tmp_path: Path,
) -> None:
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
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [resolved] Release owner approval is recorded.\n",
        encoding="utf-8",
    )

    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    resume_result = prepare_stage_resume_after_answers(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert resume_result.unblock_state.unblocked is True
    assert resume_result.preparation_bundle is not None
    assert resume_result.execution_state is not None
    assert resume_result.adapter_invocation is not None
    assert resume_result.execution_state.attempt_number == 1
    assert resume_result.execution_state.attempt_path.name == "attempt-0001"
    assert resume_result.adapter_invocation.attempt_number == 1
    assert resume_result.adapter_invocation.input_bundle_path.exists()
