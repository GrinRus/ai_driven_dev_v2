from __future__ import annotations

import pytest

from aidd.core.interview import (
    InterviewQuestion,
    QuestionPolicy,
    interview_requires_input,
    question_policy_from_marker,
    unresolved_blocking_questions,
)


def test_question_policy_from_marker_accepts_contract_markers() -> None:
    assert question_policy_from_marker("[blocking]") == QuestionPolicy.BLOCKING
    assert question_policy_from_marker("non-blocking") == QuestionPolicy.NON_BLOCKING


def test_question_policy_from_marker_rejects_invalid_marker() -> None:
    with pytest.raises(ValueError, match="Question marker must be one of"):
        question_policy_from_marker("[urgent]")


def test_interview_question_requires_stable_id_and_text() -> None:
    with pytest.raises(ValueError, match="Question id must use a stable `Q`-prefixed token"):
        InterviewQuestion(
            question_id="issue-1",
            text="Need clarification",
            policy=QuestionPolicy.BLOCKING,
        )

    with pytest.raises(ValueError, match="Question text must not be empty"):
        InterviewQuestion(question_id="Q1", text="   ", policy=QuestionPolicy.NON_BLOCKING)


def test_unresolved_blocking_questions_returns_only_open_blockers() -> None:
    questions = (
        InterviewQuestion(
            question_id="Q1",
            text="Confirm which environment is in scope.",
            policy=QuestionPolicy.BLOCKING,
        ),
        InterviewQuestion(
            question_id="Q2",
            text="Confirm whether metrics export can be deferred.",
            policy=QuestionPolicy.NON_BLOCKING,
        ),
        InterviewQuestion(
            question_id="Q3",
            text="Confirm deadline authority for launch freeze.",
            policy=QuestionPolicy.BLOCKING,
        ),
    )

    unresolved = unresolved_blocking_questions(
        questions=questions,
        resolved_question_ids={"Q3"},
    )

    assert unresolved == (questions[0],)


def test_interview_requires_input_depends_on_unresolved_blockers() -> None:
    questions = (
        InterviewQuestion(
            question_id="Q1",
            text="Confirm legal review owner.",
            policy=QuestionPolicy.BLOCKING,
        ),
        InterviewQuestion(
            question_id="Q2",
            text="Optional formatting preference for reports.",
            policy=QuestionPolicy.NON_BLOCKING,
        ),
    )

    assert interview_requires_input(questions=questions, resolved_question_ids=set())
    assert not interview_requires_input(questions=questions, resolved_question_ids={"Q1"})
