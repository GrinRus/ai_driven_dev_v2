from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.interview import (
    InterviewMarkdownParseError,
    InterviewQuestion,
    QuestionPolicy,
    parse_questions_markdown,
    persist_questions_document,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _example_root() -> Path:
    return _repo_root() / "contracts" / "examples" / "common-documents" / "interview-resume"


def test_interview_contract_example_bundle_has_each_candidate_disposition() -> None:
    example_root = _example_root()
    readme = (example_root / "README.md").read_text(encoding="utf-8")

    for filename in (
        "canonical-questions.md",
        "canonical-answers.md",
        "safe-candidate.md",
        "duplicate-candidate.md",
        "ambiguous-candidate.md",
        "omitted-candidate.md",
    ):
        assert (example_root / filename).is_file(), filename

    assert "operator-attention" in readme
    assert "preserving the omitted `Q2` question and answer" in readme


def test_canonical_and_omitted_interview_examples_preserve_qid_order_and_meaning() -> None:
    example_root = _example_root()
    assert parse_questions_markdown(
        (example_root / "canonical-questions.md").read_text(encoding="utf-8")
    ) == (
        InterviewQuestion(
            question_id="Q1",
            policy=QuestionPolicy.BLOCKING,
            text="Confirm which deployment environment is in scope for the resumed attempt.",
        ),
        InterviewQuestion(
            question_id="Q2",
            policy=QuestionPolicy.NON_BLOCKING,
            text="Confirm whether the optional metrics export can wait until the follow-up.",
        ),
    )
    omitted = parse_questions_markdown(
        (example_root / "omitted-candidate.md").read_text(encoding="utf-8")
    )
    assert tuple(question.question_id for question in omitted) == ("Q1",)


def test_omitted_candidate_does_not_erase_the_existing_unresolved_ledger(
    tmp_path: Path,
) -> None:
    example_root = _example_root()
    workspace_root = tmp_path / ".aidd"
    persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-INTERVIEW",
        stage="plan",
        stage_output_questions_markdown=(
            (example_root / "canonical-questions.md").read_text(encoding="utf-8")
        ),
    )

    questions_path = persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-INTERVIEW",
        stage="plan",
        stage_output_questions_markdown=(
            (example_root / "omitted-candidate.md").read_text(encoding="utf-8")
        ),
    )

    assert tuple(
        question.question_id
        for question in parse_questions_markdown(questions_path.read_text(encoding="utf-8"))
    ) == ("Q1", "Q2")


@pytest.mark.parametrize("filename", ("duplicate-candidate.md", "ambiguous-candidate.md"))
def test_rejected_candidate_examples_stop_before_mutating_the_ledger(
    tmp_path: Path,
    filename: str,
) -> None:
    example_root = _example_root()
    workspace_root = tmp_path / ".aidd"
    persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-INTERVIEW",
        stage="plan",
        stage_output_questions_markdown=(
            "# Questions\n\n## Questions\n\n"
            "- Q1 [blocking] Confirm which deployment environment is in scope.\n"
            "- Q2 [blocking] Preserve the second unresolved question.\n"
        ),
    )
    questions_path = workspace_root / "workitems/WI-INTERVIEW/stages/plan/questions.md"
    before = questions_path.read_text(encoding="utf-8")

    candidate = (example_root / filename).read_text(encoding="utf-8")
    with pytest.raises(InterviewMarkdownParseError) as error:
        persist_questions_document(
            workspace_root=workspace_root,
            work_item="WI-INTERVIEW",
            stage="plan",
            stage_output_questions_markdown=candidate,
        )

    assert error.value.kind == "duplicate-id"
    assert questions_path.read_text(encoding="utf-8") == before


def test_safe_candidate_example_is_explicitly_presentation_only() -> None:
    candidate = (_example_root() / "safe-candidate.md").read_text(encoding="utf-8")

    assert "* `Q1` [blocking]:" in candidate
    assert "  Keep the staging environment" in candidate
    assert "* `Q3` [non-blocking]" in candidate
