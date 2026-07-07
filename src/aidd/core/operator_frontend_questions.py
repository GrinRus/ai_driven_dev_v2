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
from aidd.core.operator_intervention import latest_operator_intervention_request
from aidd.core.run_inspection import StageResultSummary, resolve_stage_result_summary
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
        validation=validation,
        raw_log=raw_log,
        approvals=approvals,
        stopped=stopped,
    )
    return OperatorStageDiagnostics(
        status=status,
        blocking_questions=blocking,
        validation=validation,
        raw_log=raw_log,
        approvals=approvals,
        request_change=request_change,
        stopped=stopped,
    )


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
    return OperatorValidationRepairDiagnostics(
        status=status,
        final_state=result.final_state,
        validator_pass_count=result.validator_pass_count,
        validator_fail_count=result.validator_fail_count,
        validator_report_path=result.validator_report_path,
        repair_attempts=repair_attempts,
        validation_findings=validation_findings,
        primary_validation_finding=validation_findings[0] if validation_findings else None,
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
        requests_path = (
            workspace_root
            / "workitems"
            / work_item
            / "runs"
            / run_id
            / "stages"
            / stage
            / "attempt-0001"
            / OPERATOR_REQUESTS_FILENAME
        )
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
    status = "ready" if target_documents else "stage-scope-only"
    if latest_request is not None:
        status = "has-request"
    return OperatorRequestChangeContext(
        status=status,
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
        reason=(
            "Latest operator request is available."
            if latest_request is not None
            else "Target documents are available."
            if target_documents
            else "No current-stage writable target documents are indexed yet."
        ),
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
    artifact_index = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
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
    validation: OperatorValidationRepairDiagnostics,
    raw_log: OperatorRawLogSourceDiagnostics,
    approvals: OperatorRuntimeApprovalQueueDiagnostics,
    stopped: OperatorStoppedDiagnostics,
) -> str:
    if approvals.pending_count:
        return "approval-waiting"
    if blocking.unresolved_count:
        return "blocked"
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
