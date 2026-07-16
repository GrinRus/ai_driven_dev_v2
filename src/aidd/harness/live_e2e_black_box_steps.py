from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import Literal, TextIO, cast

from aidd.harness.runner import HarnessCommandTranscript

StepClassification = Literal[
    "pass",
    "fail",
    "blocked",
    "infra-fail",
    "skipped",
    "awaiting-quality-review",
    "manual-quality-stop",
]

PROVIDER_NO_PROGRESS_EXIT_CODE = 125


@dataclass(frozen=True, slots=True)
class BlackBoxCommandResult:
    command: tuple[str, ...]
    transcript: HarnessCommandTranscript
    no_progress: bool = False
    no_progress_details: dict[str, object] | None = None

    @property
    def exit_code(self) -> int:
        return self.transcript.exit_code

    @property
    def stdout_text(self) -> str:
        return self.transcript.stdout_text

    @property
    def stderr_text(self) -> str:
        return self.transcript.stderr_text

    @property
    def duration_seconds(self) -> float:
        return self.transcript.duration_seconds


class LiveE2EInterrupted(Exception):
    def __init__(
        self,
        message: str,
        *,
        signum: int | None = None,
        command_result: BlackBoxCommandResult | None = None,
        cleanup: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.signum = signum
        self.command_result = command_result
        self.cleanup = cleanup or {}


def _command_text(command: Sequence[str]) -> str:
    return " ".join(command)


def _run_black_box_command(
    *,
    command: tuple[str, ...],
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: float | None,
    no_progress_timeout_seconds: float | None = None,
    progress_probe: Callable[[], dict[str, object]] | None = None,
    loop_observer: Callable[[], None] | None = None,
    heartbeat_label: str | None = None,
    heartbeat_interval_seconds: float | None = None,
    heartbeat_runtime_log_path: Path | None = None,
    heartbeat_stream: TextIO | None = None,
) -> BlackBoxCommandResult:
    started = time.monotonic()
    timed_out = False
    no_progress = False
    no_progress_details: dict[str, object] | None = None
    process: subprocess.Popen[str] | None = None
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    output_queue: Queue[tuple[str, str | None]] = Queue()
    reader_threads: list[threading.Thread] = []
    stream_done = {"stdout": False, "stderr": False}
    hard_deadline = None if timeout_seconds is None else started + max(timeout_seconds, 0.0)
    last_progress_monotonic = started
    last_progress_utc = _utc_now()
    last_progress_reason = "process-started"
    last_progress_snapshot: dict[str, object] | None = None
    last_progress_signature: str | None = None
    heartbeat_interval = (
        max(heartbeat_interval_seconds, 0.0)
        if heartbeat_label is not None and heartbeat_interval_seconds is not None
        else None
    )
    next_heartbeat = (
        started + heartbeat_interval
        if heartbeat_interval is not None and heartbeat_interval > 0
        else None
    )

    if progress_probe is not None:
        try:
            last_progress_snapshot = progress_probe()
        except OSError as exc:
            last_progress_snapshot = {"probe_error": str(exc)}
        last_progress_signature = _progress_snapshot_signature(last_progress_snapshot)

    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=os.name != "nt",
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
                if os.name == "nt"
                else 0
            ),
        )

        reader_threads = [
            threading.Thread(
                target=_read_command_stream,
                args=("stdout", process.stdout, output_queue),
                daemon=True,
            ),
            threading.Thread(
                target=_read_command_stream,
                args=("stderr", process.stderr, output_queue),
                daemon=True,
            ),
        ]
        for thread in reader_threads:
            thread.start()

        exit_code: int | None = None
        while True:
            try:
                stream_name, chunk = output_queue.get(timeout=0.05)
            except Empty:
                stream_name = ""
                chunk = None
            if stream_name in stream_done and chunk is None:
                stream_done[stream_name] = True
            elif stream_name == "stdout" and chunk is not None:
                stdout_chunks.append(chunk)
                last_progress_monotonic = time.monotonic()
                last_progress_utc = _utc_now()
                last_progress_reason = "stdout"
            elif stream_name == "stderr" and chunk is not None:
                stderr_chunks.append(chunk)
                last_progress_monotonic = time.monotonic()
                last_progress_utc = _utc_now()
                last_progress_reason = "stderr"

            if progress_probe is not None:
                try:
                    snapshot = progress_probe()
                except OSError as exc:
                    snapshot = {"probe_error": str(exc)}
                signature = _progress_snapshot_signature(snapshot)
                if signature != last_progress_signature:
                    last_progress_signature = signature
                    last_progress_snapshot = snapshot
                    last_progress_monotonic = time.monotonic()
                    last_progress_utc = _utc_now()
                    last_progress_reason = "watched-files"

            if loop_observer is not None:
                loop_observer()

            now = time.monotonic()
            if next_heartbeat is not None and now >= next_heartbeat:
                _emit_command_heartbeat(
                    stream=heartbeat_stream or sys.stderr,
                    label=heartbeat_label or "command",
                    elapsed_seconds=max(now - started, 0.0),
                    last_progress_seconds_ago=max(now - last_progress_monotonic, 0.0),
                    last_progress_reason=last_progress_reason,
                    timeout_seconds=timeout_seconds,
                    no_progress_timeout_seconds=no_progress_timeout_seconds,
                    runtime_log_path=heartbeat_runtime_log_path,
                )
                assert heartbeat_interval is not None
                while next_heartbeat <= now:
                    next_heartbeat += heartbeat_interval

            if hard_deadline is not None and now >= hard_deadline:
                timed_out = True
                exit_code = 124
                _stop_process_group_for_streaming(process)
                timeout_label = (
                    f"{timeout_seconds:.3f}s"
                    if timeout_seconds is not None
                    else "configured timeout"
                )
                stderr_chunks.append(f"Command timed out after {timeout_label}.\n")
                break

            if (
                no_progress_timeout_seconds is not None
                and now - last_progress_monotonic >= no_progress_timeout_seconds
            ):
                no_progress = True
                exit_code = PROVIDER_NO_PROGRESS_EXIT_CODE
                cleanup = _stop_process_group_for_streaming(process)
                no_progress_details = {
                    "reason": "provider-no-progress",
                    "message": "provider-no-progress before completed stage artifact",
                    "duration_seconds": max(now - started, 0.0),
                    "no_progress_timeout_seconds": no_progress_timeout_seconds,
                    "hard_timeout_seconds": timeout_seconds,
                    "last_progress_at_utc": last_progress_utc,
                    "last_progress_seconds_ago": max(now - last_progress_monotonic, 0.0),
                    "last_progress_reason": last_progress_reason,
                    "observed_files": last_progress_snapshot or {},
                    "stdout_tail": _text_tail("".join(stdout_chunks)),
                    "stderr_tail": _text_tail("".join(stderr_chunks)),
                    "process_exit_code": cleanup.get("return_code"),
                    "terminated_process_group": cleanup.get("terminated_process_group"),
                }
                stderr_chunks.append(
                    "Command stopped because provider made no progress for "
                    f"{no_progress_timeout_seconds:.3f}s before completed stage artifact.\n"
                )
                break

            if process.poll() is not None and all(stream_done.values()):
                exit_code = process.returncode
                break

        for thread in reader_threads:
            thread.join(timeout=1.0)
        stdout_text = "".join(stdout_chunks)
        stderr_text = "".join(stderr_chunks)
        if exit_code is None:
            exit_code = process.returncode if process.returncode is not None else 1
    except LiveE2EInterrupted as exc:
        cleanup = _stop_process_group_for_streaming(process)
        _join_threads(reader_threads)
        transcript = HarnessCommandTranscript(
            command=_command_text(command),
            exit_code=130,
            stdout_text="".join(stdout_chunks),
            stderr_text="".join(stderr_chunks),
            duration_seconds=time.monotonic() - started,
            timed_out=False,
            timeout_seconds=timeout_seconds,
        )
        exc.command_result = BlackBoxCommandResult(command=command, transcript=transcript)
        exc.cleanup = {
            "command": list(command),
            "process_exit_code": cleanup.get("return_code"),
            "terminated_process_group": cleanup.get("terminated_process_group"),
            "signal": exc.signum,
        }
        raise
    except KeyboardInterrupt as exc:
        cleanup = _stop_process_group_for_streaming(process)
        _join_threads(reader_threads)
        transcript = HarnessCommandTranscript(
            command=_command_text(command),
            exit_code=130,
            stdout_text="".join(stdout_chunks),
            stderr_text="".join(stderr_chunks),
            duration_seconds=time.monotonic() - started,
            timed_out=False,
            timeout_seconds=timeout_seconds,
        )
        raise LiveE2EInterrupted(
            "Black-box live E2E interrupted by operator.",
            command_result=BlackBoxCommandResult(command=command, transcript=transcript),
            cleanup={
                "command": list(command),
                "process_exit_code": cleanup.get("return_code"),
                "terminated_process_group": cleanup.get("terminated_process_group"),
                "signal": None,
            },
        ) from exc
    except OSError as exc:
        exit_code = 127
        stdout_text = ""
        stderr_text = f"Failed to execute command: {exc}\n"
    except BaseException:
        _stop_process_group_for_streaming(process)
        _join_threads(reader_threads)
        raise
    duration_seconds = time.monotonic() - started
    transcript = HarnessCommandTranscript(
        command=_command_text(command),
        exit_code=exit_code,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        duration_seconds=duration_seconds,
        timed_out=timed_out,
        timeout_seconds=timeout_seconds,
    )
    return BlackBoxCommandResult(
        command=command,
        transcript=transcript,
        no_progress=no_progress,
        no_progress_details=no_progress_details,
    )


