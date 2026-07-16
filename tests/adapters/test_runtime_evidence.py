from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.adapters.runtime_evidence import (
    RuntimeAdapterOutcome,
    RuntimeEvidenceCommitRequest,
    RuntimeStopReason,
    adapter_outcome_for_classification,
    commit_runtime_evidence,
)


@pytest.mark.parametrize(
    ("exit_classification", "expected_outcome"),
    (
        ("success", RuntimeAdapterOutcome.SUCCESS),
        ("document_complete", RuntimeAdapterOutcome.SUCCESS),
        ("non_zero_exit", RuntimeAdapterOutcome.RUNTIME_FAILURE),
        ("runtime_non_zero_exit", RuntimeAdapterOutcome.RUNTIME_FAILURE),
        ("provider_error", RuntimeAdapterOutcome.RUNTIME_FAILURE),
        ("timeout", RuntimeAdapterOutcome.TIMEOUT),
        ("cancelled", RuntimeAdapterOutcome.CANCELLATION),
        ("user_cancelled", RuntimeAdapterOutcome.CANCELLATION),
        ("denied", RuntimeAdapterOutcome.DENIAL),
        ("blocked", RuntimeAdapterOutcome.BLOCKED),
        ("launch_failure", RuntimeAdapterOutcome.LAUNCH_FAILURE),
        ("adapter_failure", RuntimeAdapterOutcome.LAUNCH_FAILURE),
    ),
)
def test_cross_adapter_classification_table_has_canonical_outcome(
    exit_classification: str,
    expected_outcome: RuntimeAdapterOutcome,
) -> None:
    assert adapter_outcome_for_classification(exit_classification) is expected_outcome


def test_unknown_adapter_classification_is_not_inferred() -> None:
    with pytest.raises(ValueError, match="Unknown runtime exit classification"):
        adapter_outcome_for_classification("provider-no-progress")


def test_runtime_evidence_commit_writes_log_and_metadata_atomically(
    tmp_path: Path,
) -> None:
    attempt_path = tmp_path / "attempt-0001"
    paths = commit_runtime_evidence(
        RuntimeEvidenceCommitRequest(
            attempt_path=attempt_path,
            adapter_outcome=RuntimeAdapterOutcome.BLOCKED,
            exit_classification="blocked",
            exit_code=None,
            stdout_text="stdout\n",
            stderr_text="stderr\n",
            runtime_log_text="stdout\nstderr\n",
            stop_reason=RuntimeStopReason.BLOCKED,
        )
    )

    assert paths.runtime_log_path.read_text(encoding="utf-8") == "stdout\nstderr\n"
    metadata = json.loads(paths.runtime_exit_metadata_path.read_text(encoding="utf-8"))
    assert metadata == {
        "adapter_outcome": "blocked",
        "exit_classification": "blocked",
        "exit_code": None,
        "runtime_log_char_count": 14,
        "schema_version": 1,
        "stderr_char_count": 7,
        "stdout_char_count": 7,
        "stop_reason": "blocked",
    }
    assert not tuple(attempt_path.glob(".*.tmp"))


def test_success_evidence_has_no_stop_reason(tmp_path: Path) -> None:
    paths = commit_runtime_evidence(
        RuntimeEvidenceCommitRequest(
            attempt_path=tmp_path,
            adapter_outcome=RuntimeAdapterOutcome.SUCCESS,
            exit_classification="success",
            exit_code=0,
            stdout_text="",
            stderr_text="",
            runtime_log_text="",
        )
    )

    metadata = json.loads(paths.runtime_exit_metadata_path.read_text(encoding="utf-8"))
    assert "stop_reason" not in metadata


def test_runtime_evidence_request_requires_consistent_stop_reason(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="requires a stop reason"):
        RuntimeEvidenceCommitRequest(
            attempt_path=tmp_path,
            adapter_outcome=RuntimeAdapterOutcome.TIMEOUT,
            exit_classification="timeout",
            exit_code=124,
            stdout_text="",
            stderr_text="",
            runtime_log_text="",
        )
    with pytest.raises(ValueError, match="must not have a stop reason"):
        RuntimeEvidenceCommitRequest(
            attempt_path=tmp_path,
            adapter_outcome=RuntimeAdapterOutcome.SUCCESS,
            exit_classification="success",
            exit_code=0,
            stdout_text="",
            stderr_text="",
            runtime_log_text="",
            stop_reason=RuntimeStopReason.CANCELLATION,
        )
