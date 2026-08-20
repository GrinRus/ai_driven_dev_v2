from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from aidd.core.run_archive import RunArchiveProtocolError, resolve_run_archive_decision
from aidd.core.run_lookup import latest_attempt_number
from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    RUN_RUNTIME_LOG_FILENAME,
    load_attempt_artifact_index,
    load_stage_metadata,
    run_attempt_root,
    run_root,
    run_stage_root,
    work_item_runs_root,
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
    attempt_mode: str = "unknown"
    runtime_id: str | None = None
    started_at_utc: str | None = None
    updated_at_utc: str | None = None
    duration_seconds: float | None = None
    validator_outcome: str | None = None
    first_decisive_failure: str | None = None
    primary_artifact: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    copy_id: str | None = None
    retained: bool = True
    event_message: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorTimelineView:
    run_id: str
    stage: str | None
    events: tuple[OperatorTimelineEvent, ...]
    frames: tuple[OperatorTimelineFrame, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OperatorRunHistoryEntry:
    run_id: str
    work_item: str
    runtime_id: str | None
    adapter_id: str | None
    stage_target: str | None
    status: str
    created_at_utc: str | None
    updated_at_utc: str | None
    attempt_count: int
    retained_attempt_count: int
    attempt_modes: tuple[str, ...]
    archived: bool
    source_run_id: str | None
    source_work_item_id: str | None
    child_work_item_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OperatorRunHistoryView:
    work_item: str
    selected_run_id: str | None
    runs: tuple[OperatorRunHistoryEntry, ...]
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


def _manifest_payload(*, workspace_root: Path, work_item: str, run_id: str) -> dict[str, Any]:
    path = run_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    ) / "run-manifest.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _sha256_paths(paths: tuple[tuple[str, Path], ...]) -> str | None:
    digest = hashlib.sha256()
    included = False
    for label, path in paths:
        file_hash = _sha256_file(path)
        if file_hash is None:
            continue
        included = True
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest() if included else None


def _first_text(payloads: tuple[dict[str, object], ...], keys: tuple[str, ...]) -> str | None:
    for payload in payloads:
        for key in keys:
            value = payload.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
    return None


def _duration_seconds(
    payloads: tuple[dict[str, object], ...],
    *,
    started_at_utc: str | None,
    updated_at_utc: str | None,
) -> float | None:
    for payload in payloads:
        for key in ("duration_seconds", "elapsed_seconds", "duration"):
            value = payload.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return max(0.0, float(value))
    if not started_at_utc or not updated_at_utc:
        return None
    try:
        from datetime import datetime

        started = datetime.fromisoformat(started_at_utc.replace("Z", "+00:00"))
        updated = datetime.fromisoformat(updated_at_utc.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0.0, (updated - started).total_seconds())


def _validator_outcome(
    *, stage_root: Path, attempt_root: Path, payloads: tuple[dict[str, object], ...]
) -> str | None:
    explicit = _first_text(
        payloads,
        ("validator_outcome", "validator_status", "validation_status", "verdict"),
    )
    if explicit:
        return explicit
    for path in (attempt_root / "validator-report.md", stage_root / "validator-report.md"):
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match = re.search(r"(?:verdict|status)\s*:\s*`?([A-Za-z][A-Za-z -]*)", text, re.I)
        if match:
            return match.group(1).strip().lower()
    return None


