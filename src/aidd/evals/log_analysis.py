from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RuntimeEventCategory = Literal[
    "error",
    "warning",
    "question",
    "repair",
    "validator",
    "stage",
    "info",
]


@dataclass(frozen=True, slots=True)
class CoarseRuntimeEvent:
    line_number: int
    category: RuntimeEventCategory
    message: str


def _classify_runtime_log_line(line: str) -> RuntimeEventCategory:
    normalized = line.strip()
    lower = normalized.lower()
    if any(token in lower for token in ("error", "exception", "traceback", "failed")):
        return "error"
    if "warning" in lower:
        return "warning"
    if normalized.endswith("?") or any(
        token in lower for token in ("question", "clarify", "clarification")
    ):
        return "question"
    if "repair" in lower:
        return "repair"
    if "validator" in lower or "validation" in lower:
        return "validator"
    if any(token in lower for token in ("stage", "phase", "step")) and "->" in lower:
        return "stage"
    return "info"


def parse_runtime_log_text(runtime_log_text: str) -> tuple[CoarseRuntimeEvent, ...]:
    events: list[CoarseRuntimeEvent] = []
    for line_number, raw_line in enumerate(runtime_log_text.splitlines(), start=1):
        normalized_line = raw_line.strip()
        if not normalized_line:
            continue
        events.append(
            CoarseRuntimeEvent(
                line_number=line_number,
                category=_classify_runtime_log_line(normalized_line),
                message=normalized_line,
            )
        )
    return tuple(events)


def parse_runtime_log(runtime_log_path: Path) -> tuple[CoarseRuntimeEvent, ...]:
    if not runtime_log_path.exists() or not runtime_log_path.is_file():
        raise ValueError(f"runtime.log file does not exist: {runtime_log_path.as_posix()}")
    return parse_runtime_log_text(runtime_log_path.read_text(encoding="utf-8"))


def summarize_first_failure(
    *, runtime_log_path: Path | None = None, runtime_log_text: str | None = None
) -> str:
    if runtime_log_path is None and runtime_log_text is None:
        raise ValueError("Either runtime_log_path or runtime_log_text must be provided.")

    events = (
        parse_runtime_log(runtime_log_path)
        if runtime_log_path is not None
        else parse_runtime_log_text(runtime_log_text or "")
    )
    for event in events:
        if event.category == "error":
            return f"line {event.line_number}: {event.message}"
    return "no failure signal found"
