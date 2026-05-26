from __future__ import annotations

import json
import re
import shlex
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
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
from aidd.core.adapter_interview import (
    AdapterQuestionEvent,
    QuestionPolicy,
    load_answers_document,
    load_questions_document,
    persist_answers_document,
    persist_questions_document,
    resolved_question_ids,
    unresolved_blocking_questions,
)
from aidd.core.run_store import run_stage_metadata_path
from aidd.runtime_catalog import RuntimeExecutionMode, normalize_execution_mode
from aidd.runtime_logs.events import normalize_structured_events as normalize_runtime_log_events


@dataclass(frozen=True, slots=True)
class ClaudeCodeCommandContext:
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
class ClaudeCodeConfigFlag:
    flag: str
    value: str | None = None

    def __post_init__(self) -> None:
        if not self.flag.strip():
            raise ValueError("Config flag name must not be empty.")

    @property
    def normalized_flag(self) -> str:
        stripped = self.flag.strip()
        if stripped.startswith("--"):
            return stripped
        return f"--{stripped}"


@dataclass(frozen=True, slots=True)
class ClaudeCodeLaunchOptions:
    sandbox_mode: str | None = None
    permission_mode: str | None = None
    config_flags: tuple[ClaudeCodeConfigFlag, ...] = ()

    def __post_init__(self) -> None:
        if self.sandbox_mode is not None and not self.sandbox_mode.strip():
            raise ValueError("Sandbox mode must not be blank when provided.")
        if self.permission_mode is not None and not self.permission_mode.strip():
            raise ValueError("Permission mode must not be blank when provided.")


@dataclass(frozen=True, slots=True)
class ClaudeCodeSubprocessSpec(RuntimeSubprocessSpec):
    pass


@dataclass(frozen=True, slots=True)
class ClaudeCodeRuntimeArtifacts:
    runtime_log_path: Path
    runtime_exit_metadata_path: Path


class ClaudeCodeExitClassification(StrEnum):
    SUCCESS = "success"
    RUNTIME_NON_ZERO_EXIT = "runtime_non_zero_exit"
    TIMEOUT = "timeout"
    USER_CANCELLED = "user_cancelled"
    ADAPTER_FAILURE = "adapter_failure"


@dataclass(frozen=True, slots=True)
class ClaudeCodeRunResult(RuntimeRunResult[ClaudeCodeExitClassification]):
    pass


EVENTS_JSONL_FILENAME = "events.jsonl"
QUESTION_ID_PATTERN = re.compile(r"^Q[\w-]*$")


def _assemble_launch_flags(options: ClaudeCodeLaunchOptions | None) -> tuple[str, ...]:
    if options is None:
        return ()

    launch_flags: list[str] = []
    if options.sandbox_mode is not None:
        launch_flags.extend(("--sandbox", options.sandbox_mode.strip()))

    if options.permission_mode is not None:
        normalized_permission_mode = options.permission_mode.strip()
        if normalized_permission_mode == "bypass":
            launch_flags.append("--dangerously-skip-permissions")
        else:
            launch_flags.extend(("--permission-mode", normalized_permission_mode))

    for config_flag in options.config_flags:
        launch_flags.append(config_flag.normalized_flag)
        if config_flag.value is not None:
            launch_flags.append(config_flag.value)
    return tuple(launch_flags)


