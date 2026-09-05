from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from aidd.core.interview import (
    InterviewMarkdownParseError,
    InterviewQuestion,
    load_questions_document,
    parse_answer_candidate_entries,
    parse_question_candidate_entries,
    parse_questions_markdown,
    render_answers_markdown,
    render_questions_markdown,
)
from aidd.core.models.run import RepairHistoryEntry
from aidd.core.project_set import ResolvedProjectSet
from aidd.core.remediation import latest_remediation_input_documents
from aidd.core.repair import RepairBudgetPolicy, persist_repair_history_snapshot
from aidd.core.run_store import (
    load_attempt_artifact_index,
    load_stage_metadata,
    next_attempt_number,
    persist_stage_status,
    run_attempt_root,
    run_stage_metadata_path,
    write_adapter_exception_artifact,
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
    historical_repair_brief_trace_path,
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
    retain_unexpected_runtime_documents,
    run_structural_validation_after_output_discovery,
)
from aidd.core.stage_paths import (
    workspace_relative_path as _workspace_relative_path,
)
from aidd.core.stage_paths import (
    workspace_relative_paths as _to_workspace_relative_paths,
)
from aidd.core.stage_preparation import (
    StageInputPreflightError,
    persist_execution_state,
    prepare_stage_bundle,
    validate_required_stage_inputs,
)
from aidd.core.stage_preparation import (
    render_stage_brief as _render_stage_brief,
)
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT
from aidd.core.stage_terminal import (
    CanonicalStageResultProjection,
    ensure_repair_brief_records_exhausted_budget,
    ensure_stage_result_references_repair_brief,
    exhausted_budget_validation_finding,
    force_stage_result_failed_for_exhausted_budget,
    normalize_success_stage_result_blockers_if_empty,
    prepare_bootstrap_stage_result_for_validation,
    repair_brief_exhausts_terminal_budget,
    strip_stage_result_success_claims_for_validator_findings,
    write_stage_result_from_lifecycle_state,
)
from aidd.core.stage_validation import (
    decide_post_validation_transition,
    derive_validation_verdict,
    persist_validation_state,
    persist_validation_state_with_repair_budget,
    prepare_stage_resume_after_answers,
    reconcile_and_validate_stage_result_after_validation_pass,
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
    defer_success_publication: bool,
) -> bool:
    if (
        defer_success_publication
        and validation_transition.resolved_verdict is ValidationVerdict.PASS
    ):
        return True
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
    if metadata.status == StageState.REPAIR_NEEDED.value:
        return True
    return metadata.status == StageState.PREPARING.value and any(
        status_change.status == StageState.BLOCKED.value
        for status_change in metadata.status_history
    )


def _canonical_stage_result_blockers(
    *,
    findings: tuple[ValidationFinding, ...],
    interview_routing: StageInterviewRouting | None = None,
) -> tuple[str, ...]:
    blockers = tuple(
        f"`{finding.code}`: {finding.message.strip()}"
        for finding in findings
    )
    if interview_routing is not None and interview_routing.requires_interview:
        blockers = (
            *blockers,
            *(
                f"Unresolved blocking question `{question_id}`."
                for question_id in interview_routing.unresolved_blocking_question_ids
            ),
        )
        if interview_routing.operator_attention_evidence_path is not None:
            blockers = (
                *blockers,
                "Interview candidate requires operator attention; inspect "
                f"`{interview_routing.operator_attention_evidence_path.name}`.",
            )
    return tuple(dict.fromkeys(blockers))


def _write_canonical_stage_result(
    *,
    workspace_root: Path,
    execution_state: StageExecutionState,
    lifecycle_status: StageState,
    attempt_mode: str,
    attempt_outcome: str,
    repair_history: tuple[RepairHistoryEntry, ...],
    produced_output_paths: tuple[Path, ...] = (),
    missing_output_paths: tuple[Path, ...] = (),
    validator_verdict: str | None = None,
    validator_report_path: Path | None = None,
    repair_brief_path: Path | None = None,
    blockers: tuple[str, ...] = (),
    repair_budget_status: str | None = None,
) -> Path:
    return write_stage_result_from_lifecycle_state(
        CanonicalStageResultProjection(
            stage=execution_state.stage,
            work_item=execution_state.work_item,
            status=lifecycle_status.value,
            attempt_number=execution_state.attempt_number,
            attempt_mode=attempt_mode,
            attempt_outcome=attempt_outcome,
            repair_history=tuple(repair_history),
            produced_output_paths=tuple(produced_output_paths),
            missing_output_paths=tuple(missing_output_paths),
            validator_verdict=validator_verdict,
            validator_report_path=validator_report_path,
            repair_brief_path=repair_brief_path,
            blockers=blockers,
            repair_budget_status=repair_budget_status,
        ),
        workspace_root=workspace_root,
    )


