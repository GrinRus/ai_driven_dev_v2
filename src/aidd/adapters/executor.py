from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aidd.adapters.base import (
    CapabilityReport,
    RuntimeCapabilities,
    RuntimeStartRequest,
    RuntimeStartResult,
    RuntimeStream,
)
from aidd.adapters.claude_code.probe import probe as probe_claude_code
from aidd.adapters.claude_code.runner import (
    ClaudeCodeCommandContext,
    detect_question_or_pause_events,
    normalize_structured_events,
    persist_normalized_events_jsonl,
    persist_surfaced_questions,
    route_questions_with_file_fallback,
)
from aidd.adapters.claude_code.runner import (
    build_subprocess_spec as build_claude_subprocess_spec,
)
from aidd.adapters.claude_code.runner import (
    persist_attempt_runtime_log as persist_claude_runtime_log,
)
from aidd.adapters.claude_code.runner import (
    run_subprocess_with_streaming as run_claude_subprocess_with_streaming,
)
from aidd.adapters.codex.probe import probe as probe_codex
from aidd.adapters.codex.runner import (
    CodexCommandContext,
)
from aidd.adapters.codex.runner import (
    build_subprocess_spec as build_codex_subprocess_spec,
)
from aidd.adapters.codex.runner import (
    persist_attempt_runtime_log as persist_codex_runtime_log,
)
from aidd.adapters.codex.runner import (
    run_subprocess_with_streaming as run_codex_subprocess_with_streaming,
)
from aidd.adapters.generic_cli.probe import probe as probe_generic_cli
from aidd.adapters.generic_cli.runner import (
    GenericCliStageContext,
    persist_attempt_runtime_artifacts,
)
from aidd.adapters.generic_cli.runner import (
    build_subprocess_spec as build_generic_subprocess_spec,
)
from aidd.adapters.generic_cli.runner import (
    run_subprocess_with_streaming as run_generic_subprocess_with_streaming,
)
from aidd.adapters.opencode.probe import probe as probe_opencode
from aidd.adapters.opencode.runner import (
    OpenCodeCommandContext,
)
from aidd.adapters.opencode.runner import (
    build_subprocess_spec as build_opencode_subprocess_spec,
)
from aidd.adapters.opencode.runner import (
    persist_attempt_runtime_log as persist_opencode_runtime_log,
)
from aidd.adapters.opencode.runner import (
    run_subprocess_with_streaming as run_opencode_subprocess_with_streaming,
)
from aidd.adapters.pi_mono.probe import probe as probe_pi_mono
from aidd.adapters.pi_mono.runner import (
    PiMonoCommandContext,
)
from aidd.adapters.pi_mono.runner import (
    build_subprocess_spec as build_pi_mono_subprocess_spec,
)
from aidd.adapters.pi_mono.runner import (
    persist_attempt_runtime_log as persist_pi_mono_runtime_log,
)
from aidd.adapters.pi_mono.runner import (
    run_subprocess_with_streaming as run_pi_mono_subprocess_with_streaming,
)
from aidd.config import AiddConfig
from aidd.core.run_store import RUN_RUNTIME_LOG_FILENAME

SUPPORTED_RUNTIMES: tuple[str, ...] = (
    "generic-cli",
    "claude-code",
    "codex",
    "opencode",
    "pi-mono",
)

StreamCallback = Callable[[RuntimeStream, str], None]


@dataclass(frozen=True, slots=True)
class RuntimeExecutionContext:
    runtime_id: str
    configured_command: str
    request: RuntimeStartRequest
    on_stream: StreamCallback | None = None


def resolve_runtime_command(*, runtime_id: str, config: AiddConfig) -> str:
    runtime = runtime_id.strip().lower()
    if runtime == "generic-cli":
        return config.generic_cli_command
    if runtime == "claude-code":
        return config.claude_code_command
    if runtime == "codex":
        return config.codex_command
    if runtime == "opencode":
        return config.opencode_command
    if runtime == "pi-mono":
        return config.pi_mono_command
    raise ValueError(
        f"Unsupported runtime '{runtime_id}'. Expected one of: {', '.join(SUPPORTED_RUNTIMES)}"
    )


def probe_runtime(*, runtime_id: str, command: str) -> RuntimeCapabilities:
    runtime = runtime_id.strip().lower()
    if runtime == "generic-cli":
        return probe_generic_cli(command)
    if runtime == "claude-code":
        return probe_claude_code(command)
    if runtime == "codex":
        return probe_codex(command)
    if runtime == "opencode":
        return probe_opencode(command)
    if runtime == "pi-mono":
        return probe_pi_mono(command)
    raise ValueError(
        f"Unsupported runtime '{runtime_id}'. Expected one of: {', '.join(SUPPORTED_RUNTIMES)}"
    )


