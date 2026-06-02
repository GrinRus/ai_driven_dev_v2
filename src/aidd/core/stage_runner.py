from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from aidd.core.interview import (
    load_questions_document,
    render_answers_markdown,
)
from aidd.core.project_set import ResolvedProjectSet
from aidd.core.remediation import latest_remediation_input_documents
from aidd.core.repair import RepairBudgetPolicy, persist_repair_history_snapshot
from aidd.core.run_store import (
    load_stage_metadata,
    persist_stage_status,
    write_attempt_artifact_index,
)
from aidd.core.stage_interview_routing import (
    MALFORMED_INTERVIEW_DOCUMENT_CODE,
    route_stage_questions_to_interview,
    route_stage_questions_to_interview_with_validation,
)
from aidd.core.stage_invocation import (
    ATTEMPT_INPUT_BUNDLE_FILENAME,
    ATTEMPT_REPAIR_CONTEXT_FILENAME,
    prepare_adapter_invocation,
    restore_core_owned_repair_brief,
)
from aidd.core.stage_models import (
    AdapterExecutionOutcome,
    AdapterExecutionStatus,
    AdapterInvocationBundle,
    PostValidationAction,
    PostValidationTransition,
    RepairBudgetValidationTransition,
    StageExecutionState,
    StageInterviewRouting,
    StageOrchestrationResult,
    StageOutputDiscovery,
    StageOutputPublication,
    StagePreparationBundle,
    StageResumeResult,
    StageStructuralValidationResult,
    StageUnblockState,
    StageValidationState,
    ValidationVerdict,
)
from aidd.core.stage_outputs import (
    discover_stage_markdown_outputs,
    publish_stage_outputs_after_validation_pass,
    run_structural_validation_after_output_discovery,
)
from aidd.core.stage_paths import (
    workspace_relative_path as _workspace_relative_path,
)
from aidd.core.stage_paths import (
    workspace_relative_paths as _to_workspace_relative_paths,
)
from aidd.core.stage_preparation import (
    persist_execution_state,
    prepare_stage_bundle,
)
from aidd.core.stage_preparation import (
    render_stage_brief as _render_stage_brief,
)
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT
from aidd.core.stage_terminal import (
    ensure_repair_brief_records_exhausted_budget,
    ensure_stage_result_references_repair_brief,
    exhausted_budget_validation_finding,
    force_stage_result_failed_for_exhausted_budget,
    repair_brief_exhausts_terminal_budget,
    strip_stage_result_success_claims_for_validator_findings,
)
from aidd.core.stage_validation import (
    decide_post_validation_transition,
    derive_validation_verdict,
    persist_validation_state,
    persist_validation_state_with_repair_budget,
    prepare_stage_resume_after_answers,
    update_stage_unblock_state,
)
from aidd.core.state_machine import StageState, transition_stage_state
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.validators.models import ValidationFinding
from aidd.validators.reports import write_validator_report

_route_stage_questions_to_interview_with_validation = (
    route_stage_questions_to_interview_with_validation
)


def _append_validation_findings(
    *,
    validation_result: StageStructuralValidationResult,
    findings: tuple[ValidationFinding, ...],
) -> StageStructuralValidationResult:
    write_validator_report(path=validation_result.validator_report_path, findings=findings)
    return StageStructuralValidationResult(
        stage=validation_result.stage,
        work_item=validation_result.work_item,
        run_id=validation_result.run_id,
        attempt_number=validation_result.attempt_number,
        validator_report_path=validation_result.validator_report_path,
        findings=findings,
    )


def _fail_after_adapter_error(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    changed_at_utc: datetime | None,
) -> StageValidationState:
    failed_metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.FAILED.value,
        changed_at_utc=changed_at_utc,
    )
    return StageValidationState(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        verdict=ValidationVerdict.FAIL,
        next_state=StageState.FAILED,
        stage_metadata_path=failed_metadata_path,
    )


def _block_after_operator_request(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    changed_at_utc: datetime | None,
) -> StageValidationState:
    return persist_validation_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        verdict=ValidationVerdict.BLOCKED,
        from_state=StageState.EXECUTING,
        changed_at_utc=changed_at_utc,
    )


def _repair_history_trigger(*, adapter_invocation: AdapterInvocationBundle) -> str:
    return adapter_invocation.attempt_mode


def _repair_history_outcome(
    *,
    validation_transition: RepairBudgetValidationTransition,
) -> str:
    if validation_transition.resolved_verdict is ValidationVerdict.PASS:
        return "succeeded"
    if validation_transition.resolved_verdict is ValidationVerdict.BLOCKED:
        return "blocked by questions"
    if validation_transition.requested_verdict is ValidationVerdict.REPAIR:
        return "failed validation"
    return "failed"


