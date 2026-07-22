from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from queue import Empty, Queue
from typing import Literal, TextIO

from aidd.adapters.process_io import ManagedStdinWriter
from aidd.adapters.process_supervisor import OwnedProcessSupervisor
from aidd.adapters.runtime_execution import RuntimeSubprocessSpec
from aidd.adapters.runtime_log_capture import DiskBackedRuntimeLogSink
from aidd.runtime_budget import validate_runtime_budget

StreamTarget = Literal["stdout", "stderr"]


@dataclass(frozen=True, slots=True)
class StreamedSubprocessResult[ExitClassificationT: StrEnum]:
    exit_code: int | None
    stdout_text: str
    stderr_text: str
    runtime_log_text: str
    stop_reason: ExitClassificationT | None
    runtime_log_source_path: Path | None = None
    structured_events_source_path: Path | None = None
    stdout_byte_count: int | None = None
    stderr_byte_count: int | None = None
    runtime_log_byte_count: int | None = None
    stdout_char_count: int | None = None
    stderr_char_count: int | None = None
    runtime_log_char_count: int | None = None
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    runtime_log_truncated: bool = False


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


def safe_launch_failure_message(exc: OSError) -> str:
    message = str(exc).replace("\r", " ").replace("\n", " ").strip()
    return f"[launch-failure] {type(exc).__name__}: {message}\n"


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
    capture_directory: Path | None = None,
) -> StreamedSubprocessResult[ExitClassificationT]:
    timeout_seconds = validate_runtime_budget(timeout_seconds)
    if completion_requested is not None and completion_stop_reason is None:
        raise ValueError("completion_stop_reason is required when completion_requested is set.")

    try:
        supervisor = OwnedProcessSupervisor.launch(spec)
    except (FileNotFoundError, PermissionError, OSError) as exc:
        if launch_failure_stop_reason is None:
            raise
        message = safe_launch_failure_message(exc)
        return StreamedSubprocessResult(
            exit_code=None,
            stdout_text="",
            stderr_text=message,
            runtime_log_text=message,
            stop_reason=launch_failure_stop_reason,
        )
    process = supervisor.process
    sink = DiskBackedRuntimeLogSink(directory=capture_directory or spec.cwd)

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
            sink.abort()
            raise

    while True:
        parent_exited = process.poll() is not None
        if not parent_exited and parent_exit_drain_deadline is None:
            _maybe_request_stop()
            parent_exited = process.poll() is not None
        if parent_exited and parent_exit_drain_deadline is None:
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
            sink.abort()
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

        try:
            sink.write(target, chunk)
        except BaseException:
            supervisor.request_stop()
            supervisor.drain_streams(reader_threads)
            if stdin_writer is not None:
                stdin_writer.join()
            sink.abort()
            raise
        if target == "stdout":
            _invoke_stream_callback(on_stdout, chunk)
            continue

        _invoke_stream_callback(on_stderr, chunk)

    supervisor.drain_streams(reader_threads)
    if stdin_writer is not None:
        stdin_writer.join()
        if stdin_writer.error is not None and stop_reason is None:
            sink.abort()
            raise stdin_writer.error

    snapshot = sink.finish()
    return StreamedSubprocessResult(
        exit_code=process.wait(),
        stdout_text=snapshot.stdout_text,
        stderr_text=snapshot.stderr_text,
        runtime_log_text=snapshot.runtime_log_text,
        stop_reason=stop_reason,
        runtime_log_source_path=snapshot.runtime_log_source_path,
        structured_events_source_path=snapshot.structured_events_source_path,
        stdout_byte_count=snapshot.stdout_byte_count,
        stderr_byte_count=snapshot.stderr_byte_count,
        runtime_log_byte_count=snapshot.runtime_log_byte_count,
        stdout_char_count=snapshot.stdout_char_count,
        stderr_char_count=snapshot.stderr_char_count,
        runtime_log_char_count=snapshot.runtime_log_char_count,
        stdout_truncated=snapshot.stdout_truncated,
        stderr_truncated=snapshot.stderr_truncated,
        runtime_log_truncated=snapshot.runtime_log_truncated,
    )
