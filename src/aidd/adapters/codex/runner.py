from __future__ import annotations

import shlex
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from aidd.adapters.native_prompt import build_native_prompt_text as compile_native_prompt_text
from aidd.adapters.path_resolution import (
    resolve_prompt_pack_paths_for_execution,
    resolve_stage_brief_path_for_execution,
)
from aidd.adapters.runner_support import (
    build_aidd_execution_environment,
    persist_runtime_log_artifacts,
    resolve_exit_classification,
    split_configured_command,
    validate_stage_command_context,
)
from aidd.adapters.runtime_execution import RuntimeRunResult, RuntimeSubprocessSpec
from aidd.adapters.subprocess_streaming import run_streamed_subprocess
from aidd.runtime_catalog import RuntimeExecutionMode, normalize_execution_mode


@dataclass(frozen=True, slots=True)
class CodexCommandContext:
    stage: str
    work_item: str
    run_id: str
    workspace_root: Path
    stage_brief_path: Path
    prompt_pack_paths: tuple[Path, ...]
    attempt_number: int = 1
    attempt_mode: str = "initial"
    repair_mode: bool = False
    input_bundle_path: Path | None = None
    repair_brief_path: Path | None = None
    repair_context_markdown: str | None = None
    operator_request_path: Path | None = None
    operator_request_markdown: str | None = None

    def __post_init__(self) -> None:
        validate_stage_command_context(
            stage=self.stage,
            work_item=self.work_item,
            run_id=self.run_id,
            workspace_root=self.workspace_root,
            stage_brief_path=self.stage_brief_path,
            prompt_pack_paths=self.prompt_pack_paths,
            attempt_number=self.attempt_number,
            attempt_mode=self.attempt_mode,
            input_bundle_path=self.input_bundle_path,
            repair_brief_path=self.repair_brief_path,
            operator_request_path=self.operator_request_path,
        )


@dataclass(frozen=True, slots=True)
class CodexSubprocessSpec(RuntimeSubprocessSpec):
    pass


class CodexExitClassification(StrEnum):
    SUCCESS = "success"
    NON_ZERO_EXIT = "non_zero_exit"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    DENIED = "denied"
    BLOCKED = "blocked"
    PROTOCOL_FAILURE = "protocol_failure"
    LAUNCH_FAILURE = "launch_failure"


@dataclass(frozen=True, slots=True)
class CodexRunResult(RuntimeRunResult[CodexExitClassification]):
    pass


