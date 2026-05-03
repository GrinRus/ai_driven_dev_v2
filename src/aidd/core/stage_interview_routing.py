from __future__ import annotations

import re
from pathlib import Path

from aidd.core.interview import (
    load_answers_document,
    load_questions_document,
    resolved_question_ids,
    unresolved_blocking_questions,
)
from aidd.core.stage_models import StageInterviewRouting, StageOutputDiscovery
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.validators.models import ValidationFinding, ValidationIssueLocation

MALFORMED_INTERVIEW_DOCUMENT_CODE = "INTERVIEW-MALFORMED-DOCUMENT"


def route_stage_questions_to_interview(
    *,
    workspace_root: Path,
    discovery: StageOutputDiscovery,
) -> StageInterviewRouting:
    stage_documents_root = workspace_stage_root(
        root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    questions_path = stage_documents_root / "questions.md"
    answers_path = stage_documents_root / "answers.md"

    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    answers = load_answers_document(
        workspace_root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    unresolved = unresolved_blocking_questions(
        questions=questions,
        resolved_question_ids=resolved_question_ids(answers=answers),
    )
    unresolved_ids = tuple(question.question_id for question in unresolved)
    return StageInterviewRouting(
        stage=discovery.stage,
        work_item=discovery.work_item,
        run_id=discovery.run_id,
        attempt_number=discovery.attempt_number,
        questions_path=questions_path,
        answers_path=answers_path,
        unresolved_blocking_question_ids=unresolved_ids,
        requires_interview=bool(unresolved_ids),
    )


def route_stage_questions_to_interview_with_validation(
    *,
    workspace_root: Path,
    discovery: StageOutputDiscovery,
) -> tuple[StageInterviewRouting, tuple[ValidationFinding, ...]]:
    try:
        return (
            route_stage_questions_to_interview(
                workspace_root=workspace_root,
                discovery=discovery,
            ),
            (),
        )
    except ValueError as exc:
        document_name = "answers.md" if "answer" in str(exc).lower() else "questions.md"
        stage_documents_root = workspace_stage_root(
            root=workspace_root,
            work_item=discovery.work_item,
            stage=discovery.stage,
        )
        line_match = re.search(r"line\s+(\d+)", str(exc))
        line_number = int(line_match.group(1)) if line_match is not None else None
        routing = StageInterviewRouting(
            stage=discovery.stage,
            work_item=discovery.work_item,
            run_id=discovery.run_id,
            attempt_number=discovery.attempt_number,
            questions_path=stage_documents_root / "questions.md",
            answers_path=stage_documents_root / "answers.md",
            unresolved_blocking_question_ids=(),
            requires_interview=False,
        )
        finding = ValidationFinding(
            code=MALFORMED_INTERVIEW_DOCUMENT_CODE,
            message=(
                f"Malformed interview document `{document_name}`: {exc}. "
                "Use `- <QID> [blocking|non-blocking] <text>` for questions, "
                "`- <QID> [resolved|partial|deferred] <text>` for answers, "
                "or `- none` when there are no entries. Use non-bullet continuation "
                "prose for explanatory metadata."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=workspace_relative_path(
                    workspace_root,
                    stage_documents_root / document_name,
                ),
                line_number=line_number,
            ),
        )
        return routing, (finding,)


__all__ = [
    "MALFORMED_INTERVIEW_DOCUMENT_CODE",
    "route_stage_questions_to_interview",
    "route_stage_questions_to_interview_with_validation",
]