def _emit_stream(callback: StreamCallback | None, *, stream: RuntimeStream, chunk: str) -> None:
    if callback is None:
        return
    callback(stream, chunk)


def _adapter_failure_result(
    *,
    request: RuntimeStartRequest,
    runtime_id: str,
    exc: Exception,
) -> RuntimeStartResult:
    request.attempt_path.mkdir(parents=True, exist_ok=True)
    runtime_log_path = request.attempt_path / RUN_RUNTIME_LOG_FILENAME
    failure_message = f"[adapter-failure] {exc}\n"
    runtime_log_path.write_text(failure_message, encoding="utf-8")
    return RuntimeStartResult(
        runtime_id=runtime_id,
        exit_code=-1,
        exit_classification="adapter_failure",
        runtime_log_path=runtime_log_path,
        stdout_text="",
        stderr_text=failure_message,
    )


def _assert_prompt_pack_paths(request: RuntimeStartRequest) -> None:
    if request.prompt_pack_paths:
        return
    raise ValueError("Runtime execution requires at least one prompt-pack path.")


def _execute_generic(context: RuntimeExecutionContext) -> RuntimeStartResult:
    _assert_prompt_pack_paths(context.request)
    request = context.request
    runtime_id = "generic-cli"
    adapter_context = GenericCliStageContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        prompt_pack_path=request.prompt_pack_paths[0],
    )
    spec = build_generic_subprocess_spec(
        configured_command=context.configured_command,
        workspace_root=request.workspace_root,
        context=adapter_context,
        repository_root=request.repository_root,
    )
    run_result = run_generic_subprocess_with_streaming(
        spec=spec,
        on_stdout=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stdout",
            chunk=chunk,
        ),
        on_stderr=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stderr",
            chunk=chunk,
        ),
        timeout_seconds=request.timeout_seconds,
    )
    artifacts = persist_attempt_runtime_artifacts(
        attempt_path=request.attempt_path,
        run_result=run_result,
    )
    return RuntimeStartResult(
        runtime_id=runtime_id,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        runtime_log_path=artifacts.runtime_log_path,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
    )


def _execute_claude(context: RuntimeExecutionContext) -> RuntimeStartResult:
    _assert_prompt_pack_paths(context.request)
    request = context.request
    runtime_id = "claude-code"
    adapter_context = ClaudeCodeCommandContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        workspace_root=request.workspace_root,
        stage_brief_path=request.stage_brief_path,
        prompt_pack_paths=request.prompt_pack_paths,
    )
    spec = build_claude_subprocess_spec(
        configured_command=context.configured_command,
        context=adapter_context,
        repository_root=request.repository_root,
    )
    run_result = run_claude_subprocess_with_streaming(
        spec=spec,
        on_stdout=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stdout",
            chunk=chunk,
        ),
        on_stderr=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stderr",
            chunk=chunk,
        ),
        timeout_seconds=request.timeout_seconds,
    )
    runtime_artifacts = persist_claude_runtime_log(
        attempt_path=request.attempt_path,
        run_result=run_result,
    )
    normalized_events = normalize_structured_events(run_result=run_result)
    normalized_events_path = persist_normalized_events_jsonl(
        attempt_path=request.attempt_path,
        run_result=run_result,
    )
    question_detection = detect_question_or_pause_events(normalized_events=normalized_events)
    question_routing = route_questions_with_file_fallback(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        stage=request.stage,
        runtime_detection=question_detection,
    )
    unresolved_ids: tuple[str, ...] = ()
    if question_routing.question_events or question_routing.pause_detected:
        stage_questions_path = (
            request.workspace_root
            / "workitems"
            / request.work_item
            / "stages"
            / request.stage
            / "questions.md"
        )
        stage_questions_markdown = (
            stage_questions_path.read_text(encoding="utf-8")
            if stage_questions_path.exists()
            else None
        )
        persistence = persist_surfaced_questions(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
            adapter_question_events=question_routing.question_events,
            stage_output_questions_markdown=stage_questions_markdown,
        )
        unresolved_ids = persistence.unresolved_blocking_question_ids
    return RuntimeStartResult(
        runtime_id=runtime_id,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        runtime_log_path=runtime_artifacts.runtime_log_path,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
        normalized_events_path=normalized_events_path,
        normalized_events=normalized_events,
        unresolved_blocking_question_ids=unresolved_ids,
    )


