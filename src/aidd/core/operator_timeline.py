from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from aidd.core.run_lookup import latest_attempt_number
from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    RUN_RUNTIME_LOG_FILENAME,
    load_attempt_artifact_index,
    load_stage_metadata,
    run_attempt_root,
    run_stage_root,
)
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.workspace import stage_root as workspace_stage_root


@dataclass(frozen=True, slots=True)
class OperatorTimelineEvent:
    kind: str
    stage: str | None
    status: str | None
    attempt_number: int | None
    time_utc: str | None
    message: str
    path: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorTimelineFrame:
    identity: str
    kind: str
    stage: str | None
    task_id: str | None
    attempt_number: int | None
    status: str
    time_utc: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OperatorTimelineView:
    run_id: str
    stage: str | None
    events: tuple[OperatorTimelineEvent, ...]
    frames: tuple[OperatorTimelineFrame, ...] = ()
    warnings: tuple[str, ...] = ()


def _workspace_relative(workspace_root: Path, path: Path) -> str:
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_workspace):
        return path.as_posix()
    return resolved_path.relative_to(resolved_workspace).as_posix()


def _event_sort_key(event: OperatorTimelineEvent) -> tuple[str, str, int]:
    return (
        event.time_utc or "",
        event.stage or "",
        event.attempt_number or 0,
    )


def _frame_sort_key(frame: OperatorTimelineFrame) -> tuple[int, str, int, str, str]:
    stage_index = STAGES.index(frame.stage) if frame.stage in STAGES else len(STAGES)
    kind_order = {
        "stage-attempt": "0",
        "task-attempt": "1",
        "finalization-attempt": "2",
        "event-marker": "3",
    }
    return (
        stage_index,
        frame.task_id or "",
        frame.attempt_number or 0,
        frame.time_utc or "",
        f"{kind_order.get(frame.kind, '9')}:{frame.identity}",
    )


def _state_payload(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"status": "unknown"}
    return payload if isinstance(payload, dict) else {"status": "unknown"}


def _retained_refs(workspace_root: Path, root: Path) -> tuple[str, ...]:
    names = (
        "attempt-state.json",
        "finalization-state.json",
        "repository-baseline.json",
        "repository-final.json",
        "task-diff.json",
        "implementation-report.md",
        "runtime.log",
        "runtime-exit.json",
        RUN_EVENTS_JSONL_FILENAME,
        "artifact-index.json",
    )
    return tuple(
        _workspace_relative(workspace_root, path)
        for name in names
        if (path := root / name).exists()
    )


def _stage_attempt_frames(
    *, workspace_root: Path, work_item: str, run_id: str, stage: str
) -> list[OperatorTimelineFrame]:
    stage_attempts_root = run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    ) / "attempts"
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    status = metadata.status if metadata is not None else "unknown"
    return [
        OperatorTimelineFrame(
            identity=f"stage:{stage}:attempt:{int(path.name.removeprefix('attempt-')):04d}",
            kind="stage-attempt",
            stage=stage,
            task_id=None,
            attempt_number=int(path.name.removeprefix("attempt-")),
            status=status,
            time_utc=None,
            evidence_refs=_retained_refs(workspace_root, path),
        )
        for path in sorted(stage_attempts_root.glob("attempt-[0-9][0-9][0-9][0-9]"))
    ]


def _task_attempt_frames(
    *, workspace_root: Path, work_item: str, run_id: str
) -> list[OperatorTimelineFrame]:
    tasks_root = run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
    ) / "tasks"
    frames: list[OperatorTimelineFrame] = []
    for task_path in sorted(path for path in tasks_root.glob("*") if path.is_dir()):
        for attempt_path in sorted(
            task_path.joinpath("attempts").glob("attempt-[0-9][0-9][0-9][0-9]")
        ):
            attempt_number = int(attempt_path.name.removeprefix("attempt-"))
            state = _state_payload(attempt_path / "attempt-state.json")
            frames.append(
                OperatorTimelineFrame(
                    identity=f"task:{task_path.name}:attempt:{attempt_number:04d}",
                    kind="task-attempt",
                    stage="implement",
                    task_id=task_path.name,
                    attempt_number=attempt_number,
                    status=str(state.get("status", "unknown")),
                    time_utc=(
                        str(state["updated_at_utc"])
                        if state.get("updated_at_utc") is not None
                        else None
                    ),
                    evidence_refs=_retained_refs(workspace_root, attempt_path),
                )
            )
    return frames


def _finalization_frames(
    *, workspace_root: Path, work_item: str, run_id: str
) -> list[OperatorTimelineFrame]:
    attempts_root = run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
    ) / "finalization" / "attempts"
    frames: list[OperatorTimelineFrame] = []
    for path in sorted(attempts_root.glob("attempt-[0-9][0-9][0-9][0-9]")):
        attempt_number = int(path.name.removeprefix("attempt-"))
        state = _state_payload(path / "finalization-state.json")
        frames.append(
            OperatorTimelineFrame(
                identity=f"finalization:implement:attempt:{attempt_number:04d}",
                kind="finalization-attempt",
                stage="implement",
                task_id=None,
                attempt_number=attempt_number,
                status=str(state.get("status", "unknown")),
                time_utc=(
                    str(state["updated_at_utc"])
                    if state.get("updated_at_utc") is not None
                    else None
                ),
                evidence_refs=_retained_refs(workspace_root, path),
            )
        )
    return frames


