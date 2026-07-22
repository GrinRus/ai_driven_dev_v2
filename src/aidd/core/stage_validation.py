from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aidd.core.interview import stage_has_unresolved_blocking_questions
from aidd.core.repair import RepairBudgetPolicy, evaluate_stage_repair_counter
from aidd.core.run_store import (
    load_stage_metadata,
    next_attempt_number,
    persist_stage_status,
    run_attempt_root,
    run_stage_metadata_path,
)
from aidd.core.runtime_operator import unapproved_operator_request_ids
from aidd.core.stage_invocation import prepare_adapter_invocation
from aidd.core.stage_models import (
    PostValidationAction,
    PostValidationTransition,
    RepairBudgetValidationTransition,
    StageInterviewRouting,
    StageResumeResult,
    StageUnblockState,
    StageValidationState,
    ValidationVerdict,
)
from aidd.core.stage_outputs import publish_stage_outputs_after_validation_pass
from aidd.core.stage_preparation import (
    persist_execution_state,
    prepare_stage_bundle,
    validate_required_stage_inputs,
)
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT
from aidd.core.stage_terminal import reconcile_stage_result_after_validation_pass
from aidd.core.state_machine import StageState, is_terminal_state, transition_stage_state
from aidd.validators.cross_document import BLOCKING_UNANSWERED_CODE
from aidd.validators.models import ValidationFinding
from aidd.validators.reports import write_validator_report
from aidd.validators.semantic import validate_semantic_outputs


def derive_validation_verdict(
    *,
    findings: tuple[ValidationFinding, ...],
    interview_routing: StageInterviewRouting | None = None,
) -> ValidationVerdict:
    if findings:
        if all(finding.code == BLOCKING_UNANSWERED_CODE for finding in findings):
            return ValidationVerdict.BLOCKED
        return ValidationVerdict.REPAIR
    if interview_routing is not None and interview_routing.requires_interview:
        return ValidationVerdict.BLOCKED
    return ValidationVerdict.PASS


def persist_validation_state(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    verdict: ValidationVerdict,
    from_state: StageState = StageState.VALIDATING,
    changed_at_utc: datetime | None = None,
    defer_success_persistence: bool = False,
) -> StageValidationState:
    next_state_map = {
        ValidationVerdict.PASS: StageState.SUCCEEDED,
        ValidationVerdict.REPAIR: StageState.REPAIR_NEEDED,
        ValidationVerdict.BLOCKED: StageState.BLOCKED,
        ValidationVerdict.FAIL: StageState.FAILED,
    }
    next_state = next_state_map[verdict]
    transition_stage_state(from_state=from_state, to_state=next_state)

    if next_state is StageState.SUCCEEDED and defer_success_persistence:
        # Success is a commit state. Keep durable metadata in `validating` until
        # reconciliation and atomic publication both complete.
        stage_metadata_path = run_stage_metadata_path(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
    else:
        stage_metadata_path = persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            status=next_state.value,
            changed_at_utc=changed_at_utc,
        )
    return StageValidationState(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        verdict=verdict,
        next_state=next_state,
        stage_metadata_path=stage_metadata_path,
    )


def persist_validation_state_with_repair_budget(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    verdict: ValidationVerdict,
    repair_policy: RepairBudgetPolicy | None = None,
    from_state: StageState = StageState.VALIDATING,
    changed_at_utc: datetime | None = None,
    defer_success_persistence: bool = False,
) -> RepairBudgetValidationTransition:
    resolved_verdict = verdict
    budget_exhausted = False
    remaining_repair_attempts: int | None = None

    if verdict is ValidationVerdict.REPAIR:
        repair_counter = evaluate_stage_repair_counter(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            policy=repair_policy,
        )
        budget_exhausted = repair_counter.budget_exhausted
        remaining_repair_attempts = repair_counter.remaining_repair_attempts
        if budget_exhausted:
            resolved_verdict = ValidationVerdict.FAIL

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        verdict=resolved_verdict,
        from_state=from_state,
        changed_at_utc=changed_at_utc,
        defer_success_persistence=defer_success_persistence,
    )
    return RepairBudgetValidationTransition(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        requested_verdict=verdict,
        resolved_verdict=resolved_verdict,
        budget_exhausted=budget_exhausted,
        remaining_repair_attempts=remaining_repair_attempts,
        validation_state=validation_state,
    )


def update_stage_unblock_state(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    changed_at_utc: datetime | None = None,
) -> StageUnblockState:
    stage_metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if stage_metadata is None:
        return StageUnblockState(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            was_blocked=False,
            unblocked=False,
            next_state=None,
            stage_metadata_path=None,
        )

    current_status = stage_metadata.status.lower()
    if current_status != StageState.BLOCKED.value:
        try:
            next_state: StageState | None = StageState(current_status)
        except ValueError:
            next_state = None
        return StageUnblockState(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            was_blocked=False,
            unblocked=False,
            next_state=next_state,
            stage_metadata_path=run_stage_metadata_path(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            ),
        )

    if _stage_has_unapproved_operator_requests(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    ):
        return StageUnblockState(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            was_blocked=True,
            unblocked=False,
            next_state=StageState.BLOCKED,
            stage_metadata_path=run_stage_metadata_path(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            ),
        )

    if stage_has_unresolved_blocking_questions(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    ):
        return StageUnblockState(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            was_blocked=True,
            unblocked=False,
            next_state=StageState.BLOCKED,
            stage_metadata_path=run_stage_metadata_path(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            ),
        )

    transition_stage_state(from_state=StageState.BLOCKED, to_state=StageState.PREPARING)
    stage_metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.PREPARING.value,
        changed_at_utc=changed_at_utc,
    )
    return StageUnblockState(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        was_blocked=True,
        unblocked=True,
        next_state=StageState.PREPARING,
        stage_metadata_path=stage_metadata_path,
    )


