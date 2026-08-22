from __future__ import annotations

import json
from pathlib import Path

from aidd.core.interview import (
    AnswerResolution,
    InterviewAnswer,
    QuestionPolicy,
    load_answers_document,
    load_questions_document,
    persist_answers_document,
    resolved_question_ids,
    unresolved_blocking_questions,
)
from aidd.core.operator_frontend_common import operator_answers_path, validate_operator_stage
from aidd.core.operator_frontend_logs import resolve_operator_run_log_view
from aidd.core.operator_frontend_models import (
    OperatorBlockingQuestionDiagnostics,
    OperatorInterviewCandidateDiagnostics,
    OperatorQuestionsView,
    OperatorQuestionView,
    OperatorRawLogSourceDiagnostics,
    OperatorRepairAttemptDiagnostics,
    OperatorRequestChangeContext,
    OperatorRuntimeApprovalQueueDiagnostics,
    OperatorStageDiagnostics,
    OperatorStageView,
    OperatorStoppedDiagnostics,
    OperatorValidationRepairDiagnostics,
)
from aidd.core.operator_frontend_validation import load_validator_report_findings
from aidd.core.operator_intervention import (
    ensure_intervention_allowed_for_downstream,
    latest_operator_intervention_request,
)
from aidd.core.operator_repair_extension import resolve_operator_repair_extension_preview
from aidd.core.run_inspection import (
    StageResultSummary,
    resolve_run_metadata_summary,
    resolve_stage_result_summary,
)
from aidd.core.run_lookup import latest_attempt_number
from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    load_attempt_artifact_index,
    load_stage_metadata,
    run_attempt_root,
)
from aidd.core.runtime_operator import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    RuntimeOperatorDecision,
    RuntimeOperatorRequest,
    load_operator_decisions,
    load_operator_requests,
)
from aidd.core.stage_paths import workspace_relative_path
from aidd.runtime_permissions import RuntimeOperatorDecisionAction

_REQUEST_CHANGE_BLOCKED_KEYS = frozenset(
    {
        "answers",
        "input_bundle",
        "operator_request",
        "questions",
        "repair_brief",
        "repair_context",
        "stage_brief",
        "stage_result",
        "validator_report",
    }
)
_DEFAULT_DIAGNOSTIC_LOG_TAIL_BYTES = 32 * 1024
_MAX_INTERVIEW_CANDIDATE_BYTES = 16 * 1024


def resolve_operator_questions_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> OperatorQuestionsView:
    validate_operator_stage(stage)
    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    answers = load_answers_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    answers_by_id = {answer.question_id: answer for answer in answers}
    resolved_ids = set(resolved_question_ids(answers=answers))
    question_views: list[OperatorQuestionView] = []
    for question in questions:
        answer = answers_by_id.get(question.question_id)
        if question.question_id in resolved_ids:
            status = "resolved"
        elif question.policy is QuestionPolicy.BLOCKING:
            status = "pending-blocking"
        else:
            status = "pending-non-blocking"
        question_views.append(
            OperatorQuestionView(
                question_id=question.question_id,
                text=question.text,
                policy=question.policy,
                status=status,
                answer_text=answer.text if answer else None,
                answer_resolution=answer.resolution if answer else None,
                answer_evidence_links=answer.evidence_links if answer else (),
                answer_unblock_consequence=(
                    answer.unblock_consequence if answer else None
                ),
            )
        )

    unresolved = unresolved_blocking_questions(
        questions=questions,
        resolved_question_ids=resolved_ids,
    )
    return OperatorQuestionsView(
        work_item=work_item,
        stage=stage,
        answers_path=operator_answers_path(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        ),
        questions=tuple(question_views),
        unresolved_blocking_question_ids=tuple(
            question.question_id for question in unresolved
        ),
    )


