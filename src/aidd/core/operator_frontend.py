from __future__ import annotations

from dataclasses import dataclass
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
from aidd.core.run_inspection import (
    RunArtifactsSummary,
    RunLogSummary,
    RunMetadataSummary,
    StageResultSummary,
    resolve_run_artifacts_summary,
    resolve_run_log_summary,
    resolve_run_metadata_summary,
    resolve_stage_result_summary,
)
from aidd.core.stages import STAGES, is_valid_stage


@dataclass(frozen=True, slots=True)
class OperatorQuestionView:
    question_id: str
    text: str
    policy: QuestionPolicy
    status: str


@dataclass(frozen=True, slots=True)
class OperatorQuestionsView:
    work_item: str
    stage: str
    answers_path: Path
    questions: tuple[OperatorQuestionView, ...]
    unresolved_blocking_question_ids: tuple[str, ...]

    @property
    def has_unresolved_blocking_questions(self) -> bool:
        return bool(self.unresolved_blocking_question_ids)


@dataclass(frozen=True, slots=True)
class OperatorRunView:
    metadata: RunMetadataSummary


@dataclass(frozen=True, slots=True)
class OperatorStageView:
    result: StageResultSummary
    questions: OperatorQuestionsView


def _validate_stage(stage: str) -> None:
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}.")


def _answers_path(*, workspace_root: Path, work_item: str, stage: str) -> Path:
    return workspace_root / "workitems" / work_item / "stages" / stage / "answers.md"


def resolve_operator_run_view(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str | None = None,
) -> OperatorRunView:
    return OperatorRunView(
        metadata=resolve_run_metadata_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )
    )


def resolve_operator_run_log_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunLogSummary:
    _validate_stage(stage)
    return resolve_run_log_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        attempt_number=attempt_number,
    )


def resolve_operator_artifacts_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunArtifactsSummary:
    _validate_stage(stage)
    return resolve_run_artifacts_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        attempt_number=attempt_number,
    )


def resolve_operator_questions_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> OperatorQuestionsView:
    _validate_stage(stage)
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
    resolved_ids = set(resolved_question_ids(answers=answers))
    question_views: list[OperatorQuestionView] = []
    for question in questions:
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
            )
        )

    unresolved = unresolved_blocking_questions(
        questions=questions,
        resolved_question_ids=resolved_ids,
    )
    return OperatorQuestionsView(
        work_item=work_item,
        stage=stage,
        answers_path=_answers_path(
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
    _validate_stage(stage)
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
    _validate_stage(stage)
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
