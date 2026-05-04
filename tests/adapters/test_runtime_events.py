from __future__ import annotations

from pathlib import Path

from aidd.adapters.runtime_events import (
    detect_question_or_pause_events,
    persist_adapter_question_events,
)
from aidd.core.adapter_interview import AdapterQuestionEvent, QuestionPolicy


def test_detect_question_or_pause_events_ignores_invalid_runtime_question_ids() -> None:
    detection = detect_question_or_pause_events(
        normalized_events=(
            {
                "event": "question_raised",
                "question_id": "Question 1",
                "question": "Who owns rollout approval?",
                "source": "stdout",
            },
        )
    )

    assert len(detection.question_events) == 1
    assert detection.question_events[0].question_id is None
    assert detection.question_events[0].text == "Who owns rollout approval?"
    assert detection.question_events[0].policy is QuestionPolicy.BLOCKING


def test_detect_question_or_pause_events_uses_default_text_only_for_pause_event() -> None:
    detection = detect_question_or_pause_events(
        normalized_events=(
            {"event": "input_required", "source": "stderr"},
            {"event": "question_raised", "source": "stdout"},
        )
    )

    assert detection.pause_detected is True
    assert len(detection.question_events) == 1
    assert detection.question_events[0].text == "Runtime paused and requires operator input."


def test_persist_adapter_question_events_creates_empty_answers_document(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    questions_path = persist_adapter_question_events(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        adapter_question_events=(
            AdapterQuestionEvent(
                text="Who approves release?",
                question_id="Q1",
                policy=QuestionPolicy.BLOCKING,
            ),
        ),
    )

    assert questions_path is not None
    assert "Who approves release?" in questions_path.read_text(encoding="utf-8")
    answers_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "answers.md"
    assert "- none" in answers_path.read_text(encoding="utf-8")


def test_persist_adapter_question_events_preserves_misplaced_answers_for_promotion(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    output_answers_path = stage_root / "output" / "answers.md"
    output_answers_path.parent.mkdir(parents=True)
    output_answers_path.write_text(
        "# Answers\n\n- `Q1` `[resolved]` Release manager approves.\n",
        encoding="utf-8",
    )

    persist_adapter_question_events(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        adapter_question_events=(
            AdapterQuestionEvent(text="Who approves release?", question_id="Q1"),
        ),
    )

    assert not (stage_root / "answers.md").exists()
