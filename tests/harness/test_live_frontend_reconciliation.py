from __future__ import annotations

import pytest

from aidd.harness.live_frontend_reconciliation import (
    provisional_frontend_status,
    reconcile_frontend_checkpoints,
)


@pytest.mark.parametrize(
    ("classification", "expected"),
    (
        ("pass", "provisional-pass"),
        ("fail", "provisional-fail"),
        ("skipped", "superseded-transition"),
    ),
)
def test_running_checkpoint_starts_provisional(
    classification: str,
    expected: str,
) -> None:
    assert provisional_frontend_status(
        phase="running-stage",
        classification=classification,  # type: ignore[arg-type]
    ) == expected


def test_running_failure_is_superseded_by_durable_success_and_post_pass() -> None:
    result = reconcile_frontend_checkpoints(
        running_observed=True,
        running_classification="fail",
        post_stage_classification="pass",
        durable_stage_status="succeeded",
        stage_classification="pass",
    )

    assert result.running_status == "superseded-transition"
    assert result.post_stage_status == "provisional-pass"
    assert result.effective_classification == "pass"


@pytest.mark.parametrize("running_classification", ("fail", "pass", "skipped"))
def test_post_stage_failure_is_confirmed(
    running_classification: str,
) -> None:
    result = reconcile_frontend_checkpoints(
        running_observed=True,
        running_classification=running_classification,  # type: ignore[arg-type]
        post_stage_classification="fail",
        durable_stage_status="succeeded",
        stage_classification="pass",
    )

    assert result.running_status == "confirmed-fail"
    assert result.post_stage_status == "confirmed-fail"
    assert result.effective_classification == "fail"


def test_running_failure_remains_fail_closed_without_durable_success() -> None:
    result = reconcile_frontend_checkpoints(
        running_observed=True,
        running_classification="fail",
        post_stage_classification="pass",
        durable_stage_status="executing",
        stage_classification="pass",
    )

    assert result.running_status == "provisional-fail"
    assert result.effective_classification == "fail"
