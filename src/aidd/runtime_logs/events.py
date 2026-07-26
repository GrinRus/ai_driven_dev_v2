from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from aidd.core.run_store import RUN_EVENTS_JSONL_FILENAME, RUN_RUNTIME_JSONL_FILENAME

StreamSource = Literal["stdout", "stderr"]
MAX_LIFECYCLE_EVENT_BYTES = 1024
MAX_LIFECYCLE_EVENTS = 1023
MAX_LIFECYCLE_PROJECTION_BYTES = 1024 * 1024


class RuntimeRunResultLike(Protocol):
    @property
    def stdout_text(self) -> str:
        ...

    @property
    def stderr_text(self) -> str:
        ...

    @property
    def structured_events_source_path(self) -> Path | None:
        ...


@dataclass(frozen=True, slots=True)
class RuntimeEventArtifacts:
    runtime_jsonl_path: Path | None
    events_jsonl_path: Path | None


@dataclass(frozen=True, slots=True)
class RuntimeEventIdentity:
    work_item: str
    run_id: str
    stage: str
    attempt: str


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
    source_path = getattr(run_result, "structured_events_source_path", None)
    if source_path is not None and source_path.exists():
        events: list[dict[str, object]] = []
        with source_path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    events.append(payload)
        return tuple(events)
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


def _attempt_identity(attempt_path: Path) -> RuntimeEventIdentity:
    parts = attempt_path.parts
    try:
        runs_index = parts.index("runs")
        work_item = parts[runs_index + 1]
        run_id = parts[runs_index + 2]
        stages_index = parts.index("stages", runs_index + 3)
        stage = parts[stages_index + 1]
        attempts_index = parts.index("attempts", stages_index + 2)
        attempt = parts[attempts_index + 1]
    except (ValueError, IndexError):
        return RuntimeEventIdentity(
            work_item="unknown",
            run_id="unknown",
            stage="unknown",
            attempt=attempt_path.name or "unknown",
        )
    return RuntimeEventIdentity(
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt=attempt,
    )


def _provider_payload(event: Mapping[str, object]) -> Mapping[str, object]:
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else event


def _canonical_event_kind(payload: Mapping[str, object]) -> str:
    raw = str(
        payload.get("event")
        or payload.get("type")
        or payload.get("method")
        or payload.get("subtype")
        or ""
    ).lower()
    if any(token in raw for token in ("question", "input_required", "ask_user")):
        return "operator-request"
    if any(token in raw for token in ("approval", "permission", "request")):
        return "operator-request"
    if any(token in raw for token in ("decision", "approved", "denied")):
        return "operator-decision"
    if any(token in raw for token in ("cancel", "abort", "interrupt")):
        return "lifecycle-cancel"
    if any(token in raw for token in ("fail", "error", "exception")):
        return "lifecycle-fail"
    if any(token in raw for token in ("complete", "success", "finished", "result")):
        return "lifecycle-complete"
    if any(token in raw for token in ("start", "begin", "created")):
        return "lifecycle-start"
    if "tool" in raw:
        return "tool-activity"
    return "runtime-event"


def _bounded_scalar(value: object, *, limit: int = 160) -> str | float | int | bool | None:
    if isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        normalized = " ".join(value.split())
        return normalized[:limit] if normalized else None
    return None


def _first_scalar(
    payload: Mapping[str, object],
    keys: tuple[str, ...],
) -> str | float | int | bool | None:
    for key in keys:
        value = _bounded_scalar(payload.get(key))
        if value is not None:
            return value
    return None


