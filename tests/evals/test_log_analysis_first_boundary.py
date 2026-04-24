from __future__ import annotations

from aidd.evals.log_analysis import (
    CoarseRuntimeEvent,
    FailureBoundarySelection,
    NormalizedRuntimeEvent,
    select_first_failure_boundary,
)


def _runtime_event(*, line_number: int, category: str, message: str) -> CoarseRuntimeEvent:
    return CoarseRuntimeEvent(line_number=line_number, category=category, message=message)


def test_select_first_failure_boundary_prioritizes_environment_signals() -> None:
    selection = select_first_failure_boundary(
        runtime_events=(
            _runtime_event(
                line_number=8,
                category="error",
                message="network unreachable while fetching repository",
            ),
            _runtime_event(
                line_number=2,
                category="error",
                message="runtime failed with exit 1",
            ),
        ),
    )

    assert selection.category == "environment"
    assert selection.signal_source == "runtime.log"
    assert selection.signal_line_number == 8


def test_select_first_failure_boundary_uses_smallest_line_within_same_rank() -> None:
    selection = select_first_failure_boundary(
        runtime_events=(
            _runtime_event(line_number=9, category="error", message="runtime failed later"),
            _runtime_event(line_number=3, category="error", message="runtime failed earlier"),
        ),
    )

    assert selection.category == "runtime"
    assert selection.signal_line_number == 3
    assert selection.reason == "runtime failed earlier"


def test_select_first_failure_boundary_prioritizes_runtime_over_validation() -> None:
    selection = select_first_failure_boundary(
        runtime_events=(
            _runtime_event(line_number=4, category="error", message="runtime crashed"),
        ),
        validator_failures=(
            _runtime_event(
                line_number=1,
                category="validator",
                message="validator report verdict is fail",
            ),
        ),
    )

    assert selection.category == "runtime"


def test_select_first_failure_boundary_prioritizes_validation_over_verification() -> None:
    selection = select_first_failure_boundary(
        validator_failures=(
            _runtime_event(
                line_number=2,
                category="validator",
                message="validation issue detected",
            ),
        ),
        verification_exit_code=1,
    )

    assert selection.category == "validation"


def test_select_first_failure_boundary_handles_adapter_event_signal() -> None:
    selection = select_first_failure_boundary(
        normalized_events=(
            NormalizedRuntimeEvent(
                line_number=7,
                event_kind="adapter_failure",
                source="stderr",
                payload={"event": "adapter_failure"},
            ),
        ),
    )

    assert selection == FailureBoundarySelection(
        category="adapter",
        signal_source="events.jsonl",
        signal_line_number=7,
        reason="adapter_failure",
    )


def test_select_first_failure_boundary_detects_noop_runtime_signal() -> None:
    selection = select_first_failure_boundary(
        runtime_events=(
            _runtime_event(
                line_number=6,
                category="info",
                message="Workflow run completed: no runnable stages found.",
            ),
        ),
    )

    assert selection == FailureBoundarySelection(
        category="scenario-verification",
        signal_source="runtime.log",
        signal_line_number=6,
        reason="Workflow run completed: no runnable stages found.",
    )


def test_select_first_failure_boundary_returns_none_when_no_signals() -> None:
    selection = select_first_failure_boundary()

    assert selection == FailureBoundarySelection(
        category="none",
        signal_source="none",
        signal_line_number=None,
        reason="No failure signal detected.",
    )


def test_select_first_failure_boundary_ignores_successful_adapter_outcome_lines() -> None:
    selection = select_first_failure_boundary(
        runtime_events=(
            _runtime_event(
                line_number=5,
                category="info",
                message="Adapter outcome: success",
            ),
        ),
    )

    assert selection == FailureBoundarySelection(
        category="none",
        signal_source="none",
        signal_line_number=None,
        reason="No failure signal detected.",
    )
