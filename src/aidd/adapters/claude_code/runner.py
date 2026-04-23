from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import threading
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from queue import Empty, Queue
from typing import Literal, TextIO

from aidd.adapters.runtime_artifacts import write_runtime_exit_metadata
from aidd.core.interview import (
    AdapterQuestionEvent,
    QuestionPolicy,
    load_answers_document,
    load_questions_document,
    persist_questions_document,
    resolved_question_ids,
    unresolved_blocking_questions,
)
from aidd.core.run_store import RUN_RUNTIME_LOG_FILENAME, run_stage_metadata_path


@dataclass(frozen=True, slots=True)
class ClaudeCodeCommandContext:
    stage: str
    work_item: str
    run_id: str
    workspace_root: Path
    stage_brief_path: Path
    prompt_pack_paths: tuple[Path, ...]

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
class ClaudeCodeSubprocessSpec:
    command: tuple[str, ...]
    cwd: Path
    env: dict[str, str]


@dataclass(frozen=True, slots=True)
class ClaudeCodeRunResult:
    exit_code: int
    stdout_text: str
    stderr_text: str
    runtime_log_text: str
    exit_classification: ClaudeCodeExitClassification


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


StreamTarget = Literal["stdout", "stderr"]
EVENTS_JSONL_FILENAME = "events.jsonl"
QUESTION_ID_PATTERN = re.compile(r"^Q[\w-]*$")


def _resolve_stage_brief_path_for_execution(
    *,
    stage_brief_path: Path,
    workspace_root: Path,
) -> Path:
    if stage_brief_path.is_absolute():
        return stage_brief_path.resolve(strict=False)

    return (workspace_root / stage_brief_path).resolve(strict=False)


