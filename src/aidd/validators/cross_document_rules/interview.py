from __future__ import annotations

from aidd.core.interview import (
    AnswerResolution,
    InterviewMarkdownParseError,
    QuestionPolicy,
    parse_answer_entries,
    parse_question_entries,
)
from aidd.validators.cross_document_rules.context import (
    CrossDocumentContext,
    extract_section_lines,
    workspace_relative,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation

ANSWER_WITHOUT_QUESTION_CODE = "CROSS-ANSWER-WITHOUT-QUESTION"
DUPLICATE_QUESTION_ID_CODE = "CROSS-DUPLICATE-QUESTION-ID"
DUPLICATE_ANSWER_ID_CODE = "CROSS-DUPLICATE-ANSWER-ID"
BLOCKING_UNANSWERED_CODE = "CROSS-BLOCKING-UNANSWERED"
MALFORMED_INTERVIEW_DOCUMENT_CODE = "INTERVIEW-MALFORMED-DOCUMENT"


def _stage_status(stage_result_text: str | None) -> str | None:
    if stage_result_text is None:
        return None
    import re

    pattern = re.compile(r"`?(succeeded|failed|blocked|needs-input)`?", re.IGNORECASE)
    for _, line in extract_section_lines(stage_result_text, heading="Status"):
        match = pattern.search(line)
        if match is not None:
            return match.group(1).lower()
    return None


def _parse_finding(error: InterviewMarkdownParseError) -> ValidationFinding:
    if error.kind == "duplicate-id" and error.entry_id is not None:
        is_question = error.document_name == "questions.md"
        return ValidationFinding(
            code=DUPLICATE_QUESTION_ID_CODE if is_question else DUPLICATE_ANSWER_ID_CODE,
            message=(
                f"Duplicate {'question' if is_question else 'answer'} id "
                f"`{error.entry_id}` in {error.document_name}."
            ),
            severity="high",
            location=ValidationIssueLocation(error.document_name, error.line_number),
        )
    return ValidationFinding(
        code=MALFORMED_INTERVIEW_DOCUMENT_CODE,
        message=f"Malformed interview document `{error.document_name}`: {error}",
        severity="high",
        location=ValidationIssueLocation(error.document_name, error.line_number),
    )


def validate_interview(context: CrossDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    question_ids: dict[str, int] = {}
    blocking_ids: dict[str, int] = {}
    answer_ids: dict[str, int] = {}
    resolved_ids: set[str] = set()
    questions_usable = True
    answers_usable = True

    if context.questions_text is not None:
        try:
            questions = parse_question_entries(context.questions_text)
        except InterviewMarkdownParseError as error:
            questions = error.parsed_questions
            questions_usable = error.kind == "duplicate-id" or bool(questions)
            finding = _parse_finding(error)
            findings.append(
                ValidationFinding(
                    finding.code,
                    finding.message,
                    finding.severity,
                    ValidationIssueLocation(
                        workspace_relative(context.questions_path, context.workspace_root),
                        finding.location.line_number if finding.location else None,
                    ),
                )
            )
        question_ids = {entry.value.question_id: entry.line_number for entry in questions}
        blocking_ids = {
            entry.value.question_id: entry.line_number
            for entry in questions
            if entry.value.policy is QuestionPolicy.BLOCKING
        }

    if context.answers_text is not None:
        try:
            answers = parse_answer_entries(context.answers_text)
        except InterviewMarkdownParseError as error:
            answers = error.parsed_answers
            answers_usable = error.kind == "duplicate-id" or bool(answers)
            finding = _parse_finding(error)
            findings.append(
                ValidationFinding(
                    finding.code,
                    finding.message,
                    finding.severity,
                    ValidationIssueLocation(
                        workspace_relative(context.answers_path, context.workspace_root),
                        finding.location.line_number if finding.location else None,
                    ),
                )
            )
        answer_ids = {entry.value.question_id: entry.line_number for entry in answers}
        resolved_ids = {
            entry.value.question_id
            for entry in answers
            if entry.value.resolution is AnswerResolution.RESOLVED
        }
        if questions_usable and answers_usable:
            for question_id, line_number in answer_ids.items():
                if question_id in question_ids:
                    continue
                findings.append(
                    ValidationFinding(
                        code=ANSWER_WITHOUT_QUESTION_CODE,
                        message=(
                            f"Answer references `{question_id}` but no matching question exists "
                            "in questions.md."
                        ),
                        severity="high",
                        location=ValidationIssueLocation(
                            workspace_relative(context.answers_path, context.workspace_root),
                            line_number,
                        ),
                    )
                )

    if questions_usable and answers_usable:
        stage_status = _stage_status(context.stage_result_text)
        for question_id, line_number in blocking_ids.items():
            if question_id in resolved_ids:
                continue
            message = (
                f"`{question_id}` is marked `[blocking]` and has no matching `[resolved]` answer "
                "in `answers.md`."
            )
            if stage_status == "succeeded":
                message += " Stage status must not be `succeeded` while blocking questions remain."
            findings.append(
                ValidationFinding(
                    code=BLOCKING_UNANSWERED_CODE,
                    message=message,
                    severity="critical",
                    location=ValidationIssueLocation(
                        workspace_relative(context.questions_path, context.workspace_root),
                        line_number,
                    ),
                )
            )
    return tuple(findings)
