from __future__ import annotations

import pytest

from aidd.evals.log_analysis import select_first_failure_boundary
from aidd.harness.eval_reports import stage_failure_events_from_timing_payload


@pytest.mark.parametrize("stage_status", ("failed", "blocked"))
def test_stage_failure_evidence_retains_repair_and_terminal_details(stage_status: str) -> None:
    payload: dict[str, object] = {
        "stages": [
            {
                "stage": "qa",
                "status": stage_status,
                "final_failure_code": "repair-limit-exceeded",
                "attempts": [
                    {
                        "attempt": 1,
                        "validation_result": "failed",
                        "terminal_status": "repair-needed",
                        "runtime_exit_classification": "success",
                        "repair_reason": "missing verification evidence",
                    },
                    {
                        "attempt": 2,
                        "validation_result": stage_status,
                        "terminal_status": stage_status,
                        "runtime_exit_classification": "success",
                        "repair_reason": "verification evidence still incomplete",
                    },
                ],
            },
        ],
    }

    events = stage_failure_events_from_timing_payload(payload)
    selection = select_first_failure_boundary(
        stage_metadata_failures=events,
        aidd_exit_code=1,
        verification_exit_code=9,
    )

    assert len(events) == 2
    assert [event.category for event in events] == ["validator", "validator"]
    assert [event.line_number for event in events] == [101, 102]
    assert "stage `qa` attempt `1` validator `failed`" in events[0].message
    assert "repair reason: missing verification evidence" in events[0].message
    assert "final failure code `repair-limit-exceeded`" in events[1].message
    assert "preceding repair reason: verification evidence still incomplete" in events[1].message
    assert selection.category == "validation"
    assert selection.signal_source == "stage-metadata"
    assert selection.signal_line_number == 101
    assert selection.reason == events[0].message


def test_successful_repair_does_not_become_a_terminal_failure() -> None:
    events = stage_failure_events_from_timing_payload(
        {
            "stages": [
                {
                    "stage": "qa",
                    "status": "succeeded",
                    "attempts": [
                        {"attempt": 1, "validation_result": "failed"},
                        {"attempt": 2, "validation_result": "passed"},
                    ],
                },
            ],
        }
    )

    assert events == ()
    assert select_first_failure_boundary(stage_metadata_failures=events).category == "none"