def _resolve_prompt_pack_paths_for_execution(
    *,
    prompt_pack_paths: tuple[Path, ...],
    repository_root: Path | None,
) -> tuple[Path, ...]:
    base_dir = (repository_root or Path.cwd()).resolve(strict=False)
    resolved: list[Path] = []
    for prompt_path in prompt_pack_paths:
        if prompt_path.is_absolute():
            resolved.append(prompt_path.resolve(strict=False))
            continue
        resolved.append((base_dir / prompt_path).resolve(strict=False))
    return tuple(resolved)


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
    stripped = configured_command.strip()
    if not stripped:
        raise ValueError("Configured claude-code command must not be empty.")

    try:
        base_tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(
            "Configured claude-code command is not valid shell syntax: "
            f"{configured_command!r}"
        ) from exc
    if not base_tokens:
        raise ValueError("Configured claude-code command must produce at least one token.")

    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    resolved_stage_brief_path = _resolve_stage_brief_path_for_execution(
        stage_brief_path=context.stage_brief_path,
        workspace_root=resolved_workspace_root,
    )
    resolved_prompt_pack_paths = _resolve_prompt_pack_paths_for_execution(
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


def build_execution_environment(
    *,
    context: ClaudeCodeCommandContext,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> dict[str, str]:
    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    resolved_stage_brief_path = _resolve_stage_brief_path_for_execution(
        stage_brief_path=context.stage_brief_path,
        workspace_root=resolved_workspace_root,
    )
    resolved_prompt_pack_paths = _resolve_prompt_pack_paths_for_execution(
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
            "AIDD_STAGE_BRIEF_PATH": resolved_stage_brief_path.as_posix(),
            "AIDD_PROMPT_PACK_PATHS": os.pathsep.join(
                path.as_posix() for path in resolved_prompt_pack_paths
            ),
            "AIDD_RUNTIME_ID": "claude-code",
        }
    )
    return env


def build_subprocess_spec(
    *,
    configured_command: str,
    context: ClaudeCodeCommandContext,
    launch_options: ClaudeCodeLaunchOptions | None = None,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> ClaudeCodeSubprocessSpec:
    resolved_workspace_root = context.workspace_root.resolve(strict=False)
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
    if stop_reason is not None:
        return stop_reason
    if exit_code == 0:
        return ClaudeCodeExitClassification.SUCCESS
    return ClaudeCodeExitClassification.RUNTIME_NON_ZERO_EXIT


def _request_subprocess_stop(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    try:
        process.terminate()
    except (OSError, ProcessLookupError):
        return

    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except (OSError, ProcessLookupError):
            return


def _stream_reader(
    *,
    target: StreamTarget,
    pipe: TextIO | None,
    queue: Queue[tuple[StreamTarget, str | None]],
) -> None:
    if pipe is None:
        queue.put((target, None))
        return

    try:
        for chunk in iter(pipe.readline, ""):
            queue.put((target, chunk))
    finally:
        pipe.close()
        queue.put((target, None))


def run_subprocess_with_streaming(
    *,
    spec: ClaudeCodeSubprocessSpec,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    timeout_seconds: float | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> ClaudeCodeRunResult:
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero when provided.")

    try:
        process = subprocess.Popen(
            spec.command,
            cwd=spec.cwd,
            env=spec.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        message = f"[adapter-failure] {exc}\n"
        return ClaudeCodeRunResult(
            exit_code=-1,
            stdout_text="",
            stderr_text=message,
            runtime_log_text=message,
            exit_classification=ClaudeCodeExitClassification.ADAPTER_FAILURE,
        )

    queue: Queue[tuple[StreamTarget, str | None]] = Queue()
    reader_threads = (
        threading.Thread(
            target=_stream_reader,
            kwargs={"target": "stdout", "pipe": process.stdout, "queue": queue},
            daemon=True,
        ),
        threading.Thread(
            target=_stream_reader,
            kwargs={"target": "stderr", "pipe": process.stderr, "queue": queue},
            daemon=True,
        ),
    )
    for thread in reader_threads:
        thread.start()

    stdout_chunks: deque[str] = deque()
    stderr_chunks: deque[str] = deque()
    runtime_log_chunks: deque[str] = deque()
    stream_done: dict[StreamTarget, bool] = {"stdout": False, "stderr": False}
    started_at = time.monotonic()
    stop_reason: ClaudeCodeExitClassification | None = None

    while True:
        if cancel_requested is not None and cancel_requested():
            stop_reason = ClaudeCodeExitClassification.USER_CANCELLED
            _request_subprocess_stop(process)

        if (
            timeout_seconds is not None
            and stop_reason is None
            and (time.monotonic() - started_at) >= timeout_seconds
        ):
            stop_reason = ClaudeCodeExitClassification.TIMEOUT
            _request_subprocess_stop(process)

        try:
            target, chunk = queue.get(timeout=0.05)
        except Empty:
            if process.poll() is not None and all(stream_done.values()):
                break
            continue

        if chunk is None:
            stream_done[target] = True
            if process.poll() is not None and all(stream_done.values()):
                break
            continue

        runtime_log_chunks.append(chunk)
        if target == "stdout":
            stdout_chunks.append(chunk)
            if on_stdout is not None:
                on_stdout(chunk)
        else:
            stderr_chunks.append(chunk)
            if on_stderr is not None:
                on_stderr(chunk)

    for thread in reader_threads:
        thread.join(timeout=0.1)

    exit_code = process.wait()
    exit_classification = _resolve_exit_classification(
        exit_code=exit_code,
        stop_reason=stop_reason,
    )
    return ClaudeCodeRunResult(
        exit_code=exit_code,
        stdout_text="".join(stdout_chunks),
        stderr_text="".join(stderr_chunks),
        runtime_log_text="".join(runtime_log_chunks),
        exit_classification=exit_classification,
    )


def persist_attempt_runtime_log(
    *,
    attempt_path: Path,
    run_result: ClaudeCodeRunResult,
) -> ClaudeCodeRuntimeArtifacts:
    attempt_path.mkdir(parents=True, exist_ok=True)
    runtime_log_path = attempt_path / RUN_RUNTIME_LOG_FILENAME
    runtime_log_path.write_text(run_result.runtime_log_text, encoding="utf-8")
    runtime_exit_metadata_path = write_runtime_exit_metadata(
        attempt_path=attempt_path,
        exit_code=run_result.exit_code,
        exit_classification=run_result.exit_classification.value,
        stdout_text=run_result.stdout_text,
        stderr_text=run_result.stderr_text,
        runtime_log_text=run_result.runtime_log_text,
    )
    return ClaudeCodeRuntimeArtifacts(
        runtime_log_path=runtime_log_path,
        runtime_exit_metadata_path=runtime_exit_metadata_path,
    )


def _normalize_stream_events(
    *,
    stream_text: str,
    source: StreamTarget,
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for line in stream_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            normalized.append({**parsed, "source": source})
            continue

        normalized.append({"payload": parsed, "source": source})
    return normalized


def normalize_structured_events(
    *,
    run_result: ClaudeCodeRunResult,
) -> tuple[dict[str, object], ...]:
    stdout_events = _normalize_stream_events(
        stream_text=run_result.stdout_text,
        source="stdout",
    )
    stderr_events = _normalize_stream_events(
        stream_text=run_result.stderr_text,
        source="stderr",
    )
    return tuple((*stdout_events, *stderr_events))


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

    stripped = configured_command.strip()
    if not stripped:
        raise ValueError("Configured claude-code command must not be empty.")
    try:
        base_tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(
            "Configured claude-code command is not valid shell syntax: "
            f"{configured_command!r}"
        ) from exc
    if not base_tokens:
        raise ValueError("Configured claude-code command must produce at least one token.")

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
