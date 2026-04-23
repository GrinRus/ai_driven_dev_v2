from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

GraderStatus = Literal["pass", "fail", "blocked"]


def _overall_status(*statuses: GraderStatus) -> GraderStatus:
    if any(status == "fail" for status in statuses):
        return "fail"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    return "pass"


def build_stage_grader_payload(
    *,
    run_id: str,
    work_item: str,
    runtime_id: str,
    stage: str,
    attempt_number: int,
    runtime_exit_classification: str,
    validator_finding_count: int,
    unresolved_blocking_question_ids: tuple[str, ...],
    resolved_verdict: str,
    next_state: str,
    action: str,
) -> dict[str, object]:
    contract_compliance: GraderStatus = "pass" if validator_finding_count == 0 else "fail"
    process_compliance: GraderStatus
    if runtime_exit_classification.strip().lower() != "success":
        process_compliance = "fail"
    elif unresolved_blocking_question_ids:
        process_compliance = "blocked"
    else:
        process_compliance = "pass"

    task_outcome: GraderStatus
    if next_state == "succeeded" and action == "advance":
        task_outcome = "pass"
    elif next_state == "blocked":
        task_outcome = "blocked"
    else:
        task_outcome = "fail"

    return {
        "schema_version": 1,
        "kind": "stage-attempt",
        "run_id": run_id,
        "work_item": work_item,
        "runtime_id": runtime_id,
        "stage": stage,
        "attempt_number": attempt_number,
        "overall_status": _overall_status(
            contract_compliance,
            process_compliance,
            task_outcome,
        ),
        "contract_compliance": {
            "status": contract_compliance,
            "validator_finding_count": validator_finding_count,
            "resolved_verdict": resolved_verdict,
        },
        "process_compliance": {
            "status": process_compliance,
            "runtime_exit_classification": runtime_exit_classification,
            "unresolved_blocking_question_ids": list(unresolved_blocking_question_ids),
        },
        "task_outcome": {
            "status": task_outcome,
            "next_state": next_state,
            "action": action,
        },
    }


def build_eval_grader_payload(
    *,
    run_id: str,
    scenario_id: str,
    runtime_id: str,
    verdict_status: str,
    validator_failure_count: int,
    aidd_exit_code: int | None,
    verification_failed: bool,
    blocked_by_questions: bool,
    infrastructure_failure: bool,
    failure_taxonomy_category: str,
    failure_taxonomy_reason: str,
    first_failure_category: str,
    first_failure_signal_source: str,
    first_failure_signal_line_number: int | None,
    first_failure_reason: str,
) -> dict[str, object]:
    contract_compliance: GraderStatus = "pass" if validator_failure_count == 0 else "fail"

    process_compliance: GraderStatus
    if infrastructure_failure:
        process_compliance = "fail"
    elif blocked_by_questions:
        process_compliance = "blocked"
    elif verification_failed:
        process_compliance = "fail"
    elif aidd_exit_code == 0:
        process_compliance = "pass"
    else:
        process_compliance = "fail"

    task_outcome: GraderStatus
    if verdict_status == "pass":
        task_outcome = "pass"
    elif verdict_status == "blocked":
        task_outcome = "blocked"
    else:
        task_outcome = "fail"

    return {
        "schema_version": 1,
        "kind": "eval-scenario",
        "run_id": run_id,
        "scenario_id": scenario_id,
        "runtime_id": runtime_id,
        "verdict_status": verdict_status,
        "overall_status": _overall_status(
            contract_compliance,
            process_compliance,
            task_outcome,
        ),
        "contract_compliance": {
            "status": contract_compliance,
            "validator_failure_count": validator_failure_count,
        },
        "process_compliance": {
            "status": process_compliance,
            "aidd_exit_code": aidd_exit_code,
            "verification_failed": verification_failed,
            "blocked_by_questions": blocked_by_questions,
            "infrastructure_failure": infrastructure_failure,
        },
        "task_outcome": {
            "status": task_outcome,
            "verdict_status": verdict_status,
        },
        "failure_taxonomy": {
            "category": failure_taxonomy_category,
            "reason": failure_taxonomy_reason,
        },
        "first_failure_boundary": {
            "category": first_failure_category,
            "signal_source": first_failure_signal_source,
            "signal_line_number": first_failure_signal_line_number,
            "reason": first_failure_reason,
        },
    }


def write_grader_payload(*, path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
