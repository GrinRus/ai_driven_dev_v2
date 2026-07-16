from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

_STOP_GRACE_SECONDS = 0.5
_DRAIN_GRACE_SECONDS = 0.5


@dataclass(frozen=True, slots=True)
class HarnessLifecycleBudget:
    started_at: float
    deadline: float | None

    @classmethod
    def start(
        cls,
        timeout_seconds: float | None,
        *,
        now: float | None = None,
    ) -> HarnessLifecycleBudget:
        started_at = time.monotonic() if now is None else now
        deadline = None if timeout_seconds is None else started_at + max(timeout_seconds, 0.0)
        return cls(started_at=started_at, deadline=deadline)

    def remaining_seconds(self, *, now: float | None = None) -> float | None:
        if self.deadline is None:
            return None
        current = time.monotonic() if now is None else now
        return max(0.0, self.deadline - current)

    def exhausted(self, *, now: float | None = None) -> bool:
        remaining = self.remaining_seconds(now=now)
        return remaining is not None and remaining <= 0.0


@dataclass(frozen=True, slots=True)
class HarnessProcessResult:
    exit_code: int
    stdout_text: str
    stderr_text: str
    duration_seconds: float
    timed_out: bool
    timeout_seconds: float | None


def _process_group_exists(process: subprocess.Popen[str]) -> bool:
    if os.name == "nt":
        return process.poll() is None
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_group_exit(
    process: subprocess.Popen[str],
    *,
    timeout_seconds: float,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _process_group_exists(process):
            return True
        time.sleep(0.01)
    return not _process_group_exists(process)


def _stop_owned_process_group(process: subprocess.Popen[str]) -> None:
    if os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass
        else:
            if _wait_for_group_exit(process, timeout_seconds=_STOP_GRACE_SECONDS):
                return
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass
            try:
                process.wait(timeout=_STOP_GRACE_SECONDS)
            except subprocess.TimeoutExpired:
                pass
            return

    if process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=_STOP_GRACE_SECONDS)
        return
    except (OSError, ProcessLookupError, subprocess.TimeoutExpired):
        pass
    try:
        process.kill()
        process.wait(timeout=_STOP_GRACE_SECONDS)
    except (OSError, ProcessLookupError, subprocess.TimeoutExpired):
        pass


def run_owned_process(
    *,
    command: tuple[str, ...],
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: float | None,
) -> HarnessProcessResult:
    if timeout_seconds is not None and timeout_seconds <= 0.0:
        return HarnessProcessResult(
            exit_code=124,
            stdout_text="",
            stderr_text="Lifecycle budget was exhausted before command launch.\n",
            duration_seconds=0.0,
            timed_out=True,
            timeout_seconds=0.0,
        )

    started_at = time.monotonic()
    creationflags = (
        subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        if os.name == "nt"
        else 0
    )
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name != "nt",
        creationflags=creationflags,
    )
    timed_out = False
    try:
        stdout_text, stderr_text = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        _stop_owned_process_group(process)
        try:
            stdout_text, stderr_text = process.communicate(timeout=_DRAIN_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            _stop_owned_process_group(process)
            stdout_text = _output_text(exc.stdout)
            stderr_text = _output_text(exc.stderr)
        exit_code = 124
    else:
        exit_code = process.returncode
        if _process_group_exists(process):
            _stop_owned_process_group(process)

    return HarnessProcessResult(
        exit_code=exit_code,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        duration_seconds=time.monotonic() - started_at,
        timed_out=timed_out,
        timeout_seconds=timeout_seconds,
    )


def _output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


__all__ = [
    "HarnessLifecycleBudget",
    "HarnessProcessResult",
    "run_owned_process",
]
