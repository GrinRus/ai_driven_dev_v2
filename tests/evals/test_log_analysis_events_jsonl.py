from __future__ import annotations

import pytest

from aidd.evals.log_analysis import (
    parse_events_jsonl_text,
    select_first_failure_boundary,
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


@pytest.mark.parametrize(
    ("event_kind", "expected_category"),
    (
        ("runtime_error", "runtime"),
        ("warning", "none"),
        ("question_raised", "none"),
        ("repair_attempt", "none"),
        ("validator_result", "none"),
        ("stage_transition", "none"),
        ("custom", "none"),
    ),
)
def test_normalized_event_failure_selection_preserves_nonfailure_signals(
    event_kind: str,
    expected_category: str,
) -> None:
    events = parse_events_jsonl_text("\n" + '{"event":"' + event_kind + '"}\n')

    selection = select_first_failure_boundary(normalized_events=events)

    assert selection.category == expected_category
    if expected_category == "runtime":
        assert selection.signal_source == "events.jsonl"
        assert selection.signal_line_number == 2
        assert selection.reason == event_kind
    else:
        assert selection.signal_source == "none"
        assert selection.signal_line_number is None
