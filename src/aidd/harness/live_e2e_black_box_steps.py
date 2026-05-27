from __future__ import annotations

import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from aidd.harness.runner import HarnessCommandTranscript


@dataclass(frozen=True, slots=True)
class BlackBoxCommandResult:
    command: tuple[str, ...]
    transcript: HarnessCommandTranscript

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


def _command_text(command: Sequence[str]) -> str:
    return " ".join(command)


def _run_black_box_command(
    *,
    command: tuple[str, ...],
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: float | None,
) -> BlackBoxCommandResult:
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        exit_code = completed.returncode
        stdout_text = completed.stdout
        stderr_text = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout_text = _timeout_output_to_text(exc.stdout)
        stderr_text = _timeout_output_to_text(exc.stderr)
        timeout_label = (
            f"{timeout_seconds:.3f}s" if timeout_seconds is not None else "configured timeout"
        )
        stderr_text = (
            f"{stderr_text.rstrip()}\nCommand timed out after {timeout_label}.\n"
        ).lstrip()
    except OSError as exc:
        exit_code = 127
        stdout_text = ""
        stderr_text = f"Failed to execute command: {exc}\n"
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
    return BlackBoxCommandResult(command=command, transcript=transcript)


def _terminate_process(process: subprocess.Popen[str]) -> tuple[str, str, int | None]:
    if process.poll() is None:
        process.terminate()
    try:
        stdout_text, stderr_text = process.communicate(timeout=2.0)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout_text, stderr_text = process.communicate(timeout=2.0)
    return stdout_text, stderr_text, process.returncode


def _timeout_output_to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


__all__ = [
    "BlackBoxCommandResult",
    "_command_text",
    "_run_black_box_command",
    "_terminate_process",
    "_timeout_output_to_text",
]