def _execute_codex(context: RuntimeExecutionContext) -> RuntimeStartResult:
    _assert_prompt_pack_paths(context.request)
    request = context.request
    runtime_id = "codex"
    adapter_context = CodexCommandContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        workspace_root=request.workspace_root,
        stage_brief_path=request.stage_brief_path,
        prompt_pack_paths=request.prompt_pack_paths,
    )
    spec = build_codex_subprocess_spec(
        configured_command=context.configured_command,
        context=adapter_context,
        repository_root=request.repository_root,
    )
    run_result = run_codex_subprocess_with_streaming(
        spec=spec,
        on_stdout=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stdout",
            chunk=chunk,
        ),
        on_stderr=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stderr",
            chunk=chunk,
        ),
        timeout_seconds=request.timeout_seconds,
    )
    runtime_log_path = persist_codex_runtime_log(
        attempt_path=request.attempt_path,
        run_result=run_result,
    )
    return RuntimeStartResult(
        runtime_id=runtime_id,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        runtime_log_path=runtime_log_path,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
    )


def _execute_opencode(context: RuntimeExecutionContext) -> RuntimeStartResult:
    _assert_prompt_pack_paths(context.request)
    request = context.request
    runtime_id = "opencode"
    adapter_context = OpenCodeCommandContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        workspace_root=request.workspace_root,
        stage_brief_path=request.stage_brief_path,
        prompt_pack_paths=request.prompt_pack_paths,
    )
    spec = build_opencode_subprocess_spec(
        configured_command=context.configured_command,
        context=adapter_context,
        repository_root=request.repository_root,
    )
    run_result = run_opencode_subprocess_with_streaming(
        spec=spec,
        on_stdout=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stdout",
            chunk=chunk,
        ),
        on_stderr=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stderr",
            chunk=chunk,
        ),
        timeout_seconds=request.timeout_seconds,
    )
    runtime_log_path = persist_opencode_runtime_log(
        attempt_path=request.attempt_path,
        run_result=run_result,
    )
    return RuntimeStartResult(
        runtime_id=runtime_id,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        runtime_log_path=runtime_log_path,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
    )


def _execute_pi_mono(context: RuntimeExecutionContext) -> RuntimeStartResult:
    _assert_prompt_pack_paths(context.request)
    request = context.request
    runtime_id = "pi-mono"
    adapter_context = PiMonoCommandContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        workspace_root=request.workspace_root,
        stage_brief_path=request.stage_brief_path,
        prompt_pack_paths=request.prompt_pack_paths,
    )
    spec = build_pi_mono_subprocess_spec(
        configured_command=context.configured_command,
        context=adapter_context,
        repository_root=request.repository_root,
    )
    run_result = run_pi_mono_subprocess_with_streaming(
        spec=spec,
        on_stdout=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stdout",
            chunk=chunk,
        ),
        on_stderr=lambda chunk: _emit_stream(
            context.on_stream,
            stream="stderr",
            chunk=chunk,
        ),
        timeout_seconds=request.timeout_seconds,
    )
    runtime_log_path = persist_pi_mono_runtime_log(
        attempt_path=request.attempt_path,
        run_result=run_result,
    )
    return RuntimeStartResult(
        runtime_id=runtime_id,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        runtime_log_path=runtime_log_path,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
    )


def execute_runtime_stage(context: RuntimeExecutionContext) -> RuntimeStartResult:
    runtime = context.runtime_id.strip().lower()
    try:
        if runtime == "generic-cli":
            return _execute_generic(context)
        if runtime == "claude-code":
            return _execute_claude(context)
        if runtime == "codex":
            return _execute_codex(context)
        if runtime == "opencode":
            return _execute_opencode(context)
        if runtime == "pi-mono":
            return _execute_pi_mono(context)
    except Exception as exc:
        return _adapter_failure_result(
            request=context.request,
            runtime_id=context.runtime_id,
            exc=exc,
        )
    raise ValueError(
        f"Unsupported runtime '{context.runtime_id}'. Expected one of: "
        f"{', '.join(SUPPORTED_RUNTIMES)}"
    )


def is_runtime_available(*, runtime_id: str, command: str) -> bool:
    report: CapabilityReport = probe_runtime(runtime_id=runtime_id, command=command)
    return report.available
