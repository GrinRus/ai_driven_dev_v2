from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DEFAULT_LOG_READ_BYTES = 64 * 1024
MAX_LOG_READ_BYTES = 256 * 1024
LogReadMode = Literal["head", "tail"]


@dataclass(frozen=True, slots=True)
class BoundedLogRead:
    path: Path
    text: str
    byte_size: int
    start_byte: int
    end_byte: int
    retained_bytes: int
    requested_bytes: int
    max_bytes: int
    mode: LogReadMode
    truncated: bool
    truncated_head: bool
    truncated_tail: bool
    partial_head_line: bool
    partial_tail_line: bool
    oversized_line: bool


def read_bounded_log(
    path: Path,
    *,
    mode: LogReadMode = "tail",
    requested_bytes: int = DEFAULT_LOG_READ_BYTES,
    max_bytes: int = MAX_LOG_READ_BYTES,
) -> BoundedLogRead:
    if requested_bytes <= 0:
        raise ValueError("requested_bytes must be greater than zero.")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero.")
    retained_limit = min(requested_bytes, max_bytes)
    byte_size = path.stat().st_size
    if mode == "tail":
        start_byte = max(0, byte_size - retained_limit)
        end_byte = byte_size
    elif mode == "head":
        start_byte = 0
        end_byte = min(byte_size, retained_limit)
    else:
        raise ValueError(f"Unsupported bounded log read mode: {mode!r}.")

    with path.open("rb") as stream:
        stream.seek(start_byte)
        raw = stream.read(end_byte - start_byte)
    partial_head_line = (
        start_byte > 0
        and _byte_before(path, start_byte) != b"\n"
        and not raw.startswith(b"\n")
    )
    partial_tail_line = end_byte < byte_size and (
        not raw.endswith(b"\n")
    )
    oversized_line = (
        partial_head_line and b"\n" not in raw
    ) or (
        partial_tail_line and b"\n" not in raw
    )
    return BoundedLogRead(
        path=path,
        text=raw.decode("utf-8", errors="replace"),
        byte_size=byte_size,
        start_byte=start_byte,
        end_byte=end_byte,
        retained_bytes=len(raw),
        requested_bytes=retained_limit,
        max_bytes=max_bytes,
        mode=mode,
        truncated=start_byte > 0 or end_byte < byte_size,
        truncated_head=start_byte > 0,
        truncated_tail=end_byte < byte_size,
        partial_head_line=partial_head_line,
        partial_tail_line=partial_tail_line,
        oversized_line=oversized_line,
    )


def _byte_before(path: Path, offset: int) -> bytes:
    if offset <= 0:
        return b""
    with path.open("rb") as stream:
        stream.seek(offset - 1)
        return stream.read(1)


__all__ = [
    "BoundedLogRead",
    "DEFAULT_LOG_READ_BYTES",
    "MAX_LOG_READ_BYTES",
    "read_bounded_log",
]
