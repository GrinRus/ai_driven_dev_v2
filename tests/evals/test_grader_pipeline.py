from __future__ import annotations

from pathlib import Path

from aidd.evals.grader_pipeline import (
    build_eval_grader_payload,
    build_stage_grader_payload,
    write_grader_payload,
)


def test_build_stage_grader_payload_reports_pass_status() -> None:
    payload = build_stage_grader_payload(
        run_id="run-001",
        work_item="WI-001",
        runtime_id="generic-cli",
        stage="idea",
        attempt_number=1,
        runtime_exit_classification="success",
        validator_finding_count=0,
        unresolved_blocking_question_ids=(),
        resolved_verdict="pass",
        next_state="succeeded",
        action="advance",
    )

    assert payload["overall_status"] == "pass"
    assert payload["contract_compliance"]["status"] == "pass"
    assert payload["process_compliance"]["status"] == "pass"
    assert payload["task_outcome"]["status"] == "pass"


def test_build_stage_grader_payload_reports_blocked_status() -> None:
    payload = build_stage_grader_payload(
        run_id="run-002",
        work_item="WI-002",
        runtime_id="claude-code",
        stage="plan",
        attempt_number=2,
        runtime_exit_classification="success",
        validator_finding_count=0,
        unresolved_blocking_question_ids=("Q-001",),
        resolved_verdict="blocked",
        next_state="blocked",
        action="block",
    )

    assert payload["overall_status"] == "blocked"
    assert payload["process_compliance"]["status"] == "blocked"
    assert payload["task_outcome"]["status"] == "blocked"


def test_build_eval_grader_payload_reports_fail_status() -> None:
    payload = build_eval_grader_payload(
        run_id="eval-001",
        scenario_id="AIDD-LIVE-001",
        runtime_id="opencode",
        verdict_status="fail",
        validator_failure_count=2,
        aidd_exit_code=2,
        verification_failed=True,
        blocked_by_questions=False,
        infrastructure_failure=False,
        failure_taxonomy_category="validation_fail",
        failure_taxonomy_reason="validator findings",
        first_failure_category="validation_fail",
        first_failure_signal_source="validator-report",
        first_failure_signal_line_number=12,
        first_failure_reason="missing section",
    )

    assert payload["overall_status"] == "fail"
    assert payload["contract_compliance"]["status"] == "fail"
    assert payload["process_compliance"]["status"] == "fail"
    assert payload["task_outcome"]["status"] == "fail"


def test_write_grader_payload_writes_json_file(tmp_path: Path) -> None:
    path = tmp_path / "reports" / "evals" / "eval-001" / "grader.json"
    payload = build_stage_grader_payload(
        run_id="run-001",
        work_item="WI-001",
        runtime_id="generic-cli",
        stage="idea",
        attempt_number=1,
        runtime_exit_classification="success",
        validator_finding_count=0,
        unresolved_blocking_question_ids=(),
        resolved_verdict="pass",
        next_state="succeeded",
        action="advance",
    )

    written = write_grader_payload(path=path, payload=payload)

    assert written == path
    assert path.exists()
    assert '"overall_status": "pass"' in path.read_text(encoding="utf-8")
