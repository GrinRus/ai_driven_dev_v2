from __future__ import annotations

from pathlib import Path

import pytest

from aidd.evals.log_analysis import (
    coarse_events_from_normalized_events,
    parse_events_jsonl,
    parse_events_jsonl_text,
)


def test_parse_events_jsonl_text_parses_structured_events() -> None:
    events_jsonl_text = "\n".join(
        (
            '{"event":"stage_transition","message":"plan -> research","source":"stdout"}',
            '{"type":"validator_result","message":"validator fail","source":"stderr"}',
            '{"event":"question_raised","message":"Need user input?"}',
            '{"message":"event without type"}',
        )
    )

    events = parse_events_jsonl_text(events_jsonl_text)

    assert [event.event_kind for event in events] == [
        "stage_transition",
        "validator_result",
        "question_raised",
        "unknown",
    ]
    assert events[0].source == "stdout"
    assert events[1].source == "stderr"
    assert events[3].source is None
    assert events[0].line_number == 1
    assert events[3].line_number == 4


def test_parse_events_jsonl_text_rejects_invalid_json_line() -> None:
    with pytest.raises(ValueError, match="Invalid JSON in events.jsonl at line 2"):
        parse_events_jsonl_text('{"event":"ok"}\n{not-json}\n')


def test_parse_events_jsonl_text_rejects_non_object_payload() -> None:
    with pytest.raises(ValueError, match="must be a JSON object"):
        parse_events_jsonl_text('["array-is-not-supported"]\n')


def test_parse_events_jsonl_reads_from_file(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text('{"event":"repair_applied","message":"repair loop"}\n', encoding="utf-8")

    events = parse_events_jsonl(events_path)

    assert len(events) == 1
    assert events[0].event_kind == "repair_applied"


def test_parse_events_jsonl_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="events.jsonl file does not exist"):
        parse_events_jsonl(tmp_path / "missing-events.jsonl")


def test_coarse_events_from_normalized_events_maps_categories() -> None:
    normalized_events = parse_events_jsonl_text(
        "\n".join(
            (
                '{"event":"runtime_error","message":"runtime failed"}',
                '{"event":"warning","message":"watch this"}',
                '{"event":"question_raised","message":"clarify?"}',
                '{"event":"repair_attempt","message":"repairing"}',
                '{"event":"validator_result","message":"validator status"}',
                '{"event":"stage_transition","message":"plan -> review"}',
                '{"event":"custom","message":"plain info"}',
            )
        )
    )

    coarse_events = coarse_events_from_normalized_events(normalized_events)

    assert [event.category for event in coarse_events] == [
        "error",
        "warning",
        "question",
        "repair",
        "validator",
        "stage",
        "info",
    ]
