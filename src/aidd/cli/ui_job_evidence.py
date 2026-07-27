from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

UiJobEvidenceStatus = Literal[
    "cancelled",
    "completed",
    "failed",
    "waiting-for-operator",
]

_ATTEMPT_DIRECTORY = re.compile(r"attempt-(?P<number>[0-9]{4})")


@dataclass(frozen=True, slots=True)
class UiJobRuntimeExitEvidence:
    artifact_path: str
    exists: bool
    adapter_outcome: str | None
    exit_classification: str | None
    exit_code: int | None
    stop_reason: str | None


@dataclass(frozen=True, slots=True)
class UiJobDurableMutationWinner:
    evidence_path: str
    status: str
    changed_at_utc: str | None


@dataclass(frozen=True, slots=True)
class UiJobDecisiveCause:
    kind: str
    detail: str
    evidence_path: str | None


@dataclass(frozen=True, slots=True)
class UiJobTerminalEvidence:
    schema_version: int
    work_item: str | None
    run_id: str | None
    stage: str | None
    attempt_number: int | None
    job_status: UiJobEvidenceStatus
    exit_code: int | None
    attempt_path: str | None
    runtime_exit: UiJobRuntimeExitEvidence | None
    adapter_outcome: str | None
    durable_mutation_winner: UiJobDurableMutationWinner | None
    first_decisive_cause: UiJobDecisiveCause
    cancellation: dict[str, object]
    operator_wait: dict[str, object]

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def _read_json_object(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return {str(key): value for key, value in payload.items()}


def _optional_text(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value else None


def _optional_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _attempt_number(attempt_path: Path | None) -> int | None:
    if attempt_path is None:
        return None
    match = _ATTEMPT_DIRECTORY.fullmatch(attempt_path.name)
    if match is None:
        return None
    number = int(match.group("number"))
    return number if number >= 1 else None


def _runtime_exit_evidence(
    attempt_path: Path | None,
) -> UiJobRuntimeExitEvidence | None:
    if attempt_path is None:
        return None
    artifact_path = attempt_path / "runtime-exit.json"
    payload = _read_json_object(artifact_path)
    return UiJobRuntimeExitEvidence(
        artifact_path=artifact_path.as_posix(),
        exists=payload is not None,
        adapter_outcome=(
            _optional_text(payload, "adapter_outcome") if payload is not None else None
        ),
        exit_classification=(
            _optional_text(payload, "exit_classification")
            if payload is not None
            else None
        ),
        exit_code=_optional_int(payload, "exit_code") if payload is not None else None,
        stop_reason=_optional_text(payload, "stop_reason") if payload is not None else None,
    )


def _durable_mutation_winner(
    attempt_path: Path | None,
) -> UiJobDurableMutationWinner | None:
    if attempt_path is None:
        return None
    metadata_path = attempt_path.parent.parent / "stage-metadata.json"
    payload = _read_json_object(metadata_path)
    if payload is None:
        return None
    status = _optional_text(payload, "status")
    if status is None:
        return None
    return UiJobDurableMutationWinner(
        evidence_path=metadata_path.as_posix(),
        status=status,
        changed_at_utc=_optional_text(payload, "updated_at_utc"),
    )


def _operator_wait_payload(
    *,
    status: UiJobEvidenceStatus,
    result: object,
    attempt_path: Path | None,
) -> dict[str, object]:
    result_payload = result if isinstance(result, Mapping) else {}
    return {
        "waiting": status == "waiting-for-operator",
        "request_id": _optional_text(result_payload, "request_id"),
        "attempt_path": (
            attempt_path.as_posix()
            if attempt_path is not None
            else _optional_text(result_payload, "attempt_path")
        ),
    }


def _first_decisive_cause(
    *,
    status: UiJobEvidenceStatus,
    message: str,
    result: object,
    runtime_exit: UiJobRuntimeExitEvidence | None,
    winner: UiJobDurableMutationWinner | None,
) -> UiJobDecisiveCause:
    if (
        runtime_exit is not None
        and runtime_exit.exists
        and runtime_exit.adapter_outcome not in {None, "success"}
    ):
        detail = (
            runtime_exit.stop_reason
            or runtime_exit.exit_classification
            or runtime_exit.adapter_outcome
        )
        return UiJobDecisiveCause(
            kind="adapter-outcome",
            detail=detail,
            evidence_path=runtime_exit.artifact_path,
        )
    if status == "cancelled":
        return UiJobDecisiveCause(
            kind="cancellation",
            detail=message or "UI job was cancelled.",
            evidence_path=None,
        )
    if status == "waiting-for-operator":
        return UiJobDecisiveCause(
            kind="operator-wait",
            detail=message or "Runtime is waiting for an operator decision.",
            evidence_path=None,
        )
    result_payload = result if isinstance(result, Mapping) else {}
    blocker = result_payload.get("finalization_blocker")
    if blocker is not None:
        return UiJobDecisiveCause(
            kind="finalization-blocker",
            detail=str(blocker),
            evidence_path=None,
        )
    if status == "failed":
        return UiJobDecisiveCause(
            kind="job-failure",
            detail=message or "UI job failed without a more specific runtime cause.",
            evidence_path=None,
        )
    if winner is not None:
        return UiJobDecisiveCause(
            kind="durable-stage-status",
            detail=winner.status,
            evidence_path=winner.evidence_path,
        )
    return UiJobDecisiveCause(
        kind="job-completion",
        detail=message or "UI job completed.",
        evidence_path=None,
    )


def build_ui_job_terminal_evidence(
    *,
    work_item: str | None,
    run_id: str | None,
    stage: str | None,
    status: UiJobEvidenceStatus,
    exit_code: int | None,
    message: str,
    result: object,
    operator_wait_result: object,
    attempt_path: Path | None,
    cancel_requested_at_utc: str | None,
    cancelled_at_utc: str | None,
) -> UiJobTerminalEvidence:
    runtime_exit = _runtime_exit_evidence(attempt_path)
    winner = _durable_mutation_winner(attempt_path)
    return UiJobTerminalEvidence(
        schema_version=1,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=_attempt_number(attempt_path),
        job_status=status,
        exit_code=exit_code,
        attempt_path=attempt_path.as_posix() if attempt_path is not None else None,
        runtime_exit=runtime_exit,
        adapter_outcome=(
            runtime_exit.adapter_outcome if runtime_exit is not None else None
        ),
        durable_mutation_winner=winner,
        first_decisive_cause=_first_decisive_cause(
            status=status,
            message=message,
            result=result,
            runtime_exit=runtime_exit,
            winner=winner,
        ),
        cancellation={
            "requested": cancel_requested_at_utc is not None,
            "requested_at_utc": cancel_requested_at_utc,
            "cancelled_at_utc": cancelled_at_utc,
        },
        operator_wait=_operator_wait_payload(
            status=status,
            result=(
                operator_wait_result
                if operator_wait_result is not None
                else result
            ),
            attempt_path=attempt_path,
        ),
    )


__all__ = [
    "UiJobDecisiveCause",
    "UiJobDurableMutationWinner",
    "UiJobEvidenceStatus",
    "UiJobRuntimeExitEvidence",
    "UiJobTerminalEvidence",
    "build_ui_job_terminal_evidence",
]