def _utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _progress_snapshot_signature(snapshot: dict[str, object]) -> str:
    comparable = dict(snapshot)
    comparable.pop("captured_at_utc", None)
    return json.dumps(comparable, sort_keys=True, separators=(",", ":"))


def _format_heartbeat_duration(seconds: float) -> str:
    total_seconds = max(int(seconds), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _format_heartbeat_timeout(seconds: float | None) -> str:
    return "unbounded" if seconds is None else _format_heartbeat_duration(seconds)


def _runtime_log_heartbeat_label(path: Path | None) -> str:
    if path is None:
        return "n/a"
    status = "present" if path.exists() else "waiting for first runtime event"
    return f"{path.resolve(strict=False).as_posix()} ({status})"


def _heartbeat_next_evidence_hint(
    *, last_progress_reason: str, runtime_log_path: Path | None
) -> str:
    if runtime_log_path is not None and runtime_log_path.exists():
        return "open runtime log for raw adapter output"
    if last_progress_reason == "watched-files":
        return "stage files changed before first runtime event; inspect artifacts or wait"
    if last_progress_reason in {"stdout", "stderr"}:
        return "command output was observed; wait for runtime log publication"
    return "stage command is alive; waiting for runtime output or file activity"


def _emit_command_heartbeat(
    *,
    stream: TextIO,
    label: str,
    elapsed_seconds: float,
    last_progress_seconds_ago: float,
    last_progress_reason: str,
    timeout_seconds: float | None,
    no_progress_timeout_seconds: float | None,
    runtime_log_path: Path | None,
) -> None:
    next_evidence = _heartbeat_next_evidence_hint(
        last_progress_reason=last_progress_reason,
        runtime_log_path=runtime_log_path,
    )
    print(
        "[aidd live] "
        f"{label} still running after {_format_heartbeat_duration(elapsed_seconds)}; "
        f"last signal: {last_progress_reason} "
        f"{_format_heartbeat_duration(last_progress_seconds_ago)} ago; "
        f"hard timeout: {_format_heartbeat_timeout(timeout_seconds)}; "
        f"no-progress timeout: {_format_heartbeat_timeout(no_progress_timeout_seconds)}; "
        f"runtime log: {_runtime_log_heartbeat_label(runtime_log_path)}; "
        f"next evidence: {next_evidence}.",
        file=stream,
        flush=True,
    )


def _read_command_stream(
    name: str,
    stream: TextIO | None,
    output_queue: Queue[tuple[str, str | None]],
) -> None:
    if stream is None:
        output_queue.put((name, None))
        return
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            output_queue.put((name, line))
    finally:
        output_queue.put((name, None))


def _join_threads(threads: Sequence[threading.Thread]) -> None:
    for thread in threads:
        thread.join(timeout=1.0)


def _stop_process_group_for_streaming(
    process: subprocess.Popen[str] | None,
) -> dict[str, object]:
    if process is None:
        return {
            "return_code": None,
            "stdout_text": "",
            "stderr_text": "",
            "terminated_process_group": False,
        }
    terminated_process_group = False
    if process.poll() is None:
        if os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGTERM)
                terminated_process_group = True
            except ProcessLookupError:
                pass
            except OSError:
                process.terminate()
        else:
            process.terminate()
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            if process.poll() is None:
                if os.name != "nt":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                        terminated_process_group = True
                    except ProcessLookupError:
                        pass
                    except OSError:
                        process.kill()
                else:
                    process.kill()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                pass
    return {
        "return_code": process.returncode,
        "stdout_text": "",
        "stderr_text": "",
        "terminated_process_group": terminated_process_group,
    }


