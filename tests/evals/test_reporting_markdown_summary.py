from __future__ import annotations

from pathlib import Path

from aidd.evals.log_analysis import parse_events_jsonl_text
from aidd.evals.reporting import (
    ScenarioSummaryRow,
    render_eval_summary_markdown,
    write_eval_summary_markdown,
)
from aidd.harness.eval_reports import render_runtime_diagnostics_markdown


def test_render_eval_summary_markdown_includes_runtime_and_scenario_tables() -> None:
    scenario_rows = (
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
            duration_seconds=15.25,
            failure_boundary="runtime",
        ),
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-003",
            run_id="eval-run-003",
            runtime_id="claude-code",
            verdict_status="blocked",
            duration_seconds=3.5,
            failure_boundary="validation",
        ),
    )

    markdown = render_eval_summary_markdown(
        scenario_rows=scenario_rows,
        created_at_utc="2026-04-22T12:40:00Z",
    )

    assert markdown.startswith("# Eval Summary\n\n## Overview\n")
    assert "- Generated At (UTC): `2026-04-22T12:40:00Z`" in markdown
    assert "| Runtime | Scenarios | Pass | Fail | Blocked | Infra Fail |" in markdown
    assert "| `claude-code` | 1 | 0 | 0 | 1 | 0 | 3.500 | 3.500 |" in markdown
    assert "| `generic-cli` | 2 | 1 | 1 | 0 | 0 | 25.250 | 12.625 |" in markdown
    assert "| Scenario | Run | Runtime | Verdict | Duration (s) | Failure Boundary |" in markdown
    assert (
        "| `AIDD-LIVE-001` | `eval-run-001` | `generic-cli` | `pass` | 10.000 | `none` |"
        in markdown
    )
    assert (
        "| `AIDD-LIVE-003` | `eval-run-003` | `claude-code` | `blocked` | 3.500 | "
        "`validation` |" in markdown
    )
    assert markdown.endswith("\n")


def test_render_eval_summary_markdown_handles_empty_rows() -> None:
    markdown = render_eval_summary_markdown(
        scenario_rows=(),
        created_at_utc="2026-04-22T12:41:00Z",
    )

    assert "- Scenario Rows: `0`" in markdown
    assert "- Runtime Rows: `0`" in markdown
    assert "- No runtime summary rows." in markdown
    assert "- No scenario summary rows." in markdown


def test_write_eval_summary_markdown_persists_rendered_report(tmp_path: Path) -> None:
    path = tmp_path / "reports" / "evals" / "summary.md"
    scenario_rows = (
        ScenarioSummaryRow(
            scenario_id="AIDD-LIVE-010",
            run_id="eval-run-010",
            runtime_id="generic-cli",
            verdict_status="infra-fail",
            duration_seconds=1.0,
            failure_boundary="environment",
        ),
    )

    written_path = write_eval_summary_markdown(
        path=path,
        scenario_rows=scenario_rows,
        created_at_utc="2026-04-22T12:42:00Z",
    )

    assert written_path == path
    content = path.read_text(encoding="utf-8")
    assert "# Eval Summary" in content
    assert "- Generated At (UTC): `2026-04-22T12:42:00Z`" in content
    assert (
        "| `AIDD-LIVE-010` | `eval-run-010` | `generic-cli` | `infra-fail` | 1.000 | "
        "`environment` |" in content
    )


def test_render_runtime_diagnostics_markdown_includes_timeout_profile(
    tmp_path: Path,
) -> None:
    runtime_config_path = tmp_path / "aidd.example.toml"
    runtime_config_path.write_text(
        "\n".join(
            (
                "[runtime.claude_code]",
                "timeout_seconds = 1200",
                "",
                "[runtime.claude_code.stage_timeouts]",
                "idea = 1500",
            )
        ),
        encoding="utf-8",
    )
    normalized_events = parse_events_jsonl_text(
        "\n".join(
            (
                (
                    '{"source":"stdout","type":"system","subtype":"init",'
                    '"model":"kimi-for-coding","claude_code_version":"2.1.85"}'
                ),
                (
                    '{"source":"stdout","type":"system","subtype":"api_retry",'
                    '"error":"rate_limit","error_status":429,"attempt":1}'
                ),
            )
        )
    )
    stage_timing_payload = {
        "stages": [
            {
                "stage": "idea",
                "attempts": [
                    {
                        "attempt": 1,
                        "runtime_exit_classification": "timeout",
                        "runtime_exit_code": 143,
                        "timed_out": True,
                    }
                ],
            }
        ]
    }

    markdown = render_runtime_diagnostics_markdown(
        normalized_events=normalized_events,
        stage_timing_payload=stage_timing_payload,
        runtime_id="claude-code",
        runtime_config_path=runtime_config_path,
        harness_timeout_seconds=14400,
    )

    assert "- Runtime ID: `claude-code`" in markdown
    assert "model=kimi-for-coding" in markdown
    assert "error=rate_limit" in markdown
    assert "Timeout Stage/Budget: `idea` attempt `1` runtime exit `timeout`/`143`" in markdown
    assert "stage budget `1500.000s`" in markdown
    assert "- Default Runtime Timeout: `1200.000s`" in markdown
    assert "- Harness Run Timeout: `14400.000s`" in markdown
