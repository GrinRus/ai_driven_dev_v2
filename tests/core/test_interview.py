from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.interview import (
    AdapterQuestionEvent,
    AnswerResolution,
    InterviewAnswer,
    InterviewQuestion,
    QuestionPolicy,
    answer_resolution_from_marker,
    interview_requires_input,
    parse_answers_markdown,
    parse_questions_markdown,
    persist_answers_document,
    persist_questions_document,
    question_policy_from_marker,
    render_answers_markdown,
    render_questions_markdown,
    stage_has_unresolved_blocking_questions,
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


def test_parse_and_render_questions_markdown_round_trip() -> None:
    questions = (
        InterviewQuestion(
            question_id="Q1",
            text="Confirm launch scope for the first milestone.",
            policy=QuestionPolicy.BLOCKING,
        ),
        InterviewQuestion(
            question_id="Q2",
            text="Optional naming convention alignment for stage outputs.",
            policy=QuestionPolicy.NON_BLOCKING,
        ),
    )

    rendered = render_questions_markdown(questions)
    parsed = parse_questions_markdown(rendered)

    assert parsed == questions


def test_persist_questions_document_uses_stage_output_when_provided(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_output = (
        "# Questions\n\n"
        "## Questions\n\n"
        "- Q1 [blocking] Confirm the deployment environment for the first release.\n"
    )

    questions_path = persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="idea",
        stage_output_questions_markdown=stage_output,
    )

    assert questions_path.exists()
    assert parse_questions_markdown(questions_path.read_text(encoding="utf-8")) == (
        InterviewQuestion(
            question_id="Q1",
            text="Confirm the deployment environment for the first release.",
            policy=QuestionPolicy.BLOCKING,
        ),
    )


def test_persist_questions_document_appends_adapter_events(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="idea",
        stage_output_questions_markdown=(
            "# Questions\n\n"
            "## Questions\n\n"
            "- Q1 [blocking] Confirm whether compliance review is required.\n"
        ),
    )

    questions_path = persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="idea",
        adapter_question_events=(
            AdapterQuestionEvent(
                text="Clarify fallback behavior when no release owner is assigned.",
                policy=QuestionPolicy.BLOCKING,
            ),
            AdapterQuestionEvent(
                question_id="Q9",
                text="Optional preference for report section ordering.",
                policy=QuestionPolicy.NON_BLOCKING,
            ),
        ),
    )

    assert parse_questions_markdown(questions_path.read_text(encoding="utf-8")) == (
        InterviewQuestion(
            question_id="Q1",
            text="Confirm whether compliance review is required.",
            policy=QuestionPolicy.BLOCKING,
        ),
        InterviewQuestion(
            question_id="Q2",
            text="Clarify fallback behavior when no release owner is assigned.",
            policy=QuestionPolicy.BLOCKING,
        ),
        InterviewQuestion(
            question_id="Q9",
            text="Optional preference for report section ordering.",
            policy=QuestionPolicy.NON_BLOCKING,
        ),
    )


def test_answer_resolution_from_marker_accepts_contract_markers() -> None:
    assert answer_resolution_from_marker("[resolved]") == AnswerResolution.RESOLVED
    assert answer_resolution_from_marker("partial") == AnswerResolution.PARTIAL
    assert answer_resolution_from_marker("deferred") == AnswerResolution.DEFERRED


def test_parse_and_render_answers_markdown_round_trip() -> None:
    answers = (
        InterviewAnswer(
            question_id="Q1",
            resolution=AnswerResolution.RESOLVED,
            text="Deployment environment is staging-first, then production.",
        ),
        InterviewAnswer(
            question_id="Q2",
            resolution=AnswerResolution.PARTIAL,
            text="Metrics export schema is agreed, retention policy still pending.",
        ),
    )

    rendered = render_answers_markdown(answers)
    parsed = parse_answers_markdown(rendered)

    assert parsed == answers


def test_persist_answers_document_merges_without_losing_prior_answers(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    persist_answers_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="idea",
        stage_output_answers_markdown=(
            "# Answers\n\n"
            "## Answers\n\n"
            "- Q1 [resolved] Compliance review is required before rollout.\n"
            "- Q2 [partial] Launch checklist draft is ready; legal sign-off is pending.\n"
        ),
    )

    answers_path = persist_answers_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="idea",
        incoming_answers=(
            InterviewAnswer(
                question_id="Q2",
                resolution=AnswerResolution.RESOLVED,
                text="Legal sign-off completed; checklist is approved.",
            ),
            InterviewAnswer(
                question_id="Q3",
                resolution=AnswerResolution.DEFERRED,
                text="Observability naming convention deferred to `plan` stage.",
            ),
        ),
    )

    assert parse_answers_markdown(answers_path.read_text(encoding="utf-8")) == (
        InterviewAnswer(
            question_id="Q1",
            resolution=AnswerResolution.RESOLVED,
            text="Compliance review is required before rollout.",
        ),
        InterviewAnswer(
            question_id="Q2",
            resolution=AnswerResolution.RESOLVED,
            text="Legal sign-off completed; checklist is approved.",
        ),
        InterviewAnswer(
            question_id="Q3",
            resolution=AnswerResolution.DEFERRED,
            text="Observability naming convention deferred to `plan` stage.",
        ),
    )


def test_partial_answers_keep_blocking_questions_unresolved(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_questions_markdown=(
            "# Questions\n\n"
            "## Questions\n\n"
            "- Q1 [blocking] Confirm release owner approval before rollout.\n"
        ),
    )
    persist_answers_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_answers_markdown=(
            "# Answers\n\n"
            "## Answers\n\n"
            "- Q1 [partial] Approval thread started; final sign-off still pending.\n"
        ),
    )

    assert stage_has_unresolved_blocking_questions(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
