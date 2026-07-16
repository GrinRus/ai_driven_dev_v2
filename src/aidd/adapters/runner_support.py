from __future__ import annotations

import os
import shlex
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path

from aidd.adapters.runtime_evidence import (
    RUNTIME_LOG_FILENAME,
    RuntimeAdapterOutcome,
    RuntimeEvidenceCommitRequest,
    RuntimeEvidencePaths,
    adapter_outcome_for_classification,
    commit_runtime_evidence,
    stop_reason_for_outcome,
)

RuntimeArtifactPaths = RuntimeEvidencePaths


def split_configured_command(*, configured_command: str, runtime_label: str) -> tuple[str, ...]:
    stripped = configured_command.strip()
    if not stripped:
        raise ValueError(f"Configured {runtime_label} command must not be empty.")

    try:
        base_tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(
            f"Configured {runtime_label} command is not valid shell syntax: "
            f"{configured_command!r}"
        ) from exc
    if not base_tokens:
        raise ValueError(f"Configured {runtime_label} command must produce at least one token.")
    return tuple(base_tokens)


def validate_stage_command_context(
    *,
    stage: str,
    work_item: str,
    run_id: str,
    workspace_root: Path | None = None,
    stage_brief_path: Path | None = None,
    prompt_pack_path: Path | None = None,
    prompt_pack_paths: tuple[Path, ...] | None = None,
    attempt_number: int | None = None,
    attempt_mode: str | None = None,
    input_bundle_path: Path | None = None,
    repair_brief_path: Path | None = None,
    operator_request_path: Path | None = None,
) -> None:
    if not stage.strip():
        raise ValueError("Stage context requires a non-empty stage id.")
    if not work_item.strip():
        raise ValueError("Stage context requires a non-empty work item id.")
    if not run_id.strip():
        raise ValueError("Stage context requires a non-empty run id.")
    if workspace_root is not None and str(workspace_root).strip() == "":
        raise ValueError("Stage context requires a workspace root path.")
    if stage_brief_path is not None and str(stage_brief_path).strip() == "":
        raise ValueError("Stage context requires a stage brief path.")
    if prompt_pack_path is not None and str(prompt_pack_path).strip() == "":
        raise ValueError("Stage context requires a prompt-pack path.")
    if prompt_pack_paths is not None:
        if not prompt_pack_paths:
            raise ValueError("Stage context requires at least one prompt-pack path.")
        if any(str(path).strip() == "" for path in prompt_pack_paths):
            raise ValueError("Stage context prompt-pack paths must not be empty.")
    if attempt_number is not None and attempt_number < 1:
        raise ValueError("Stage context attempt number must be greater than zero.")
    if attempt_mode is not None and not attempt_mode.strip():
        raise ValueError("Stage context attempt mode must not be empty.")
    if input_bundle_path is not None and str(input_bundle_path).strip() == "":
        raise ValueError("Stage context input bundle path must not be empty.")
    if repair_brief_path is not None and str(repair_brief_path).strip() == "":
        raise ValueError("Stage context repair brief path must not be empty.")
    if operator_request_path is not None and str(operator_request_path).strip() == "":
        raise ValueError("Stage context operator request path must not be empty.")


def resolve_exit_classification[ExitClassificationT: StrEnum](
    *,
    exit_code: int | None,
    stop_reason: ExitClassificationT | None,
    success_value: ExitClassificationT,
    non_zero_value: ExitClassificationT,
) -> ExitClassificationT:
    if stop_reason is not None:
        return stop_reason
    if exit_code == 0:
        return success_value
    return non_zero_value


def build_aidd_execution_environment(
    *,
    runtime_id: str,
    workspace_root: Path,
    stage: str,
    work_item: str,
    run_id: str,
    base_env: Mapping[str, str] | None = None,
    stage_brief_path: Path | None = None,
    prompt_pack_path: Path | None = None,
    prompt_pack_paths: tuple[Path, ...] = (),
    attempt_number: int | None = None,
    attempt_mode: str | None = None,
    repair_mode: bool | None = None,
    input_bundle_path: Path | None = None,
    repair_brief_path: Path | None = None,
    operator_request_path: Path | None = None,
) -> dict[str, str]:
    env = dict(base_env or {})
    env.update(
        {
            "AIDD_WORKSPACE_ROOT": workspace_root.as_posix(),
            "AIDD_STAGE": stage,
            "AIDD_WORK_ITEM": work_item,
            "AIDD_RUN_ID": run_id,
            "AIDD_RUNTIME_ID": runtime_id,
        }
    )
    if stage_brief_path is not None:
        env["AIDD_STAGE_BRIEF_PATH"] = stage_brief_path.as_posix()
    if prompt_pack_path is not None:
        env["AIDD_PROMPT_PACK_PATH"] = prompt_pack_path.as_posix()
    if prompt_pack_paths:
        env["AIDD_PROMPT_PACK_PATHS"] = os.pathsep.join(
            path.as_posix() for path in prompt_pack_paths
        )
    if attempt_number is not None:
        env["AIDD_ATTEMPT_NUMBER"] = str(attempt_number)
    if attempt_mode is not None:
        env["AIDD_ATTEMPT_MODE"] = attempt_mode
    if repair_mode is not None:
        env["AIDD_REPAIR_MODE"] = "true" if repair_mode else "false"
    if input_bundle_path is not None:
        env["AIDD_INPUT_BUNDLE_PATH"] = input_bundle_path.resolve(strict=False).as_posix()
    if repair_brief_path is not None:
        env["AIDD_REPAIR_BRIEF_PATH"] = repair_brief_path.resolve(strict=False).as_posix()
    if operator_request_path is not None:
        env["AIDD_OPERATOR_REQUEST_PATH"] = (
            operator_request_path.resolve(strict=False).as_posix()
        )
    return env


def persist_runtime_log_artifacts(
    *,
    attempt_path: Path,
    exit_code: int | None,
    exit_classification: str,
    stdout_text: str,
    stderr_text: str,
    runtime_log_text: str,
    adapter_outcome: RuntimeAdapterOutcome | None = None,
) -> RuntimeArtifactPaths:
    resolved_outcome = adapter_outcome or adapter_outcome_for_classification(
        exit_classification
    )
    return commit_runtime_evidence(
        RuntimeEvidenceCommitRequest(
            attempt_path=attempt_path,
            adapter_outcome=resolved_outcome,
            exit_classification=exit_classification,
            exit_code=exit_code,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            runtime_log_text=runtime_log_text,
            stop_reason=stop_reason_for_outcome(resolved_outcome),
        )
    )


__all__ = [
    "RUNTIME_LOG_FILENAME",
    "RuntimeArtifactPaths",
    "build_aidd_execution_environment",
    "persist_runtime_log_artifacts",
    "resolve_exit_classification",
    "split_configured_command",
    "validate_stage_command_context",
]
