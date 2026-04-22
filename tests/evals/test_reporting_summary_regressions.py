from __future__ import annotations

from aidd.evals.reporting import (
    ScenarioSummaryRow,
    aggregate_runtime_summary_rows,
    render_eval_summary_markdown,
)


def test_eval_summary_regression_empty_eval_set() -> None:
    runtime_rows = aggregate_runtime_summary_rows(())
    markdown = render_eval_summary_markdown(
        scenario_rows=(),
        runtime_summaries=runtime_rows,
        created_at_utc="2026-04-22T13:00:00Z",
    )

    assert runtime_rows == ()
    assert "- Scenario Rows: `0`" in markdown
    assert "- Runtime Rows: `0`" in markdown
    assert "- No runtime summary rows." in markdown
    assert "- No scenario summary rows." in markdown


def test_eval_summary_regression_mixed_outcomes() -> None:
    scenario_rows = (
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-001",
            run_id="eval-run-001",
            runtime_id="generic-cli",
            verdict_status="pass",
            duration_seconds=5.0,
            failure_boundary="none",
        ),
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-002",
            run_id="eval-run-002",
            runtime_id="generic-cli",
            verdict_status="fail",
            duration_seconds=8.0,
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
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-004",
            run_id="eval-run-004",
            runtime_id="claude-code",
            verdict_status="infra-fail",
            duration_seconds=3.0,
            failure_boundary="environment",
        ),
    )

    runtime_rows = aggregate_runtime_summary_rows(scenario_rows)
    markdown = render_eval_summary_markdown(
        scenario_rows=scenario_rows,
        runtime_summaries=runtime_rows,
        created_at_utc="2026-04-22T13:01:00Z",
    )

    assert "| `claude-code` | 2 | 0 | 0 | 1 | 1 | 7.000 | 3.500 |" in markdown
    assert "| `generic-cli` | 2 | 1 | 1 | 0 | 0 | 13.000 | 6.500 |" in markdown
    assert (
        "| `AIDD-LIVE-004` | `eval-run-004` | `claude-code` | `infra-fail` | 3.000 | "
        "`environment` |" in markdown
    )


def test_eval_summary_regression_repeated_scenario_runs() -> None:
    scenario_rows = (
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-010",
            run_id="eval-run-010",
            runtime_id="generic-cli",
            verdict_status="fail",
            duration_seconds=9.0,
            failure_boundary="runtime",
        ),
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-010",
            run_id="eval-run-011",
            runtime_id="generic-cli",
            verdict_status="pass",
            duration_seconds=6.0,
            failure_boundary="none",
        ),
    )

    runtime_rows = aggregate_runtime_summary_rows(scenario_rows)
    markdown = render_eval_summary_markdown(
        scenario_rows=scenario_rows,
        runtime_summaries=runtime_rows,
        created_at_utc="2026-04-22T13:02:00Z",
    )

    assert runtime_rows[0].runtime_id == "generic-cli"
    assert runtime_rows[0].scenario_count == 2
    assert runtime_rows[0].fail_count == 1
    assert runtime_rows[0].pass_count == 1
    assert (
        "| `AIDD-LIVE-010` | `eval-run-010` | `generic-cli` | `fail` | 9.000 | "
        "`runtime` |" in markdown
    )
    assert (
        "| `AIDD-LIVE-010` | `eval-run-011` | `generic-cli` | `pass` | 6.000 | "
        "`none` |" in markdown
    )
