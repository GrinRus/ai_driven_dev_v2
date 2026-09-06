from __future__ import annotations

import pytest

from aidd.evals.log_analysis import (
    CoarseRuntimeEvent,
    FailureBoundarySelection,
    NormalizedRuntimeEvent,
    select_first_failure_boundary,
)


def _runtime_error_event(message: str) -> CoarseRuntimeEvent:
    return CoarseRuntimeEvent(line_number=1, category="error", message=message)


def test_select_first_failure_boundary_detects_environment_failures() -> None:
    result = select_first_failure_boundary(
        runtime_events=(_runtime_error_event("git clone failed: network unreachable"),),
    )

    assert result.category == "environment"


def test_select_first_failure_boundary_detects_adapter_failures_from_normalized_events() -> None:
    result = select_first_failure_boundary(
        normalized_events=(
            NormalizedRuntimeEvent(
                line_number=1,
                event_kind="adapter_failure",
                source="stderr",
                payload={"event": "adapter_failure"},
            ),
        ),
    )

    assert result.category == "adapter"


def test_select_first_failure_boundary_detects_runtime_failures_from_exit_code() -> None:
    result = select_first_failure_boundary(aidd_exit_code=2)

    assert result == FailureBoundarySelection(
        category="runtime",
        signal_source="aidd-exit-code",
        signal_line_number=None,
        reason="AIDD exited with 2",
    )


def test_select_first_failure_boundary_detects_validation_failures() -> None:
    result = select_first_failure_boundary(
        aidd_exit_code=0,
        validator_failures=(
            CoarseRuntimeEvent(
                line_number=5,
                category="validator",
                message="STRUCT-001 (high) in doc: missing section",
            ),
        ),
    )

    assert result.category == "validation"
    assert "STRUCT-001" in result.reason


def test_select_first_failure_boundary_prioritizes_validation_over_aidd_exit() -> None:
    result = select_first_failure_boundary(
        aidd_exit_code=1,
        stage_metadata_failures=(
            CoarseRuntimeEvent(
                line_number=301,
                category="validator",
                message="stage `plan` attempt `3` validator `failed`",
            ),
        ),
    )

    assert result.category == "validation"
    assert "plan" in result.reason


def test_select_first_failure_boundary_detects_scenario_verification_failures() -> None:
    result = select_first_failure_boundary(
        aidd_exit_code=0,
        verification_exit_code=1,
    )

    assert result.category == "scenario-verification"


def test_select_first_failure_boundary_detects_noop_execution_signals() -> None:
    result = select_first_failure_boundary(
        runtime_events=(
            CoarseRuntimeEvent(
                line_number=10,
                category="info",
                message="Workflow run completed: no runnable stages found.",
            ),
        ),
    )

    assert result.category == "scenario-verification"
    assert result.signal_source == "runtime.log"
    assert "no runnable stages found" in result.reason


def test_select_first_failure_boundary_prioritizes_validation_over_verification() -> None:
    result = select_first_failure_boundary(
        aidd_exit_code=0,
        verification_exit_code=1,
        validator_failures=(
            CoarseRuntimeEvent(
                line_number=1,
                category="validator",
                message="validator report verdict is fail",
            ),
        ),
    )

    assert result.category == "validation"


def test_select_first_failure_boundary_prioritizes_environment_over_runtime() -> None:
    result = select_first_failure_boundary(
        runtime_events=(_runtime_error_event("network unreachable"),),
        aidd_exit_code=2,
    )

    assert result.category == "environment"


def test_select_first_failure_boundary_returns_none_without_signals() -> None:
    result = select_first_failure_boundary()

    assert result == FailureBoundarySelection(
        category="none",
        signal_source="none",
        signal_line_number=None,
        reason="No failure signal detected.",
    )


@pytest.mark.parametrize(
    ("message", "expected_category"),
    [
        ("AssertionError: expected true", "runtime"),
        ("HTTP status 503 from provider", "environment"),
        ("executable not found: codex", "environment"),
        ("No such file or directory: config.toml", "environment"),
        ("temporary failure in name resolution", "environment"),
        ("operation timed out", "environment"),
    ],
)
def test_first_failure_boundary_classifies_runtime_log_signals(
    message: str,
    expected_category: str,
) -> None:
    runtime_events = (_runtime_error_event(message),)

    boundary = select_first_failure_boundary(runtime_events=runtime_events)

    assert boundary.category == expected_category
    assert boundary.signal_source == "runtime.log"
    assert boundary.signal_line_number == 1
    assert boundary.reason == message


def test_normalized_runtime_failure_retains_event_location() -> None:
    normalized_events = (
        NormalizedRuntimeEvent(
            line_number=3,
            event_kind="provider_exception",
            source="runtime",
            payload={"event": "provider_exception"},
        ),
    )

    boundary = select_first_failure_boundary(normalized_events=normalized_events)

    assert boundary.category == "runtime"
    assert boundary.signal_source == "events.jsonl"
    assert boundary.signal_line_number == 3
    assert boundary.reason == "provider_exception"


def test_unknown_informational_message_has_no_prefix_fallback() -> None:
    runtime_events = (
        CoarseRuntimeEvent(
            line_number=1,
            category="info",
            message="provider performed a custom operation",
        ),
    )

    assert select_first_failure_boundary(runtime_events=runtime_events).category == "none"
