from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidd.adapters.runtime_events import (
    detect_question_or_pause_events,
    persist_adapter_question_events,
)
from aidd.core.adapter_interview import AdapterQuestionEvent, QuestionPolicy
from aidd.runtime_logs.events import (
    MAX_LIFECYCLE_EVENT_BYTES,
    MAX_LIFECYCLE_EVENTS,
    MAX_LIFECYCLE_PROJECTION_BYTES,
    RuntimeEventIdentity,
    normalize_structured_events,
    persist_lifecycle_projection_from_jsonl,
    project_lifecycle_events,
    structured_runtime_events,
)


def test_runtime_log_events_own_structured_and_normalized_jsonl_parsing() -> None:
    run_result = SimpleNamespace(
        stdout_text='{"event":"run_started","id":"abc"}\nnot-json\n',
        stderr_text='["structured", "array"]\n',
    )
    assert structured_runtime_events(run_result=run_result) == (
        {"payload": {"event": "run_started", "id": "abc"}, "source": "stdout"},
        {"payload": ["structured", "array"], "source": "stderr"},
    )
    assert normalize_structured_events(run_result=run_result) == (
        {"event": "run_started", "id": "abc", "source": "stdout"},
        {"payload": ["structured", "array"], "source": "stderr"},
    )


@pytest.mark.parametrize(
    ("provider", "payload", "event_kind"),
    (
        (
            "codex",
            {"method": "turn/started", "timestamp": "2026-07-26T00:00:00Z"},
            "lifecycle-start",
        ),
        (
            "claude",
            {"type": "result", "status": "success", "duration": 1.25},
            "lifecycle-complete",
        ),
        (
            "qwen",
            {"event": "approval_requested", "request_id": "REQ-1"},
            "operator-request",
        ),
        (
            "generic",
            {"event": "runtime_error", "status": "failed"},
            "lifecycle-fail",
        ),
    ),
)
def test_provider_payloads_project_to_bounded_canonical_lifecycle_events(
    provider: str,
    payload: dict[str, object],
    event_kind: str,
) -> None:
    payload["prompt"] = "secret-provider-payload-" + ("x" * 20_000)
    projected = project_lifecycle_events(
        structured_events=({"payload": payload, "source": provider},),
        identity=RuntimeEventIdentity(
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            attempt="attempt-0001",
        ),
    )

    assert len(projected) == 1
    event = projected[0]
    assert event["event_kind"] == event_kind
    assert event["identity"] == {
        "work_item": "WI-001",
        "run_id": "run-001",
        "stage": "plan",
        "attempt": "attempt-0001",
    }
    assert event["evidence"] == "runtime.jsonl#line=1"
    assert len(event["payload_sha256"]) == 64
    encoded = json.dumps(event, sort_keys=True)
    assert len(encoded.encode()) <= MAX_LIFECYCLE_EVENT_BYTES
    assert "secret-provider-payload" not in encoded
    assert "prompt" not in event


def test_lifecycle_projection_has_a_fixed_total_size_bound() -> None:
    events = tuple(
        {
            "payload": {
                "event": "tool_result",
                "tool_payload": "x" * 20_000,
                "sequence": index,
            },
            "source": "generic",
        }
        for index in range(5_000)
    )

    projected = project_lifecycle_events(
        structured_events=events,
        identity=RuntimeEventIdentity(
            work_item="WI-001",
            run_id="run-001",
            stage="implement",
            attempt="attempt-0001",
        ),
    )
    encoded = b"".join(
        json.dumps(row, sort_keys=True).encode() + b"\n" for row in projected
    )

    assert len(projected) == MAX_LIFECYCLE_EVENTS + 1
    assert projected[-1]["event_kind"] == "projection-truncated"
    assert projected[-1]["outcome"] == f"omitted={5_000 - MAX_LIFECYCLE_EVENTS}"
    assert len(encoded) <= MAX_LIFECYCLE_PROJECTION_BYTES


def test_live_jsonl_keeps_native_payload_only_in_runtime_artifact(
    tmp_path: Path,
) -> None:
    attempt_path = (
        tmp_path
        / ".aidd"
        / "reports"
        / "runs"
        / "WI-007"
        / "run-007"
        / "stages"
        / "qa"
        / "attempts"
        / "attempt-0002"
    )
    attempt_path.mkdir(parents=True)
    source = attempt_path / "provider-events.jsonl"
    source.write_text(
        json.dumps(
            {
                "event": "tool_result",
                "tool_payload": "provider-secret",
                "status": "success",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    artifacts = persist_lifecycle_projection_from_jsonl(
        attempt_path=attempt_path,
        source_path=source,
    )

    assert artifacts.runtime_jsonl_path is not None
    assert "provider-secret" in artifacts.runtime_jsonl_path.read_text()
    assert artifacts.events_jsonl_path is not None
    projection = json.loads(artifacts.events_jsonl_path.read_text())
    assert "provider-secret" not in json.dumps(projection)
    assert projection["identity"] == {
        "work_item": "WI-007",
        "run_id": "run-007",
        "stage": "qa",
        "attempt": "attempt-0002",
    }

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
