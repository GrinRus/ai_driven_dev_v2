from __future__ import annotations

from aidd.evals.log_analysis import (
    CoarseRuntimeEvent,
    FailureBoundarySelection,
    parse_events_jsonl_text,
    parse_runtime_log_text,
    select_first_failure_boundary,
    summarize_first_failure,
)


def _event(*, line_number: int, category: str, message: str) -> CoarseRuntimeEvent:
    return CoarseRuntimeEvent(line_number=line_number, category=category, message=message)


def test_regression_ambiguous_signals_prioritize_lifecycle_boundary() -> None:
    selection = select_first_failure_boundary(
        runtime_events=(
            _event(line_number=1, category="error", message="runtime failed with exit 1"),
        ),
        normalized_events=parse_events_jsonl_text(
            '{"event":"adapter_failure","message":"adapter protocol mismatch"}\n'
        ),
        validator_failures=(
            _event(
                line_number=1,
                category="validator",
                message="validator report verdict is fail",
            ),
        ),
    )

    assert selection == FailureBoundarySelection(
        category="adapter",
        signal_source="events.jsonl",
        signal_line_number=1,
        reason="adapter_failure",
    )


def test_regression_multi_error_prefers_earliest_runtime_line_signal() -> None:
    selection = select_first_failure_boundary(
        runtime_events=(
            _event(line_number=9, category="error", message="late runtime failure"),
            _event(line_number=2, category="error", message="early runtime failure"),
        ),
        aidd_exit_code=4,
    )

    assert selection == FailureBoundarySelection(
        category="runtime",
        signal_source="runtime.log",
        signal_line_number=2,
        reason="early runtime failure",
    )


def test_regression_empty_runtime_log_inputs_remain_stable() -> None:
    runtime_events = parse_runtime_log_text("")
    summary = summarize_first_failure(runtime_log_text="")
    selection = select_first_failure_boundary(runtime_events=runtime_events)

    assert runtime_events == ()
    assert summary == "no failure signal found"
    assert selection.category == "none"


def test_regression_empty_events_jsonl_inputs_remain_stable() -> None:
    normalized_events = parse_events_jsonl_text("")
    selection = select_first_failure_boundary(normalized_events=normalized_events)

    assert normalized_events == ()
    assert selection == FailureBoundarySelection(
        category="none",
        signal_source="none",
        signal_line_number=None,
        reason="No failure signal detected.",
    )


def test_regression_environment_beats_adapter_on_competing_normalized_signals() -> None:
    normalized_events = parse_events_jsonl_text(
        "\n".join(
            (
                '{"event":"adapter_failure"}',
                '{"event":"network_unreachable"}',
            )
        )
    )
    selection = select_first_failure_boundary(normalized_events=normalized_events)

    assert selection.category == "environment"
    assert selection.signal_line_number == 2