def assemble_command(
    *,
    configured_command: str,
    context: ClaudeCodeCommandContext,
    launch_options: ClaudeCodeLaunchOptions | None = None,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    base_tokens = split_configured_command(
        configured_command=configured_command,
        runtime_label="claude-code",
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
    launch_flags = _assemble_launch_flags(launch_options)

    command: list[str] = [
        *base_tokens,
        *launch_flags,
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
    context: ClaudeCodeCommandContext,
    repository_root: Path | None,
) -> str:
    return compile_native_prompt_text(
        runtime_id="claude-code",
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
    context: ClaudeCodeCommandContext,
    launch_options: ClaudeCodeLaunchOptions | None = None,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    _ = context, launch_options, repository_root
    return _split_configured_command(
        configured_command=configured_command,
        runtime_label="claude-code",
    )


def build_execution_environment(
    *,
    context: ClaudeCodeCommandContext,
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
        runtime_id="claude-code",
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
    context: ClaudeCodeCommandContext,
    launch_options: ClaudeCodeLaunchOptions | None = None,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
    execution_mode: str | RuntimeExecutionMode = RuntimeExecutionMode.ADAPTER_FLAGS,
) -> ClaudeCodeSubprocessSpec:
    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    mode = normalize_execution_mode(runtime_id="claude-code", value=execution_mode)
    if mode is RuntimeExecutionMode.NATIVE:
        resolved_repository_root = (repository_root or Path.cwd()).resolve(strict=False)
        return ClaudeCodeSubprocessSpec(
            command=assemble_native_command(
                configured_command=configured_command,
                context=context,
                launch_options=launch_options,
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
    return ClaudeCodeSubprocessSpec(
        command=assemble_command(
            configured_command=configured_command,
            context=context,
            launch_options=launch_options,
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
    stop_reason: ClaudeCodeExitClassification | None,
) -> ClaudeCodeExitClassification:
    return resolve_exit_classification(
        exit_code=exit_code,
        stop_reason=stop_reason,
        success_value=ClaudeCodeExitClassification.SUCCESS,
        non_zero_value=ClaudeCodeExitClassification.RUNTIME_NON_ZERO_EXIT,
    )


def run_subprocess_with_streaming(
    *,
    spec: ClaudeCodeSubprocessSpec,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    timeout_seconds: float | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> ClaudeCodeRunResult:
    streamed_result = run_streamed_subprocess(
        spec=spec,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
        timeout_seconds=timeout_seconds,
        cancel_requested=cancel_requested,
        timeout_stop_reason=ClaudeCodeExitClassification.TIMEOUT,
        cancel_stop_reason=ClaudeCodeExitClassification.USER_CANCELLED,
        launch_failure_stop_reason=ClaudeCodeExitClassification.ADAPTER_FAILURE,
        queue_timeout_seconds=0.05,
    )
    exit_classification = _resolve_exit_classification(
        exit_code=streamed_result.exit_code,
        stop_reason=streamed_result.stop_reason,
    )
    return ClaudeCodeRunResult(
        exit_code=streamed_result.exit_code,
        stdout_text=streamed_result.stdout_text,
        stderr_text=streamed_result.stderr_text,
        runtime_log_text=streamed_result.runtime_log_text,
        exit_classification=exit_classification,
    )


def persist_attempt_runtime_log(
    *,
    attempt_path: Path,
    run_result: ClaudeCodeRunResult,
) -> ClaudeCodeRuntimeArtifacts:
    paths = persist_runtime_log_artifacts(
        attempt_path=attempt_path,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
        runtime_log_text=run_result.runtime_log_text,
    )
    return ClaudeCodeRuntimeArtifacts(
        runtime_log_path=paths.runtime_log_path,
        runtime_exit_metadata_path=paths.runtime_exit_metadata_path,
    )


def normalize_structured_events(
    *,
    run_result: ClaudeCodeRunResult,
) -> tuple[dict[str, object], ...]:
    return normalize_runtime_log_events(run_result=run_result)


@dataclass(frozen=True, slots=True)
class ClaudeCodeQuestionDetection:
    question_events: tuple[AdapterQuestionEvent, ...]
    pause_detected: bool


@dataclass(frozen=True, slots=True)
class ClaudeCodeQuestionRouting:
    question_events: tuple[AdapterQuestionEvent, ...]
    pause_detected: bool
    used_file_fallback: bool


@dataclass(frozen=True, slots=True)
class ClaudeCodeQuestionPersistence:
    questions_path: Path
    stage_metadata_path: Path
    unresolved_blocking_question_ids: tuple[str, ...]
    metadata_updated: bool


@dataclass(frozen=True, slots=True)
class ClaudeCodeResumeDecision:
    can_resume: bool
    resume_command: tuple[str, ...] | None
    unresolved_blocking_question_ids: tuple[str, ...]


def _question_policy_from_runtime_event(event: Mapping[str, object]) -> QuestionPolicy:
    policy_value = event.get("policy")
    if isinstance(policy_value, str):
        normalized = policy_value.strip().lower()
        if normalized in {"non-blocking", "non_blocking", "nonblocking"}:
            return QuestionPolicy.NON_BLOCKING
        if normalized == "blocking":
            return QuestionPolicy.BLOCKING

    blocking_value = event.get("blocking")
    if isinstance(blocking_value, bool):
        return QuestionPolicy.BLOCKING if blocking_value else QuestionPolicy.NON_BLOCKING

    return QuestionPolicy.BLOCKING


def _question_id_from_runtime_event(event: Mapping[str, object]) -> str | None:
    for field_name in ("question_id", "questionId", "id"):
        raw_value = event.get(field_name)
        if not isinstance(raw_value, str):
            continue
        candidate = raw_value.strip()
        if QUESTION_ID_PATTERN.match(candidate):
            return candidate
    return None


def _question_text_from_runtime_event(event: Mapping[str, object]) -> str | None:
    for field_name in ("question", "text", "prompt", "message"):
        raw_value = event.get(field_name)
        if isinstance(raw_value, str) and raw_value.strip():
            return raw_value.strip()
    return None


def detect_question_or_pause_events(
    *,
    normalized_events: tuple[dict[str, object], ...],
) -> ClaudeCodeQuestionDetection:
    question_events: list[AdapterQuestionEvent] = []
    pause_detected = False

    for event in normalized_events:
        event_kind = str(event.get("event") or event.get("type") or "").strip().lower()
        pause_flag = bool(event.get("paused", False))
        is_question_kind = event_kind in {
            "question",
            "question_raised",
            "question-raised",
            "ask_user",
            "ask-user",
        }
        is_pause_kind = event_kind in {
            "pause",
            "paused",
            "awaiting_input",
            "awaiting-input",
            "input_required",
            "input-required",
        }
        if not (is_question_kind or is_pause_kind or pause_flag):
            continue

        pause_detected = pause_detected or is_pause_kind or pause_flag
        question_text = _question_text_from_runtime_event(event)
        if question_text is None and pause_detected:
            question_text = "Runtime paused and requires operator input."
        if question_text is None:
            continue

        question_events.append(
            AdapterQuestionEvent(
                text=question_text,
                policy=_question_policy_from_runtime_event(event),
                question_id=_question_id_from_runtime_event(event),
            )
        )

    return ClaudeCodeQuestionDetection(
        question_events=tuple(question_events),
        pause_detected=pause_detected,
    )


def route_questions_with_file_fallback(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    runtime_detection: ClaudeCodeQuestionDetection,
) -> ClaudeCodeQuestionRouting:
    if runtime_detection.question_events or runtime_detection.pause_detected:
        return ClaudeCodeQuestionRouting(
            question_events=runtime_detection.question_events,
            pause_detected=runtime_detection.pause_detected,
            used_file_fallback=False,
        )

    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    answers = load_answers_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    unresolved = unresolved_blocking_questions(
        questions=questions,
        resolved_question_ids=resolved_question_ids(answers=answers),
    )
    fallback_events = tuple(
        AdapterQuestionEvent(
            question_id=question.question_id,
            text=question.text,
            policy=question.policy,
        )
        for question in unresolved
    )
    return ClaudeCodeQuestionRouting(
        question_events=fallback_events,
        pause_detected=bool(fallback_events),
        used_file_fallback=bool(fallback_events),
    )


def _workspace_relative_path(workspace_root: Path, path: Path) -> str:
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    return resolved_path.relative_to(resolved_workspace).as_posix()


def persist_surfaced_questions(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    adapter_question_events: tuple[AdapterQuestionEvent, ...],
    stage_output_questions_markdown: str | None = None,
) -> ClaudeCodeQuestionPersistence:
    questions_path = persist_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        stage_output_questions_markdown=stage_output_questions_markdown,
        adapter_question_events=adapter_question_events,
    )
    stage_root = workspace_root / "workitems" / work_item / "stages" / stage
    answers_path = stage_root / "answers.md"
    misplaced_answers_path = stage_root / "output" / "answers.md"
    if not answers_path.exists() and not misplaced_answers_path.exists():
        persist_answers_document(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    answers = load_answers_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    unresolved_ids = tuple(
        question.question_id
        for question in unresolved_blocking_questions(
            questions=questions,
            resolved_question_ids=resolved_question_ids(answers=answers),
        )
    )

    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    metadata_updated = False
    if metadata_path.exists():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        payload["claude_question_artifact"] = {
            "questions_path": _workspace_relative_path(workspace_root, questions_path),
            "unresolved_blocking_question_ids": list(unresolved_ids),
        }
        payload["updated_at_utc"] = (
            datetime.now(UTC).astimezone(UTC).replace(microsecond=0).isoformat().replace(
                "+00:00",
                "Z",
            )
        )
        metadata_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        metadata_updated = True

    return ClaudeCodeQuestionPersistence(
        questions_path=questions_path,
        stage_metadata_path=metadata_path,
        unresolved_blocking_question_ids=unresolved_ids,
        metadata_updated=metadata_updated,
    )


def prepare_resume_after_answers(
    *,
    configured_command: str,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
) -> ClaudeCodeResumeDecision:
    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    answers = load_answers_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    unresolved = unresolved_blocking_questions(
        questions=questions,
        resolved_question_ids=resolved_question_ids(answers=answers),
    )
    unresolved_ids = tuple(question.question_id for question in unresolved)
    if unresolved_ids:
        return ClaudeCodeResumeDecision(
            can_resume=False,
            resume_command=None,
            unresolved_blocking_question_ids=unresolved_ids,
        )

    base_tokens = split_configured_command(
        configured_command=configured_command,
        runtime_label="claude-code",
    )

    resume_command = (
        *base_tokens,
        "resume",
        "--run-id",
        run_id,
        "--stage",
        stage,
        "--work-item",
        work_item,
    )
    return ClaudeCodeResumeDecision(
        can_resume=True,
        resume_command=resume_command,
        unresolved_blocking_question_ids=(),
    )


def persist_normalized_events_jsonl(
    *,
    attempt_path: Path,
    run_result: ClaudeCodeRunResult,
) -> Path | None:
    normalized_events = normalize_structured_events(run_result=run_result)
    if not normalized_events:
        return None

    attempt_path.mkdir(parents=True, exist_ok=True)
    events_path = attempt_path / EVENTS_JSONL_FILENAME
    lines = [json.dumps(event, sort_keys=True) for event in normalized_events]
    events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return events_path


def command_preview(
    *,
    configured_command: str,
    context: ClaudeCodeCommandContext,
    launch_options: ClaudeCodeLaunchOptions | None = None,
    repository_root: Path | None = None,
) -> str:
    return " ".join(
        shlex.quote(token)
        for token in assemble_command(
            configured_command=configured_command,
            context=context,
            launch_options=launch_options,
            repository_root=repository_root,
        )
    )
