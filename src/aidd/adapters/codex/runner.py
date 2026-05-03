from __future__ import annotations

import os
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
from aidd.adapters.runtime_artifacts import write_runtime_exit_metadata
from aidd.adapters.runtime_execution import RuntimeRunResult, RuntimeSubprocessSpec
from aidd.adapters.runtime_registry import RuntimeExecutionMode, normalize_execution_mode
from aidd.adapters.subprocess_streaming import run_streamed_subprocess
from aidd.core.run_store import RUN_RUNTIME_LOG_FILENAME


@dataclass(frozen=True, slots=True)
class CodexCommandContext:
    stage: str
    work_item: str
    run_id: str
    workspace_root: Path
    stage_brief_path: Path
    prompt_pack_paths: tuple[Path, ...]
    attempt_number: int = 1
    repair_mode: bool = False
    input_bundle_path: Path | None = None
    repair_brief_path: Path | None = None
    repair_context_markdown: str | None = None

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("Stage context requires a non-empty stage id.")
        if not self.work_item.strip():
            raise ValueError("Stage context requires a non-empty work item id.")
        if not self.run_id.strip():
            raise ValueError("Stage context requires a non-empty run id.")
        if str(self.workspace_root).strip() == "":
            raise ValueError("Stage context requires a workspace root path.")
        if str(self.stage_brief_path).strip() == "":
            raise ValueError("Stage context requires a stage brief path.")
        if not self.prompt_pack_paths:
            raise ValueError("Stage context requires at least one prompt-pack path.")
        if any(str(path).strip() == "" for path in self.prompt_pack_paths):
            raise ValueError("Stage context prompt-pack paths must not be empty.")
        if self.attempt_number < 1:
            raise ValueError("Stage context attempt number must be greater than zero.")
        if self.input_bundle_path is not None and str(self.input_bundle_path).strip() == "":
            raise ValueError("Stage context input bundle path must not be empty.")
        if self.repair_brief_path is not None and str(self.repair_brief_path).strip() == "":
            raise ValueError("Stage context repair brief path must not be empty.")


@dataclass(frozen=True, slots=True)
class CodexSubprocessSpec(RuntimeSubprocessSpec):
    pass


class CodexExitClassification(StrEnum):
    SUCCESS = "success"
    NON_ZERO_EXIT = "non_zero_exit"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class CodexRunResult(RuntimeRunResult[CodexExitClassification]):
    pass


def assemble_command(
    *,
    configured_command: str,
    context: CodexCommandContext,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    stripped = configured_command.strip()
    if not stripped:
        raise ValueError("Configured codex command must not be empty.")

    try:
        base_tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(
            f"Configured codex command is not valid shell syntax: {configured_command!r}"
        ) from exc
    if not base_tokens:
        raise ValueError("Configured codex command must produce at least one token.")

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
        repair_mode=context.repair_mode,
        input_bundle_path=context.input_bundle_path,
        repair_brief_path=context.repair_brief_path,
        repair_context_markdown=context.repair_context_markdown,
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

    env = dict(base_env or {})
    env.update(
        {
            "AIDD_WORKSPACE_ROOT": resolved_workspace_root.as_posix(),
            "AIDD_STAGE": context.stage,
            "AIDD_WORK_ITEM": context.work_item,
            "AIDD_RUN_ID": context.run_id,
            "AIDD_ATTEMPT_NUMBER": str(context.attempt_number),
            "AIDD_REPAIR_MODE": "true" if context.repair_mode else "false",
            "AIDD_STAGE_BRIEF_PATH": resolved_stage_brief_path.as_posix(),
            "AIDD_PROMPT_PACK_PATHS": os.pathsep.join(
                path.as_posix() for path in resolved_prompt_pack_paths
            ),
            "AIDD_RUNTIME_ID": "codex",
        }
    )
    if context.input_bundle_path is not None:
        env["AIDD_INPUT_BUNDLE_PATH"] = context.input_bundle_path.resolve(
            strict=False
        ).as_posix()
    if context.repair_brief_path is not None:
        env["AIDD_REPAIR_BRIEF_PATH"] = context.repair_brief_path.resolve(
            strict=False
        ).as_posix()
    return env


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
    exit_code: int,
    stop_reason: CodexExitClassification | None,
) -> CodexExitClassification:
    if stop_reason is not None:
        return stop_reason
    if exit_code == 0:
        return CodexExitClassification.SUCCESS
    return CodexExitClassification.NON_ZERO_EXIT


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
    runtime_log_path = attempt_path / RUN_RUNTIME_LOG_FILENAME
    runtime_log_path.write_text(run_result.runtime_log_text, encoding="utf-8")
    write_runtime_exit_metadata(
        attempt_path=attempt_path,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
        runtime_log_text=run_result.runtime_log_text,
    )
    return runtime_log_path


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
