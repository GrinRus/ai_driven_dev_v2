from __future__ import annotations

import shlex
import time
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
class QwenCommandContext:
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
        validate_stage_command_context(
            stage=self.stage,
            work_item=self.work_item,
            run_id=self.run_id,
            workspace_root=self.workspace_root,
            stage_brief_path=self.stage_brief_path,
            prompt_pack_paths=self.prompt_pack_paths,
            attempt_number=self.attempt_number,
            input_bundle_path=self.input_bundle_path,
            repair_brief_path=self.repair_brief_path,
        )


@dataclass(frozen=True, slots=True)
class QwenSubprocessSpec(RuntimeSubprocessSpec):
    pass


class QwenExitClassification(StrEnum):
    SUCCESS = "success"
    DOCUMENT_COMPLETE = "document_complete"
    NON_ZERO_EXIT = "non_zero_exit"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    DENIED = "denied"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class QwenRunResult(RuntimeRunResult[QwenExitClassification]):
    pass


_DOCUMENT_COMPLETION_SETTLE_SECONDS = 30.0
_DOCUMENT_PLACEHOLDERS = {
    "# Questions\n\nNo questions yet.",
    "# Answers\n\nNo answers yet.",
    "# Validator report\n\nNo validator output yet.",
    "# Stage result\n\nStage not run yet.",
}
_TERMINAL_DOCUMENT_NAMES = {"stage-result.md", "validator-report.md"}


def assemble_command(
    *,
    configured_command: str,
    context: QwenCommandContext,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    base_tokens = split_configured_command(
        configured_command=configured_command,
        runtime_label="qwen",
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


def _split_configured_command(*, configured_command: str) -> tuple[str, ...]:
    return split_configured_command(
        configured_command=configured_command,
        runtime_label="qwen",
    )


def _document_text_is_complete(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return False
    return bool(text) and text not in _DOCUMENT_PLACEHOLDERS


def _expected_documents_are_complete(paths: tuple[Path, ...]) -> bool:
    incomplete_documents = tuple(path for path in paths if not _document_text_is_complete(path))
    if not incomplete_documents:
        return True

    # `answers.md` is user/harness-owned when a stage blocks on fresh questions.
    # Let canonical validation decide whether the unanswered questions block progression.
    if all(path.name == "answers.md" for path in incomplete_documents):
        return any(
            _document_text_is_complete(path) for path in paths if path.name == "questions.md"
        )

    return False


def _document_mtime_ns(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


def _build_document_completion_requested(
    *,
    expected_output_documents: tuple[Path, ...],
    settle_seconds: float = _DOCUMENT_COMPLETION_SETTLE_SECONDS,
) -> Callable[[], bool] | None:
    expected_markdown_documents = tuple(
        path.resolve(strict=False)
        for path in expected_output_documents
        if path.suffix.lower() == ".md"
    )
    if not expected_markdown_documents:
        return None

    baseline_mtimes = {
        path: _document_mtime_ns(path) for path in expected_markdown_documents
    }
    terminal_documents = tuple(
        path for path in expected_markdown_documents if path.name in _TERMINAL_DOCUMENT_NAMES
    )
    complete_since: float | None = None

    def _document_changed(path: Path) -> bool:
        return _document_mtime_ns(path) != baseline_mtimes[path]

    def _completion_requested() -> bool:
        nonlocal complete_since
        if not _expected_documents_are_complete(expected_markdown_documents):
            complete_since = None
            return False
        if terminal_documents:
            terminal_docs_changed = all(_document_changed(path) for path in terminal_documents)
            if not terminal_docs_changed:
                complete_since = None
                return False
        elif not any(_document_changed(path) for path in expected_markdown_documents):
            complete_since = None
            return False

        now = time.monotonic()
        if complete_since is None:
            complete_since = now
            return False
        return now - complete_since >= settle_seconds

    return _completion_requested


def _build_native_prompt_text(
    *,
    context: QwenCommandContext,
    repository_root: Path | None,
) -> str:
    return compile_native_prompt_text(
        runtime_id="qwen",
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
    context: QwenCommandContext,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    _ = context, repository_root
    return _split_configured_command(configured_command=configured_command)


def build_execution_environment(
    *,
    context: QwenCommandContext,
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
        runtime_id="qwen",
        workspace_root=resolved_workspace_root,
        stage=context.stage,
        work_item=context.work_item,
        run_id=context.run_id,
        base_env=base_env,
        stage_brief_path=resolved_stage_brief_path,
        prompt_pack_paths=resolved_prompt_pack_paths,
        attempt_number=context.attempt_number,
        repair_mode=context.repair_mode,
        input_bundle_path=context.input_bundle_path,
        repair_brief_path=context.repair_brief_path,
    )


def build_subprocess_spec(
    *,
    configured_command: str,
    context: QwenCommandContext,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
    execution_mode: str | RuntimeExecutionMode = RuntimeExecutionMode.ADAPTER_FLAGS,
) -> QwenSubprocessSpec:
    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    mode = normalize_execution_mode(runtime_id="qwen", value=execution_mode)
    if mode is RuntimeExecutionMode.NATIVE:
        resolved_repository_root = (repository_root or Path.cwd()).resolve(strict=False)
        return QwenSubprocessSpec(
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
    return QwenSubprocessSpec(
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
    stop_reason: QwenExitClassification | None,
) -> QwenExitClassification:
    return resolve_exit_classification(
        exit_code=exit_code,
        stop_reason=stop_reason,
        success_value=QwenExitClassification.SUCCESS,
        non_zero_value=QwenExitClassification.NON_ZERO_EXIT,
    )


def run_subprocess_with_streaming(
    *,
    spec: QwenSubprocessSpec,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    timeout_seconds: float | None = None,
    cancel_requested: Callable[[], bool] | None = None,
    document_completion_paths: tuple[Path, ...] = (),
    document_completion_settle_seconds: float = _DOCUMENT_COMPLETION_SETTLE_SECONDS,
) -> QwenRunResult:
    completion_requested = _build_document_completion_requested(
        expected_output_documents=document_completion_paths,
        settle_seconds=document_completion_settle_seconds,
    )
    streamed_result = run_streamed_subprocess(
        spec=spec,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
        timeout_seconds=timeout_seconds,
        cancel_requested=cancel_requested,
        completion_requested=completion_requested,
        completion_stop_reason=(
            QwenExitClassification.DOCUMENT_COMPLETE
            if completion_requested is not None
            else None
        ),
        timeout_stop_reason=QwenExitClassification.TIMEOUT,
        cancel_stop_reason=QwenExitClassification.CANCELLED,
    )
    exit_classification = _resolve_exit_classification(
        exit_code=streamed_result.exit_code,
        stop_reason=streamed_result.stop_reason,
    )
    return QwenRunResult(
        exit_code=streamed_result.exit_code,
        stdout_text=streamed_result.stdout_text,
        stderr_text=streamed_result.stderr_text,
        runtime_log_text=streamed_result.runtime_log_text,
        exit_classification=exit_classification,
    )


def persist_attempt_runtime_log(
    *,
    attempt_path: Path,
    run_result: QwenRunResult,
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
    context: QwenCommandContext,
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
