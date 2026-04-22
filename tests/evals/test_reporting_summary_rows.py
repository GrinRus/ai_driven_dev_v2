from __future__ import annotations

import pytest

from aidd.evals.reporting import ScenarioSummaryRow, build_scenario_summary_row
from aidd.evals.verdicts import ScenarioVerdict, build_scenario_verdict


def _verdict() -> ScenarioVerdict:
    return build_scenario_verdict(
        scenario_id="AIDD-LIVE-001",
        run_id="eval-run-001",
        runtime_id="generic-cli",
        status="pass",
        summary="Scenario completed successfully.",
        created_at_utc="2026-04-22T12:00:00Z",
    )


def test_build_scenario_summary_row_uses_verdict_fields_and_metrics() -> None:
    row = build_scenario_summary_row(
        verdict=_verdict(),
        duration_seconds=12.5,
        failure_boundary="runtime",
    )

    assert row == ScenarioSummaryRow(
        scenario_id="AIDD-LIVE-001",
        run_id="eval-run-001",
        runtime_id="generic-cli",
        verdict_status="pass",
        duration_seconds=12.5,
        failure_boundary="runtime",
    )


def test_build_scenario_summary_row_defaults_failure_boundary_to_none() -> None:
    row = build_scenario_summary_row(verdict=_verdict(), duration_seconds=0.0)

    assert row.failure_boundary == "none"


def test_build_scenario_summary_row_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="duration_seconds must be greater than or equal to 0"):
        build_scenario_summary_row(
            verdict=_verdict(),
            duration_seconds=-0.1,
        )


def test_build_scenario_summary_row_rejects_non_finite_duration() -> None:
    with pytest.raises(ValueError, match="duration_seconds must be finite"):
        build_scenario_summary_row(
            verdict=_verdict(),
            duration_seconds=float("nan"),
        )


def test_build_scenario_summary_row_rejects_unknown_failure_boundary() -> None:
    with pytest.raises(ValueError, match="failure_boundary must be one of"):
        build_scenario_summary_row(
            verdict=_verdict(),
            duration_seconds=1.0,
            failure_boundary="document",
        )
