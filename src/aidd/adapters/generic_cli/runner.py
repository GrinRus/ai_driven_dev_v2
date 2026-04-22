from __future__ import annotations

import json
import shlex
import subprocess
import threading
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from queue import Empty, Queue
from typing import Literal, TextIO

from aidd.core.run_store import RUN_RUNTIME_LOG_FILENAME


@dataclass(frozen=True, slots=True)
class GenericCliStageContext:
    stage: str
    work_item: str
    run_id: str
    prompt_pack_path: Path

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("Stage context requires a non-empty stage id.")
        if not self.work_item.strip():
            raise ValueError("Stage context requires a non-empty work item id.")
        if not self.run_id.strip():
            raise ValueError("Stage context requires a non-empty run id.")
        if str(self.prompt_pack_path).strip() == "":
            raise ValueError("Stage context requires a prompt-pack path.")


@dataclass(frozen=True, slots=True)
class GenericCliSubprocessSpec:
    command: tuple[str, ...]
    cwd: Path
    env: dict[str, str]


@dataclass(frozen=True, slots=True)
class GenericCliRunResult:
    exit_code: int
    stdout_text: str
    stderr_text: str
    runtime_log_text: str
    exit_classification: GenericCliExitClassification


@dataclass(frozen=True, slots=True)
class GenericCliRuntimeArtifacts:
    runtime_log_path: Path
    runtime_exit_metadata_path: Path


class GenericCliExitClassification(StrEnum):
    SUCCESS = "success"
    NON_ZERO_EXIT = "non_zero_exit"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


StreamTarget = Literal["stdout", "stderr"]
RUNTIME_EXIT_METADATA_FILENAME = "runtime-exit.json"


def _resolve_exit_classification(
    *,
    exit_code: int,
    stop_reason: GenericCliExitClassification | None,
) -> GenericCliExitClassification:
    if stop_reason is not None:
        return stop_reason
    if exit_code == 0:
        return GenericCliExitClassification.SUCCESS
    return GenericCliExitClassification.NON_ZERO_EXIT


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


def assemble_command(
    *,
    configured_command: str,
    context: GenericCliStageContext,
) -> tuple[str, ...]:
    stripped = configured_command.strip()
    if not stripped:
        raise ValueError("Configured generic-cli command must not be empty.")

    try:
        base_tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(
            f"Configured generic-cli command is not valid shell syntax: {configured_command!r}"
        ) from exc

    if not base_tokens:
        raise ValueError("Configured generic-cli command must produce at least one token.")

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
    env = dict(base_env or {})
    env.update(
        {
            "AIDD_WORKSPACE_ROOT": workspace_root.as_posix(),
            "AIDD_STAGE": context.stage,
            "AIDD_WORK_ITEM": context.work_item,
            "AIDD_RUN_ID": context.run_id,
            "AIDD_PROMPT_PACK_PATH": context.prompt_pack_path.as_posix(),
            "AIDD_RUNTIME_ID": "generic-cli",
        }
    )
    return env


def _resolve_prompt_pack_path_for_execution(
    *,
    prompt_pack_path: Path,
    repository_root: Path | None,
) -> Path:
    if prompt_pack_path.is_absolute():
        return prompt_pack_path.resolve(strict=False)

    base_dir = (repository_root or Path.cwd()).resolve(strict=False)
    return (base_dir / prompt_pack_path).resolve(strict=False)


def build_subprocess_spec(
    *,
    configured_command: str,
    workspace_root: Path,
    context: GenericCliStageContext,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> GenericCliSubprocessSpec:
    resolved_workspace_root = workspace_root.resolve(strict=False)
    resolved_prompt_pack_path = _resolve_prompt_pack_path_for_execution(
        prompt_pack_path=context.prompt_pack_path,
        repository_root=repository_root,
    )
    resolved_context = GenericCliStageContext(
        stage=context.stage,
        work_item=context.work_item,
        run_id=context.run_id,
        prompt_pack_path=resolved_prompt_pack_path,
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
    spec: GenericCliSubprocessSpec,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    timeout_seconds: float | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> GenericCliRunResult:
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero when provided.")

    process = subprocess.Popen(
        spec.command,
        cwd=spec.cwd,
        env=spec.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
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
    deadline = (
        time.monotonic() + timeout_seconds
        if timeout_seconds is not None
        else None
    )
    stop_reason: GenericCliExitClassification | None = None
    completed_readers = 0
    while completed_readers < 2:
        if stop_reason is None:
            if cancel_requested is not None and cancel_requested():
                stop_reason = GenericCliExitClassification.CANCELLED
                _request_subprocess_stop(process)
            elif deadline is not None and time.monotonic() >= deadline:
                stop_reason = GenericCliExitClassification.TIMEOUT
                _request_subprocess_stop(process)

        try:
            target, chunk = queue.get(timeout=0.1)
        except Empty:
            continue

        if chunk is None:
            completed_readers += 1
            continue

        runtime_log_chunks.append(chunk)
        if target == "stdout":
            stdout_chunks.append(chunk)
            if on_stdout is not None:
                on_stdout(chunk)
            continue

        stderr_chunks.append(chunk)
        if on_stderr is not None:
            on_stderr(chunk)

    for thread in reader_threads:
        thread.join(timeout=0.5)
    exit_code = process.wait()
    exit_classification = _resolve_exit_classification(
        exit_code=exit_code,
        stop_reason=stop_reason,
    )
    return GenericCliRunResult(
        exit_code=exit_code,
        stdout_text="".join(stdout_chunks),
        stderr_text="".join(stderr_chunks),
        runtime_log_text="".join(runtime_log_chunks),
        exit_classification=exit_classification,
    )


def persist_attempt_runtime_artifacts(
    *,
    attempt_path: Path,
    run_result: GenericCliRunResult,
) -> GenericCliRuntimeArtifacts:
    attempt_path.mkdir(parents=True, exist_ok=True)

    runtime_log_path = attempt_path / RUN_RUNTIME_LOG_FILENAME
    runtime_log_path.write_text(run_result.runtime_log_text, encoding="utf-8")

    runtime_exit_metadata_path = attempt_path / RUNTIME_EXIT_METADATA_FILENAME
    runtime_exit_metadata = {
        "schema_version": 1,
        "exit_code": run_result.exit_code,
        "exit_classification": run_result.exit_classification.value,
        "stdout_char_count": len(run_result.stdout_text),
        "stderr_char_count": len(run_result.stderr_text),
        "runtime_log_char_count": len(run_result.runtime_log_text),
    }
    runtime_exit_metadata_path.write_text(
        json.dumps(runtime_exit_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return GenericCliRuntimeArtifacts(
        runtime_log_path=runtime_log_path,
        runtime_exit_metadata_path=runtime_exit_metadata_path,
    )