def _should_persist_terminal_repair_history(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
    attempt_mode: str,
    validation_transition: RepairBudgetValidationTransition,
) -> bool:
    if validation_transition.requested_verdict is ValidationVerdict.REPAIR:
        return validation_transition.resolved_verdict is ValidationVerdict.FAIL
    if attempt_mode == "intervention":
        return True
    if attempt_number > 1:
        return True
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    return metadata is not None and bool(metadata.repair_history)


def _should_include_existing_stage_outputs_for_resume(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> bool:
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if metadata is None:
        return False
    return (
        metadata.status == StageState.PREPARING.value
        and any(
            status_change.status == StageState.BLOCKED.value
            for status_change in metadata.status_history
        )
    )


def _read_stage_answers_text(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> str | None:
    answers_path = workspace_stage_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    ) / "answers.md"
    if not answers_path.exists():
        return None
    return answers_path.read_text(encoding="utf-8")


def _restore_operator_owned_answers_after_runtime_attempt(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    answers_text_before_attempt: str | None,
) -> None:
    answers_path = workspace_stage_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    ) / "answers.md"
    try:
        questions = load_questions_document(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
    except ValueError:
        return

    try:
        answers_text_after_attempt = answers_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        answers_text_after_attempt = None

    question_ids = {question.question_id for question in questions}
    empty_answers_text = render_answers_markdown(())

    if answers_text_before_attempt is None:
        if question_ids and answers_text_after_attempt != empty_answers_text:
            answers_path.parent.mkdir(parents=True, exist_ok=True)
            answers_path.write_text(empty_answers_text, encoding="utf-8")
        return

    if question_ids and answers_text_after_attempt != answers_text_before_attempt:
        answers_path.parent.mkdir(parents=True, exist_ok=True)
        answers_path.write_text(answers_text_before_attempt, encoding="utf-8")


def _intervention_context_documents(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    operator_request_path: Path,
) -> tuple[Path, ...]:
    stage_documents_root = workspace_stage_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    candidates = (
        operator_request_path,
        stage_documents_root / "questions.md",
        stage_documents_root / "answers.md",
    )
    return tuple(path for path in candidates if path.exists())


def run_single_stage_orchestration(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    adapter_executor: Callable[
        [AdapterInvocationBundle, StageExecutionState],
        AdapterExecutionOutcome,
    ],
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    repair_policy: RepairBudgetPolicy | None = None,
    project_set: ResolvedProjectSet | None = None,
    changed_at_utc: datetime | None = None,
    intervention_request_path: Path | None = None,
) -> StageOrchestrationResult:
    answers_text_before_attempt = _read_stage_answers_text(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    include_existing_stage_outputs = _should_include_existing_stage_outputs_for_resume(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if intervention_request_path is not None:
        include_existing_stage_outputs = True
    extra_input_documents = (
        ()
        if intervention_request_path is None
        else _intervention_context_documents(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            operator_request_path=intervention_request_path,
        )
    )
    if stage == "implement":
        extra_input_documents = (
            *extra_input_documents,
            *latest_remediation_input_documents(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                target_stage=stage,
            ),
        )

    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        contracts_root=contracts_root,
        project_set=project_set,
        include_existing_stage_outputs=include_existing_stage_outputs,
        extra_input_documents=extra_input_documents,
    )
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        contracts_root=contracts_root,
        changed_at_utc=changed_at_utc,
    )
    try:
        adapter_invocation = prepare_adapter_invocation(
            workspace_root=workspace_root,
            preparation_bundle=preparation_bundle,
            execution_state=execution_state,
            contracts_root=contracts_root,
            intervention_request_path=intervention_request_path,
        )
    except Exception:
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            status=StageState.FAILED.value,
            changed_at_utc=changed_at_utc,
        )
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=execution_state.attempt_number,
            contracts_root=contracts_root,
        )
        raise
    try:
        adapter_outcome = adapter_executor(adapter_invocation, execution_state)
    finally:
        restore_core_owned_repair_brief(
            invocation_bundle=adapter_invocation,
            workspace_root=workspace_root,
        )
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=execution_state.attempt_number,
            contracts_root=contracts_root,
        )

    if adapter_outcome.blocked_for_operator:
        blocked_validation_state = _block_after_operator_request(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            changed_at_utc=changed_at_utc,
        )
        transition = decide_post_validation_transition(blocked_validation_state)
        return StageOrchestrationResult(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            preparation_bundle=preparation_bundle,
            execution_state=execution_state,
            adapter_invocation=adapter_invocation,
            adapter_outcome=adapter_outcome,
            discovery=None,
            validation_result=None,
            interview_routing=None,
            validation_transition=None,
            transition=transition,
        )

    if not adapter_outcome.succeeded:
        failed_validation_state = _fail_after_adapter_error(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            changed_at_utc=changed_at_utc,
        )
        transition = decide_post_validation_transition(failed_validation_state)
        return StageOrchestrationResult(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            preparation_bundle=preparation_bundle,
            execution_state=execution_state,
            adapter_invocation=adapter_invocation,
            adapter_outcome=adapter_outcome,
            discovery=None,
            validation_result=None,
            interview_routing=None,
            validation_transition=None,
            transition=transition,
        )

    transition_stage_state(from_state=StageState.EXECUTING, to_state=StageState.VALIDATING)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.VALIDATING.value,
        changed_at_utc=changed_at_utc,
    )
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=adapter_invocation,
    )
    _restore_operator_owned_answers_after_runtime_attempt(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        answers_text_before_attempt=answers_text_before_attempt,
    )
    exhausted_repair_budget = repair_brief_exhausts_terminal_budget(
        repair_brief_path=adapter_invocation.repair_brief_path,
        repair_context_markdown=adapter_invocation.repair_context_markdown,
    )
    exhausted_stage_result_path: Path | None = None
    if exhausted_repair_budget:
        ensure_repair_brief_records_exhausted_budget(adapter_invocation.repair_brief_path)
        exhausted_stage_result_path = force_stage_result_failed_for_exhausted_budget(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
    ensure_stage_result_references_repair_brief(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        repair_brief_path=adapter_invocation.repair_brief_path,
    )
    validation_result = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
        contracts_root=contracts_root,
    )
    if exhausted_repair_budget and exhausted_stage_result_path is not None:
        findings = validation_result.findings
        if not any(finding.code == "CROSS-REPAIR-BUDGET-EXHAUSTED" for finding in findings):
            findings = (
                *findings,
                exhausted_budget_validation_finding(
                    workspace_root=workspace_root,
                    stage_result_path=exhausted_stage_result_path,
                ),
            )
        validation_result = _append_validation_findings(
            validation_result=validation_result,
            findings=findings,
        )
    interview_routing, interview_findings = _route_stage_questions_to_interview_with_validation(
        workspace_root=workspace_root,
        discovery=discovery,
    )
    if interview_findings:
        validation_result = _append_validation_findings(
            validation_result=validation_result,
            findings=(*validation_result.findings, *interview_findings),
        )
    if validation_result.findings:
        strip_stage_result_success_claims_for_validator_findings(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
    verdict = derive_validation_verdict(
        findings=validation_result.findings,
        interview_routing=interview_routing,
    )
    validation_transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        verdict=verdict,
        repair_policy=repair_policy,
        from_state=StageState.VALIDATING,
        changed_at_utc=changed_at_utc,
    )
    if _should_persist_terminal_repair_history(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=execution_state.attempt_number,
        attempt_mode=adapter_invocation.attempt_mode,
        validation_transition=validation_transition,
    ):
        persist_repair_history_snapshot(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=execution_state.attempt_number,
            trigger=_repair_history_trigger(adapter_invocation=adapter_invocation),
            outcome=_repair_history_outcome(validation_transition=validation_transition),
            stage_status=validation_transition.validation_state.next_state.value,
            validator_report_path=validation_result.validator_report_path,
            repair_brief_path=adapter_invocation.repair_brief_path,
            changed_at_utc=changed_at_utc,
        )
    transition = decide_post_validation_transition(
        validation_transition.validation_state,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    return StageOrchestrationResult(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
        adapter_invocation=adapter_invocation,
        adapter_outcome=adapter_outcome,
        discovery=discovery,
        validation_result=validation_result,
        interview_routing=interview_routing,
        validation_transition=validation_transition,
        transition=transition,
    )


__all__ = [
    "ATTEMPT_INPUT_BUNDLE_FILENAME",
    "ATTEMPT_REPAIR_CONTEXT_FILENAME",
    "AdapterExecutionOutcome",
    "AdapterExecutionStatus",
    "AdapterInvocationBundle",
    "MALFORMED_INTERVIEW_DOCUMENT_CODE",
    "PostValidationAction",
    "PostValidationTransition",
    "RepairBudgetValidationTransition",
    "StageExecutionState",
    "StageInterviewRouting",
    "StageOrchestrationResult",
    "StageOutputDiscovery",
    "StageOutputPublication",
    "StagePreparationBundle",
    "StageResumeResult",
    "StageStructuralValidationResult",
    "StageUnblockState",
    "StageValidationState",
    "ValidationVerdict",
    "_render_stage_brief",
    "_route_stage_questions_to_interview_with_validation",
    "_to_workspace_relative_paths",
    "_workspace_relative_path",
    "decide_post_validation_transition",
    "derive_validation_verdict",
    "discover_stage_markdown_outputs",
    "persist_execution_state",
    "persist_validation_state",
    "persist_validation_state_with_repair_budget",
    "prepare_adapter_invocation",
    "prepare_stage_bundle",
    "prepare_stage_resume_after_answers",
    "publish_stage_outputs_after_validation_pass",
    "restore_core_owned_repair_brief",
    "route_stage_questions_to_interview",
    "run_single_stage_orchestration",
    "run_structural_validation_after_output_discovery",
    "update_stage_unblock_state",
]
