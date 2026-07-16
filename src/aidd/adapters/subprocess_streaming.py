from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from queue import Empty, Queue
from typing import Literal, TextIO

from aidd.adapters.process_io import ManagedStdinWriter
from aidd.adapters.process_supervisor import OwnedProcessSupervisor
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
        supervisor = OwnedProcessSupervisor.launch(spec)
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
    process = supervisor.process

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
    parent_exit_drain_deadline: float | None = None
    stop_reason: ExitClassificationT | None = None
    stdin_writer = ManagedStdinWriter.start(process.stdin, spec.stdin_text)

    def _maybe_request_stop() -> None:
        nonlocal stop_reason
        if stop_reason is not None:
            return
        if cancel_requested is not None and cancel_requested():
            stop_reason = cancel_stop_reason
            supervisor.request_stop()
            return
        if completion_requested is not None and completion_requested():
            stop_reason = completion_stop_reason
            supervisor.request_stop()
            return
        if deadline is not None and time.monotonic() >= deadline:
            stop_reason = timeout_stop_reason
            supervisor.request_stop()

    def _invoke_stream_callback(callback: Callable[[str], None] | None, chunk: str) -> None:
        if callback is None:
            return
        try:
            callback(chunk)
        except BaseException:
            supervisor.request_stop()
            supervisor.drain_streams(reader_threads)
            if stdin_writer is not None:
                stdin_writer.join()
            raise

    while True:
        _maybe_request_stop()
        if process.poll() is not None and parent_exit_drain_deadline is None:
            parent_exit_drain_deadline = time.monotonic() + 0.2
        if (
            parent_exit_drain_deadline is not None
            and time.monotonic() >= parent_exit_drain_deadline
            and not all(stream_done.values())
        ):
            supervisor.request_stop()
            parent_exit_drain_deadline = None
        if (
            stdin_writer is not None
            and stdin_writer.error is not None
            and stop_reason is None
        ):
            writer_error = stdin_writer.error
            supervisor.request_stop()
            supervisor.drain_streams(reader_threads)
            stdin_writer.join()
            assert writer_error is not None
            raise writer_error
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

    supervisor.drain_streams(reader_threads)
    if stdin_writer is not None:
        stdin_writer.join()
        if stdin_writer.error is not None and stop_reason is None:
            raise stdin_writer.error

    return StreamedSubprocessResult(
        exit_code=process.wait(),
        stdout_text="".join(stdout_chunks),
        stderr_text="".join(stderr_chunks),
        runtime_log_text="".join(runtime_log_chunks),
        stop_reason=stop_reason,
    )
