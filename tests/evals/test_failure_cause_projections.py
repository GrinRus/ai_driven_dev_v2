from __future__ import annotations

from aidd.evals.failure_causes import (
    FailureCauseCategory,
    FailureCausePhase,
    FailureCauseSource,
)
from aidd.evals.log_analysis import (
    CoarseRuntimeEvent,
    FailureBoundarySelection,
    parse_validator_report_failures_text,
    select_first_failure_boundary,
)
from aidd.evals.reporting import build_scenario_summary_row, render_eval_summary_markdown
from aidd.evals.verdicts import build_scenario_verdict, render_scenario_verdict_markdown
from aidd.harness.eval_models import EvalExecutionState
from aidd.harness.eval_reports import (
    _boundary_for_failure_cause,
    _failure_cause_for_state,
    render_log_analysis_markdown,
    render_validator_report_source,
)


def test_setup_failure_projects_to_infrastructure_without_validator_finding() -> None:
    state = EvalExecutionState(setup_error=RuntimeError("fixture setup failed"))
    cause = _failure_cause_for_state(
        status="infra-fail",
        state=state,
        stage_timing_payload={"stages": []},
    )

    assert cause.category is FailureCauseCategory.INFRASTRUCTURE
    assert cause.phase is FailureCausePhase.SETUP
    assert cause.source is FailureCauseSource.HARNESS
    validator_report = render_validator_report_source(
        status="infra-fail",
        summary="setup failed",
        prep_error=None,
        install_error=None,
        setup_error=state.setup_error,
        run_error=None,
        verification_error=None,
        teardown_error=None,
        failure_cause=cause,
    )
    assert parse_validator_report_failures_text(validator_report) == ()

    boundary = _boundary_for_failure_cause(
        cause=cause,
        fallback=FailureBoundarySelection(
            category="validation",
            signal_source="validator-report",
            signal_line_number=1,
            reason="synthetic finding",
        ),
    )
    assert boundary.category == "infrastructure"
    assert boundary.signal_source == "harness"

    log_analysis = render_log_analysis_markdown(
        status="infra-fail",
        boundary=boundary,
        failure_cause=cause,
    )
    assert "Failure Cause Category: `infrastructure`" in log_analysis
    assert "Failure Cause Phase: `setup`" in log_analysis


def test_log_analysis_recognizes_setup_failure_without_synthetic_validator_signal() -> None:
    boundary = select_first_failure_boundary(
        runtime_events=(
            CoarseRuntimeEvent(
                line_number=1,
                category="error",
                message="Setup command failed with non-zero exit (2)",
            ),
        )
    )

    assert boundary.category == "infrastructure"
    assert boundary.signal_source == "runtime.log"


def test_validator_failure_remains_validation_across_verdict_and_summary() -> None:
    cause = _failure_cause_for_state(
        status="fail",
        state=EvalExecutionState(),
        stage_timing_payload={
            "stages": [
                {
                    "stage": "plan",
                    "final_failure_code": "STRUCT-MISSING-REQUIRED-DOCUMENT",
                    "attempts": [{"validation_result": "failed"}],
                }
            ]
        },
    )

    assert cause.category is FailureCauseCategory.VALIDATION
    validator_report = render_validator_report_source(
        status="fail",
        summary="document validation failed",
        prep_error=None,
        install_error=None,
        setup_error=None,
        run_error=None,
        verification_error=None,
        teardown_error=None,
        failure_cause=cause,
    )
    assert len(parse_validator_report_failures_text(validator_report)) == 1

    verdict = build_scenario_verdict(
        scenario_id="DET-VALIDATION",
        run_id="run-validation",
        runtime_id="generic-cli",
        status="fail",
        summary="document validation failed",
        created_at_utc="2026-09-06T00:00:00Z",
        failure_cause=cause,
    )
    assert "- Category: `validation`" in render_scenario_verdict_markdown(verdict)
    row = build_scenario_summary_row(
        verdict=verdict,
        duration_seconds=1.0,
        failure_boundary="validation",
    )
    summary = render_eval_summary_markdown(
        scenario_rows=(row,),
        created_at_utc="2026-09-06T00:00:00Z",
    )
    assert "| Scenario | Run | Runtime | Verdict | Duration (s) | Failure Boundary |" in summary
    assert "`validation` |" in summary