def _read_stage_answers_text(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> str | None:
    answers_path = (
        workspace_stage_root(
            root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        / "answers.md"
    )
    if not answers_path.exists():
        return None
    return answers_path.read_text(encoding="utf-8")


def _read_stage_questions_text(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> str | None:
    questions_path = (
        workspace_stage_root(
            root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        / "questions.md"
    )
    if not questions_path.exists():
        return None
    return questions_path.read_text(encoding="utf-8")


def _retain_interview_candidate_evidence(
    *,
    execution_state: StageExecutionState,
    document_name: str,
    candidate_text: str,
    error: InterviewMarkdownParseError | None = None,
) -> None:
    candidate_path = execution_state.attempt_path / (
        f"runtime-{document_name.removesuffix('.md')}-candidate.md"
    )
    candidate_path.write_text(candidate_text, encoding="utf-8")
    if error is None:
        return

    disposition_path = execution_state.attempt_path / "interview-candidate-disposition.md"
    lines = [
        "# Interview Candidate Disposition",
        "",
        f"- Document: `{document_name}`",
        "- Disposition: `operator-attention`",
        f"- Reason: `{error.kind}`",
        f"- Line: `{error.line_number}`",
    ]
    if error.entry_id is not None:
        lines.append(f"- QID: `{error.entry_id}`")
    lines.extend(
        (
            "- Raw candidate: `"
            f"runtime-{document_name.removesuffix('.md')}-candidate.md`",
            "",
            "The canonical interview ledger was not mutated by this candidate.",
            "",
        )
    )
    disposition_path.write_text("\n".join(lines), encoding="utf-8")


def _restore_operator_owned_answers_after_runtime_attempt(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    answers_text_before_attempt: str | None,
    execution_state: StageExecutionState,
) -> None:
    answers_path = (
        workspace_stage_root(
            root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        / "answers.md"
    )
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
            if answers_text_after_attempt is not None:
                try:
                    candidate_entries = parse_answer_candidate_entries(answers_text_after_attempt)
                except InterviewMarkdownParseError as error:
                    _retain_interview_candidate_evidence(
                        execution_state=execution_state,
                        document_name="answers.md",
                        candidate_text=answers_text_after_attempt,
                        error=error,
                    )
                else:
                    unknown_entry = next(
                        (
                            entry
                            for entry in candidate_entries
                            if entry.value.question_id not in question_ids
                        ),
                        None,
                    )
                    if unknown_entry is not None:
                        _retain_interview_candidate_evidence(
                            execution_state=execution_state,
                            document_name="answers.md",
                            candidate_text=answers_text_after_attempt,
                            error=InterviewMarkdownParseError(
                                f"Unknown answer question id `{unknown_entry.value.question_id}`.",
                                document_name="answers.md",
                                kind="unknown-question-id",
                                line_number=unknown_entry.line_number,
                                entry_id=unknown_entry.value.question_id,
                                parsed_answers=tuple(candidate_entries),
                                raw_candidate=answers_text_after_attempt,
                            ),
                        )
                    elif candidate_entries:
                        _retain_interview_candidate_evidence(
                            execution_state=execution_state,
                            document_name="answers.md",
                            candidate_text=answers_text_after_attempt,
                        )
            answers_path.parent.mkdir(parents=True, exist_ok=True)
            answers_path.write_text(empty_answers_text, encoding="utf-8")
        return

    if question_ids and answers_text_after_attempt != answers_text_before_attempt:
        if answers_text_after_attempt is not None:
            try:
                candidate_entries = parse_answer_candidate_entries(answers_text_after_attempt)
            except InterviewMarkdownParseError as error:
                _retain_interview_candidate_evidence(
                    execution_state=execution_state,
                    document_name="answers.md",
                    candidate_text=answers_text_after_attempt,
                    error=error,
                )
            else:
                unknown_entry = next(
                    (
                        entry
                        for entry in candidate_entries
                        if entry.value.question_id not in question_ids
                    ),
                    None,
                )
                if unknown_entry is not None:
                    _retain_interview_candidate_evidence(
                        execution_state=execution_state,
                        document_name="answers.md",
                        candidate_text=answers_text_after_attempt,
                        error=InterviewMarkdownParseError(
                            f"Unknown answer question id `{unknown_entry.value.question_id}`.",
                            document_name="answers.md",
                            kind="unknown-question-id",
                            line_number=unknown_entry.line_number,
                            entry_id=unknown_entry.value.question_id,
                            parsed_answers=tuple(candidate_entries),
                            raw_candidate=answers_text_after_attempt,
                        ),
                    )
                elif candidate_entries:
                    _retain_interview_candidate_evidence(
                        execution_state=execution_state,
                        document_name="answers.md",
                        candidate_text=answers_text_after_attempt,
                    )
        answers_path.parent.mkdir(parents=True, exist_ok=True)
        answers_path.write_text(answers_text_before_attempt, encoding="utf-8")


def _restore_and_merge_questions_after_runtime_attempt(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    questions_text_before_attempt: str | None,
    execution_state: StageExecutionState,
) -> None:
    """Merge runtime questions into the durable ledger without dropping prior QIDs."""

    try:
        previous_questions = (
            ()
            if questions_text_before_attempt is None
            else parse_questions_markdown(questions_text_before_attempt)
        )
    except ValueError:
        # Preserve the runtime document so canonical validation can report its malformed
        # syntax instead of masking it with a core-authored replacement.
        return

    questions_path = (
        workspace_stage_root(
            root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        / "questions.md"
    )
    try:
        current_questions_text = questions_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        current_questions_text = None

    current_questions: tuple[InterviewQuestion, ...]
    if current_questions_text is None:
        current_questions = ()
    else:
        try:
            current_questions = tuple(
                entry.value for entry in parse_question_candidate_entries(current_questions_text)
            )
        except InterviewMarkdownParseError as error:
            _retain_interview_candidate_evidence(
                execution_state=execution_state,
                document_name="questions.md",
                candidate_text=current_questions_text,
                error=error,
            )
            questions_path.parent.mkdir(parents=True, exist_ok=True)
            questions_path.write_text(
                render_questions_markdown(previous_questions),
                encoding="utf-8",
            )
            return

    merged = list(previous_questions)
    index_by_question_id = {
        question.question_id: index for index, question in enumerate(merged)
    }
    for question in current_questions:
        existing_index = index_by_question_id.get(question.question_id)
        if existing_index is None:
            index_by_question_id[question.question_id] = len(merged)
            merged.append(question)
        else:
            merged[existing_index] = question

    questions_path.parent.mkdir(parents=True, exist_ok=True)
    questions_path.write_text(render_questions_markdown(merged), encoding="utf-8")


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


def _terminalize_unhandled_post_execution_exception(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    contracts_root: Path,
    changed_at_utc: datetime | None,
    exception: Exception,
    previous_status: str | None = None,
) -> None:
    """Best-effort terminalization for exceptions after an attempt starts.

    Normal validation findings still use the repair state machine. An unexpected exception
    in discovery, interview reconciliation, or validation is a failed terminal outcome, and
    all secondary evidence writes must never replace the original exception.
    """

    if previous_status in {
        StageState.EXECUTING.value,
        StageState.VALIDATING.value,
    }:
        # A call that did not acquire a new attempt must not rewrite an existing live
        # owner. Stale lifecycle convergence is handled by the explicit reconciliation API.
        return
    try:
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
    except Exception as cleanup_error:
        exception.add_note(
            "Could not inspect stage metadata during post-execution terminalization: "
            f"{type(cleanup_error).__name__}: {cleanup_error}"
        )
        return
    if metadata is None or metadata.status not in {
        StageState.EXECUTING.value,
        StageState.VALIDATING.value,
    }:
        return

    try:
        attempt_number = (
            next_attempt_number(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            )
            - 1
        )
    except Exception as cleanup_error:
        exception.add_note(
            "Could not locate the failed attempt during post-execution terminalization: "
            f"{type(cleanup_error).__name__}: {cleanup_error}"
        )
        return
    if attempt_number < 1:
        try:
            persist_stage_status(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                status=StageState.FAILED.value,
                changed_at_utc=changed_at_utc,
            )
        except Exception as cleanup_error:
            exception.add_note(
                "Could not persist failed stage state: "
                f"{type(cleanup_error).__name__}: {cleanup_error}"
            )
        return

    attempt_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    try:
        artifact_index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
    except Exception as cleanup_error:
        exception.add_note(
            "Could not read attempt artifact index during post-execution terminalization: "
            f"{type(cleanup_error).__name__}: {cleanup_error}"
        )
        artifact_index = None
    attempt_mode = (
        "initial"
        if artifact_index is None or artifact_index.attempt_mode is None
        else artifact_index.attempt_mode
    )
    execution_state = StageExecutionState(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        attempt_number=attempt_number,
        attempt_path=attempt_path,
        stage_metadata_path=run_stage_metadata_path(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        ),
    )
    failure_message = " ".join(str(exception).split())[:2000] or type(exception).__name__
    try:
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            status=StageState.FAILED.value,
            changed_at_utc=changed_at_utc,
        )
    except Exception as cleanup_error:
        exception.add_note(
            "Could not persist failed stage state: "
            f"{type(cleanup_error).__name__}: {cleanup_error}"
        )
    try:
        write_adapter_exception_artifact(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
            exception=exception,
        )
    except Exception as cleanup_error:
        exception.add_note(
            "Could not write post-execution exception evidence: "
            f"{type(cleanup_error).__name__}: {cleanup_error}"
        )
    try:
        _write_canonical_stage_result(
            workspace_root=workspace_root,
            execution_state=execution_state,
            lifecycle_status=StageState.FAILED,
            attempt_mode=attempt_mode,
            attempt_outcome=f"post-execution processing failed: {failure_message}",
            repair_history=metadata.repair_history,
            validator_verdict="not-run",
            blockers=(f"Post-execution processing failed: {failure_message}",),
        )
    except Exception as cleanup_error:
        exception.add_note(
            "Could not write canonical failed stage result: "
            f"{type(cleanup_error).__name__}: {cleanup_error}"
        )
    try:
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
            contracts_root=contracts_root,
            attempt_mode=attempt_mode,
        )
    except Exception as cleanup_error:
        exception.add_note(
            "Could not write attempt artifact index: "
            f"{type(cleanup_error).__name__}: {cleanup_error}"
        )


def _run_single_stage_orchestration(
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
    resume_mode: bool = False,
    defer_success_publication: bool = False,
    validation_finding_provider: Callable[
        [StageExecutionState, StageOutputDiscovery], tuple[ValidationFinding, ...]
    ]
    | None = None,
) -> StageOrchestrationResult:
    questions_text_before_attempt = _read_stage_questions_text(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
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
    try:
        adapter_invocation = prepare_adapter_invocation(
            workspace_root=workspace_root,
            preparation_bundle=preparation_bundle,
            execution_state=execution_state,
            contracts_root=contracts_root,
            intervention_request_path=intervention_request_path,
            resume_mode=resume_mode,
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
    # Runtime logs and exit metadata mutate the attempt directory after stage document writes.
    # Retention must compare drafts against this stable pre-runtime boundary instead.
    attempt_started_at_ns = execution_state.attempt_path.stat().st_mtime_ns
    try:
        adapter_outcome = adapter_executor(adapter_invocation, execution_state)
    except Exception as adapter_exception:
        original_exception = adapter_exception

        def run_cleanup(action_name: str, action: Callable[[], object]) -> None:
            try:
                action()
            except Exception as cleanup_error:
                original_exception.add_note(
                    f"Could not {action_name}: {type(cleanup_error).__name__}: {cleanup_error}"
                )

        run_cleanup(
            "persist failed stage state",
            lambda: _fail_after_adapter_error(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                changed_at_utc=changed_at_utc,
            ),
        )
        try:
            write_adapter_exception_artifact(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                attempt_number=execution_state.attempt_number,
                exception=adapter_exception,
            )
        except Exception as cleanup_error:
            adapter_exception.add_note(
                "Could not write adapter exception evidence: "
                f"{type(cleanup_error).__name__}: {cleanup_error}"
            )
        run_cleanup(
            "retain unexpected runtime documents",
            lambda: retain_unexpected_runtime_documents(
                workspace_root=workspace_root,
                execution_state=execution_state,
                contracts_root=contracts_root,
                attempt_started_at_ns=attempt_started_at_ns,
            ),
        )
        run_cleanup(
            "restore core-owned repair brief",
            lambda: restore_core_owned_repair_brief(
                invocation_bundle=adapter_invocation,
                workspace_root=workspace_root,
            ),
        )
        run_cleanup(
            "write attempt artifact index",
            lambda: write_attempt_artifact_index(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                attempt_number=execution_state.attempt_number,
                contracts_root=contracts_root,
            ),
        )
        raise
    else:
        retain_unexpected_runtime_documents(
            workspace_root=workspace_root,
            execution_state=execution_state,
            contracts_root=contracts_root,
            attempt_started_at_ns=attempt_started_at_ns,
        )
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
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        _write_canonical_stage_result(
            workspace_root=workspace_root,
            execution_state=execution_state,
            lifecycle_status=StageState.BLOCKED,
            attempt_mode=adapter_invocation.attempt_mode,
            attempt_outcome=adapter_outcome.details or "blocked for operator",
            repair_history=() if metadata is None else metadata.repair_history,
            validator_verdict="not-run",
            blockers=(adapter_outcome.details or "Operator decision is required.",),
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
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        _write_canonical_stage_result(
            workspace_root=workspace_root,
            execution_state=execution_state,
            lifecycle_status=StageState.FAILED,
            attempt_mode=adapter_invocation.attempt_mode,
            attempt_outcome=adapter_outcome.details or "adapter execution failed",
            repair_history=() if metadata is None else metadata.repair_history,
            validator_verdict="not-run",
            blockers=(adapter_outcome.details or "Adapter execution failed before validation.",),
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
        contracts_root=contracts_root,
    )
    _restore_and_merge_questions_after_runtime_attempt(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        questions_text_before_attempt=questions_text_before_attempt,
        execution_state=execution_state,
    )
    _restore_operator_owned_answers_after_runtime_attempt(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        answers_text_before_attempt=answers_text_before_attempt,
        execution_state=execution_state,
    )
    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=execution_state.attempt_number,
        contracts_root=contracts_root,
        attempt_mode=adapter_invocation.attempt_mode,
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
    repair_brief_trace_path = adapter_invocation.repair_brief_path
    if repair_brief_trace_path is None:
        repair_brief_trace_path = historical_repair_brief_trace_path(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
    ensure_stage_result_references_repair_brief(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        repair_brief_path=repair_brief_trace_path,
    )
    interview_routing, interview_findings = _route_stage_questions_to_interview_with_validation(
        workspace_root=workspace_root,
        discovery=discovery,
    )
    if not interview_findings and not interview_routing.requires_interview:
        normalize_success_stage_result_blockers_if_empty(
            workspace_stage_root(
                root=workspace_root,
                work_item=work_item,
                stage=stage,
            )
            / "stage-result.md"
        )
    bootstrap_stage_result = prepare_bootstrap_stage_result_for_validation(
        workspace_root=workspace_root, work_item=work_item, stage=stage,
    )
    validation_result = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
        contracts_root=contracts_root,
    )
    if validation_finding_provider is not None:
        task_findings = validation_finding_provider(execution_state, discovery)
        if task_findings:
            validation_result = _append_validation_findings(
                validation_result=validation_result,
                findings=(*validation_result.findings, *task_findings),
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
    if interview_findings:
        validation_result = _append_validation_findings(
            validation_result=validation_result,
            findings=(*validation_result.findings, *interview_findings),
        )
    if not validation_result.findings and not interview_routing.requires_interview:
        if bootstrap_stage_result:
            # The recognized bootstrap record belongs to AIDD, not to the runtime. Render
            # its complete lifecycle record before validating it; substantive findings and
            # non-placeholder runtime drafts still follow the existing validation path.
            metadata = load_stage_metadata(
                workspace_root=workspace_root, work_item=work_item, run_id=run_id, stage=stage
            )
            _write_canonical_stage_result(
                workspace_root=workspace_root,
                execution_state=execution_state,
                lifecycle_status=StageState.SUCCEEDED,
                attempt_mode=adapter_invocation.attempt_mode,
                attempt_outcome="succeeded",
                repair_history=() if metadata is None else metadata.repair_history,
                produced_output_paths=discovery.discovered_markdown_documents,
                missing_output_paths=discovery.missing_markdown_documents,
                validator_verdict="pass",
                validator_report_path=validation_result.validator_report_path,
                repair_brief_path=repair_brief_trace_path,
            )
        final_stage_result_findings = reconcile_and_validate_stage_result_after_validation_pass(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            contracts_root=contracts_root,
        )
        if final_stage_result_findings:
            validation_result = _append_validation_findings(
                validation_result=validation_result,
                findings=final_stage_result_findings,
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
        defer_success_persistence=True,
    )
    if _should_persist_terminal_repair_history(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=execution_state.attempt_number,
        attempt_mode=adapter_invocation.attempt_mode,
        validation_transition=validation_transition,
        defer_success_publication=defer_success_publication,
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
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    repair_budget_status: str | None = None
    if validation_transition.budget_exhausted:
        repair_budget_status = "repair-budget-exhausted"
    elif validation_transition.requested_verdict is ValidationVerdict.REPAIR:
        repair_budget_status = (
            "repair-budget-final-attempt"
            if validation_transition.remaining_repair_attempts == 1
            else "repair-budget-available"
        )
    _write_canonical_stage_result(
        workspace_root=workspace_root,
        execution_state=execution_state,
        lifecycle_status=validation_transition.validation_state.next_state,
        attempt_mode=adapter_invocation.attempt_mode,
        attempt_outcome=_repair_history_outcome(validation_transition=validation_transition),
        repair_history=() if metadata is None else metadata.repair_history,
        produced_output_paths=discovery.discovered_markdown_documents,
        missing_output_paths=discovery.missing_markdown_documents,
        validator_verdict=validation_transition.resolved_verdict.value,
        validator_report_path=validation_result.validator_report_path,
        repair_brief_path=repair_brief_trace_path,
        blockers=_canonical_stage_result_blockers(
            findings=validation_result.findings,
            interview_routing=interview_routing,
        ),
        repair_budget_status=repair_budget_status,
    )
    transition = decide_post_validation_transition(
        validation_transition.validation_state,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
        defer_success_publication=defer_success_publication,
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
    resume_mode: bool = False,
    defer_success_publication: bool = False,
    validation_finding_provider: Callable[
        [StageExecutionState, StageOutputDiscovery], tuple[ValidationFinding, ...]
    ]
    | None = None,
) -> StageOrchestrationResult:
    """Run one stage and terminalize unexpected post-execution failures safely."""

    metadata_before_attempt = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    try:
        return _run_single_stage_orchestration(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            adapter_executor=adapter_executor,
            contracts_root=contracts_root,
            repair_policy=repair_policy,
            project_set=project_set,
            changed_at_utc=changed_at_utc,
            intervention_request_path=intervention_request_path,
            resume_mode=resume_mode,
            defer_success_publication=defer_success_publication,
            validation_finding_provider=validation_finding_provider,
        )
    except Exception as exception:
        _terminalize_unhandled_post_execution_exception(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            contracts_root=contracts_root,
            changed_at_utc=changed_at_utc,
            exception=exception,
            previous_status=(
                None if metadata_before_attempt is None else metadata_before_attempt.status
            ),
        )
        raise


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
    "StageInputPreflightError",
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
    "validate_required_stage_inputs",
    "publish_stage_outputs_after_validation_pass",
    "restore_core_owned_repair_brief",
    "route_stage_questions_to_interview",
    "run_single_stage_orchestration",
    "run_structural_validation_after_output_discovery",
    "update_stage_unblock_state",
]
