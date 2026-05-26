from __future__ import annotations

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
from aidd.core.operator_frontend_models import (
    OperatorQuestionsView,
    OperatorQuestionView,
    OperatorStageView,
)
from aidd.core.run_inspection import resolve_stage_result_summary


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
                answer_text=answer.text if status == "resolved" and answer else None,
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
    return OperatorStageView(
        result=resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        ),
        questions=resolve_operator_questions_view(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        ),
    )


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
