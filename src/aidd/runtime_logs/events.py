from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from aidd.core.run_store import RUN_EVENTS_JSONL_FILENAME, RUN_RUNTIME_JSONL_FILENAME

StreamSource = Literal["stdout", "stderr"]


class RuntimeRunResultLike(Protocol):
    @property
    def stdout_text(self) -> str:
        ...

    @property
    def stderr_text(self) -> str:
        ...


@dataclass(frozen=True, slots=True)
class RuntimeEventArtifacts:
    runtime_jsonl_path: Path | None
    events_jsonl_path: Path | None


def _structured_stream_events(
    *,
    stream_text: str,
    source: StreamSource,
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in stream_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            continue

        events.append({"payload": parsed, "source": source})
    return events


def structured_runtime_events(
    *,
    run_result: RuntimeRunResultLike,
) -> tuple[dict[str, object], ...]:
    stdout_events = _structured_stream_events(
        stream_text=run_result.stdout_text,
        source="stdout",
    )
    stderr_events = _structured_stream_events(
        stream_text=run_result.stderr_text,
        source="stderr",
    )
    return tuple((*stdout_events, *stderr_events))


def _normalized_event_from_structured_event(
    event: Mapping[str, object],
) -> dict[str, object]:
    payload = event.get("payload")
    source = event.get("source")
    if isinstance(payload, dict):
        return {**payload, "source": source}
    return {"payload": payload, "source": source}


def normalize_structured_events(
    *,
    run_result: RuntimeRunResultLike,
) -> tuple[dict[str, object], ...]:
    return tuple(
        _normalized_event_from_structured_event(event)
        for event in structured_runtime_events(run_result=run_result)
    )


def write_jsonl(path: Path, rows: tuple[Mapping[str, object], ...]) -> Path | None:
    if not rows:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(dict(row), sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return path


def persist_runtime_event_artifacts(
    *,
    attempt_path: Path,
    run_result: RuntimeRunResultLike,
) -> RuntimeEventArtifacts:
    structured_events = structured_runtime_events(run_result=run_result)
    normalized_events = tuple(
        _normalized_event_from_structured_event(event) for event in structured_events
    )
    return RuntimeEventArtifacts(
        runtime_jsonl_path=write_jsonl(
            attempt_path / RUN_RUNTIME_JSONL_FILENAME,
            structured_events,
        ),
        events_jsonl_path=write_jsonl(
            attempt_path / RUN_EVENTS_JSONL_FILENAME,
            normalized_events,
        ),
    )


__all__ = [
    "RuntimeEventArtifacts",
    "RuntimeRunResultLike",
    "StreamSource",
    "normalize_structured_events",
    "persist_runtime_event_artifacts",
    "structured_runtime_events",
    "write_jsonl",
]
