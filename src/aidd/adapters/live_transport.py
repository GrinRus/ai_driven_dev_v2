from __future__ import annotations

import json
import shlex
import subprocess
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from aidd.adapters.runtime_execution import RuntimeRunResult
from aidd.adapters.runtime_log_capture import (
    DiskBackedRuntimeLogSink,
    RuntimeLogCaptureSnapshot,
    StreamTarget,
)
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_catalog import RuntimeExecutionMode
from aidd.runtime_permissions import RuntimeInteractionMode, RuntimePermissionPolicy

ExitClassificationT = TypeVar("ExitClassificationT")


@dataclass(frozen=True, slots=True)
class LiveTransportResult[ExitClassificationT]:
    run_result: RuntimeRunResult[ExitClassificationT] | None
    status: AdapterExecutionStatus
    details: str
    runtime_jsonl_path: Path | None = None
    events_jsonl_path: Path | None = None
    operator_requests_path: Path | None = None
    operator_decisions_path: Path | None = None
    pending_operator_request_ids: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return self.status is AdapterExecutionStatus.SUCCEEDED


class StreamCapture:
    def __init__(
        self,
        *,
        directory: Path,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
    ) -> None:
        self._sink = DiskBackedRuntimeLogSink(directory=directory)
        self._on_stdout = on_stdout
        self._on_stderr = on_stderr
        self._threads: list[threading.Thread] = []
        self._errors: list[BaseException] = []

    @property
    def stdout_text(self) -> str:
        return self.snapshot.stdout_text

    @property
    def stderr_text(self) -> str:
        return self.snapshot.stderr_text

    @property
    def runtime_log_text(self) -> str:
        return self.snapshot.runtime_log_text

    @property
    def snapshot(self) -> RuntimeLogCaptureSnapshot:
        return self._sink.finish()

    def abort(self) -> None:
        self._sink.abort()

    @property
    def reader_threads(self) -> tuple[threading.Thread, ...]:
        return tuple(self._threads)

    @property
    def error(self) -> BaseException | None:
        return self._errors[0] if self._errors else None

    def attach(self, process: subprocess.Popen[str]) -> None:
        if process.stdout is not None:
            thread = threading.Thread(
                target=self._read_stream,
                args=(
                    process.stdout,
                    "stdout",
                    self._on_stdout,
                    self._errors,
                ),
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)
        if process.stderr is not None:
            thread = threading.Thread(
                target=self._read_stream,
                args=(
                    process.stderr,
                    "stderr",
                    self._on_stderr,
                    self._errors,
                ),
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

    def join(self, *, timeout_seconds: float = 1.0) -> None:
        for thread in self._threads:
            thread.join(timeout=timeout_seconds)

    def _read_stream(
        self,
        stream: Any,
        target: StreamTarget,
        callback: Callable[[str], None] | None,
        errors: list[BaseException],
    ) -> None:
        try:
            for line in stream:
                self._sink.write(target, line)
                if callback is not None:
                    callback(line)
        except BaseException as exc:
            errors.append(exc)
        finally:
            try:
                stream.close()
            except OSError:
                pass


def append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), sort_keys=True) + "\n")


def split_command(configured_command: str, *, runtime_label: str) -> tuple[str, ...]:
    stripped = configured_command.strip()
    if not stripped:
        raise ValueError(f"Configured {runtime_label} command must not be empty.")
    try:
        tokens = tuple(shlex.split(stripped))
    except ValueError as exc:
        raise ValueError(
            f"Configured {runtime_label} command is not valid shell syntax: "
            f"{configured_command!r}"
        ) from exc
    if not tokens:
        raise ValueError(f"Configured {runtime_label} command must produce at least one token.")
    return tokens


def command_executable_name(configured_command: str, *, runtime_label: str) -> str:
    tokens = split_command(configured_command, runtime_label=runtime_label)
    return Path(tokens[0]).name


def should_use_live_transport(
    *,
    permission_policy: RuntimePermissionPolicy,
    interaction_mode: RuntimeInteractionMode,
    execution_mode: RuntimeExecutionMode,
    provider_present: bool,
) -> bool:
    return (
        permission_policy is not RuntimePermissionPolicy.FULL_ACCESS
        and interaction_mode is RuntimeInteractionMode.LIVE
        and execution_mode is RuntimeExecutionMode.NATIVE
        and provider_present
    )


def run_help_text(command: tuple[str, ...], *, timeout_seconds: float = 5.0) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except (FileNotFoundError, PermissionError, OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout or result.stderr or ""


__all__ = [
    "LiveTransportResult",
    "StreamCapture",
    "append_jsonl",
    "command_executable_name",
    "run_help_text",
    "should_use_live_transport",
    "split_command",
]
