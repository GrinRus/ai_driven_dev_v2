from __future__ import annotations

import pytest

from aidd.evals.log_analysis import (
    CoarseRuntimeEvent,
    FailureTaxonomyResult,
    NormalizedRuntimeEvent,
    classify_failure_taxonomy,
    select_first_failure_boundary,
)


def _runtime_error_event(message: str) -> CoarseRuntimeEvent:
    return CoarseRuntimeEvent(line_number=1, category="error", message=message)


def test_classify_failure_taxonomy_detects_environment_failures() -> None:
    result = classify_failure_taxonomy(
        runtime_events=(_runtime_error_event("git clone failed: network unreachable"),),
    )

    assert result.category == "environment"


def test_classify_failure_taxonomy_detects_adapter_failures_from_normalized_events() -> None:
    result = classify_failure_taxonomy(
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


def test_classify_failure_taxonomy_detects_runtime_failures_from_exit_code() -> None:
    result = classify_failure_taxonomy(aidd_exit_code=2)

    assert result == FailureTaxonomyResult(
        category="runtime",
        reason="AIDD run exited with non-zero status 2.",
    )


def test_classify_failure_taxonomy_detects_validation_failures() -> None:
    result = classify_failure_taxonomy(
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


def test_classify_failure_taxonomy_prioritizes_validation_over_aidd_exit() -> None:
    result = classify_failure_taxonomy(
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


def test_classify_failure_taxonomy_detects_scenario_verification_failures() -> None:
    result = classify_failure_taxonomy(
        aidd_exit_code=0,
        verification_exit_code=1,
    )

    assert result.category == "scenario-verification"


def test_classify_failure_taxonomy_detects_noop_execution_signals() -> None:
    result = classify_failure_taxonomy(
        runtime_events=(
            CoarseRuntimeEvent(
                line_number=10,
                category="info",
                message="Workflow run completed: no runnable stages found.",
            ),
        ),
    )

    assert result.category == "scenario-verification"
    assert "no-op execution signal" in result.reason


def test_classify_failure_taxonomy_prioritizes_validation_over_verification() -> None:
    result = classify_failure_taxonomy(
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


def test_classify_failure_taxonomy_prioritizes_environment_over_runtime() -> None:
    result = classify_failure_taxonomy(
        runtime_events=(_runtime_error_event("network unreachable"),),
        aidd_exit_code=2,
    )

    assert result.category == "environment"


def test_classify_failure_taxonomy_returns_none_without_signals() -> None:
    result = classify_failure_taxonomy()

    assert result == FailureTaxonomyResult(
        category="none",
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
def test_public_failure_classifiers_share_one_decision(
    message: str,
    expected_category: str,
) -> None:
    runtime_events = (_runtime_error_event(message),)

    taxonomy = classify_failure_taxonomy(runtime_events=runtime_events)
    boundary = select_first_failure_boundary(runtime_events=runtime_events)

    assert taxonomy.category == expected_category
    assert boundary.category == expected_category


def test_normalized_runtime_failure_is_not_lost_by_taxonomy() -> None:
    normalized_events = (
        NormalizedRuntimeEvent(
            line_number=3,
            event_kind="provider_exception",
            source="runtime",
            payload={"event": "provider_exception"},
        ),
    )

    taxonomy = classify_failure_taxonomy(normalized_events=normalized_events)
    boundary = select_first_failure_boundary(normalized_events=normalized_events)

    assert taxonomy.category == "runtime"
    assert boundary.category == "runtime"


def test_unknown_informational_message_has_no_prefix_fallback() -> None:
    runtime_events = (
        CoarseRuntimeEvent(
            line_number=1,
            category="info",
            message="provider performed a custom operation",
        ),
    )

    assert classify_failure_taxonomy(runtime_events=runtime_events).category == "none"
    assert select_first_failure_boundary(runtime_events=runtime_events).category == "none"