def assemble_command(
    *,
    configured_command: str,
    context: CodexCommandContext,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    base_tokens = split_configured_command(
        configured_command=configured_command,
        runtime_label="codex",
    )

    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    resolved_stage_brief_path = resolve_stage_brief_path_for_execution(
        stage_brief_path=context.stage_brief_path,
        workspace_root=resolved_workspace_root,
    )
    resolved_prompt_pack_paths = resolve_prompt_pack_paths_for_execution(
        prompt_pack_paths=context.prompt_pack_paths,
        repository_root=repository_root,
    )

    command: list[str] = [
        *base_tokens,
        "--stage",
        context.stage,
        "--work-item",
        context.work_item,
        "--run-id",
        context.run_id,
        "--workspace-root",
        resolved_workspace_root.as_posix(),
        "--stage-brief",
        resolved_stage_brief_path.as_posix(),
    ]
    for prompt_pack_path in resolved_prompt_pack_paths:
        command.extend(("--prompt-pack", prompt_pack_path.as_posix()))

    return tuple(command)


def _split_configured_command(*, configured_command: str, runtime_label: str) -> tuple[str, ...]:
    return split_configured_command(
        configured_command=configured_command,
        runtime_label=runtime_label,
    )


def _read_text_for_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"[missing file: {path.as_posix()}]\n"


def _build_native_prompt_text(
    *,
    context: CodexCommandContext,
    repository_root: Path | None,
) -> str:
    return compile_native_prompt_text(
        runtime_id="codex",
        stage=context.stage,
        work_item=context.work_item,
        run_id=context.run_id,
        workspace_root=context.workspace_root,
        stage_brief_path=context.stage_brief_path,
        prompt_pack_paths=context.prompt_pack_paths,
        repository_root=repository_root,
        attempt_number=context.attempt_number,
        attempt_mode=context.attempt_mode,
        repair_mode=context.repair_mode,
        input_bundle_path=context.input_bundle_path,
        repair_brief_path=context.repair_brief_path,
        repair_context_markdown=context.repair_context_markdown,
        operator_request_path=context.operator_request_path,
        operator_request_markdown=context.operator_request_markdown,
    )


def assemble_native_command(
    *,
    configured_command: str,
    context: CodexCommandContext,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    _ = context, repository_root
    return _split_configured_command(
        configured_command=configured_command,
        runtime_label="codex",
    )


def build_execution_environment(
    *,
    context: CodexCommandContext,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> dict[str, str]:
    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    resolved_stage_brief_path = resolve_stage_brief_path_for_execution(
        stage_brief_path=context.stage_brief_path,
        workspace_root=resolved_workspace_root,
    )
    resolved_prompt_pack_paths = resolve_prompt_pack_paths_for_execution(
        prompt_pack_paths=context.prompt_pack_paths,
        repository_root=repository_root,
    )

    return build_aidd_execution_environment(
        runtime_id="codex",
        workspace_root=resolved_workspace_root,
        stage=context.stage,
        work_item=context.work_item,
        run_id=context.run_id,
        base_env=base_env,
        stage_brief_path=resolved_stage_brief_path,
        prompt_pack_paths=resolved_prompt_pack_paths,
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
    context: CodexCommandContext,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
    execution_mode: str | RuntimeExecutionMode = RuntimeExecutionMode.ADAPTER_FLAGS,
) -> CodexSubprocessSpec:
    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    mode = normalize_execution_mode(runtime_id="codex", value=execution_mode)
    if mode is RuntimeExecutionMode.NATIVE:
        resolved_repository_root = (repository_root or Path.cwd()).resolve(strict=False)
        return CodexSubprocessSpec(
            command=assemble_native_command(
                configured_command=configured_command,
                context=context,
                repository_root=repository_root,
            ),
            cwd=resolved_repository_root,
            env=build_execution_environment(
                context=context,
                base_env=base_env,
                repository_root=repository_root,
            ),
            stdin_text=_build_native_prompt_text(
                context=context,
                repository_root=repository_root,
            ),
        )
    return CodexSubprocessSpec(
        command=assemble_command(
            configured_command=configured_command,
            context=context,
            repository_root=repository_root,
        ),
        cwd=resolved_workspace_root,
        env=build_execution_environment(
            context=context,
            base_env=base_env,
            repository_root=repository_root,
        ),
    )


def _resolve_exit_classification(
    *,
    exit_code: int | None,
    stop_reason: CodexExitClassification | None,
) -> CodexExitClassification:
    return resolve_exit_classification(
        exit_code=exit_code,
        stop_reason=stop_reason,
        success_value=CodexExitClassification.SUCCESS,
        non_zero_value=CodexExitClassification.NON_ZERO_EXIT,
    )


def run_subprocess_with_streaming(
    *,
    spec: CodexSubprocessSpec,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    timeout_seconds: float | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> CodexRunResult:
    streamed_result = run_streamed_subprocess(
        spec=spec,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
        timeout_seconds=timeout_seconds,
        cancel_requested=cancel_requested,
        timeout_stop_reason=CodexExitClassification.TIMEOUT,
        cancel_stop_reason=CodexExitClassification.CANCELLED,
        launch_failure_stop_reason=CodexExitClassification.LAUNCH_FAILURE,
    )
    exit_classification = _resolve_exit_classification(
        exit_code=streamed_result.exit_code,
        stop_reason=streamed_result.stop_reason,
    )
    return CodexRunResult(
        exit_code=streamed_result.exit_code,
        stdout_text=streamed_result.stdout_text,
        stderr_text=streamed_result.stderr_text,
        runtime_log_text=streamed_result.runtime_log_text,
        exit_classification=exit_classification,
    )


def persist_attempt_runtime_log(
    *,
    attempt_path: Path,
    run_result: CodexRunResult,
) -> Path:
    attempt_path.mkdir(parents=True, exist_ok=True)
    paths = persist_runtime_log_artifacts(
        attempt_path=attempt_path,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
        runtime_log_text=run_result.runtime_log_text,
    )
    return paths.runtime_log_path


def command_preview(
    *,
    configured_command: str,
    context: CodexCommandContext,
    repository_root: Path | None = None,
) -> str:
    return " ".join(
        shlex.quote(token)
        for token in assemble_command(
            configured_command=configured_command,
            context=context,
            repository_root=repository_root,
        )
    )