def resolve_operator_stage_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    current_configuration_identity: str | None = None,
    selected_runner: str | None = None,
    active_job: bool = False,
    max_repair_attempts: int = 2,
) -> OperatorStageView:
    validate_operator_stage(stage)
    result = resolve_stage_result_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
    )
    questions = resolve_operator_questions_view(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    return OperatorStageView(
        result=result,
        questions=questions,
        diagnostics=_stage_diagnostics(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=result.run_id,
            result=result,
            questions=questions,
            current_configuration_identity=current_configuration_identity,
            selected_runner=selected_runner,
            active_job=active_job,
            max_repair_attempts=max_repair_attempts,
        ),
    )


def _stage_diagnostics(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    result: StageResultSummary,
    questions: OperatorQuestionsView,
    current_configuration_identity: str | None = None,
    selected_runner: str | None = None,
    active_job: bool = False,
    max_repair_attempts: int = 2,
) -> OperatorStageDiagnostics:
    blocking = _blocking_question_diagnostics(
        workspace_root=workspace_root,
        questions=questions,
    )
    validation = _validation_repair_diagnostics(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        result=result,
        current_configuration_identity=current_configuration_identity,
        selected_runner=selected_runner,
        active_job=active_job,
        max_repair_attempts=max_repair_attempts,
    )
    interview_candidate = _interview_candidate_diagnostics(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        questions=questions,
    )
    raw_log = _raw_log_diagnostics(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
    )
    approvals = _approval_queue_diagnostics(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
    )
    request_change = _request_change_context(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
    )
    stopped = _stopped_diagnostics(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        result=result,
    )
    status = _stage_diagnostics_status(
        blocking=blocking,
        interview_candidate=interview_candidate,
        validation=validation,
        raw_log=raw_log,
        approvals=approvals,
        stopped=stopped,
    )
    return OperatorStageDiagnostics(
        status=status,
        blocking_questions=blocking,
        interview_candidate=interview_candidate,
        validation=validation,
        raw_log=raw_log,
        approvals=approvals,
        request_change=request_change,
        stopped=stopped,
    )


def _interview_candidate_diagnostics(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    questions: OperatorQuestionsView,
) -> OperatorInterviewCandidateDiagnostics:
    """Project retained candidate evidence without parsing runtime Markdown in the UI."""

    latest_attempt = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if latest_attempt is None:
        return _empty_interview_candidate_diagnostics()

    evidence: tuple[int, Path | None, Path | None, str | None] | None = None
    for attempt_number in range(latest_attempt, 0, -1):
        attempt_path = run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
        candidate_path: Path | None = None
        disposition_path: Path | None = None
        try:
            index = load_attempt_artifact_index(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                attempt_number=attempt_number,
            )
        except PermissionError:
            return _permission_unavailable_candidate_diagnostics(
                workspace_root=workspace_root,
                attempt_number=attempt_number,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            )
        except (OSError, ValueError, KeyError, TypeError):
            index = None
        if index is not None:
            candidate_value = index.documents.get("runtime_questions_candidate")
            if not candidate_value:
                candidate_value = index.documents.get("runtime_answers_candidate")
            disposition_value = index.documents.get("interview_candidate_disposition")
            if candidate_value:
                candidate_path = workspace_root / candidate_value
            if disposition_value:
                disposition_path = workspace_root / disposition_value
        candidate_path = candidate_path or _first_existing_candidate_path(attempt_path)
        disposition_path = disposition_path or attempt_path / "interview-candidate-disposition.md"
        if candidate_path is not None or disposition_path.exists():
            document = _candidate_document_name(candidate_path)
            evidence = (attempt_number, candidate_path, disposition_path, document)
            break

    if evidence is None:
        return _empty_interview_candidate_diagnostics()

    source_attempt, candidate_path, disposition_path, document = evidence
    try:
        disposition_text = (
            disposition_path.read_text(encoding="utf-8")
            if disposition_path is not None and disposition_path.exists()
            else ""
        )
        candidate_text, candidate_truncated = _read_bounded_candidate(candidate_path)
    except PermissionError:
        return _permission_unavailable_candidate_diagnostics(
            workspace_root=workspace_root,
            attempt_number=source_attempt,
            candidate_path=candidate_path,
            disposition_path=disposition_path,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
    except OSError as exc:
        return OperatorInterviewCandidateDiagnostics(
            status="permission-unavailable",
            document=document,
            canonical_question=None,
            raw_candidate_path=_workspace_optional_path(workspace_root, candidate_path),
            raw_candidate=None,
            raw_candidate_truncated=False,
            disposition_path=_workspace_optional_path(workspace_root, disposition_path),
            source_attempt=source_attempt,
            attempt_mode=_attempt_mode_for_candidate(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                attempt_number=source_attempt,
            ),
            runtime_id=_runtime_id_or_none(workspace_root, work_item, run_id),
            reason=f"Candidate evidence is unavailable: {exc}",
            eligible_recovery_action=None,
            eligible_recovery_detail="Restore candidate evidence access before recovery.",
        )

    qid = _disposition_value(disposition_text, "QID")
    canonical_question = next(
        (question for question in questions.questions if question.question_id == qid),
        None,
    )
    rejected = bool(disposition_text.strip())
    stale = source_attempt != latest_attempt
    status = "stale" if stale else "rejected" if rejected else "accepted"
    reason = _disposition_value(disposition_text, "Reason")
    recovery_action = "resume-stage" if status == "rejected" else None
    recovery_detail = (
        "Review the retained candidate against the canonical ledger, then resume without a repair."
        if recovery_action
        else "No recovery action is required for this candidate state."
    )
    return OperatorInterviewCandidateDiagnostics(
        status=status,
        document=document,
        canonical_question=canonical_question,
        raw_candidate_path=_workspace_optional_path(workspace_root, candidate_path),
        raw_candidate=candidate_text,
        raw_candidate_truncated=candidate_truncated,
        disposition_path=(
            _workspace_optional_path(workspace_root, disposition_path)
            if rejected
            else None
        ),
        source_attempt=source_attempt,
        attempt_mode=_attempt_mode_for_candidate(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=source_attempt,
        ),
        runtime_id=_runtime_id_or_none(workspace_root, work_item, run_id),
        reason=reason,
        eligible_recovery_action=recovery_action,
        eligible_recovery_detail=recovery_detail,
    )


def _empty_interview_candidate_diagnostics() -> OperatorInterviewCandidateDiagnostics:
    return OperatorInterviewCandidateDiagnostics(
        status="absent",
        document=None,
        canonical_question=None,
        raw_candidate_path=None,
        raw_candidate=None,
        raw_candidate_truncated=False,
        disposition_path=None,
        source_attempt=None,
        attempt_mode=None,
        runtime_id=None,
        reason=None,
        eligible_recovery_action=None,
        eligible_recovery_detail="No retained interview candidate evidence is available.",
    )


def _permission_unavailable_candidate_diagnostics(
    *,
    workspace_root: Path,
    attempt_number: int,
    work_item: str | None = None,
    run_id: str | None = None,
    stage: str | None = None,
    candidate_path: Path | None = None,
    disposition_path: Path | None = None,
) -> OperatorInterviewCandidateDiagnostics:
    attempt_mode = None
    runtime_id = None
    if work_item is not None and run_id is not None and stage is not None:
        attempt_mode = _attempt_mode_for_candidate(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
        runtime_id = _runtime_id_or_none(workspace_root, work_item, run_id)
    return OperatorInterviewCandidateDiagnostics(
        status="permission-unavailable",
        document=_candidate_document_name(candidate_path),
        canonical_question=None,
        raw_candidate_path=_workspace_optional_path(workspace_root, candidate_path),
        raw_candidate=None,
        raw_candidate_truncated=False,
        disposition_path=_workspace_optional_path(workspace_root, disposition_path),
        source_attempt=attempt_number,
        attempt_mode=attempt_mode,
        runtime_id=runtime_id,
        reason="Candidate evidence cannot be read with the current operator permissions.",
        eligible_recovery_action=None,
        eligible_recovery_detail="Restore read access before recovery.",
    )


def _first_existing_candidate_path(attempt_path: Path) -> Path | None:
    for name in ("runtime-questions-candidate.md", "runtime-answers-candidate.md"):
        candidate = attempt_path / name
        if candidate.exists():
            return candidate
    return None


def _candidate_document_name(path: Path | None) -> str | None:
    if path is None:
        return None
    if path.name == "runtime-questions-candidate.md":
        return "questions.md"
    if path.name == "runtime-answers-candidate.md":
        return "answers.md"
    return None


def _read_bounded_candidate(path: Path | None) -> tuple[str | None, bool]:
    if path is None:
        return None, False
    if not path.exists():
        return None, False
    text = path.read_text(encoding="utf-8")
    encoded = text.encode("utf-8")
    if len(encoded) <= _MAX_INTERVIEW_CANDIDATE_BYTES:
        return text, False
    bounded = encoded[:_MAX_INTERVIEW_CANDIDATE_BYTES].decode("utf-8", errors="ignore")
    return bounded, True


def _disposition_value(text: str, label: str) -> str | None:
    prefix = f"- {label}: `"
    for line in text.splitlines():
        if line.startswith(prefix) and line.endswith("`"):
            return line[len(prefix) : -1].strip() or None
    return None


def _workspace_optional_path(workspace_root: Path, path: Path | None) -> str | None:
    return workspace_relative_path(workspace_root, path) if path is not None else None


def _attempt_mode_for_candidate(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> str | None:
    try:
        index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return None if index is None else index.attempt_mode


def _runtime_id_or_none(workspace_root: Path, work_item: str, run_id: str) -> str | None:
    try:
        return resolve_run_metadata_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        ).runtime_id
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _blocking_question_diagnostics(
    *,
    workspace_root: Path,
    questions: OperatorQuestionsView,
) -> OperatorBlockingQuestionDiagnostics:
    unresolved = questions.unresolved_blocking_question_ids
    return OperatorBlockingQuestionDiagnostics(
        status="blocked" if unresolved else "clear",
        unresolved_count=len(unresolved),
        unresolved_question_ids=unresolved,
        answers_path=workspace_relative_path(workspace_root, questions.answers_path),
    )


def _validation_repair_diagnostics(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    result: StageResultSummary,
    current_configuration_identity: str | None = None,
    selected_runner: str | None = None,
    active_job: bool = False,
    max_repair_attempts: int = 2,
) -> OperatorValidationRepairDiagnostics:
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    repair_attempts = (
        tuple(
            OperatorRepairAttemptDiagnostics(
                attempt_number=entry.attempt_number,
                trigger=entry.trigger,
                outcome=entry.outcome,
                recorded_at_utc=entry.recorded_at_utc,
                validator_report_path=entry.validator_report_path,
                repair_brief_path=entry.repair_brief_path,
            )
            for entry in metadata.repair_history
        )
        if metadata is not None
        else ()
    )
    if result.validator_fail_count:
        status = (
            "repair-exhausted"
            if _stage_result_records_repair_exhaustion(
                workspace_root=workspace_root,
                result=result,
            )
            else "repair-available"
        )
    elif repair_attempts:
        status = "repair-history"
    else:
        status = "clear"
    validation_findings = load_validator_report_findings(
        workspace_root=workspace_root,
        validator_report_path=result.validator_report_path,
    )
    repair_extension = resolve_operator_repair_extension_preview(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        result=result,
        current_configuration_identity=current_configuration_identity,
        selected_runner=selected_runner,
        active_job=active_job,
        max_repair_attempts=max_repair_attempts,
    )
    return OperatorValidationRepairDiagnostics(
        status=status,
        final_state=result.final_state,
        validator_pass_count=result.validator_pass_count,
        validator_fail_count=result.validator_fail_count,
        validator_report_path=result.validator_report_path,
        repair_attempts=repair_attempts,
        validation_findings=validation_findings,
        primary_validation_finding=validation_findings[0] if validation_findings else None,
        repair_extension=repair_extension,
    )


def _stage_result_records_repair_exhaustion(
    *,
    workspace_root: Path,
    result: StageResultSummary,
) -> bool:
    for relative_path in result.document_artifact_paths:
        if not relative_path.endswith("/stage-result.md"):
            continue
        stage_result_path = workspace_root / relative_path
        try:
            text = stage_result_path.read_text(encoding="utf-8").lower()
        except OSError:
            return False
        return "repair-budget-exhausted" in text or "repair budget exhausted" in text
    return False


def _raw_log_diagnostics(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
) -> OperatorRawLogSourceDiagnostics:
    try:
        view = resolve_operator_run_log_view(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
            tail_bytes=_DEFAULT_DIAGNOSTIC_LOG_TAIL_BYTES,
        )
    except ValueError as exc:
        return OperatorRawLogSourceDiagnostics(
            status="missing",
            path=None,
            byte_size=None,
            start_byte=None,
            end_byte=None,
            truncated=False,
            truncated_head=False,
            truncated_tail=False,
            message=str(exc),
        )
    return OperatorRawLogSourceDiagnostics(
        status="truncated" if view.truncated else "available",
        path=workspace_relative_path(workspace_root, view.runtime_log_path),
        byte_size=view.byte_size,
        start_byte=view.start_byte,
        end_byte=view.end_byte,
        truncated=view.truncated,
        truncated_head=view.truncated_head,
        truncated_tail=view.truncated_tail,
        message=None,
    )


def _latest_attempt_root_or_none(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> Path | None:
    attempt_number = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_number is None:
        return None
    return run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )


def _approval_queue_diagnostics(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
) -> OperatorRuntimeApprovalQueueDiagnostics:
    attempt_root = _latest_attempt_root_or_none(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_root is None:
        requests_path = run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=1,
        ) / OPERATOR_REQUESTS_FILENAME
        decisions_path = requests_path.with_name(OPERATOR_DECISIONS_FILENAME)
        requests: tuple[RuntimeOperatorRequest, ...] = ()
        decisions: tuple[RuntimeOperatorDecision, ...] = ()
    else:
        requests_path = attempt_root / OPERATOR_REQUESTS_FILENAME
        decisions_path = attempt_root / OPERATOR_DECISIONS_FILENAME
        requests = load_operator_requests(requests_path)
        decisions = load_operator_decisions(decisions_path)
    decision_by_request = {decision.request_id: decision for decision in decisions}
    pending_ids = tuple(
        request.id
        for request in requests
        if request.id not in decision_by_request
    )
    approved = sum(1 for decision in decisions if decision.is_approval)
    denied = sum(
        1
        for decision in decisions
        if decision.action is RuntimeOperatorDecisionAction.DENY
    )
    cancelled = sum(
        1
        for decision in decisions
        if decision.action is RuntimeOperatorDecisionAction.CANCEL
    )
    return OperatorRuntimeApprovalQueueDiagnostics(
        status="approval-waiting" if pending_ids else "clear",
        requests_path=workspace_relative_path(workspace_root, requests_path),
        decisions_path=workspace_relative_path(workspace_root, decisions_path),
        requested_count=len(requests),
        pending_count=len(pending_ids),
        approved_count=approved,
        denied_count=denied,
        cancelled_count=cancelled,
        pending_request_ids=pending_ids,
    )


def _request_change_context(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
) -> OperatorRequestChangeContext:
    latest_request = latest_operator_intervention_request(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    target_documents = _request_change_target_documents(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
    )
    eligible = True
    eligibility_reason: str | None = None
    try:
        ensure_intervention_allowed_for_downstream(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
    except ValueError as exc:
        eligible = False
        eligibility_reason = str(exc)
    status = "ready" if target_documents else "stage-scope-only"
    if not eligible:
        status = "blocked-downstream-succeeded"
    elif latest_request is not None:
        status = "has-request"
    reason = (
        eligibility_reason
        or (
            "Latest operator request is available."
            if latest_request is not None
            else "Target documents are available."
            if target_documents
            else "No current-stage writable target documents are indexed yet."
        )
    )
    return OperatorRequestChangeContext(
        status=status,
        eligible=eligible,
        latest_request_id=latest_request.request_id if latest_request else None,
        latest_request_path=(
            workspace_relative_path(workspace_root, latest_request.request_path)
            if latest_request
            else None
        ),
        latest_request_excerpt=(
            latest_request.request_text[:240]
            if latest_request is not None
            else None
        ),
        target_documents=target_documents,
        reason=reason,
    )


def _request_change_target_documents(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
) -> tuple[str, ...]:
    attempt_number = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_number is None:
        return ()
    try:
        artifact_index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
    except (OSError, ValueError, KeyError, TypeError):
        return ()
    if artifact_index is None:
        return ()
    stage_marker = f"/stages/{stage}/"
    return tuple(
        path
        for key, path in sorted(artifact_index.documents.items())
        if key not in _REQUEST_CHANGE_BLOCKED_KEYS
        and path.endswith(".md")
        and stage_marker in path
    )


def _stopped_diagnostics(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    result: StageResultSummary,
) -> OperatorStoppedDiagnostics:
    attempt_root = _latest_attempt_root_or_none(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_root is not None:
        events_path = attempt_root / RUN_EVENTS_JSONL_FILENAME
        event_detail = _latest_stopped_event_detail(events_path)
        if event_detail is not None:
            return OperatorStoppedDiagnostics(
                stopped=True,
                source=workspace_relative_path(workspace_root, events_path),
                detail=event_detail,
            )
    if result.final_state == "failed" and result.validator_fail_count == 0:
        return OperatorStoppedDiagnostics(
            stopped=True,
            source=result.validator_report_path,
            detail="Stage failed without validator failures.",
        )
    return OperatorStoppedDiagnostics(stopped=False, source=None, detail=None)


def _latest_stopped_event_detail(events_path: Path) -> str | None:
    if not events_path.exists():
        return None
    latest_detail: str | None = None
    for line in events_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        event = str(payload.get("event") or payload.get("kind") or "").lower()
        message = str(payload.get("message") or payload.get("details") or "")
        if "stopped" in event or "stopped" in message.lower():
            latest_detail = message or "Workflow stopped."
    return latest_detail


def _stage_diagnostics_status(
    *,
    blocking: OperatorBlockingQuestionDiagnostics,
    interview_candidate: OperatorInterviewCandidateDiagnostics,
    validation: OperatorValidationRepairDiagnostics,
    raw_log: OperatorRawLogSourceDiagnostics,
    approvals: OperatorRuntimeApprovalQueueDiagnostics,
    stopped: OperatorStoppedDiagnostics,
) -> str:
    if approvals.pending_count:
        return "approval-waiting"
    if blocking.unresolved_count:
        return "blocked"
    if interview_candidate.status == "rejected":
        return "operator-attention"
    if interview_candidate.status == "permission-unavailable":
        return "evidence-unavailable"
    if validation.status in {"repair-available", "repair-exhausted"}:
        return validation.status
    if stopped.stopped:
        return "stopped"
    if raw_log.truncated:
        return "log-truncated"
    return "clear"


def persist_operator_answer(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    question_id: str,
    text: str,
    resolution: AnswerResolution = AnswerResolution.RESOLVED,
    evidence_links: tuple[str, ...] = (),
    unblock_consequence: str | None = None,
) -> OperatorQuestionsView:
    validate_operator_stage(stage)
    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    question_ids = {question.question_id for question in questions}
    if question_id not in question_ids:
        raise ValueError(
            f"Question id `{question_id}` does not exist for work item "
            f"`{work_item}` stage `{stage}`."
        )

    persist_answers_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        incoming_answers=(
            InterviewAnswer(
                question_id=question_id,
                text=text,
                resolution=resolution,
                evidence_links=evidence_links,
                unblock_consequence=unblock_consequence,
            ),
        ),
    )
    return resolve_operator_questions_view(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )

__all__ = [
    "persist_operator_answer",
    "resolve_operator_questions_view",
    "resolve_operator_stage_view",
]