def _stage_has_unapproved_operator_requests(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> bool:
    latest_attempt_number = (
        next_attempt_number(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        - 1
    )
    if latest_attempt_number < 1:
        return False
    attempt_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=latest_attempt_number,
    )
    return bool(unapproved_operator_request_ids(attempt_path=attempt_path))


def prepare_stage_resume_after_answers(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    changed_at_utc: datetime | None = None,
) -> StageResumeResult:
    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        changed_at_utc=changed_at_utc,
    )
    if not unblock_state.unblocked:
        return StageResumeResult(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            unblock_state=unblock_state,
            preparation_bundle=None,
            execution_state=None,
            adapter_invocation=None,
        )

    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        contracts_root=contracts_root,
        include_existing_stage_outputs=True,
    )
    validate_required_stage_inputs(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
    )
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        contracts_root=contracts_root,
        changed_at_utc=changed_at_utc,
    )
    adapter_invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
        contracts_root=contracts_root,
    )
    return StageResumeResult(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        unblock_state=unblock_state,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
        adapter_invocation=adapter_invocation,
    )


def decide_post_validation_transition(
    validation_state: StageValidationState,
    *,
    workspace_root: Path | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    defer_success_publication: bool = False,
) -> PostValidationTransition:
    next_state = validation_state.next_state
    stage_metadata_path = validation_state.stage_metadata_path

    if (
        workspace_root is not None
        and next_state == StageState.SUCCEEDED
        and stage_has_unresolved_blocking_questions(
            workspace_root=workspace_root,
            work_item=validation_state.work_item,
            stage=validation_state.stage,
        )
    ):
        next_state = StageState.BLOCKED
        stage_metadata_path = persist_stage_status(
            workspace_root=workspace_root,
            work_item=validation_state.work_item,
            run_id=validation_state.run_id,
            stage=validation_state.stage,
            status=StageState.BLOCKED.value,
        )
    elif workspace_root is not None and next_state == StageState.SUCCEEDED:
        try:
            final_findings = reconcile_and_validate_stage_result_after_validation_pass(
                workspace_root=workspace_root,
                work_item=validation_state.work_item,
                stage=validation_state.stage,
                contracts_root=contracts_root,
            )
            if final_findings:
                validator_report_path = (
                    workspace_root
                    / "workitems"
                    / validation_state.work_item
                    / "stages"
                    / validation_state.stage
                    / "validator-report.md"
                )
                write_validator_report(
                    path=validator_report_path,
                    findings=final_findings,
                )
                raise ValueError("Final post-normalization stage-result validation failed.")
            if not defer_success_publication:
                publish_stage_outputs_after_validation_pass(
                    workspace_root=workspace_root,
                    work_item=validation_state.work_item,
                    run_id=validation_state.run_id,
                    stage=validation_state.stage,
                    contracts_root=contracts_root,
                )
        except BaseException:
            persist_stage_status(
                workspace_root=workspace_root,
                work_item=validation_state.work_item,
                run_id=validation_state.run_id,
                stage=validation_state.stage,
                status=StageState.FAILED.value,
            )
            raise
        stage_metadata_path = persist_stage_status(
            workspace_root=workspace_root,
            work_item=validation_state.work_item,
            run_id=validation_state.run_id,
            stage=validation_state.stage,
            status=(
                StageState.PENDING.value
                if defer_success_publication
                else StageState.SUCCEEDED.value
            ),
        )

    action_map: dict[StageState, PostValidationAction] = {
        StageState.SUCCEEDED: PostValidationAction.ADVANCE,
        StageState.REPAIR_NEEDED: PostValidationAction.REPAIR,
        StageState.BLOCKED: PostValidationAction.WAIT,
        StageState.FAILED: PostValidationAction.STOP,
    }
    if next_state not in action_map:
        raise ValueError(f"Unsupported post-validation state: {next_state}")

    return PostValidationTransition(
        stage=validation_state.stage,
        work_item=validation_state.work_item,
        run_id=validation_state.run_id,
        next_state=next_state,
        action=action_map[next_state],
        is_terminal=is_terminal_state(next_state),
        stage_metadata_path=stage_metadata_path,
    )


def reconcile_and_validate_stage_result_after_validation_pass(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[ValidationFinding, ...]:
    """Normalize success-owned fields, then validate the complete stage result."""

    reconcile_stage_result_after_validation_pass(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    return validate_semantic_outputs(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
        validate_stage_result_document=True,
    )


__all__ = [
    "decide_post_validation_transition",
    "derive_validation_verdict",
    "persist_validation_state",
    "persist_validation_state_with_repair_budget",
    "reconcile_and_validate_stage_result_after_validation_pass",
    "prepare_stage_resume_after_answers",
    "update_stage_unblock_state",
]
