from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

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


@dataclass(frozen=True, slots=True)
class NormalizedRuntimeEvent:
    line_number: int
    event_kind: str
    source: str | None
    payload: dict[str, Any]


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


def _classify_normalized_event(event: NormalizedRuntimeEvent) -> RuntimeEventCategory:
    normalized_kind = event.event_kind.strip().lower()
    if any(token in normalized_kind for token in ("error", "fail", "exception", "timeout")):
        return "error"
    if "warn" in normalized_kind:
        return "warning"
    if any(token in normalized_kind for token in ("question", "pause", "awaiting", "input")):
        return "question"
    if "repair" in normalized_kind:
        return "repair"
    if any(token in normalized_kind for token in ("validator", "validation")):
        return "validator"
    if "stage" in normalized_kind:
        return "stage"
    return "info"


def parse_events_jsonl_text(events_jsonl_text: str) -> tuple[NormalizedRuntimeEvent, ...]:
    events: list[NormalizedRuntimeEvent] = []
    for line_number, raw_line in enumerate(events_jsonl_text.splitlines(), start=1):
        normalized_line = raw_line.strip()
        if not normalized_line:
            continue
        try:
            payload = json.loads(normalized_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in events.jsonl at line {line_number}.") from exc
        if not isinstance(payload, dict):
            payload_type = type(payload).__name__
            raise ValueError(
                "events.jsonl line "
                f"{line_number} must be a JSON object, got {payload_type}."
            )

        event_kind = str(payload.get("event") or payload.get("type") or "").strip().lower()
        source_value = payload.get("source")
        source = source_value.strip().lower() if isinstance(source_value, str) else None
        events.append(
            NormalizedRuntimeEvent(
                line_number=line_number,
                event_kind=event_kind or "unknown",
                source=source,
                payload=payload,
            )
        )
    return tuple(events)


def parse_events_jsonl(events_jsonl_path: Path) -> tuple[NormalizedRuntimeEvent, ...]:
    if not events_jsonl_path.exists() or not events_jsonl_path.is_file():
        raise ValueError(f"events.jsonl file does not exist: {events_jsonl_path.as_posix()}")
    return parse_events_jsonl_text(events_jsonl_path.read_text(encoding="utf-8"))


def coarse_events_from_normalized_events(
    normalized_events: tuple[NormalizedRuntimeEvent, ...],
) -> tuple[CoarseRuntimeEvent, ...]:
    coarse_events: list[CoarseRuntimeEvent] = []
    for event in normalized_events:
        message = (
            str(event.payload.get("message")).strip()
            if isinstance(event.payload.get("message"), str)
            else event.event_kind
        )
        coarse_events.append(
            CoarseRuntimeEvent(
                line_number=event.line_number,
                category=_classify_normalized_event(event),
                message=message or event.event_kind,
            )
        )
    return tuple(coarse_events)


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
