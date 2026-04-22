from __future__ import annotations

import os
import shlex
import subprocess
import threading
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import Literal, TextIO

from aidd.core.run_store import RUN_RUNTIME_LOG_FILENAME


@dataclass(frozen=True, slots=True)
class OpenCodeCommandContext:
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
class OpenCodeSubprocessSpec:
    command: tuple[str, ...]
    cwd: Path
    env: dict[str, str]


@dataclass(frozen=True, slots=True)
class OpenCodeRunResult:
    exit_code: int
    stdout_text: str
    stderr_text: str
    runtime_log_text: str


StreamTarget = Literal["stdout", "stderr"]


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


def assemble_command(
    *,
    configured_command: str,
    context: OpenCodeCommandContext,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    stripped = configured_command.strip()
    if not stripped:
        raise ValueError("Configured opencode command must not be empty.")

    try:
        base_tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(
            f"Configured opencode command is not valid shell syntax: {configured_command!r}"
        ) from exc
    if not base_tokens:
        raise ValueError("Configured opencode command must produce at least one token.")

    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    resolved_stage_brief_path = _resolve_stage_brief_path_for_execution(
        stage_brief_path=context.stage_brief_path,
        workspace_root=resolved_workspace_root,
    )
    resolved_prompt_pack_paths = _resolve_prompt_pack_paths_for_execution(
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


def command_preview(
    *,
    configured_command: str,
    context: OpenCodeCommandContext,
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


def build_execution_environment(
    *,
    context: OpenCodeCommandContext,
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
            "AIDD_RUNTIME_ID": "opencode",
        }
    )
    return env


def build_subprocess_spec(
    *,
    configured_command: str,
    context: OpenCodeCommandContext,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> OpenCodeSubprocessSpec:
    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    return OpenCodeSubprocessSpec(
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
    spec: OpenCodeSubprocessSpec,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
) -> OpenCodeRunResult:
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
    completed_readers = 0
    while completed_readers < 2:
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
    return OpenCodeRunResult(
        exit_code=exit_code,
        stdout_text="".join(stdout_chunks),
        stderr_text="".join(stderr_chunks),
        runtime_log_text="".join(runtime_log_chunks),
    )


def persist_attempt_runtime_log(
    *,
    attempt_path: Path,
    run_result: OpenCodeRunResult,
) -> Path:
    attempt_path.mkdir(parents=True, exist_ok=True)
    runtime_log_path = attempt_path / RUN_RUNTIME_LOG_FILENAME
    runtime_log_path.write_text(run_result.runtime_log_text, encoding="utf-8")
    return runtime_log_path
