from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import uuid4

StreamTarget = Literal["stdout", "stderr"]

STDIO_TAIL_BYTES = 256 * 1024
COMBINED_TAIL_BYTES = 512 * 1024
_STRUCTURED_LINE_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class RuntimeLogCaptureSnapshot:
    runtime_log_source_path: Path
    structured_events_source_path: Path
    stdout_text: str
    stderr_text: str
    runtime_log_text: str
    stdout_byte_count: int
    stderr_byte_count: int
    runtime_log_byte_count: int
    stdout_char_count: int
    stderr_char_count: int
    runtime_log_char_count: int
    stdout_truncated: bool
    stderr_truncated: bool
    runtime_log_truncated: bool


class _BoundedUtf8Tail:
    def __init__(self, maximum_bytes: int) -> None:
        self._maximum_bytes = maximum_bytes
        self._value = b""
        self.byte_count = 0
        self.char_count = 0

    def append(self, text: str) -> None:
        payload = text.encode("utf-8")
        self.byte_count += len(payload)
        self.char_count += len(text)
        combined = self._value + payload
        if len(combined) > self._maximum_bytes:
            combined = combined[-self._maximum_bytes :]
        self._value = combined.decode("utf-8", errors="ignore").encode("utf-8")

    @property
    def text(self) -> str:
        return self._value.decode("utf-8")

    @property
    def truncated(self) -> bool:
        return self.byte_count > len(self._value)


class DiskBackedRuntimeLogSink:
    def __init__(self, *, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        nonce = uuid4().hex
        self._runtime_log_path = directory / f".runtime-log.{nonce}.tmp"
        self._structured_events_path = directory / f".runtime-events.{nonce}.tmp"
        self._runtime_log = self._runtime_log_path.open("wb")
        self._structured_events = self._structured_events_path.open(
            "w",
            encoding="utf-8",
        )
        self._stdout = _BoundedUtf8Tail(STDIO_TAIL_BYTES)
        self._stderr = _BoundedUtf8Tail(STDIO_TAIL_BYTES)
        self._combined = _BoundedUtf8Tail(COMBINED_TAIL_BYTES)
        self._line_buffers: dict[StreamTarget, str] = {"stdout": "", "stderr": ""}
        self._discard_line: dict[StreamTarget, bool] = {
            "stdout": False,
            "stderr": False,
        }
        self._lock = threading.Lock()
        self._snapshot: RuntimeLogCaptureSnapshot | None = None

    def write(self, target: StreamTarget, text: str) -> None:
        payload = text.encode("utf-8")
        with self._lock:
            if self._snapshot is not None:
                raise RuntimeError("Runtime log sink is already finalized.")
            self._runtime_log.write(payload)
            self._combined.append(text)
            stream_tail = self._stdout if target == "stdout" else self._stderr
            stream_tail.append(text)
            self._consume_structured_lines(target, text)

    def finish(self) -> RuntimeLogCaptureSnapshot:
        with self._lock:
            if self._snapshot is not None:
                return self._snapshot
            for target in ("stdout", "stderr"):
                self._commit_structured_line(target, self._line_buffers[target])
                self._line_buffers[target] = ""
            self._runtime_log.flush()
            os.fsync(self._runtime_log.fileno())
            self._structured_events.flush()
            os.fsync(self._structured_events.fileno())
            self._runtime_log.close()
            self._structured_events.close()
            self._snapshot = RuntimeLogCaptureSnapshot(
                runtime_log_source_path=self._runtime_log_path,
                structured_events_source_path=self._structured_events_path,
                stdout_text=self._stdout.text,
                stderr_text=self._stderr.text,
                runtime_log_text=self._combined.text,
                stdout_byte_count=self._stdout.byte_count,
                stderr_byte_count=self._stderr.byte_count,
                runtime_log_byte_count=self._combined.byte_count,
                stdout_char_count=self._stdout.char_count,
                stderr_char_count=self._stderr.char_count,
                runtime_log_char_count=self._combined.char_count,
                stdout_truncated=self._stdout.truncated,
                stderr_truncated=self._stderr.truncated,
                runtime_log_truncated=self._combined.truncated,
            )
            return self._snapshot

    def abort(self) -> None:
        with self._lock:
            for handle in (self._runtime_log, self._structured_events):
                if not handle.closed:
                    handle.close()
            self._runtime_log_path.unlink(missing_ok=True)
            self._structured_events_path.unlink(missing_ok=True)

    def _consume_structured_lines(self, target: StreamTarget, text: str) -> None:
        pending = self._line_buffers[target] + text
        lines = pending.splitlines(keepends=True)
        self._line_buffers[target] = ""
        for line in lines:
            if line.endswith(("\n", "\r")):
                self._commit_structured_line(target, line)
                continue
            self._line_buffers[target] = line
        buffer_bytes = len(self._line_buffers[target].encode("utf-8"))
        if buffer_bytes > _STRUCTURED_LINE_BYTES:
            self._line_buffers[target] = ""
            self._discard_line[target] = True

    def _commit_structured_line(self, target: StreamTarget, line: str) -> None:
        if self._discard_line[target]:
            self._discard_line[target] = False
            return
        stripped = line.strip()
        if not stripped:
            return
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return
        self._structured_events.write(
            json.dumps({"payload": payload, "source": target}, sort_keys=True) + "\n"
        )


__all__ = [
    "COMBINED_TAIL_BYTES",
    "STDIO_TAIL_BYTES",
    "DiskBackedRuntimeLogSink",
    "RuntimeLogCaptureSnapshot",
    "StreamTarget",
]
