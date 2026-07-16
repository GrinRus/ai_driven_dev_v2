from __future__ import annotations

import shlex
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from aidd.adapters.path_resolution import resolve_prompt_pack_path_for_execution
from aidd.adapters.runner_support import (
    build_aidd_execution_environment,
    persist_runtime_log_artifacts,
    resolve_exit_classification,
    split_configured_command,
    validate_stage_command_context,
)
from aidd.adapters.runtime_artifacts import (
    RUNTIME_EXIT_METADATA_FILENAME as _RUNTIME_EXIT_METADATA_FILENAME,
)
from aidd.adapters.runtime_execution import RuntimeRunResult, RuntimeSubprocessSpec
from aidd.adapters.subprocess_streaming import run_streamed_subprocess


@dataclass(frozen=True, slots=True)
class GenericCliStageContext:
    stage: str
    work_item: str
    run_id: str
    prompt_pack_path: Path
    attempt_number: int = 1
    attempt_mode: str = "initial"
    repair_mode: bool = False
    input_bundle_path: Path | None = None
    repair_brief_path: Path | None = None
    operator_request_path: Path | None = None

    def __post_init__(self) -> None:
        validate_stage_command_context(
            stage=self.stage,
            work_item=self.work_item,
            run_id=self.run_id,
            prompt_pack_path=self.prompt_pack_path,
            attempt_number=self.attempt_number,
            attempt_mode=self.attempt_mode,
            input_bundle_path=self.input_bundle_path,
            repair_brief_path=self.repair_brief_path,
            operator_request_path=self.operator_request_path,
        )


@dataclass(frozen=True, slots=True)
class GenericCliSubprocessSpec(RuntimeSubprocessSpec):
    pass


@dataclass(frozen=True, slots=True)
class GenericCliRuntimeArtifacts:
    runtime_log_path: Path
    runtime_exit_metadata_path: Path


class GenericCliExitClassification(StrEnum):
    SUCCESS = "success"
    NON_ZERO_EXIT = "non_zero_exit"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    LAUNCH_FAILURE = "launch_failure"


@dataclass(frozen=True, slots=True)
class GenericCliRunResult(RuntimeRunResult[GenericCliExitClassification]):
    pass


RUNTIME_EXIT_METADATA_FILENAME = _RUNTIME_EXIT_METADATA_FILENAME


def _resolve_exit_classification(
    *,
    exit_code: int | None,
    stop_reason: GenericCliExitClassification | None,
) -> GenericCliExitClassification:
    return resolve_exit_classification(
        exit_code=exit_code,
        stop_reason=stop_reason,
        success_value=GenericCliExitClassification.SUCCESS,
        non_zero_value=GenericCliExitClassification.NON_ZERO_EXIT,
    )


def assemble_command(
    *,
    configured_command: str,
    context: GenericCliStageContext,
) -> tuple[str, ...]:
    base_tokens = split_configured_command(
        configured_command=configured_command,
        runtime_label="generic-cli",
    )

    return (
        *base_tokens,
        "--stage",
        context.stage,
        "--work-item",
        context.work_item,
        "--run-id",
        context.run_id,
        "--prompt-pack",
        context.prompt_pack_path.as_posix(),
    )


def command_preview(
    *,
    configured_command: str,
    context: GenericCliStageContext,
) -> str:
    return " ".join(shlex.quote(token) for token in assemble_command(
        configured_command=configured_command,
        context=context,
    ))


