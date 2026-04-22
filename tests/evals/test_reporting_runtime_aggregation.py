from __future__ import annotations

from aidd.evals.reporting import (
    RuntimeSummaryRow,
    ScenarioSummaryRow,
    aggregate_runtime_summary_rows,
)


def test_aggregate_runtime_summary_rows_groups_and_counts_statuses() -> None:
    rows = (
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-001",
            run_id="eval-run-001",
            runtime_id="generic-cli",
            verdict_status="pass",
            duration_seconds=10.0,
            failure_boundary="none",
        ),
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-002",
            run_id="eval-run-002",
            runtime_id="generic-cli",
            verdict_status="fail",
            duration_seconds=14.0,
            failure_boundary="runtime",
        ),
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-003",
            run_id="eval-run-003",
            runtime_id="claude-code",
            verdict_status="blocked",
            duration_seconds=4.0,
            failure_boundary="validation",
        ),
    )

    aggregated = aggregate_runtime_summary_rows(rows)

    assert aggregated == (
        RuntimeSummaryRow(
            runtime_id="claude-code",
            scenario_count=1,
            pass_count=0,
            fail_count=0,
            blocked_count=1,
            infra_fail_count=0,
            total_duration_seconds=4.0,
            average_duration_seconds=4.0,
        ),
        RuntimeSummaryRow(
            runtime_id="generic-cli",
            scenario_count=2,
            pass_count=1,
            fail_count=1,
            blocked_count=0,
            infra_fail_count=0,
            total_duration_seconds=24.0,
            average_duration_seconds=12.0,
        ),
    )


def test_aggregate_runtime_summary_rows_tracks_infra_failures() -> None:
    rows = (
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-010",
            run_id="eval-run-010",
            runtime_id="generic-cli",
            verdict_status="infra-fail",
            duration_seconds=2.5,
            failure_boundary="environment",
        ),
    )

    aggregated = aggregate_runtime_summary_rows(rows)

    assert aggregated[0].infra_fail_count == 1
    assert aggregated[0].pass_count == 0
    assert aggregated[0].fail_count == 0
    assert aggregated[0].blocked_count == 0


def test_aggregate_runtime_summary_rows_returns_empty_for_empty_input() -> None:
    assert aggregate_runtime_summary_rows(()) == ()
