from __future__ import annotations

import pytest

from aidd.harness.live_remediation_evidence import (
    classify_remediation_terminal_evidence,
    read_remediation_terminal_evidence,
)


def _job_payload(status: str = "failed") -> dict[str, object]:
    return {
        "status": status,
        "terminal_evidence": {
            "schema_version": 1,
            "work_item": "WI-LIVE",
            "run_id": "run-live",
            "stage": "implement",
            "attempt_number": 2,
            "job_status": status,
            "adapter_outcome": "runtime_failure",
            "first_decisive_cause": {
                "kind": "adapter-outcome",
                "detail": "runtime_failure",
                "evidence_path": "/bundle/runtime-exit.json",
            },
            "cancellation": {"requested": False},
            "operator_wait": {"waiting": False},
        },
    }


@pytest.mark.parametrize(
    ("status", "classification"),
    (
        ("completed", "pass"),
        ("failed", "fail"),
        ("cancelled", "fail"),
        ("waiting-for-operator", "blocked"),
    ),
)
def test_remediation_terminal_evidence_preserves_typed_outcome(
    status: str,
    classification: str,
) -> None:
    evidence = read_remediation_terminal_evidence(
        _job_payload(status),
        expected_work_item="WI-LIVE",
        expected_run_id="run-live",
        expected_stage="implement",
    )

    assert evidence.attempt_number == 2
    assert evidence.adapter_outcome == "runtime_failure"
    assert evidence.first_cause_kind == "adapter-outcome"
    assert classify_remediation_terminal_evidence(evidence) == classification


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload.pop("terminal_evidence"),
        lambda payload: payload["terminal_evidence"].update({"run_id": "wrong"}),  # type: ignore[union-attr]
        lambda payload: payload["terminal_evidence"].update({"attempt_number": 0}),  # type: ignore[union-attr]
        lambda payload: payload["terminal_evidence"].pop("first_decisive_cause"),  # type: ignore[union-attr]
    ),
)
def test_remediation_terminal_evidence_rejects_incomplete_or_wrong_identity(
    mutation: object,
) -> None:
    payload = _job_payload()
    mutation(payload)  # type: ignore[operator]

    with pytest.raises(ValueError):
        read_remediation_terminal_evidence(
            payload,
            expected_work_item="WI-LIVE",
            expected_run_id="run-live",
            expected_stage="implement",
        )