def build_execution_environment(
    *,
    workspace_root: Path,
    context: GenericCliStageContext,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    return build_aidd_execution_environment(
        runtime_id="generic-cli",
        workspace_root=workspace_root,
        stage=context.stage,
        work_item=context.work_item,
        run_id=context.run_id,
        base_env=base_env,
        prompt_pack_path=context.prompt_pack_path,
        attempt_number=context.attempt_number,
        attempt_mode=context.attempt_mode,
        repair_mode=context.repair_mode,
        input_bundle_path=context.input_bundle_path,
        repair_brief_path=context.repair_brief_path,
        operator_request_path=context.operator_request_path,
    )


def build_subprocess_spec(
    *,
    configured_command: str,
    workspace_root: Path,
    context: GenericCliStageContext,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> GenericCliSubprocessSpec:
    resolved_workspace_root = workspace_root.resolve(strict=False)
    resolved_prompt_pack_path = resolve_prompt_pack_path_for_execution(
        prompt_pack_path=context.prompt_pack_path,
        repository_root=repository_root,
    )
    resolved_context = GenericCliStageContext(
        stage=context.stage,
        work_item=context.work_item,
        run_id=context.run_id,
        prompt_pack_path=resolved_prompt_pack_path,
        attempt_number=context.attempt_number,
        attempt_mode=context.attempt_mode,
        repair_mode=context.repair_mode,
        input_bundle_path=context.input_bundle_path,
        repair_brief_path=context.repair_brief_path,
        operator_request_path=context.operator_request_path,
    )
    return GenericCliSubprocessSpec(
        command=assemble_command(
            configured_command=configured_command,
            context=resolved_context,
        ),
        cwd=resolved_workspace_root,
        env=build_execution_environment(
            workspace_root=resolved_workspace_root,
            context=resolved_context,
            base_env=base_env,
        ),
    )


def run_subprocess_with_streaming(
    *,
    spec: GenericCliSubprocessSpec,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    timeout_seconds: float | None = None,
    cancel_requested: Callable[[], bool] | None = None,
    capture_directory: Path | None = None,
) -> GenericCliRunResult:
    streamed_result = run_streamed_subprocess(
        spec=spec,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
        timeout_seconds=timeout_seconds,
        cancel_requested=cancel_requested,
        timeout_stop_reason=GenericCliExitClassification.TIMEOUT,
        cancel_stop_reason=GenericCliExitClassification.CANCELLED,
        launch_failure_stop_reason=GenericCliExitClassification.LAUNCH_FAILURE,
        capture_directory=capture_directory,
    )
    exit_classification = _resolve_exit_classification(
        exit_code=streamed_result.exit_code,
        stop_reason=streamed_result.stop_reason,
    )
    return GenericCliRunResult(
        exit_code=streamed_result.exit_code,
        stdout_text=streamed_result.stdout_text,
        stderr_text=streamed_result.stderr_text,
        runtime_log_text=streamed_result.runtime_log_text,
        exit_classification=exit_classification,
        runtime_log_source_path=streamed_result.runtime_log_source_path,
        structured_events_source_path=streamed_result.structured_events_source_path,
        stdout_byte_count=streamed_result.stdout_byte_count,
        stderr_byte_count=streamed_result.stderr_byte_count,
        runtime_log_byte_count=streamed_result.runtime_log_byte_count,
        stdout_char_count=streamed_result.stdout_char_count,
        stderr_char_count=streamed_result.stderr_char_count,
        runtime_log_char_count=streamed_result.runtime_log_char_count,
        stdout_truncated=streamed_result.stdout_truncated,
        stderr_truncated=streamed_result.stderr_truncated,
        runtime_log_truncated=streamed_result.runtime_log_truncated,
    )


def persist_attempt_runtime_artifacts(
    *,
    attempt_path: Path,
    run_result: GenericCliRunResult,
) -> GenericCliRuntimeArtifacts:
    attempt_path.mkdir(parents=True, exist_ok=True)

    paths = persist_runtime_log_artifacts(
        attempt_path=attempt_path,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
        runtime_log_text=run_result.runtime_log_text,
        runtime_log_source_path=run_result.runtime_log_source_path,
        stdout_byte_count=run_result.stdout_byte_count,
        stderr_byte_count=run_result.stderr_byte_count,
        runtime_log_byte_count=run_result.runtime_log_byte_count,
        stdout_char_count=run_result.stdout_char_count,
        stderr_char_count=run_result.stderr_char_count,
        runtime_log_char_count=run_result.runtime_log_char_count,
        stdout_truncated=run_result.stdout_truncated,
        stderr_truncated=run_result.stderr_truncated,
        runtime_log_truncated=run_result.runtime_log_truncated,
    )

    return GenericCliRuntimeArtifacts(
        runtime_log_path=paths.runtime_log_path,
        runtime_exit_metadata_path=paths.runtime_exit_metadata_path,
    )
