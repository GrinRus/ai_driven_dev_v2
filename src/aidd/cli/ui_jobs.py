from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from aidd.cli.ui_job_evidence import (
    UiJobEvidenceStatus,
    build_ui_job_terminal_evidence,
)
from aidd.core.operator_frontend import OperatorInboxRoute, OperatorInboxView
from aidd.core.stages import STAGES

_CANCELLED_JOB_EXIT_CODE = 130
_TERMINAL_JOB_STATUSES = frozenset({"cancelled", "completed", "failed"})
_DEFAULT_UI_JOB_LIVE_LOG_BYTES = 1024 * 1024
_DEFAULT_UI_JOB_LOG_RESPONSE_BYTES = 256 * 1024
_DEFAULT_UI_TERMINAL_JOB_COUNT = 64
_DEFAULT_UI_TERMINAL_JOB_TTL_SECONDS = 60 * 60


def _is_runtime_log_stream(stream: str) -> bool:
    return (stream.strip().lower() or "stdout") != "system"


@dataclass(slots=True)
class _UiStoredChunk:
    sequence: int
    stream: str
    data: bytes
    time_utc: str
    start_cursor: int
    end_cursor: int
    truncated: bool = False
    dropped_bytes: int = 0


@dataclass(slots=True)
class _UiRunJob:
    job_id: str
    kind: str
    stage: str | None
    status: str
    created_at_utc: str
    updated_at_utc: str
    ordinal: int
    work_item: str | None = None
    run_id: str | None = None
    project_root: str | None = None
    workspace_root: str | None = None
    exit_code: int | None = None
    message: str = ""
    result: object | None = None
    attempt_path: str | None = None
    cancel_requested_at_utc: str | None = None
    cancelled_at_utc: str | None = None
    last_output_at_utc: str | None = None
    last_output_text: str | None = None
    runtime_output_at_utc: str | None = None
    runtime_output_text: str | None = None
    runtime_log_chunk_count: int = 0
    chunks: deque[_UiStoredChunk] = field(default_factory=deque)
    retained_chunk_bytes: int = 0
    dropped_chunk_bytes: int = 0
    next_chunk_cursor: int = 0
    next_chunk_sequence: int = 1
    terminal_evidence: dict[str, object] | None = None
    operator_wait_result: object | None = None


@dataclass(frozen=True, slots=True)
class UiJobSummary:
    job_id: str
    kind: str
    status: str
    work_item: str | None
    run_id: str | None
    stage: str | None
    project_root: str | None
    workspace_root: str | None
    created_at_utc: str
    updated_at_utc: str
    ordinal: int
    message: str
    last_output_at_utc: str | None
    last_output_text: str | None


@dataclass(frozen=True, slots=True)
class UiRunningNowItem:
    job_id: str
    kind: str
    status: str
    identity_status: str
    route: OperatorInboxRoute | None
    project_root: str | None
    workspace_root: str | None
    created_at_utc: str
    updated_at_utc: str
    message: str
    last_output_at_utc: str | None
    last_output_text: str | None


@dataclass(frozen=True, slots=True)
class UiInboxComposition:
    durable: OperatorInboxView
    running_now: tuple[UiRunningNowItem, ...]


def compose_operator_inbox_with_jobs(
    inbox: OperatorInboxView,
    jobs: tuple[UiJobSummary, ...],
    *,
    max_running_jobs: int = 32,
) -> UiInboxComposition:
    if max_running_jobs <= 0:
        raise ValueError("Running-now job limit must be greater than zero.")
    running: list[UiRunningNowItem] = []
    for job in sorted(jobs, key=lambda item: item.ordinal):
        if job.status in _TERMINAL_JOB_STATUSES:
            continue
        route = (
            OperatorInboxRoute(
                intent="inbox-work-item",
                work_item=job.work_item,
                run_id=job.run_id,
                stage=job.stage or STAGES[0],
            )
            if job.work_item is not None and job.run_id is not None
            else None
        )
        running.append(
            UiRunningNowItem(
                job_id=job.job_id,
                kind=job.kind,
                status=job.status,
                identity_status="correlated" if route is not None else "unavailable",
                route=route,
                project_root=job.project_root,
                workspace_root=job.workspace_root,
                created_at_utc=job.created_at_utc,
                updated_at_utc=job.updated_at_utc,
                message=job.message,
                last_output_at_utc=job.last_output_at_utc,
                last_output_text=job.last_output_text,
            )
        )
    running_now = tuple(running[-max_running_jobs:])
    return UiInboxComposition(durable=inbox, running_now=running_now)


