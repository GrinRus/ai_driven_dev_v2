from __future__ import annotations

from aidd.evals.log_analysis import (
    parse_events_jsonl_text,
    parse_runtime_log_text,
    select_first_failure_boundary,
    summarize_runtime_provider_diagnostics,
)


def test_parse_runtime_log_text_classifies_coarse_events() -> None:
    runtime_log_text = "\n".join(
        (
            "Stage plan -> research",
            "Validator verdict: fail",
            "Need clarification from user?",
            "Repair attempt #1",
            "WARNING: nearing token budget",
            "Traceback (most recent call last):",
            "plain informational line",
        )
    )

    events = parse_runtime_log_text(runtime_log_text)

    assert [event.category for event in events] == [
        "stage",
        "validator",
        "question",
        "repair",
        "warning",
        "error",
        "info",
    ]
    assert events[0].line_number == 1
    assert events[-1].line_number == 7


def test_parse_runtime_log_ignores_blank_lines() -> None:
    events = parse_runtime_log_text("line one\n\n   \nline two\n")

    assert [event.message for event in events] == ["line one", "line two"]
    assert [event.line_number for event in events] == [1, 4]


def test_first_failure_boundary_returns_first_error_signal() -> None:
    selection = select_first_failure_boundary(
        runtime_events=parse_runtime_log_text(
            "\n".join(
                (
                    "initial info",
                    "validator says fail",
                    "runtime failed with exit 1",
                    "another error line",
                )
            )
        ),
    )

    assert selection.category == "runtime"
    assert selection.signal_source == "runtime.log"
    assert selection.signal_line_number == 3
    assert selection.reason == "runtime failed with exit 1"


def test_first_failure_boundary_reports_absence_of_error_signal() -> None:
    selection = select_first_failure_boundary(
        runtime_events=parse_runtime_log_text("all good\nstill good\n"),
    )

    assert selection.category == "none"
    assert selection.signal_source == "none"
    assert selection.signal_line_number is None


def test_summarize_runtime_provider_diagnostics_reports_model_retry_and_rate_limit() -> None:
    events = parse_events_jsonl_text(
        "\n".join(
            (
                (
                    '{"type":"system","subtype":"init","model":"kimi-for-coding",'
                    '"output_style":"default","claude_code_version":"2.1.85"}'
                ),
                (
                    '{"source":"stdout","type":"system","subtype":"api_retry",'
                    '"error":"rate_limit",'
                    '"error_status":429,"attempt":1,"max_retries":10,'
                    '"retry_delay_ms":591.0}'
                ),
            )
        )
    )

    summary = summarize_runtime_provider_diagnostics(events)

    assert summary.model_profiles == (
        "line 1: model=kimi-for-coding; output_style=default; runtime_version=2.1.85",
    )
    assert summary.retry_signals == (
        "line 2: source=stdout; type=system; subtype=api_retry; "
        "error=rate_limit; error_status=429; attempt=1; max_retries=10; "
        "retry_delay_ms=591.0",
    )
    assert summary.rate_limit_signals == summary.retry_signals


def test_summarize_runtime_provider_diagnostics_ignores_long_thinking_text() -> None:
    events = parse_events_jsonl_text(
        "\n".join(
            (
                (
                    '{"source":"stdout","type":"assistant","message":{"content":['
                    '{"type":"thinking","thinking":"I should inspect rate limit notes later."}'
                    "]}}"
                ),
                (
                    '{"source":"stdout","type":"system","subtype":"api_retry",'
                    '"error":"rate_limit","error_status":429}'
                ),
            )
        )
    )

    summary = summarize_runtime_provider_diagnostics(events)

    assert summary.rate_limit_signals == (
        "line 2: source=stdout; type=system; subtype=api_retry; error=rate_limit; error_status=429",
    )