def _frame_metadata(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    frame: OperatorTimelineFrame,
    manifest: dict[str, Any],
) -> OperatorTimelineFrame:
    if frame.kind == "event-marker" or frame.attempt_number is None or frame.stage is None:
        return replace(
            frame,
            runtime_id=str(manifest.get("runtime_id", "")).strip() or None,
        )
    if frame.kind == "task-attempt":
        attempt_root = (
            run_stage_root(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage="implement",
            )
            / "tasks"
            / str(frame.task_id)
            / "attempts"
            / f"attempt-{frame.attempt_number:04d}"
        )
    elif frame.kind == "finalization-attempt":
        attempt_root = (
            run_stage_root(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage="implement",
            )
            / "finalization"
            / "attempts"
            / f"attempt-{frame.attempt_number:04d}"
        )
    else:
        attempt_root = run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=frame.stage,
            attempt_number=frame.attempt_number,
        )
    state = _state_payload(attempt_root / "attempt-state.json")
    finalization_state = _state_payload(attempt_root / "finalization-state.json")
    runtime_exit = _state_payload(attempt_root / "runtime-exit.json")
    artifact_index = _state_payload(attempt_root / "artifact-index.json")
    payloads = (state, finalization_state, runtime_exit, artifact_index, manifest)
    started_at = _first_text(
        payloads,
        ("started_at_utc", "created_at_utc", "start_time_utc", "started_at"),
    )
    updated_at = _first_text(
        payloads,
        ("updated_at_utc", "completed_at_utc", "finished_at_utc", "ended_at_utc"),
    ) or frame.time_utc
    documents = artifact_index.get("documents")
    document_paths: tuple[tuple[str, Path], ...] = ()
    if isinstance(documents, dict):
        document_paths = tuple(
            (str(key), workspace_root / str(path))
            for key, path in sorted(documents.items())
            if isinstance(path, str) and "input" not in str(key).lower()
        )
    input_bundle = attempt_root / "input-bundle.md"
    input_hash = _first_text(
        payloads,
        ("input_hash", "input_sha256", "input_bundle_sha256"),
    ) or _sha256_file(input_bundle)
    output_hash = _first_text(payloads, ("output_hash", "output_sha256")) or _sha256_paths(
        document_paths
    )
    first_failure = _first_text(
        payloads,
        ("first_decisive_failure", "failure", "stop_reason", "exit_classification"),
    )
    if first_failure and first_failure.lower() in {"success", "succeeded", "none", "null"}:
        first_failure = None
    primary_artifact = _first_text(payloads, ("primary_artifact", "primary_artifact_path"))
    if primary_artifact is None and document_paths:
        primary_artifact = next(
            (
                _workspace_relative(workspace_root, path)
                for _, path in document_paths
                if path.exists()
            ),
            None,
        )
    return replace(
        frame,
        attempt_mode=str(artifact_index.get("attempt_mode", "unknown")) or "unknown",
        runtime_id=str(manifest.get("runtime_id", "")).strip() or None,
        started_at_utc=started_at,
        updated_at_utc=updated_at,
        duration_seconds=_duration_seconds(
            payloads,
            started_at_utc=started_at,
            updated_at_utc=updated_at,
        ),
        validator_outcome=_validator_outcome(
            stage_root=attempt_root.parent.parent,
            attempt_root=attempt_root,
            payloads=payloads,
        ),
        first_decisive_failure=first_failure,
        primary_artifact=primary_artifact,
        input_hash=input_hash,
        output_hash=output_hash,
        copy_id=_first_text(payloads, ("copy_id", "revision_id", "attempt_id")),
        retained=attempt_root.exists(),
    )


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
                event_message=event.message,
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
        except (KeyError, TypeError, ValueError):
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
        event_name = str(
            payload.get("event_kind")
            or payload.get("event")
            or payload.get("kind")
            or "runtime-event"
        )
        events.append(
            OperatorTimelineEvent(
                kind="runtime-event",
                stage=stage,
                status=str(payload.get("outcome") or payload.get("status") or "") or None,
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
    manifest = _manifest_payload(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    frames = [
        _frame_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            frame=frame,
            manifest=manifest,
        )
        for frame in frames
    ]
    if not events:
        warnings.append("No run timeline events were found.")
    return OperatorTimelineView(
        run_id=run_id,
        stage=stage,
        events=tuple(sorted(events, key=_event_sort_key)),
        frames=tuple(sorted(frames, key=_frame_sort_key)),
        warnings=tuple(warnings),
    )


def _history_run_status(frames: tuple[OperatorTimelineFrame, ...]) -> str:
    primary = tuple(frame for frame in frames if frame.kind != "event-marker")
    statuses = {frame.status.strip().lower() for frame in primary}
    if statuses & {"running", "executing", "pending", "waiting-for-operator"}:
        return "running"
    if statuses & {"failed", "blocked", "cancelled", "timeout"}:
        return "failed"
    if statuses & {"succeeded", "success", "completed", "done", "passed"}:
        return "completed"
    return "unknown" if primary else "created"


def resolve_operator_run_history(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str | None = None,
    status: str | None = None,
    attempt_mode: str | None = None,
) -> OperatorRunHistoryView:
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    warnings: list[str] = []
    entries: list[OperatorRunHistoryEntry] = []
    if runs_root.exists() and not runs_root.is_dir():
        warnings.append("Run history root is unavailable; no runs were listed.")
        return OperatorRunHistoryView(work_item, None, (), tuple(warnings))
    candidates = (
        sorted(runs_root.iterdir(), key=lambda path: path.name)
        if runs_root.exists()
        else ()
    )
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        candidate_id = candidate.name
        manifest = _manifest_payload(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=candidate_id,
        )
        if not manifest:
            warnings.append(
                f"Run {candidate_id} is unavailable because its manifest is missing or malformed."
            )
            continue
        timeline = resolve_operator_run_timeline(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=candidate_id,
        )
        primary_frames = tuple(frame for frame in timeline.frames if frame.kind != "event-marker")
        modes = tuple(
            dict.fromkeys(
                frame.attempt_mode for frame in primary_frames if frame.attempt_mode
            )
        )
        if attempt_mode and attempt_mode not in modes:
            continue
        run_status = _history_run_status(primary_frames)
        if status and run_status != status:
            continue
        lineage = manifest.get("lineage")
        lineage_payload = lineage if isinstance(lineage, dict) else {}
        raw_children = lineage_payload.get("child_work_item_candidates")
        child_ids = tuple(
            str(child.get("work_item_id"))
            for child in raw_children
            if isinstance(child, dict) and str(child.get("work_item_id", "")).strip()
        ) if isinstance(raw_children, list) else ()
        try:
            archive = resolve_run_archive_decision(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=candidate_id,
                manifest_payload=manifest,
            )
        except RunArchiveProtocolError as exc:
            warnings.append(f"Run {candidate_id} archive state is malformed: {exc}")
            archive = None
        entries.append(
            OperatorRunHistoryEntry(
                run_id=candidate_id,
                work_item=work_item,
                runtime_id=str(manifest.get("runtime_id", "")).strip() or None,
                adapter_id=str(manifest.get("adapter_id", "")).strip() or None,
                stage_target=str(manifest.get("stage_target", "")).strip() or None,
                status=run_status,
                created_at_utc=str(manifest.get("created_at_utc", "")).strip() or None,
                updated_at_utc=str(manifest.get("updated_at_utc", "")).strip() or None,
                attempt_count=len(primary_frames),
                retained_attempt_count=sum(1 for frame in primary_frames if frame.retained),
                attempt_modes=modes,
                archived=archive is not None,
                source_run_id=str(lineage_payload.get("source_run_id", "")).strip() or None,
                source_work_item_id=(
                    str(lineage_payload.get("source_work_item_id", "")).strip() or None
                ),
                child_work_item_ids=child_ids,
            )
        )
    entries.sort(key=lambda entry: (entry.updated_at_utc or "", entry.run_id), reverse=True)
    selected = (
        run_id
        if any(entry.run_id == run_id for entry in entries)
        else (entries[0].run_id if entries else None)
    )
    if run_id and selected is None:
        warnings.append(f"Run {run_id} is not retained in this Work Item history.")
    return OperatorRunHistoryView(
        work_item=work_item,
        selected_run_id=selected,
        runs=tuple(entries),
        warnings=tuple(warnings),
    )


__all__ = [
    "OperatorTimelineEvent",
    "OperatorTimelineFrame",
    "OperatorTimelineView",
    "OperatorRunHistoryEntry",
    "OperatorRunHistoryView",
    "resolve_operator_run_history",
    "resolve_operator_run_timeline",
]