def _text_tail(value: str, *, max_chars: int = 4000) -> str:
    return value[-max_chars:] if len(value) > max_chars else value


def _terminate_process(process: subprocess.Popen[str]) -> tuple[str, str, int | None]:
    terminated_process_group = False
    if process.poll() is None and os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGTERM)
            terminated_process_group = True
        except (OSError, ProcessLookupError):
            process.terminate()
    elif process.poll() is None:
        process.terminate()
    try:
        stdout_text, stderr_text = process.communicate(timeout=2.0)
    except subprocess.TimeoutExpired:
        if process.poll() is None and os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
                terminated_process_group = True
            except (OSError, ProcessLookupError):
                process.kill()
        elif process.poll() is None:
            process.kill()
        stdout_text, stderr_text = process.communicate(timeout=2.0)
    del terminated_process_group
    return stdout_text, stderr_text, process.returncode


def _timeout_output_to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _combined_frontend_checkpoint_classification(
    *classifications: StepClassification,
) -> StepClassification:
    for candidate in ("fail", "pass", "blocked", "infra-fail"):
        if candidate in classifications:
            return cast(StepClassification, candidate)
    return "skipped"


__all__ = [
    "BlackBoxCommandResult",
    "LiveE2EInterrupted",
    "StepClassification",
    "_command_text",
    "_combined_frontend_checkpoint_classification",
    "_run_black_box_command",
    "_terminate_process",
    "_timeout_output_to_text",
]
