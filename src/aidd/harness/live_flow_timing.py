from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Literal, cast

ProcessTerminationReason = Literal[
    "awaiting-quality-review",
    "blocked",
    "fail",
    "infra-fail",
    "interrupted",
    "manual-quality-stop",
    "pass",
    "stale-owner",
]

_TERMINAL_STATUS_REASONS: dict[str, ProcessTerminationReason] = {
    "awaiting-quality-review": "awaiting-quality-review",
    "blocked": "blocked",
    "fail": "fail",
    "infra-fail": "infra-fail",
    "interrupted-resumable": "interrupted",
    "manual-quality-stop": "manual-quality-stop",
    "pass": "pass",
}


@dataclass(frozen=True, slots=True)
class ProcessSegment:
    segment_id: str
    started_at_utc: str
    finished_at_utc: str | None
    duration_seconds: float
    owner_pid: int
    termination_reason: ProcessTerminationReason | None

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def format_segment_timestamp(value: datetime | None = None) -> str:
    return (value or datetime.now(UTC)).astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _elapsed_seconds(started_at_utc: str, finished_at_utc: str) -> float:
    started = _parse_timestamp(started_at_utc)
    finished = _parse_timestamp(finished_at_utc)
    if started is None or finished is None:
        return 0.0
    return max((finished - started).total_seconds(), 0.0)


def process_segments_from_payload(raw: object) -> tuple[ProcessSegment, ...]:
    if not isinstance(raw, list):
        return tuple()
    segments: list[ProcessSegment] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            continue
        segment_id = item.get("segment_id")
        started_at = item.get("started_at_utc")
        owner_pid = item.get("owner_pid")
        if (
            not isinstance(segment_id, str)
            or segment_id != f"segment-{index:04d}"
            or not isinstance(started_at, str)
            or _parse_timestamp(started_at) is None
            or not isinstance(owner_pid, int)
            or owner_pid <= 0
        ):
            continue
        finished_at = item.get("finished_at_utc")
        if finished_at is not None and (
            not isinstance(finished_at, str) or _parse_timestamp(finished_at) is None
        ):
            continue
        raw_reason = item.get("termination_reason")
        reason = (
            raw_reason
            if raw_reason in {
                "awaiting-quality-review",
                "blocked",
                "fail",
                "infra-fail",
                "interrupted",
                "manual-quality-stop",
                "pass",
                "stale-owner",
            }
            else None
        )
        duration = item.get("duration_seconds")
        segments.append(
            ProcessSegment(
                segment_id=segment_id,
                started_at_utc=started_at,
                finished_at_utc=finished_at,
                duration_seconds=(
                    max(float(duration), 0.0)
                    if isinstance(duration, int | float)
                    else 0.0
                ),
                owner_pid=owner_pid,
                termination_reason=cast(ProcessTerminationReason | None, reason),
            )
        )
    return tuple(segments)


def termination_reason_for_status(
    status: str,
    *,
    interruption_reason: object = None,
) -> ProcessTerminationReason | None:
    if status == "interrupted-resumable" and interruption_reason == "stale-owner":
        return "stale-owner"
    return _TERMINAL_STATUS_REASONS.get(status)


def update_process_segments(
    raw_segments: object,
    *,
    owner_pid: int,
    observed_at_utc: str,
    status: str,
    interruption_reason: object = None,
) -> tuple[ProcessSegment, ...]:
    if owner_pid <= 0 or _parse_timestamp(observed_at_utc) is None:
        raise ValueError("Process segment owner and timestamp must be canonical.")
    segments = list(process_segments_from_payload(raw_segments))
    active = segments[-1] if segments and segments[-1].finished_at_utc is None else None
    if active is not None and active.owner_pid != owner_pid:
        raise ValueError(
            "Cannot start a new process segment while another owner segment is active."
        )
    if active is None:
        active = ProcessSegment(
            segment_id=f"segment-{len(segments) + 1:04d}",
            started_at_utc=observed_at_utc,
            finished_at_utc=None,
            duration_seconds=0.0,
            owner_pid=owner_pid,
            termination_reason=None,
        )
        segments.append(active)
    reason = termination_reason_for_status(
        status,
        interruption_reason=interruption_reason,
    )
    finished_at = observed_at_utc if reason is not None else None
    updated = ProcessSegment(
        segment_id=active.segment_id,
        started_at_utc=active.started_at_utc,
        finished_at_utc=finished_at,
        duration_seconds=_elapsed_seconds(
            active.started_at_utc,
            observed_at_utc,
        ),
        owner_pid=active.owner_pid,
        termination_reason=reason,
    )
    segments[-1] = updated
    return tuple(segments)


def finish_stale_owner_segment(
    raw_segments: object,
    *,
    owner_pid: int | None,
    finished_at_utc: str,
    fallback_started_at_utc: object = None,
) -> tuple[ProcessSegment, ...]:
    if owner_pid is None or owner_pid <= 0:
        return process_segments_from_payload(raw_segments)
    segments = list(process_segments_from_payload(raw_segments))
    active = segments[-1] if segments and segments[-1].finished_at_utc is None else None
    if active is None:
        started_at = (
            fallback_started_at_utc
            if isinstance(fallback_started_at_utc, str)
            and _parse_timestamp(fallback_started_at_utc) is not None
            else finished_at_utc
        )
        active = ProcessSegment(
            segment_id=f"segment-{len(segments) + 1:04d}",
            started_at_utc=started_at,
            finished_at_utc=None,
            duration_seconds=0.0,
            owner_pid=owner_pid,
            termination_reason=None,
        )
        segments.append(active)
    if active.owner_pid != owner_pid:
        raise ValueError("Stale-owner segment identity does not match flow-state owner.")
    segments[-1] = ProcessSegment(
        segment_id=active.segment_id,
        started_at_utc=active.started_at_utc,
        finished_at_utc=finished_at_utc,
        duration_seconds=_elapsed_seconds(active.started_at_utc, finished_at_utc),
        owner_pid=active.owner_pid,
        termination_reason="stale-owner",
    )
    return tuple(segments)


def cumulative_process_duration_seconds(
    raw_segments: object,
    *,
    observed_at_utc: str | None = None,
) -> float:
    observed = observed_at_utc or format_segment_timestamp()
    total = 0.0
    for segment in process_segments_from_payload(raw_segments):
        if segment.finished_at_utc is not None:
            total += segment.duration_seconds
        else:
            total += _elapsed_seconds(segment.started_at_utc, observed)
    return max(total, 0.0)


def process_segments_payload(
    segments: Sequence[ProcessSegment],
) -> list[dict[str, object]]:
    return [segment.to_payload() for segment in segments]


__all__ = [
    "ProcessSegment",
    "ProcessTerminationReason",
    "cumulative_process_duration_seconds",
    "finish_stale_owner_segment",
    "format_segment_timestamp",
    "process_segments_from_payload",
    "process_segments_payload",
    "termination_reason_for_status",
    "update_process_segments",
]
