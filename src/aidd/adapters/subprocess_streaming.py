from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from queue import Empty, Queue
from typing import Literal, TextIO

from aidd.adapters.runtime_execution import RuntimeSubprocessSpec
from aidd.runtime_budget import validate_runtime_budget

StreamTarget = Literal["stdout", "stderr"]


@dataclass(frozen=True, slots=True)
class StreamedSubprocessResult[ExitClassificationT: StrEnum]:
    exit_code: int
    stdout_text: str
    stderr_text: str
    runtime_log_text: str
    stop_reason: ExitClassificationT | None


def request_subprocess_stop(process: subprocess.Popen[str]) -> None:
    process_group_terminated = _request_process_group_stop(process, signal.SIGTERM)
    if process_group_terminated:
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            if not _process_group_exists(process.pid):
                return
            time.sleep(0.05)
        _request_process_group_stop(process, signal.SIGKILL)
        if process.poll() is None:
            try:
                process.kill()
            except (OSError, ProcessLookupError):
                pass
        return

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


def _request_process_group_stop(process: subprocess.Popen[str], sig: signal.Signals) -> bool:
    if os.name == "nt":
        return False
    try:
        os.killpg(process.pid, sig)
    except (OSError, ProcessLookupError):
        return False
    return True


def _process_group_exists(pid: int) -> bool:
    if os.name == "nt":
        return False
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def stream_reader(
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
            if chunk == "":
                break
            queue.put((target, chunk))
    finally:
        pipe.close()
        queue.put((target, None))


def run_streamed_subprocess[ExitClassificationT: StrEnum](
    *,
    spec: RuntimeSubprocessSpec,
    timeout_seconds: float | None,
    timeout_stop_reason: ExitClassificationT,
    cancel_stop_reason: ExitClassificationT,
    cancel_requested: Callable[[], bool] | None = None,
    completion_requested: Callable[[], bool] | None = None,
    completion_stop_reason: ExitClassificationT | None = None,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    queue_timeout_seconds: float = 0.1,
    launch_failure_stop_reason: ExitClassificationT | None = None,
) -> StreamedSubprocessResult[ExitClassificationT]:
    timeout_seconds = validate_runtime_budget(timeout_seconds)
    if completion_requested is not None and completion_stop_reason is None:
        raise ValueError("completion_stop_reason is required when completion_requested is set.")

    try:
        process = subprocess.Popen(
            spec.command,
            cwd=spec.cwd,
            env=spec.env,
            stdin=subprocess.PIPE if spec.stdin_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=os.name != "nt",
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        if launch_failure_stop_reason is None:
            raise
        message = f"[adapter-failure] {exc}\n"
        return StreamedSubprocessResult(
            exit_code=-1,
            stdout_text="",
            stderr_text=message,
            runtime_log_text=message,
            stop_reason=launch_failure_stop_reason,
        )

    if spec.stdin_text is not None and process.stdin is not None:
        try:
            process.stdin.write(spec.stdin_text)
            process.stdin.close()
        except BrokenPipeError:
            pass

    queue: Queue[tuple[StreamTarget, str | None]] = Queue()
    reader_threads = (
        threading.Thread(
            target=stream_reader,
            kwargs={
                "target": "stdout",
                "pipe": process.stdout,
                "queue": queue,
            },
            daemon=True,
        ),
        threading.Thread(
            target=stream_reader,
            kwargs={
                "target": "stderr",
                "pipe": process.stderr,
                "queue": queue,
            },
            daemon=True,
        ),
    )
    for thread in reader_threads:
        thread.start()

    stdout_chunks: deque[str] = deque()
    stderr_chunks: deque[str] = deque()
    runtime_log_chunks: deque[str] = deque()
    stream_done: dict[StreamTarget, bool] = {"stdout": False, "stderr": False}
    deadline = time.monotonic() + timeout_seconds if timeout_seconds is not None else None
    stop_reason: ExitClassificationT | None = None

    def _maybe_request_stop() -> None:
        nonlocal stop_reason
        if stop_reason is not None:
            return
        if cancel_requested is not None and cancel_requested():
            stop_reason = cancel_stop_reason
            request_subprocess_stop(process)
            return
        if completion_requested is not None and completion_requested():
            stop_reason = completion_stop_reason
            request_subprocess_stop(process)
            return
        if deadline is not None and time.monotonic() >= deadline:
            stop_reason = timeout_stop_reason
            request_subprocess_stop(process)

    def _invoke_stream_callback(callback: Callable[[str], None] | None, chunk: str) -> None:
        if callback is None:
            return
        try:
            callback(chunk)
        except BaseException:
            request_subprocess_stop(process)
            for thread in reader_threads:
                thread.join(timeout=0.5)
            raise

    while True:
        _maybe_request_stop()
        try:
            target, chunk = queue.get(timeout=queue_timeout_seconds)
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
            _invoke_stream_callback(on_stdout, chunk)
            continue

        stderr_chunks.append(chunk)
        _invoke_stream_callback(on_stderr, chunk)

    for thread in reader_threads:
        thread.join(timeout=0.5)

    return StreamedSubprocessResult(
        exit_code=process.wait(),
        stdout_text="".join(stdout_chunks),
        stderr_text="".join(stderr_chunks),
        runtime_log_text="".join(runtime_log_chunks),
        stop_reason=stop_reason,
    )