class UiRunJobStore:
    def __init__(
        self,
        *,
        max_live_log_bytes: int = _DEFAULT_UI_JOB_LIVE_LOG_BYTES,
        max_log_response_bytes: int = _DEFAULT_UI_JOB_LOG_RESPONSE_BYTES,
        max_terminal_jobs: int = _DEFAULT_UI_TERMINAL_JOB_COUNT,
        terminal_job_ttl_seconds: int = _DEFAULT_UI_TERMINAL_JOB_TTL_SECONDS,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if max_live_log_bytes <= 0:
            raise ValueError("UI live-log byte limit must be greater than zero.")
        if max_log_response_bytes < 4:
            raise ValueError("UI log-response byte limit must be at least four bytes.")
        if max_terminal_jobs < 0:
            raise ValueError("UI terminal-job count limit must not be negative.")
        if terminal_job_ttl_seconds < 0:
            raise ValueError("UI terminal-job TTL must not be negative.")
        self._lock = threading.Lock()
        self._jobs: dict[str, _UiRunJob] = {}
        self._max_live_log_bytes = max_live_log_bytes
        self._max_log_response_bytes = max_log_response_bytes
        self._max_terminal_jobs = max_terminal_jobs
        self._terminal_job_ttl_seconds = terminal_job_ttl_seconds
        self._now = now or (lambda: datetime.now(UTC))
        self._next_job_ordinal = 1

    def create(
        self,
        *,
        kind: str,
        stage: str | None,
        work_item: str | None = None,
        run_id: str | None = None,
        project_root: Path | None = None,
        workspace_root: Path | None = None,
    ) -> str:
        job_id = f"job-{uuid4().hex}"
        with self._lock:
            now = self._now_utc()
            self._evict_terminal_locked(now)
            timestamp = _format_utc_timestamp(now)
            self._jobs[job_id] = _UiRunJob(
                job_id=job_id,
                kind=kind,
                stage=stage,
                status="running",
                created_at_utc=timestamp,
                updated_at_utc=timestamp,
                ordinal=self._next_job_ordinal,
                work_item=work_item,
                run_id=run_id,
                project_root=(
                    project_root.resolve(strict=False).as_posix()
                    if project_root is not None
                    else None
                ),
                workspace_root=(
                    workspace_root.resolve(strict=False).as_posix()
                    if workspace_root is not None
                    else None
                ),
            )
            self._next_job_ordinal += 1
        return job_id

    def append_chunk(self, job_id: str, *, stream: str, text: str) -> None:
        if not text:
            return
        with self._lock:
            job = self._require_job(job_id)
            self._append_chunk_locked(job, stream=stream, text=text)
            job.updated_at_utc = self._timestamp()

    def complete(
        self,
        job_id: str,
        *,
        result: object,
        exit_code: int,
        message: str,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)
            if job.status == "cancelling":
                self._mark_cancelled_locked(
                    job,
                    message="cancelled after runtime job returned",
                )
                return
            if job.status in _TERMINAL_JOB_STATUSES:
                self._refresh_terminal_evidence_locked(job)
                return
            job.status = "completed" if exit_code == 0 else "failed"
            job.exit_code = exit_code
            job.result = result
            job.message = message
            job.updated_at_utc = self._timestamp()
            self._refresh_terminal_evidence_locked(job)
            self._evict_terminal_locked(self._now_utc())

    def fail(self, job_id: str, *, message: str, exit_code: int = 1) -> None:
        with self._lock:
            job = self._require_job(job_id)
            if job.status == "cancelling":
                self._mark_cancelled_locked(
                    job,
                    message="cancelled after runtime job failed",
                )
                return
            if job.status in _TERMINAL_JOB_STATUSES:
                self._refresh_terminal_evidence_locked(job)
                return
            job.status = "failed"
            job.exit_code = exit_code
            job.message = message
            job.updated_at_utc = self._timestamp()
            self._refresh_terminal_evidence_locked(job)
            self._evict_terminal_locked(self._now_utc())

    def wait_for_operator(
        self,
        job_id: str,
        *,
        result: object,
        message: str,
        exit_code: int | None = None,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)
            if job.status == "cancelling":
                self._mark_cancelled_locked(
                    job,
                    message="cancelled before operator wait",
                )
                return
            if job.status in _TERMINAL_JOB_STATUSES:
                return
            job.status = "waiting-for-operator"
            job.exit_code = exit_code
            job.result = result
            job.operator_wait_result = result
            job.message = message
            job.updated_at_utc = self._timestamp()
            self._refresh_terminal_evidence_locked(job)

    def mark_running(self, job_id: str, *, message: str = "running") -> None:
        with self._lock:
            job = self._require_job(job_id)
            if job.status in {"cancelling", *_TERMINAL_JOB_STATUSES}:
                return
            job.status = "running"
            job.exit_code = None
            job.result = None
            job.message = message
            job.updated_at_utc = self._timestamp()
            job.terminal_evidence = None

    def set_attempt_path(self, job_id: str, attempt_path: Path) -> None:
        with self._lock:
            job = self._require_job(job_id)
            job.attempt_path = attempt_path.as_posix()
            job.updated_at_utc = self._timestamp()
            if job.status in {
                "cancelled",
                "completed",
                "failed",
                "waiting-for-operator",
            }:
                self._refresh_terminal_evidence_locked(job)

    def correlate(
        self,
        job_id: str,
        *,
        work_item: str | None = None,
        run_id: str | None = None,
        stage: str | None = None,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)
            for name, current, proposed in (
                ("work_item", job.work_item, work_item),
                ("run_id", job.run_id, run_id),
                ("stage", job.stage, stage),
            ):
                if current is not None and proposed is not None and current != proposed:
                    raise ValueError(
                        f"UI job '{job_id}' {name} identity cannot change from "
                        f"'{current}' to '{proposed}'."
                    )
            job.work_item = job.work_item or work_item
            job.run_id = job.run_id or run_id
            job.stage = job.stage or stage
            job.updated_at_utc = self._timestamp()

    def cancel(self, job_id: str) -> dict[str, object]:
        with self._lock:
            job = self._require_job(job_id)
            previous_status = job.status
            if previous_status in _TERMINAL_JOB_STATUSES:
                payload = self._view_locked(job)
                payload.update(
                    {
                        "already_finished": True,
                        "cancel_state": "already-finished",
                        "previous_status": previous_status,
                    }
                )
                return payload

            timestamp = self._timestamp()
            if job.cancel_requested_at_utc is None:
                job.cancel_requested_at_utc = timestamp
            if previous_status == "waiting-for-operator":
                self._append_chunk_locked(
                    job,
                    stream="system",
                    text="[ui] cancel requested while waiting for operator.\n",
                )
                self._mark_cancelled_locked(
                    job,
                    message="cancelled while waiting for operator",
                )
            else:
                if previous_status != "cancelling":
                    self._append_chunk_locked(
                        job,
                        stream="system",
                        text="[ui] cancel requested.\n",
                    )
                job.status = "cancelling"
                job.message = "cancel requested"
                job.updated_at_utc = timestamp

            payload = self._view_locked(job)
            payload.update(
                {
                    "already_finished": False,
                    "previous_status": previous_status,
                }
            )
            self._evict_terminal_locked(self._now_utc())
            return payload

    def cancel_requested(self, job_id: str) -> bool:
        with self._lock:
            job = self._require_job(job_id)
            return job.cancel_requested_at_utc is not None

    def view(self, job_id: str) -> dict[str, object]:
        with self._lock:
            self._evict_terminal_locked(self._now_utc())
            job = self._require_job(job_id)
            if job.status in {
                "cancelled",
                "completed",
                "failed",
                "waiting-for-operator",
            }:
                self._refresh_terminal_evidence_locked(job)
            return self._view_locked(job)

    def logs(self, job_id: str, *, cursor: int) -> dict[str, object]:
        with self._lock:
            self._evict_terminal_locked(self._now_utc())
            job = self._require_job(job_id)
            requested_cursor = min(max(cursor, 0), job.next_chunk_cursor)
            oldest_cursor = job.chunks[0].start_cursor if job.chunks else job.next_chunk_cursor
            response_cursor = max(requested_cursor, oldest_cursor)
            truncated = response_cursor != requested_cursor
            remaining_budget = self._max_log_response_bytes
            response_chunks: list[dict[str, object]] = []
            for chunk in job.chunks:
                if chunk.end_cursor <= response_cursor:
                    continue
                raw_offset = max(0, response_cursor - chunk.start_cursor)
                remaining_data = chunk.data[raw_offset:]
                normalized_data = remaining_data.decode("utf-8", errors="ignore").encode("utf-8")
                fragment_start = chunk.end_cursor - len(normalized_data)
                if fragment_start > response_cursor:
                    truncated = True
                    response_cursor = fragment_start
                fragment = _utf8_prefix(normalized_data, remaining_budget)
                if not fragment:
                    break
                fragment_end = response_cursor + len(fragment)
                payload: dict[str, object] = {
                    "sequence": chunk.sequence,
                    "stream": chunk.stream,
                    "text": fragment.decode("utf-8"),
                    "time_utc": chunk.time_utc,
                    "start_cursor": response_cursor,
                    "end_cursor": fragment_end,
                    "partial": (
                        response_cursor > chunk.start_cursor or fragment_end < chunk.end_cursor
                    ),
                }
                if chunk.truncated:
                    payload["truncated"] = True
                    payload["dropped_bytes"] = chunk.dropped_bytes
                response_chunks.append(payload)
                remaining_budget -= len(fragment)
                response_cursor = fragment_end
                if remaining_budget == 0:
                    break
            return {
                "job_id": job.job_id,
                "cursor": response_cursor,
                "oldest_cursor": oldest_cursor,
                "truncated": truncated,
                "dropped_bytes": job.dropped_chunk_bytes,
                "has_more": response_cursor < job.next_chunk_cursor,
                "chunks": tuple(response_chunks),
            }

    def has_active_jobs(self) -> bool:
        with self._lock:
            self._evict_terminal_locked(self._now_utc())
            return any(job.status not in _TERMINAL_JOB_STATUSES for job in self._jobs.values())

    def active_job(self) -> dict[str, object] | None:
        with self._lock:
            self._evict_terminal_locked(self._now_utc())
            for job in reversed(tuple(self._jobs.values())):
                if job.status not in _TERMINAL_JOB_STATUSES:
                    return self._view_locked(job)
        return None

    def active_job_for_context(
        self,
        *,
        project_root: Path,
        workspace_root: Path,
    ) -> dict[str, object] | None:
        """Return the newest active job owned by the selected project context."""
        expected_project = project_root.resolve(strict=False).as_posix()
        expected_workspace = workspace_root.resolve(strict=False).as_posix()
        with self._lock:
            self._evict_terminal_locked(self._now_utc())
            for job in reversed(tuple(self._jobs.values())):
                if job.status in _TERMINAL_JOB_STATUSES:
                    continue
                if (
                    job.project_root == expected_project
                    and job.workspace_root == expected_workspace
                ):
                    return self._view_locked(job)
        return None

    def summaries(self) -> tuple[UiJobSummary, ...]:
        with self._lock:
            self._evict_terminal_locked(self._now_utc())
            return tuple(self._summary_locked(job) for job in self._jobs.values())

    def _require_job(self, job_id: str) -> _UiRunJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise ValueError(f"Unknown UI job '{job_id}'.") from exc

    def _append_chunk_locked(self, job: _UiRunJob, *, stream: str, text: str) -> None:
        timestamp = self._timestamp()
        original_data = text.encode("utf-8")
        end_cursor = job.next_chunk_cursor + len(original_data)
        retained_data = original_data
        dropped_bytes = 0
        if len(retained_data) > self._max_live_log_bytes:
            retained_data = _utf8_tail(retained_data, self._max_live_log_bytes)
            dropped_bytes = len(original_data) - len(retained_data)
            job.dropped_chunk_bytes += dropped_bytes
        start_cursor = end_cursor - len(retained_data)
        job.chunks.append(
            _UiStoredChunk(
                sequence=job.next_chunk_sequence,
                stream=stream,
                data=retained_data,
                time_utc=timestamp,
                start_cursor=start_cursor,
                end_cursor=end_cursor,
                truncated=dropped_bytes > 0,
                dropped_bytes=dropped_bytes,
            )
        )
        job.next_chunk_sequence += 1
        job.next_chunk_cursor = end_cursor
        job.retained_chunk_bytes += len(retained_data)
        while job.retained_chunk_bytes > self._max_live_log_bytes:
            evicted = job.chunks.popleft()
            job.retained_chunk_bytes -= len(evicted.data)
            job.dropped_chunk_bytes += len(evicted.data)
        job.last_output_at_utc = timestamp
        job.last_output_text = text.strip().splitlines()[-1] if text.strip() else None
        if _is_runtime_log_stream(stream):
            job.runtime_output_at_utc = timestamp
            job.runtime_output_text = job.last_output_text
            job.runtime_log_chunk_count += 1

    def _mark_cancelled_locked(self, job: _UiRunJob, *, message: str) -> None:
        timestamp = self._timestamp()
        if job.cancel_requested_at_utc is None:
            job.cancel_requested_at_utc = timestamp
        job.status = "cancelled"
        job.exit_code = _CANCELLED_JOB_EXIT_CODE
        job.result = None
        job.message = message
        job.cancelled_at_utc = timestamp
        job.updated_at_utc = timestamp
        self._refresh_terminal_evidence_locked(job)

    @staticmethod
    def _refresh_terminal_evidence_locked(job: _UiRunJob) -> None:
        if job.status not in {
            "cancelled",
            "completed",
            "failed",
            "waiting-for-operator",
        }:
            job.terminal_evidence = None
            return
        evidence = build_ui_job_terminal_evidence(
            work_item=job.work_item,
            run_id=job.run_id,
            stage=job.stage,
            status=cast(UiJobEvidenceStatus, job.status),
            exit_code=job.exit_code,
            message=job.message,
            result=job.result,
            operator_wait_result=job.operator_wait_result,
            attempt_path=Path(job.attempt_path) if job.attempt_path is not None else None,
            cancel_requested_at_utc=job.cancel_requested_at_utc,
            cancelled_at_utc=job.cancelled_at_utc,
        )
        job.terminal_evidence = evidence.to_payload()

    def _view_locked(self, job: _UiRunJob) -> dict[str, object]:
        if job.status == "cancelled":
            cancel_state = "cancelled"
        elif job.cancel_requested_at_utc is not None:
            cancel_state = "cancelling"
        else:
            cancel_state = "none"
        last_output_age_seconds = self._seconds_since(job.last_output_at_utc)
        runtime_output_age_seconds = self._seconds_since(job.runtime_output_at_utc)
        elapsed_seconds = self._seconds_since(job.created_at_utc)
        silence_warning = job.status not in _TERMINAL_JOB_STATUSES and (
            (runtime_output_age_seconds is not None and runtime_output_age_seconds >= 120)
            or (
                job.runtime_output_at_utc is None
                and elapsed_seconds is not None
                and elapsed_seconds >= 120
            )
        )
        return {
            "job_id": job.job_id,
            "kind": job.kind,
            "work_item": job.work_item,
            "run_id": job.run_id,
            "stage": job.stage,
            "project_root": job.project_root,
            "workspace_root": job.workspace_root,
            "status": job.status,
            "exit_code": job.exit_code,
            "message": job.message,
            "result": job.result,
            "attempt_path": job.attempt_path,
            "created_at_utc": job.created_at_utc,
            "updated_at_utc": job.updated_at_utc,
            "elapsed_seconds": elapsed_seconds,
            "last_output_at_utc": job.last_output_at_utc,
            "last_output_age_seconds": last_output_age_seconds,
            "last_output_text": job.last_output_text,
            "runtime_output_at_utc": job.runtime_output_at_utc,
            "runtime_output_age_seconds": runtime_output_age_seconds,
            "runtime_output_text": job.runtime_output_text,
            "runtime_log_chunk_count": job.runtime_log_chunk_count,
            "retained_live_log_bytes": job.retained_chunk_bytes,
            "dropped_live_log_bytes": job.dropped_chunk_bytes,
            "oldest_live_log_cursor": (
                job.chunks[0].start_cursor if job.chunks else job.next_chunk_cursor
            ),
            "silence_warning": silence_warning,
            "cancel_requested": job.cancel_requested_at_utc is not None,
            "cancel_requested_at_utc": job.cancel_requested_at_utc,
            "cancelled_at_utc": job.cancelled_at_utc,
            "cancel_state": cancel_state,
            "terminal_evidence": job.terminal_evidence,
        }

    @staticmethod
    def _summary_locked(job: _UiRunJob) -> UiJobSummary:
        return UiJobSummary(
            job_id=job.job_id,
            kind=job.kind,
            status=job.status,
            work_item=job.work_item,
            run_id=job.run_id,
            stage=job.stage,
            project_root=job.project_root,
            workspace_root=job.workspace_root,
            created_at_utc=job.created_at_utc,
            updated_at_utc=job.updated_at_utc,
            ordinal=job.ordinal,
            message=job.message,
            last_output_at_utc=job.last_output_at_utc,
            last_output_text=job.last_output_text,
        )

    def _timestamp(self) -> str:
        return _format_utc_timestamp(self._now_utc())

    def _now_utc(self) -> datetime:
        value = self._now()
        if value.tzinfo is None:
            raise ValueError("UI job-store clock must return a timezone-aware datetime.")
        return value.astimezone(UTC)

    def _seconds_since(self, value: str | None) -> int | None:
        timestamp = _parse_utc_timestamp(value)
        if timestamp is None:
            return None
        return max(0, int((self._now_utc() - timestamp).total_seconds()))

    def _evict_terminal_locked(self, now: datetime) -> None:
        terminal_jobs = [job for job in self._jobs.values() if job.status in _TERMINAL_JOB_STATUSES]
        for job in terminal_jobs:
            updated_at = _parse_utc_timestamp(job.updated_at_utc)
            if (
                updated_at is not None
                and (now - updated_at).total_seconds() >= self._terminal_job_ttl_seconds
            ):
                self._jobs.pop(job.job_id, None)
        retained_terminal = sorted(
            (job for job in self._jobs.values() if job.status in _TERMINAL_JOB_STATUSES),
            key=lambda job: (
                _parse_utc_timestamp(job.updated_at_utc) or datetime.min.replace(tzinfo=UTC),
                job.ordinal,
            ),
        )
        excess = len(retained_terminal) - self._max_terminal_jobs
        for job in retained_terminal[: max(0, excess)]:
            self._jobs.pop(job.job_id, None)


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _utf8_tail(data: bytes, limit: int) -> bytes:
    if len(data) <= limit:
        return data
    return data[-limit:].decode("utf-8", errors="ignore").encode("utf-8")


def _utf8_prefix(data: bytes, limit: int) -> bytes:
    if limit <= 0:
        return b""
    if len(data) <= limit:
        return data
    return data[:limit].decode("utf-8", errors="ignore").encode("utf-8")


def _parse_utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


__all__ = [
    "UiInboxComposition",
    "UiJobSummary",
    "UiRunJobStore",
    "UiRunningNowItem",
    "compose_operator_inbox_with_jobs",
]
