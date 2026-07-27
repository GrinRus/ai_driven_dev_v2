from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

RemediationJobClassification = Literal["blocked", "fail", "pass"]


@dataclass(frozen=True, slots=True)
class RemediationTerminalEvidence:
    work_item: str
    run_id: str
    stage: str
    attempt_number: int
    job_status: str
    adapter_outcome: str | None
    first_cause_kind: str
    first_cause_detail: str
    payload: dict[str, object]


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Remediation terminal evidence requires `{key}`.")
    return value


def read_remediation_terminal_evidence(
    job_payload: Mapping[str, object],
    *,
    expected_work_item: str,
    expected_run_id: str,
    expected_stage: str,
) -> RemediationTerminalEvidence:
    raw_evidence = job_payload.get("terminal_evidence")
    if not isinstance(raw_evidence, Mapping):
        raise ValueError("Remediation job has no typed terminal evidence.")
    if raw_evidence.get("schema_version") != 1:
        raise ValueError("Remediation terminal evidence schema is unsupported.")
    work_item = _required_text(raw_evidence, "work_item")
    run_id = _required_text(raw_evidence, "run_id")
    stage = _required_text(raw_evidence, "stage")
    if (work_item, run_id, stage) != (
        expected_work_item,
        expected_run_id,
        expected_stage,
    ):
        raise ValueError("Remediation terminal evidence identity does not match the request.")
    attempt_number = raw_evidence.get("attempt_number")
    if (
        not isinstance(attempt_number, int)
        or isinstance(attempt_number, bool)
        or attempt_number < 1
    ):
        raise ValueError("Remediation terminal evidence requires a canonical attempt.")
    job_status = _required_text(raw_evidence, "job_status")
    if job_status != job_payload.get("status"):
        raise ValueError("Remediation terminal evidence status does not match job status.")
    raw_cause = raw_evidence.get("first_decisive_cause")
    if not isinstance(raw_cause, Mapping):
        raise ValueError("Remediation terminal evidence requires a first decisive cause.")
    cause_kind = _required_text(raw_cause, "kind")
    cause_detail = _required_text(raw_cause, "detail")
    adapter_outcome = raw_evidence.get("adapter_outcome")
    if adapter_outcome is not None and not isinstance(adapter_outcome, str):
        raise ValueError("Remediation terminal adapter outcome must be text or null.")
    for key in ("cancellation", "operator_wait"):
        if not isinstance(raw_evidence.get(key), Mapping):
            raise ValueError(f"Remediation terminal evidence requires `{key}` details.")
    return RemediationTerminalEvidence(
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        job_status=job_status,
        adapter_outcome=adapter_outcome,
        first_cause_kind=cause_kind,
        first_cause_detail=cause_detail,
        payload={str(key): value for key, value in raw_evidence.items()},
    )


def classify_remediation_terminal_evidence(
    evidence: RemediationTerminalEvidence,
) -> RemediationJobClassification:
    if evidence.job_status == "completed":
        return "pass"
    if evidence.job_status == "waiting-for-operator":
        return "blocked"
    return "fail"


__all__ = [
    "RemediationJobClassification",
    "RemediationTerminalEvidence",
    "classify_remediation_terminal_evidence",
    "read_remediation_terminal_evidence",
]