def _event_marker_frames(events: list[OperatorTimelineEvent]) -> list[OperatorTimelineFrame]:
    counts: dict[tuple[str | None, str, int | None], int] = {}
    frames: list[OperatorTimelineFrame] = []
    for event in sorted(events, key=_event_sort_key):
        key = (event.stage, event.kind, event.attempt_number)
        counts[key] = counts.get(key, 0) + 1
        stage = event.stage or "run"
        attempt = event.attempt_number or 0
        frames.append(
            OperatorTimelineFrame(
                identity=(
                    f"event:{stage}:{event.kind}:attempt:{attempt:04d}:"
                    f"{counts[key]:04d}"
                ),
                kind="event-marker",
                stage=event.stage,
                task_id=None,
                attempt_number=event.attempt_number,
                status=event.status or "event",
                time_utc=event.time_utc,
                evidence_refs=((event.path,) if event.path else ()),
            )
        )
    return frames


def _metadata_events(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> list[OperatorTimelineEvent]:
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if metadata is None:
        return []
    events = [
        OperatorTimelineEvent(
            kind="stage-status",
            stage=stage,
            status=change.status,
            attempt_number=None,
            time_utc=change.changed_at_utc,
            message=f"{stage} status changed to {change.status}",
        )
        for change in metadata.status_history
    ]
    for repair in metadata.repair_history:
        events.append(
            OperatorTimelineEvent(
                kind="repair",
                stage=stage,
                status=repair.outcome,
                attempt_number=repair.attempt_number,
                time_utc=repair.recorded_at_utc,
                message=(
                    f"{stage} {repair.trigger} attempt "
                    f"{repair.attempt_number}: {repair.outcome}"
                ),
                path=repair.validator_report_path or repair.repair_brief_path,
            )
        )
    return events


def _attempt_events(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> list[OperatorTimelineEvent]:
    latest = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if latest is None:
        return []
    events: list[OperatorTimelineEvent] = []
    for attempt_number in range(1, latest + 1):
        attempt_root = run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
        events.append(
            OperatorTimelineEvent(
                kind="attempt",
                stage=stage,
                status="created",
                attempt_number=attempt_number,
                time_utc=None,
                message=f"{stage} attempt {attempt_number} created",
                path=_workspace_relative(workspace_root, attempt_root),
            )
        )
        runtime_log = attempt_root / RUN_RUNTIME_LOG_FILENAME
        if runtime_log.exists():
            events.append(
                OperatorTimelineEvent(
                    kind="runtime-log",
                    stage=stage,
                    status="present",
                    attempt_number=attempt_number,
                    time_utc=None,
                    message=f"{stage} attempt {attempt_number} runtime log available",
                    path=_workspace_relative(workspace_root, runtime_log),
                )
            )
        try:
            artifact_index = load_attempt_artifact_index(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                attempt_number=attempt_number,
            )
        except ValueError:
            artifact_index = None
        if artifact_index is not None:
            produced_count = len(artifact_index.documents) + len(artifact_index.logs)
            events.append(
                OperatorTimelineEvent(
                    kind="artifacts",
                    stage=stage,
                    status="indexed",
                    attempt_number=attempt_number,
                    time_utc=None,
                    message=f"{produced_count} artifact reference(s) indexed",
                    path=None,
                )
            )
        events.extend(
            _runtime_events(
                workspace_root=workspace_root,
                attempt_root=attempt_root,
                stage=stage,
                attempt_number=attempt_number,
            )
        )
    return events


def _runtime_events(
    *,
    workspace_root: Path,
    attempt_root: Path,
    stage: str,
    attempt_number: int,
) -> list[OperatorTimelineEvent]:
    events_path = attempt_root / RUN_EVENTS_JSONL_FILENAME
    if not events_path.exists():
        return []
    events: list[OperatorTimelineEvent] = []
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines()[:200]:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        event_name = str(payload.get("event") or payload.get("kind") or "runtime-event")
        events.append(
            OperatorTimelineEvent(
                kind="runtime-event",
                stage=stage,
                status=str(payload.get("status", "")) or None,
                attempt_number=attempt_number,
                time_utc=str(payload.get("time_utc") or payload.get("timestamp") or "") or None,
                message=event_name,
                path=_workspace_relative(workspace_root, events_path),
            )
        )
    return events


def _question_events(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> list[OperatorTimelineEvent]:
    questions_path = workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage) / (
        "questions.md"
    )
    if not questions_path.exists():
        return []
    return [
        OperatorTimelineEvent(
            kind="questions",
            stage=stage,
            status="present",
            attempt_number=None,
            time_utc=None,
            message=f"{stage} questions are available",
            path=_workspace_relative(workspace_root, questions_path),
        )
    ]


def resolve_operator_run_timeline(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str | None = None,
) -> OperatorTimelineView:
    if stage is not None and not is_valid_stage(stage):
        raise ValueError(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}.")
    stages = (stage,) if stage is not None else STAGES
    events: list[OperatorTimelineEvent] = []
    frames: list[OperatorTimelineFrame] = []
    warnings: list[str] = []
    for item in stages:
        frames.extend(
            _stage_attempt_frames(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=item,
            )
        )
        events.extend(
            _metadata_events(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=item,
            )
        )
        events.extend(
            _attempt_events(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=item,
            )
        )
        events.extend(
            _question_events(
                workspace_root=workspace_root,
                work_item=work_item,
                stage=item,
            )
        )
    if stage in {None, "implement"}:
        frames.extend(
            _task_attempt_frames(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
            )
        )
        frames.extend(
            _finalization_frames(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
            )
        )
    frames.extend(_event_marker_frames(events))
    if not events:
        warnings.append("No run timeline events were found.")
    return OperatorTimelineView(
        run_id=run_id,
        stage=stage,
        events=tuple(sorted(events, key=_event_sort_key)),
        frames=tuple(sorted(frames, key=_frame_sort_key)),
        warnings=tuple(warnings),
    )


__all__ = [
    "OperatorTimelineEvent",
    "OperatorTimelineFrame",
    "OperatorTimelineView",
    "resolve_operator_run_timeline",
]
