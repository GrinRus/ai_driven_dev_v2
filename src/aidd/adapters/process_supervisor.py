from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass

from aidd.adapters.runtime_execution import RuntimeSubprocessSpec

_DEFAULT_STOP_GRACE_SECONDS = 0.5
_DEFAULT_DRAIN_GRACE_SECONDS = 0.5


@dataclass(slots=True)
class OwnedProcessSupervisor:
    process: subprocess.Popen[str]

    @classmethod
    def launch(cls, spec: RuntimeSubprocessSpec) -> OwnedProcessSupervisor:
        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
            if os.name == "nt"
            else 0
        )
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
            creationflags=creationflags,
        )
        return cls(process=process)

    def request_stop(self, *, grace_seconds: float = _DEFAULT_STOP_GRACE_SECONDS) -> None:
        if os.name != "nt" and self._signal_process_group(signal.SIGTERM):
            if self._wait_for_group_exit(grace_seconds):
                return
            self._signal_process_group(signal.SIGKILL)
            self._wait_for_parent_exit(grace_seconds)
            return

        if self.process.poll() is not None:
            return
        try:
            self.process.terminate()
        except (OSError, ProcessLookupError):
            return
        if self._wait_for_parent_exit(grace_seconds):
            return
        try:
            self.process.kill()
        except (OSError, ProcessLookupError):
            return
        self._wait_for_parent_exit(grace_seconds)

    def drain_streams(
        self,
        reader_threads: tuple[threading.Thread, ...],
        *,
        grace_seconds: float = _DEFAULT_DRAIN_GRACE_SECONDS,
    ) -> bool:
        deadline = time.monotonic() + grace_seconds
        self._join_until(reader_threads, deadline=deadline)
        if all(not thread.is_alive() for thread in reader_threads):
            return True

        self.request_stop()
        self._join_until(
            reader_threads,
            deadline=time.monotonic() + _DEFAULT_STOP_GRACE_SECONDS,
        )
        return all(not thread.is_alive() for thread in reader_threads)

    def process_group_exists(self) -> bool:
        if os.name == "nt":
            return self.process.poll() is None
        try:
            os.killpg(self.process.pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _signal_process_group(self, sig: signal.Signals) -> bool:
        try:
            os.killpg(self.process.pid, sig)
        except (OSError, ProcessLookupError):
            return False
        return True

    def _wait_for_group_exit(self, timeout_seconds: float) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if not self.process_group_exists():
                return True
            time.sleep(0.01)
        return not self.process_group_exists()

    def _wait_for_parent_exit(self, timeout_seconds: float) -> bool:
        try:
            self.process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            return False
        return True

    @staticmethod
    def _join_until(
        threads: tuple[threading.Thread, ...],
        *,
        deadline: float,
    ) -> None:
        for thread in threads:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            thread.join(timeout=remaining)


__all__ = ["OwnedProcessSupervisor"]
