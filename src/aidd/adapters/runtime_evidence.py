from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

RUNTIME_LOG_FILENAME = "runtime.log"
RUNTIME_EXIT_METADATA_FILENAME = "runtime-exit.json"


class RuntimeAdapterOutcome(StrEnum):
    SUCCESS = "success"
    RUNTIME_FAILURE = "runtime_failure"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    DENIAL = "denial"
    BLOCKED = "blocked"
    LAUNCH_FAILURE = "launch_failure"


class RuntimeStopReason(StrEnum):
    RUNTIME_FAILURE = "runtime_failure"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    DENIAL = "denial"
    BLOCKED = "blocked"
    LAUNCH_FAILURE = "launch_failure"


@dataclass(frozen=True, slots=True)
class RuntimeEvidenceCommitRequest:
    attempt_path: Path
    adapter_outcome: RuntimeAdapterOutcome
    exit_classification: str
    exit_code: int | None
    stdout_text: str
    stderr_text: str
    runtime_log_text: str
    stop_reason: RuntimeStopReason | None = None

    def __post_init__(self) -> None:
        if not self.exit_classification.strip():
            raise ValueError("Runtime exit classification must not be empty.")
        if self.adapter_outcome is RuntimeAdapterOutcome.SUCCESS:
            if self.stop_reason is not None:
                raise ValueError("Successful runtime evidence must not have a stop reason.")
            return
        if self.stop_reason is None:
            raise ValueError("Non-success runtime evidence requires a stop reason.")
        if self.stop_reason.value != self.adapter_outcome.value:
            raise ValueError("Runtime stop reason must match the canonical adapter outcome.")


@dataclass(frozen=True, slots=True)
class RuntimeEvidencePaths:
    runtime_log_path: Path
    runtime_exit_metadata_path: Path


_CLASSIFICATION_OUTCOMES: dict[str, RuntimeAdapterOutcome] = {
    "success": RuntimeAdapterOutcome.SUCCESS,
    "document_complete": RuntimeAdapterOutcome.SUCCESS,
    "non_zero_exit": RuntimeAdapterOutcome.RUNTIME_FAILURE,
    "runtime_non_zero_exit": RuntimeAdapterOutcome.RUNTIME_FAILURE,
    "provider_error": RuntimeAdapterOutcome.RUNTIME_FAILURE,
    "timeout": RuntimeAdapterOutcome.TIMEOUT,
    "cancelled": RuntimeAdapterOutcome.CANCELLATION,
    "user_cancelled": RuntimeAdapterOutcome.CANCELLATION,
    "denied": RuntimeAdapterOutcome.DENIAL,
    "blocked": RuntimeAdapterOutcome.BLOCKED,
    "launch_failure": RuntimeAdapterOutcome.LAUNCH_FAILURE,
    "adapter_failure": RuntimeAdapterOutcome.LAUNCH_FAILURE,
}


def adapter_outcome_for_classification(
    exit_classification: str,
) -> RuntimeAdapterOutcome:
    try:
        return _CLASSIFICATION_OUTCOMES[exit_classification]
    except KeyError as exc:
        raise ValueError(
            f"Unknown runtime exit classification: {exit_classification!r}"
        ) from exc


def stop_reason_for_outcome(
    adapter_outcome: RuntimeAdapterOutcome,
) -> RuntimeStopReason | None:
    if adapter_outcome is RuntimeAdapterOutcome.SUCCESS:
        return None
    return RuntimeStopReason(adapter_outcome.value)


def runtime_evidence_paths(attempt_path: Path) -> RuntimeEvidencePaths:
    return RuntimeEvidencePaths(
        runtime_log_path=attempt_path / RUNTIME_LOG_FILENAME,
        runtime_exit_metadata_path=attempt_path / RUNTIME_EXIT_METADATA_FILENAME,
    )


def _atomic_write_text(path: Path, text: str) -> None:
    temporary_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary_path.write_text(text, encoding="utf-8")
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def commit_runtime_evidence(
    request: RuntimeEvidenceCommitRequest,
) -> RuntimeEvidencePaths:
    request.attempt_path.mkdir(parents=True, exist_ok=True)
    paths = runtime_evidence_paths(request.attempt_path)
    metadata: dict[str, object] = {
        "schema_version": 1,
        "exit_code": request.exit_code,
        "exit_classification": request.exit_classification,
        "adapter_outcome": request.adapter_outcome.value,
        "stdout_char_count": len(request.stdout_text),
        "stderr_char_count": len(request.stderr_text),
        "runtime_log_char_count": len(request.runtime_log_text),
    }
    if request.stop_reason is not None:
        metadata["stop_reason"] = request.stop_reason.value

    _atomic_write_text(paths.runtime_log_path, request.runtime_log_text)
    _atomic_write_text(
        paths.runtime_exit_metadata_path,
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
    )
    return paths


__all__ = [
    "RUNTIME_EXIT_METADATA_FILENAME",
    "RUNTIME_LOG_FILENAME",
    "RuntimeAdapterOutcome",
    "RuntimeEvidenceCommitRequest",
    "RuntimeEvidencePaths",
    "RuntimeStopReason",
    "adapter_outcome_for_classification",
    "commit_runtime_evidence",
    "runtime_evidence_paths",
    "stop_reason_for_outcome",
]