def project_lifecycle_events(
    *,
    structured_events: tuple[Mapping[str, object], ...],
    identity: RuntimeEventIdentity,
    evidence_filename: str = RUN_RUNTIME_JSONL_FILENAME,
) -> tuple[dict[str, object], ...]:
    projections: list[dict[str, object]] = []
    retained_events = structured_events[:MAX_LIFECYCLE_EVENTS]
    for line_number, event in enumerate(retained_events, start=1):
        payload = _provider_payload(event)
        canonical = json.dumps(
            dict(event),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        row: dict[str, object] = {
            "event_kind": _canonical_event_kind(payload),
            "identity": {
                "work_item": identity.work_item,
                "run_id": identity.run_id,
                "stage": identity.stage,
                "attempt": identity.attempt,
            },
            "timestamp": _first_scalar(
                payload,
                ("timestamp", "timestamp_utc", "created_at", "created_at_utc", "ts"),
            ),
            "duration_seconds": _first_scalar(
                payload,
                ("duration_seconds", "duration", "elapsed_seconds"),
            ),
            "outcome": _first_scalar(
                payload,
                ("outcome", "status", "stop_reason", "result"),
            ),
            "operator_request_ref": _first_scalar(
                payload,
                ("operator_request_ref", "request_id", "requestId"),
            ),
            "operator_decision_ref": _first_scalar(
                payload,
                ("operator_decision_ref", "decision_id", "decisionId"),
            ),
            "evidence": f"{evidence_filename}#line={line_number}",
            "payload_sha256": hashlib.sha256(canonical).hexdigest(),
            "source": _bounded_scalar(event.get("source")),
        }
        row = {key: value for key, value in row.items() if value is not None}
        encoded = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
        if len(encoded) > MAX_LIFECYCLE_EVENT_BYTES:
            raise ValueError("Canonical lifecycle projection exceeds its fixed byte bound.")
        projections.append(row)
    if len(structured_events) > len(retained_events):
        omitted = structured_events[len(retained_events) :]
        omitted_digest = hashlib.sha256()
        for event in omitted:
            omitted_digest.update(
                json.dumps(
                    dict(event),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            omitted_digest.update(b"\n")
        projections.append(
            {
                "event_kind": "projection-truncated",
                "identity": {
                    "work_item": identity.work_item,
                    "run_id": identity.run_id,
                    "stage": identity.stage,
                    "attempt": identity.attempt,
                },
                "outcome": f"omitted={len(omitted)}",
                "evidence": (
                    f"{evidence_filename}#line={len(retained_events) + 1}-"
                    f"{len(structured_events)}"
                ),
                "payload_sha256": omitted_digest.hexdigest(),
            }
        )
    encoded_size = sum(
        len(json.dumps(row, sort_keys=True).encode("utf-8")) + 1
        for row in projections
    )
    if encoded_size > MAX_LIFECYCLE_PROJECTION_BYTES:
        raise ValueError("Canonical lifecycle projection exceeds its fixed file bound.")
    return tuple(projections)


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
    normalized_events = project_lifecycle_events(
        structured_events=structured_events,
        identity=_attempt_identity(attempt_path),
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


def persist_lifecycle_projection_from_jsonl(
    *,
    attempt_path: Path,
    source_path: Path | None,
) -> RuntimeEventArtifacts:
    if source_path is None or not source_path.is_file():
        return RuntimeEventArtifacts(runtime_jsonl_path=None, events_jsonl_path=None)
    structured_events: list[Mapping[str, object]] = []
    with source_path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                structured_events.append(payload)
    if not structured_events:
        return RuntimeEventArtifacts(runtime_jsonl_path=None, events_jsonl_path=None)
    attempt_path.mkdir(parents=True, exist_ok=True)
    runtime_path = attempt_path / RUN_RUNTIME_JSONL_FILENAME
    if source_path.resolve(strict=True) != runtime_path.resolve(strict=False):
        shutil.copyfile(source_path, runtime_path)
    projections = project_lifecycle_events(
        structured_events=tuple(structured_events),
        identity=_attempt_identity(attempt_path),
    )
    return RuntimeEventArtifacts(
        runtime_jsonl_path=runtime_path,
        events_jsonl_path=write_jsonl(
            attempt_path / RUN_EVENTS_JSONL_FILENAME,
            projections,
        ),
    )
__all__ = [
    "MAX_LIFECYCLE_EVENT_BYTES",
    "MAX_LIFECYCLE_EVENTS",
    "MAX_LIFECYCLE_PROJECTION_BYTES",
    "RuntimeEventArtifacts",
    "RuntimeEventIdentity",
    "RuntimeRunResultLike",
    "StreamSource",
    "normalize_structured_events",
    "persist_runtime_event_artifacts",
    "persist_lifecycle_projection_from_jsonl",
    "project_lifecycle_events",
    "structured_runtime_events",
    "write_jsonl",
]
