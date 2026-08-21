from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.interview import (
    AnswerResolution,
    InterviewAnswer,
    InterviewMarkdownParseError,
    InterviewQuestion,
    QuestionPolicy,
    parse_answer_candidates_markdown,
    parse_question_candidates_markdown,
    parse_questions_markdown,
    persist_questions_document,
)


def test_question_candidate_parser_normalizes_safe_markers_punctuation_and_continuation() -> None:
    parsed = parse_question_candidates_markdown(
        "\n".join(
            (
                "# Questions",
                "",
                "## Questions",
                "",
                "* `Q1` [blocking]: Confirm which deployment environment is in scope.",
                "  Keep the staging environment as the bounded assumption.",
                "* Q2: [non-blocking] Include the run summary in follow-up evidence.",
                "",
            )
        )
    )

    assert parsed == (
        InterviewQuestion(
            question_id="Q1",
            policy=QuestionPolicy.BLOCKING,
            text=(
                "Confirm which deployment environment is in scope. "
                "Keep the staging environment as the bounded assumption."
            ),
        ),
        InterviewQuestion(
            question_id="Q2",
            policy=QuestionPolicy.NON_BLOCKING,
            text="Include the run summary in follow-up evidence.",
        ),
    )


def test_answer_candidate_parser_normalizes_safe_markers_and_preserves_canonical_context() -> None:
    parsed = parse_answer_candidates_markdown(
        "\n".join(
            (
                "# Answers",
                "",
                "## Answers",
                "",
                "* Q1: [resolved]: Use staging for this attempt.",
                "  Production remains out of scope.",
                "",
            )
        )
    )

    assert parsed == (
        InterviewAnswer(
            question_id="Q1",
            resolution=AnswerResolution.RESOLVED,
            text="Use staging for this attempt. Production remains out of scope.",
        ),
    )
    assert parsed[0].question_id == "Q1"
    assert parsed[0].resolution == AnswerResolution.RESOLVED
    assert parsed[0].text == "Use staging for this attempt. Production remains out of scope."
    assert parsed[0].evidence_links == ()


@pytest.mark.parametrize(
    ("candidate", "expected_kind"),
    (
        (
            "# Questions\n\n## Questions\n\n"
            "- Q1 [blocking] Confirm the environment.\n"
            "- Q1 [blocking] Confirm the environment.\n",
            "duplicate-id",
        ),
        (
            "# Questions\n\n## Questions\n\n"
            "- Q1 [blocking] Use staging.\n"
            "- Q1 [non-blocking] Use production.\n",
            "ambiguous-candidate",
        ),
    ),
)
def test_candidate_parser_rejects_duplicate_or_ambiguous_qids_with_raw_evidence(
    candidate: str,
    expected_kind: str,
) -> None:
    with pytest.raises(InterviewMarkdownParseError) as error:
        parse_question_candidates_markdown(candidate)

    assert error.value.kind == expected_kind
    assert error.value.raw_candidate == candidate


def test_persistence_ingests_safe_candidate_and_writes_canonical_markdown(tmp_path: Path) -> None:
    candidate = (
        "# Questions\n\n## Questions\n\n"
        "* `Q1` [blocking]: Confirm the environment.\n"
        "  Keep staging as the bounded assumption.\n"
    )
    questions_path = persist_questions_document(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-001",
        stage="plan",
        stage_output_questions_markdown=candidate,
    )

    assert questions_path.read_text(encoding="utf-8") == (
        "# Questions\n\n## Questions\n\n"
        "- `Q1` `[blocking]` Confirm the environment. Keep staging as the bounded assumption.\n"
    )
    parsed = parse_questions_markdown(questions_path.read_text(encoding="utf-8"))
    assert parsed[0].question_id == "Q1"
