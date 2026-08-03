from __future__ import annotations

import pytest

from browser_tests.test_journey_inbox import _wait_for_durable_payload


def test_inbox_durable_payload_wait_reports_phase_and_last_payload() -> None:
    payload = {"status": "pending", "job_id": "job-browser"}

    with pytest.raises(
        pytest.fail.Exception,
        match=(
            "provider-free Inbox overlay job did not converge.*"
            "last durable payload:.*'status': 'pending'"
        ),
    ):
        _wait_for_durable_payload(
            fetch=lambda: payload,
            ready=lambda candidate: candidate.get("status") == "running",
            phase="provider-free Inbox overlay job",
            timeout_seconds=0.001,
            poll_interval_seconds=0.01,
        )
