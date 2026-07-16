from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import tomllib
from collections import deque
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import ThreadingHTTPServer

# ruff: noqa: E501
from ipaddress import ip_address
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import uuid4

import typer

from aidd import __version__
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.application.implementation import aggregate_finalization_port
from aidd.cli.stage_run import (
    StageInteractOptions,
    StageRunOptions,
    run_stage_attempt_command,
    run_stage_command,
    run_stage_interact_command,
)
from aidd.cli.support import (
    _execution_command_available,
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    console,
)
from aidd.cli.ui_assets import operator_static_asset_for_route
from aidd.cli.ui_http import (
    UiResponse,
    _error_response,
    _json_response,
)
from aidd.cli.ui_routing import OperatorUiRouter, UiJobDecisionConflict, handler_for
from aidd.config import AiddConfig, load_config
from aidd.core.implementation_eligibility import implementation_finalization_blocker
from aidd.core.implementation_service import (
    AggregateFinalizer,
    ImplementationExecutionRequest,
    ImplementationExecutionService,
    TaskAttemptOutcome,
)
from aidd.core.interview import AnswerResolution
from aidd.core.mutation_lease import (
    acquire_run_mutation_lease,
    acquire_run_mutation_lease_handle,
    release_run_mutation_lease,
    use_transferred_run_mutation_lease,
)
from aidd.core.next_flow import (
    CloneFlowDraftRequest,
    FollowUpDraftRequest,
    FollowUpSourceSelection,
    NextFlowLaunchPreflightRequest,
    create_clone_flow_draft,
    create_follow_up_work_item_draft,
    validate_next_flow_launch_preflight,
)
from aidd.core.onboarding import (
    OnboardingProjectDeclaration,
    OnboardingProjectSummary,
    OnboardingService,
    OnboardingWorkItemSummary,
)
from aidd.core.operator_frontend import (
    persist_operator_answer,
    resolve_operator_artifact_document_content,
    resolve_operator_artifacts_view,
    resolve_operator_dashboard_view,
    resolve_operator_evidence_graph_view,
    resolve_operator_project_home_view,
    resolve_operator_questions_view,
    resolve_operator_run_log_view,
    resolve_operator_run_view,
    resolve_operator_stage_document_workbench,
    resolve_operator_stage_view,
)
from aidd.core.operator_reports import (
    resolve_implementation_evidence,
    resolve_qa_verdict,
    resolve_review_findings,
)
from aidd.core.operator_timeline import resolve_operator_run_timeline
from aidd.core.remediation import (
    clear_stale_stages,
    create_remediation_request,
    list_remediation_requests,
    load_remediation_status,
    mark_downstream_stale,
)
from aidd.core.repository_diff import resolve_repository_diff
from aidd.core.run_accountability import resolve_run_accountability
from aidd.core.run_comparison import resolve_run_comparison
from aidd.core.run_lookup import latest_run_id as resolve_latest_run_id
from aidd.core.run_store import (
    next_attempt_number,
    persist_run_archive_decision,
    run_attempt_root,
    run_manifest_path,
    run_root,
)
from aidd.core.runtime_operator import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    OperatorDecisionConflict,
    RuntimeOperatorDecision,
    RuntimeOperatorRequest,
    load_operator_decisions,
    load_operator_requests,
    pending_operator_request_ids,
    resolve_operator_decision,
    unapproved_operator_request_ids,
)
from aidd.core.runtime_readiness import (
    RuntimeCommandSource,
    RuntimeReadinessProbeReport,
    resolve_runtime_readiness,
)
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.task_attempt_lifecycle import TaskExecutionContext
from aidd.core.task_read_model import resolve_task_read_model
from aidd.core.task_repository_evidence import task_validation_findings
from aidd.core.workflow_service import (
    WorkflowRunRequest,
    WorkflowRunResult,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
    allocate_workflow_run_id,
    run_workflow,
)
from aidd.runtime_catalog import runtime_definitions
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
)

WorkflowRunner = Callable[..., WorkflowRunResult]
StageRunner = Callable[[StageRunOptions], None]
StageInteractRunner = Callable[[StageInteractOptions], None]
ReadinessProbeProvider = Callable[[AiddConfig], Mapping[str, RuntimeReadinessProbeReport]]
LocalFolderOpener = Callable[[Path], None]

_CANCELLED_JOB_EXIT_CODE = 130
_TERMINAL_JOB_STATUSES = frozenset({"cancelled", "completed", "failed"})
_DEFAULT_UI_JOB_LIVE_LOG_BYTES = 1024 * 1024
_DEFAULT_UI_JOB_LOG_RESPONSE_BYTES = 256 * 1024
_DEFAULT_UI_TERMINAL_JOB_COUNT = 64
_DEFAULT_UI_TERMINAL_JOB_TTL_SECONDS = 60 * 60


def _is_runtime_log_stream(stream: str) -> bool:
    return (stream.strip().lower() or "stdout") != "system"


@dataclass(frozen=True, slots=True)
class UiServerOptions:
    work_item: str | None
    root: Path
    config: Path
    host: str
    port: int
    allow_remote_approvals: bool = False


@dataclass(frozen=True, slots=True)
class UiProjectContext:
    work_item: str
    root: Path
    config: Path
    project_root: Path


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

    def create(self, *, kind: str, stage: str | None) -> str:
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
                return
            job.status = "completed" if exit_code == 0 else "failed"
            job.exit_code = exit_code
            job.result = result
            job.message = message
            job.updated_at_utc = self._timestamp()
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
                return
            job.status = "failed"
            job.exit_code = exit_code
            job.message = message
            job.updated_at_utc = self._timestamp()
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
            job.message = message
            job.updated_at_utc = self._timestamp()

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

    def set_attempt_path(self, job_id: str, attempt_path: Path) -> None:
        with self._lock:
            job = self._require_job(job_id)
            job.attempt_path = attempt_path.as_posix()
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
            return self._view_locked(job)

    def logs(self, job_id: str, *, cursor: int) -> dict[str, object]:
        with self._lock:
            self._evict_terminal_locked(self._now_utc())
            job = self._require_job(job_id)
            requested_cursor = min(max(cursor, 0), job.next_chunk_cursor)
            oldest_cursor = (
                job.chunks[0].start_cursor if job.chunks else job.next_chunk_cursor
            )
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
                        response_cursor > chunk.start_cursor
                        or fragment_end < chunk.end_cursor
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
            "stage": job.stage,
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
        }

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
        terminal_jobs = [
            job for job in self._jobs.values() if job.status in _TERMINAL_JOB_STATUSES
        ]
        for job in terminal_jobs:
            updated_at = _parse_utc_timestamp(job.updated_at_utc)
            if (
                updated_at is not None
                and (now - updated_at).total_seconds() >= self._terminal_job_ttl_seconds
            ):
                self._jobs.pop(job.job_id, None)
        retained_terminal = sorted(
            (
                job
                for job in self._jobs.values()
                if job.status in _TERMINAL_JOB_STATUSES
            ),
            key=lambda job: (
                _parse_utc_timestamp(job.updated_at_utc) or datetime.min.replace(tzinfo=UTC),
                job.ordinal,
            ),
        )
        excess = len(retained_terminal) - self._max_terminal_jobs
        for job in retained_terminal[: max(0, excess)]:
            self._jobs.pop(job.job_id, None)


@dataclass(slots=True)
class _UiOperatorDecisionWaiter:
    job_id: str
    request_id: str
    attempt_path: Path
    condition: threading.Condition = field(default_factory=threading.Condition)
    decision: RuntimeOperatorDecision | None = None


class _UiOperatorDecisionCoordinator:
    def __init__(
        self,
        *,
        jobs: UiRunJobStore,
        attempt_path_resolver: Callable[[str], Path | None],
    ) -> None:
        self._jobs = jobs
        self._attempt_path_resolver = attempt_path_resolver
        self._lock = threading.Lock()
        self._waiters_by_request: dict[str, _UiOperatorDecisionWaiter] = {}
        self._waiters_by_job: dict[str, _UiOperatorDecisionWaiter] = {}

    def wait(
        self,
        *,
        job_id: str,
        request: RuntimeOperatorRequest,
        attempt_path: Path,
    ) -> RuntimeOperatorDecision:
        waiter = _UiOperatorDecisionWaiter(
            job_id=job_id,
            request_id=request.id,
            attempt_path=attempt_path,
        )
        with self._lock:
            self._waiters_by_request[request.id] = waiter
            self._waiters_by_job[job_id] = waiter
            self._jobs.set_attempt_path(job_id, attempt_path)
            self._jobs.wait_for_operator(
                job_id,
                result={
                    "waiting_for_operator": True,
                    "request_id": request.id,
                    "attempt_path": attempt_path.as_posix(),
                },
                message="waiting for operator decision",
            )
        try:
            with waiter.condition:
                while waiter.decision is None:
                    waiter.condition.wait()
                return waiter.decision
        finally:
            with self._lock:
                self._waiters_by_request.pop(request.id, None)
                self._waiters_by_job.pop(job_id, None)
                if (
                    waiter.decision is not None
                    and waiter.decision.action is not RuntimeOperatorDecisionAction.CANCEL
                ):
                    self._jobs.mark_running(
                        job_id,
                        message="runtime resumed after operator decision",
                    )

    def decide(
        self,
        *,
        job_id: str,
        attempt_path: Path,
        decision: RuntimeOperatorDecision,
    ) -> RuntimeOperatorDecision:
        with self._lock:
            status = str(self._jobs.view(job_id)["status"])
            if status in _TERMINAL_JOB_STATUSES:
                raise UiJobDecisionConflict(
                    f"UI job '{job_id}' is terminal and cannot accept operator decisions."
                )
            try:
                winner = resolve_operator_decision(
                    attempt_path=attempt_path,
                    decision=decision,
                )
            except OperatorDecisionConflict as exc:
                self._deliver_locked(exc.winner)
                raise
            self._deliver_locked(winner)
            return winner

    def cancel(self, job_id: str) -> dict[str, object]:
        with self._lock:
            job = self._jobs.view(job_id)
            if str(job["status"]) != "waiting-for-operator":
                return self._jobs.cancel(job_id)
            attempt_path = self._attempt_path_resolver(job_id)
            request_id = self._pending_request_id(job_id=job_id, attempt_path=attempt_path)
            if attempt_path is None or request_id is None:
                return self._jobs.cancel(job_id)
            cancellation = RuntimeOperatorDecision(
                request_id=request_id,
                action=RuntimeOperatorDecisionAction.CANCEL,
                source=RuntimeOperatorDecisionSource.UI,
            )
            try:
                winner = resolve_operator_decision(
                    attempt_path=attempt_path,
                    decision=cancellation,
                )
            except OperatorDecisionConflict as exc:
                winner = exc.winner
            if winner.action is RuntimeOperatorDecisionAction.CANCEL:
                payload = self._jobs.cancel(job_id)
            else:
                self._jobs.mark_running(
                    job_id,
                    message="runtime resumed before cancellation",
                )
                payload = self._jobs.cancel(job_id)
            self._deliver_locked(winner)
            return payload

    def has_waiter(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._waiters_by_job

    def _pending_request_id(
        self,
        *,
        job_id: str,
        attempt_path: Path | None,
    ) -> str | None:
        waiter = self._waiters_by_job.get(job_id)
        if waiter is not None:
            return waiter.request_id
        if attempt_path is None:
            return None
        pending_ids = pending_operator_request_ids(attempt_path=attempt_path)
        return pending_ids[0] if pending_ids else None

    def _deliver_locked(self, decision: RuntimeOperatorDecision) -> None:
        waiter = self._waiters_by_request.get(decision.request_id)
        if waiter is None or waiter.decision is not None:
            return
        with waiter.condition:
            waiter.decision = decision
            waiter.condition.notify_all()


@dataclass(frozen=True, slots=True)
class _UiRuntimeOperatorDecisionProvider:
    service: OperatorUiService
    job_id: str

    def request_decision(
        self,
        request: RuntimeOperatorRequest,
        *,
        requests_path: Path,
        decisions_path: Path,
    ) -> RuntimeOperatorDecision | None:
        return self.service._wait_for_operator_decision(
            job_id=self.job_id,
            request=request,
            attempt_path=requests_path.parent,
        )


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


def _first_param(params: dict[str, list[str]], name: str, default: str | None = None) -> str | None:
    values = params.get(name)
    if not values:
        return default
    value = values[0].strip()
    return value or default


def _optional_attempt(params: dict[str, list[str]]) -> int | None:
    raw_attempt = _first_param(params, "attempt")
    if raw_attempt is None:
        return None
    try:
        attempt = int(raw_attempt)
    except ValueError as exc:
        raise ValueError("attempt must be an integer.") from exc
    if attempt <= 0:
        raise ValueError("attempt must be greater than zero.")
    return attempt


def _optional_positive_int_param(params: dict[str, list[str]], name: str) -> int | None:
    raw_value = _first_param(params, name)
    if raw_value is None:
        return None
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


def _missing_runtime_log_payload(
    *,
    stage: str,
    run_id: str | None,
    attempt_number: int | None,
    message: str,
) -> dict[str, object]:
    return {
        "summary": {
            "run_id": run_id,
            "stage": stage,
            "attempt_number": attempt_number,
            "runtime_log_path": None,
        },
        "text": "",
        "byte_size": 0,
        "start_byte": 0,
        "end_byte": 0,
        "requested_bytes": 0,
        "max_bytes": 0,
        "truncated": False,
        "truncated_head": False,
        "truncated_tail": False,
        "available": False,
        "message": message,
    }


def _is_runtime_log_not_available(message: str) -> bool:
    return message.startswith("Runtime log file does not exist:") or message.startswith(
        "Runtime log path is missing in artifact index "
    )


def _cursor_param(params: dict[str, list[str]]) -> int:
    raw_cursor = _first_param(params, "cursor", "0")
    assert raw_cursor is not None
    try:
        cursor = int(raw_cursor)
    except ValueError as exc:
        raise ValueError("cursor must be an integer.") from exc
    if cursor < 0:
        raise ValueError("cursor must be zero or greater.")
    return cursor


def _runtime_from_payload(payload: dict[str, Any]) -> str:
    raw_runtime = payload.get("runtime")
    if not isinstance(raw_runtime, str):
        raise ValueError("runtime is required.")
    runtime = raw_runtime.strip()
    if not runtime:
        raise ValueError("runtime is required.")
    return runtime


def _optional_run_id_from_payload(payload: dict[str, Any]) -> str | None:
    raw_run_id = payload.get("run_id")
    if raw_run_id is None:
        return None
    if not isinstance(raw_run_id, str):
        raise ValueError("run_id must be a string.")
    return raw_run_id.strip() or None


def _source_run_id_from_payload(payload: dict[str, Any]) -> str:
    raw_source_run = payload.get("source_run_id", payload.get("run_id"))
    if not isinstance(raw_source_run, str):
        raise ValueError("source_run_id is required.")
    source_run_id = raw_source_run.strip()
    if not source_run_id:
        raise ValueError("source_run_id is required.")
    return source_run_id


def _source_work_item_from_payload(payload: dict[str, Any], *, default: str) -> str:
    raw_source_work_item = payload.get("source_work_item", default)
    if not isinstance(raw_source_work_item, str):
        raise ValueError("source_work_item must be a string.")
    source_work_item = raw_source_work_item.strip()
    if not source_work_item:
        raise ValueError("source_work_item is required.")
    return source_work_item


def _text_from_payload(
    payload: dict[str, Any],
    name: str,
    *,
    default: str | None = None,
) -> str:
    raw_value = payload.get(name, default)
    if not isinstance(raw_value, str):
        raise ValueError(f"{name} must be a string.")
    value = raw_value.strip()
    if not value:
        raise ValueError(f"{name} is required.")
    return value


def _optional_text_from_payload(payload: dict[str, Any], name: str) -> str | None:
    raw_value = payload.get(name)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise ValueError(f"{name} must be a string.")
    value = raw_value.strip()
    if not value:
        raise ValueError(f"{name} is required when provided.")
    return value


def _optional_string_tuple_from_payload(
    payload: dict[str, Any],
    name: str,
) -> tuple[str, ...] | None:
    raw_values = payload.get(name)
    if raw_values is None:
        return None
    if not isinstance(raw_values, list):
        raise ValueError(f"{name} must be a list.")
    values: list[str] = []
    for index, item in enumerate(raw_values, 1):
        if not isinstance(item, str):
            raise ValueError(f"{name}[{index}] must be a string.")
        normalized = item.strip()
        if normalized:
            values.append(normalized)
    return tuple(values)


def _contracts_root_from_payload(payload: dict[str, Any]) -> Path:
    raw_contracts_root = payload.get("contracts_root")
    if raw_contracts_root is None:
        return DEFAULT_STAGE_CONTRACTS_ROOT
    if not isinstance(raw_contracts_root, str):
        raise ValueError("contracts_root must be a string.")
    contracts_root = raw_contracts_root.strip()
    if not contracts_root:
        raise ValueError("contracts_root is required.")
    return Path(contracts_root)


def _optional_baseline_id_from_payload(payload: dict[str, Any]) -> str | None:
    raw_baseline_id = payload.get("baseline_id")
    if raw_baseline_id is None:
        return None
    if not isinstance(raw_baseline_id, str):
        raise ValueError("baseline_id must be a string.")
    return raw_baseline_id.strip() or None


def _validate_runtime(runtime: str) -> None:
    supported = {definition.runtime_id for definition in runtime_definitions()}
    if runtime not in supported:
        raise ValueError(
            f"Unsupported runtime '{runtime}'. Supported runtimes: {', '.join(sorted(supported))}."
        )


def _stage_from_payload(payload: dict[str, Any]) -> str:
    raw_stage = payload.get("stage")
    if not isinstance(raw_stage, str):
        raise ValueError("stage is required.")
    stage = raw_stage.strip()
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}.")
    return stage


def _workflow_bounds_from_payload(payload: dict[str, Any]) -> tuple[str, str]:
    stage_start = str(payload.get("from_stage", STAGES[0])).strip() or STAGES[0]
    stage_end = str(payload.get("to_stage", STAGES[-1])).strip() or STAGES[-1]
    if stage_start not in STAGES:
        raise ValueError(f"Unknown stage '{stage_start}'. Expected one of: {', '.join(STAGES)}.")
    if stage_end not in STAGES:
        raise ValueError(f"Unknown stage '{stage_end}'. Expected one of: {', '.join(STAGES)}.")
    if STAGES.index(stage_start) > STAGES.index(stage_end):
        raise ValueError(
            f"Stage start '{stage_start}' must not come after stage end '{stage_end}'."
        )
    return stage_start, stage_end


def _next_flow_source_item(
    *,
    item_id: str,
    kind: str,
    title: str,
    detail: str,
    display_label: str | None = None,
    priority: int = 50,
    recommended: bool = False,
    collapsible: bool = False,
    stage: str | None = None,
    artifact_key: str | None = None,
    artifact_kind: str | None = None,
    source_path: str | None = None,
    selected: bool = False,
) -> dict[str, object]:
    return {
        "id": item_id,
        "kind": kind,
        "title": title,
        "detail": detail,
        "display_label": display_label or title,
        "priority": priority,
        "recommended": recommended,
        "collapsible": collapsible,
        "stage": stage,
        "artifact_key": artifact_key,
        "artifact_kind": artifact_kind,
        "source_path": source_path,
        "selected": selected,
    }


def _next_flow_source_group(
    *,
    group_id: str,
    label: str,
    detail: str,
    items: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "id": group_id,
        "label": label,
        "detail": detail,
        "count": len(items),
        "items": items,
    }


def _source_artifact_display_label(key: str) -> str:
    labels = {
        "qa_report": "Final QA report",
        "stage_result": "QA stage result",
        "validator_report": "Validator report",
        "runtime_log": "Runtime log",
        "runtime_jsonl": "Runtime event stream",
        "runtime_exit_metadata": "Runtime exit metadata",
        "events_jsonl": "Stage event log",
        "input_bundle": "QA input bundle",
        "questions": "Persisted questions",
        "answers": "Persisted answers",
        "stage_brief": "Stage brief",
    }
    return labels.get(key, key.replace("_", " ").title())


def _qa_source_artifact_priority(key: str) -> int:
    priorities = {
        "qa_report": 10,
        "stage_result": 30,
        "validator_report": 35,
        "runtime_log": 70,
        "runtime_jsonl": 72,
        "events_jsonl": 74,
    }
    return priorities.get(key, 60)


def _qa_source_artifact_detail(key: str) -> str:
    if key == "qa_report":
        return "Primary completed-run QA evidence for follow-up scoping."
    if key in {"stage_result", "validator_report"}:
        return "Supporting pass/fail evidence for audit and acceptance checks."
    if key.startswith("runtime") or key == "events_jsonl":
        return "Supporting runtime evidence; use when the follow-up depends on execution traces."
    return "Supporting QA artifact available for follow-up context when needed."


def _next_flow_source_priority(item: Mapping[str, object]) -> int:
    priority = item.get("priority", 50)
    return priority if isinstance(priority, int) else 50


def _next_flow_source_findings_payload(dashboard: Any) -> dict[str, object]:
    run = dashboard.run
    handoff = dashboard.terminal_handoff
    final_artifacts = tuple(handoff.final_artifacts) if handoff is not None else ()
    qa_items = [
        _next_flow_source_item(
            item_id=f"qa-finding:{artifact.stage}:{artifact.key}",
            kind="qa-finding",
            title=f"QA artifact: {artifact.key}",
            display_label=_source_artifact_display_label(artifact.key),
            detail=_qa_source_artifact_detail(artifact.key),
            priority=_qa_source_artifact_priority(artifact.key),
            recommended=artifact.key == "qa_report",
            collapsible=artifact.key != "qa_report",
            stage=artifact.stage,
            artifact_key=artifact.key,
            artifact_kind=artifact.kind,
            source_path=artifact.path,
            selected=artifact.key == "qa_report",
        )
        for artifact in final_artifacts
        if artifact.stage == "qa"
    ]
    review_items = [
        _next_flow_source_item(
            item_id=f"review-note:{artifact.stage}:{artifact.key}",
            kind="review-note",
            title=f"Review artifact: {artifact.key}",
            display_label=_source_artifact_display_label(artifact.key),
            detail="Carry forward review-stage notes or accepted risks.",
            priority=20,
            stage=artifact.stage,
            artifact_key=artifact.key,
            artifact_kind=artifact.kind,
            source_path=artifact.path,
        )
        for artifact in dashboard.recent_artifacts
        if artifact.stage == "review"
    ]
    failed_items = [
        _next_flow_source_item(
            item_id=f"failed-evidence:blocker:{index}",
            kind="failed-evidence",
            title=blocker.title,
            display_label=blocker.title,
            detail=blocker.detail,
            priority=5,
            recommended=True,
            stage=blocker.stage,
            artifact_key=blocker.kind,
            artifact_kind="blocker",
            source_path=blocker.path,
            selected=blocker.severity == "error",
        )
        for index, blocker in enumerate(dashboard.blockers, start=1)
    ]
    manual_items = [
        _next_flow_source_item(
            item_id="manual-request:operator-note",
            kind="manual-request",
            title="Manual operator request",
            display_label="Manual request",
            detail="Add a scoped operator note in the follow-up definition step.",
            priority=40,
        )
    ]
    qa_items = sorted(qa_items, key=_next_flow_source_priority)
    review_items = sorted(review_items, key=_next_flow_source_priority)
    failed_items = sorted(failed_items, key=_next_flow_source_priority)
    groups = (
        _next_flow_source_group(
            group_id="qa-findings",
            label="QA findings",
            detail=(
                "Final QA report is the primary follow-up source; supporting QA "
                "artifacts stay available as collapsed evidence."
            ),
            items=qa_items,
        ),
        _next_flow_source_group(
            group_id="review-notes",
            label="Review notes",
            detail="Review-stage artifacts and accepted-risk notes available for handoff.",
            items=review_items,
        ),
        _next_flow_source_group(
            group_id="failed-evidence",
            label="Failed evidence",
            detail="Validation failures, blockers, or unresolved evidence to carry forward.",
            items=failed_items,
        ),
        _next_flow_source_group(
            group_id="manual-request",
            label="Manual request",
            detail="Operator-authored context that is captured before follow-up launch.",
            items=manual_items,
        ),
    )
    all_items = [*qa_items, *review_items, *failed_items, *manual_items]
    recommended_items = [item for item in all_items if item["recommended"]]
    clean_terminal = handoff is not None and handoff.status == "completed" and not handoff.blockers
    return {
        "source_work_item": dashboard.work_item,
        "source_run_id": run.run_id,
        "source_runtime_id": run.runtime_id,
        "recommendation": (
            "Clean QA run: follow-up is optional. Create New Work Item remains "
            "the recommended next action unless the operator selects specific context."
            if clean_terminal
            else "Carry forward the recommended source findings before starting follow-up work."
        ),
        "groups": groups,
        "counts": {
            "total_items": len(all_items),
            "selected_defaults": sum(1 for item in all_items if item["selected"]),
            "recommended_items": len(recommended_items),
            "collapsible_items": sum(1 for item in all_items if item["collapsible"]),
            "source_artifact_links": sum(1 for item in all_items if item["source_path"]),
            "required_context_groups": len(groups),
        },
    }


def _selected_source_ids_from_payload(payload: dict[str, Any]) -> tuple[str, ...]:
    raw_ids = payload.get("selected_source_ids")
    if not isinstance(raw_ids, list):
        raise ValueError("selected_source_ids must be a list.")
    selected = tuple(item.strip() for item in raw_ids if isinstance(item, str) and item.strip())
    if not selected:
        raise ValueError("At least one source finding must be selected.")
    return selected


def _remediation_source_ids_from_payload(payload: dict[str, Any]) -> tuple[str, ...]:
    raw_ids = payload.get("source_ids", payload.get("selected_source_ids"))
    if not isinstance(raw_ids, list):
        raise ValueError("source_ids must be a list.")
    source_ids: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_ids, 1):
        if not isinstance(item, str):
            raise ValueError(f"source_ids[{index}] must be a string.")
        normalized = item.strip()
        if normalized and normalized not in seen:
            source_ids.append(normalized)
            seen.add(normalized)
    if not source_ids:
        raise ValueError("At least one source id is required.")
    return tuple(source_ids)


def _selected_next_flow_source_items(
    *,
    dashboard: Any,
    selected_source_ids: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    findings = _next_flow_source_findings_payload(dashboard)
    groups = cast(tuple[dict[str, object], ...], findings["groups"])
    items_by_id = {
        str(item["id"]): item
        for group in groups
        for item in cast(list[dict[str, object]], group["items"])
    }
    missing_ids = tuple(item_id for item_id in selected_source_ids if item_id not in items_by_id)
    if missing_ids:
        raise ValueError(
            f"Selected source findings do not match this source run: {', '.join(missing_ids)}."
        )
    selected_items = tuple(items_by_id[item_id] for item_id in selected_source_ids)
    if not selected_items:
        raise ValueError("Selected source findings do not match this source run.")
    return selected_items


def _follow_up_source_selections_from_items(
    selected_items: tuple[dict[str, object], ...],
) -> tuple[FollowUpSourceSelection, ...]:
    selections: list[FollowUpSourceSelection] = []
    for item in selected_items:
        item_id = str(item.get("id") or "")
        source_path = item.get("source_path")
        if not isinstance(source_path, str) or not source_path.strip():
            if item.get("kind") != "manual-request":
                raise ValueError(f"Selected source '{item_id}' has no source artifact path.")
            source_path = None
        raw_stage = item.get("stage")
        selections.append(
            FollowUpSourceSelection(
                kind=str(item.get("kind") or ""),
                title=str(item.get("title") or ""),
                source_path=source_path,
                stage=raw_stage if isinstance(raw_stage, str) else None,
                note=str(item.get("detail") or "") or None,
            )
        )
    return tuple(selections)


def _next_flow_follow_up_draft_payload(
    *,
    dashboard: Any,
    selected_source_ids: tuple[str, ...],
    new_work_item: str | None = None,
    title: str | None = None,
) -> dict[str, object]:
    findings = _next_flow_source_findings_payload(dashboard)
    selected_items = _selected_next_flow_source_items(
        dashboard=dashboard,
        selected_source_ids=selected_source_ids,
    )
    source_run_id = str(findings["source_run_id"] or "")
    source_work_item = str(findings["source_work_item"] or "")
    resolved_new_work_item = new_work_item or f"{source_work_item}-FOLLOW-UP"
    resolved_title = title or f"Follow-up for {source_work_item} from {source_run_id}"
    acceptance_criteria = tuple(
        f"Resolve follow-up source: {item['title']}" for item in selected_items
    )
    required_evidence = tuple(
        f"Updated evidence for {item['title']}"
        for item in selected_items
        if item.get("source_path")
    )
    selected_lines = "\n".join(
        f"- `{item['kind']}` {item['title']} ({item.get('source_path') or 'manual request'})"
        for item in selected_items
    )
    criteria_lines = "\n".join(f"- {criterion}" for criterion in acceptance_criteria)
    preview = "\n".join(
        (
            f"# {resolved_title}",
            "",
            f"Source work item: `{source_work_item}`.",
            f"Source run: `{source_run_id}`.",
            "",
            "## Selected source findings",
            "",
            selected_lines,
            "",
            "## Acceptance criteria",
            "",
            criteria_lines,
            "",
        )
    )
    return {
        "draft": {
            "source_work_item": source_work_item,
            "source_run_id": source_run_id,
            "new_work_item": resolved_new_work_item,
            "title": resolved_title,
            "selected_sources": selected_items,
            "acceptance_criteria": acceptance_criteria,
            "required_evidence": required_evidence,
            "inherited_context": (
                {
                    "id": "source-run-lineage",
                    "label": "Source run lineage",
                    "detail": f"Keep parent run {source_run_id} visible on the new work item.",
                    "enabled": True,
                },
                {
                    "id": "selected-artifacts",
                    "label": "Selected artifact links",
                    "detail": f"{len(required_evidence)} selected source artifacts stay linked.",
                    "enabled": True,
                },
                {
                    "id": "baseline-snapshot",
                    "label": "Baseline snapshot",
                    "detail": "Use the source run as launch baseline until preflight resolves a newer baseline.",
                    "enabled": True,
                },
            ),
            "first_stage_input_preview": preview,
        }
    }


def _workspace_response_path(workspace_root: Path, path: Path) -> str:
    return workspace_relative_path(workspace_root, path)


def _follow_up_creation_payload(
    *,
    workspace_root: Path,
    result: Any,
) -> dict[str, object]:
    return {
        "work_item": result.work_item,
        "request_path": _workspace_response_path(workspace_root, result.request_path),
        "source_artifact_paths": result.source_artifact_paths,
        "context": {
            "user_request_path": _workspace_response_path(
                workspace_root,
                result.context_seed.user_request_path,
            ),
            "intake_path": _workspace_response_path(
                workspace_root,
                result.context_seed.intake_path,
            ),
        },
    }


def _draft_string_tuple(
    draft: Mapping[str, object],
    name: str,
) -> tuple[str, ...]:
    raw_values = draft.get(name, ())
    if not isinstance(raw_values, (list, tuple)):
        return ()
    values: list[str] = []
    for item in raw_values:
        normalized = str(item).strip()
        if normalized:
            values.append(normalized)
    return tuple(values)


def _draft_inherited_context_lines(draft: Mapping[str, object]) -> tuple[str, ...]:
    raw_values = draft.get("inherited_context", ())
    if not isinstance(raw_values, (list, tuple)):
        return ()
    lines: list[str] = []
    for item in raw_values:
        if not isinstance(item, Mapping):
            continue
        label = str(item.get("label") or "").strip()
        detail = str(item.get("detail") or "").strip()
        if label and detail:
            lines.append(f"{label}: {detail}")
        elif label:
            lines.append(label)
    return tuple(lines)


def _clone_creation_payload(
    *,
    workspace_root: Path,
    result: Any,
) -> dict[str, object]:
    return {
        "work_item": result.work_item,
        "draft_path": _workspace_response_path(workspace_root, result.draft_path),
        "context": {
            "user_request_path": _workspace_response_path(
                workspace_root,
                result.context_seed.user_request_path,
            ),
            "intake_path": _workspace_response_path(
                workspace_root,
                result.context_seed.intake_path,
            ),
        },
        "config": result.config,
    }


def _next_flow_launch_lineage(
    *,
    source_work_item: str,
    source_run_id: str,
    baseline_id: str | None,
    relationship: str,
) -> dict[str, object]:
    lineage: dict[str, object] = {
        "source_work_item_id": source_work_item,
        "source_run_id": source_run_id,
        "relationship": relationship,
    }
    if baseline_id is not None:
        lineage["baseline_id"] = baseline_id
    return lineage


def _exit_code_from_result(result: object) -> int:
    if isinstance(result, Mapping):
        raw_exit_code = result.get("exit_code", 0)
        completed = result.get("completed", True)
    else:
        raw_exit_code = getattr(result, "exit_code", 0)
        completed = getattr(result, "completed", True)
    try:
        exit_code = int(raw_exit_code)
    except (TypeError, ValueError):
        return 1
    if completed is False and exit_code == 0:
        return 1
    return exit_code


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized in {"localhost", "localhost.", "::1"}:
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def _warn_if_non_loopback_host(host: str) -> None:
    if _is_loopback_host(host):
        return
    console.print(
        "[yellow]Warning:[/yellow] AIDD UI has no authentication in this release; "
        f"binding to {host!r} exposes the local operator surface to that network interface."
    )


def _open_local_folder(path: Path) -> None:
    if sys.platform == "darwin":
        command = ("open", path.as_posix())
    elif sys.platform.startswith("win"):
        command = ("explorer", str(path))
    else:
        command = ("xdg-open", path.as_posix())
    subprocess.Popen(command)  # noqa: S603


def _latest_attempt_path(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> Path | None:
    next_number = next_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    latest_number = next_number - 1
    if latest_number < 1:
        return None
    return run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=latest_number,
    )


def _operator_request_view(attempt_path: Path | None) -> dict[str, object]:
    if attempt_path is None:
        return {
            "attempt_path": None,
            "requests_path": None,
            "decisions_path": None,
            "requests": (),
            "pending_request_ids": (),
            "unapproved_request_ids": (),
            "decisions": (),
            "audit_history": (),
        }
    requests_path = attempt_path / OPERATOR_REQUESTS_FILENAME
    decisions_path = attempt_path / OPERATOR_DECISIONS_FILENAME
    requests = load_operator_requests(requests_path)
    decisions = load_operator_decisions(decisions_path)
    decided_ids = {decision.request_id for decision in decisions}
    pending_ids = tuple(request.id for request in requests if request.id not in decided_ids)
    unapproved_ids = unapproved_operator_request_ids(attempt_path=attempt_path)
    return {
        "attempt_path": attempt_path.as_posix(),
        "requests_path": requests_path.as_posix() if requests_path.exists() else None,
        "decisions_path": decisions_path.as_posix() if decisions_path.exists() else None,
        "requests": tuple(request.to_dict() for request in requests),
        "pending_request_ids": pending_ids,
        "unapproved_request_ids": unapproved_ids,
        "decisions": tuple(decision.to_dict() for decision in decisions),
        "audit_history": _operator_approval_audit_history(
            requests=requests,
            decisions=decisions,
            pending_ids=frozenset(pending_ids),
            unapproved_ids=frozenset(unapproved_ids),
            requests_path=requests_path if requests_path.exists() else None,
            decisions_path=decisions_path if decisions_path.exists() else None,
        ),
    }


def _operator_approval_audit_history(
    *,
    requests: tuple[RuntimeOperatorRequest, ...],
    decisions: tuple[RuntimeOperatorDecision, ...],
    pending_ids: frozenset[str],
    unapproved_ids: frozenset[str],
    requests_path: Path | None,
    decisions_path: Path | None,
) -> tuple[dict[str, object], ...]:
    decisions_by_request = {decision.request_id: decision for decision in decisions}
    rows: list[dict[str, object]] = []
    for request in requests:
        decision = decisions_by_request.get(request.id)
        status = _operator_approval_status(
            request_id=request.id,
            decision=decision,
            pending_ids=pending_ids,
            unapproved_ids=unapproved_ids,
        )
        rows.append(
            {
                "request_id": request.id,
                "status": status,
                "runtime_id": request.runtime_id,
                "stage": request.stage,
                "kind": request.kind.value,
                "tool_name": request.tool_name,
                "risk": request.risk.value,
                "created_at_utc": request.created_at_utc,
                "command": request.payload.get("command"),
                "cwd": request.cwd.as_posix() if request.cwd is not None else None,
                "paths": tuple(path.as_posix() for path in request.paths),
                "decision_action": decision.action.value if decision is not None else None,
                "decision_source": decision.source.value if decision is not None else None,
                "decision_reason": decision.reason if decision is not None else None,
                "decision_at_utc": (decision.created_at_utc if decision is not None else None),
                "requests_path": (requests_path.as_posix() if requests_path is not None else None),
                "decisions_path": (
                    decisions_path.as_posix() if decisions_path is not None else None
                ),
            }
        )
    return tuple(rows)


def _operator_approval_status(
    *,
    request_id: str,
    decision: RuntimeOperatorDecision | None,
    pending_ids: frozenset[str],
    unapproved_ids: frozenset[str],
) -> str:
    if decision is not None and decision.is_approval:
        return "approved"
    if decision is not None:
        if decision.action is RuntimeOperatorDecisionAction.DENY:
            return "denied"
        if decision.action is RuntimeOperatorDecisionAction.CANCEL:
            return "cancelled"
        return decision.action.value
    if request_id in pending_ids:
        return "pending"
    if request_id in unapproved_ids:
        return "policy-blocked"
    return "recorded"


def _runtime_command_sources_from_config(path: Path) -> dict[str, RuntimeCommandSource]:
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("rb") as file_obj:
            data = tomllib.load(file_obj)

    raw_runtime = data.get("runtime", {})
    runtime_table = raw_runtime if isinstance(raw_runtime, dict) else {}
    sources: dict[str, RuntimeCommandSource] = {}
    for definition in runtime_definitions():
        raw_section = runtime_table.get(definition.config_section, {})
        section = raw_section if isinstance(raw_section, dict) else {}
        sources[definition.runtime_id] = "config" if "command" in section else "default"
    return sources


def _collect_runtime_readiness_probe_reports(
    cfg: AiddConfig,
) -> dict[str, RuntimeReadinessProbeReport]:
    reports: dict[str, RuntimeReadinessProbeReport] = {}
    definitions = runtime_definitions()

    def _probe_runtime(runtime_id: str) -> tuple[str, RuntimeReadinessProbeReport]:
        definition = next(item for item in definitions if item.runtime_id == runtime_id)
        provider_report = get_runtime_adapter_surface(definition.runtime_id).probe(
            definition.probe_command
        )
        runtime_config = cfg.runtime_config(definition.runtime_id)
        return (
            definition.runtime_id,
            RuntimeReadinessProbeReport(
                provider_available=provider_report.available,
                execution_command_available=_execution_command_available(runtime_config.command),
                provider_version=provider_report.version_text,
                provider_command=provider_report.command,
            ),
        )

    with ThreadPoolExecutor(max_workers=max(1, len(definitions))) as executor:
        futures = {
            executor.submit(_probe_runtime, definition.runtime_id): definition.runtime_id
            for definition in definitions
        }
        for future in as_completed(futures):
            runtime_id, report = future.result()
            reports[runtime_id] = report
    return reports


class OperatorUiService:
    def __init__(
        self,
        options: UiServerOptions,
        *,
        workflow_runner: WorkflowRunner = run_workflow,
        stage_runner: StageRunner = run_stage_command,
        stage_interact_runner: StageInteractRunner = run_stage_interact_command,
        readiness_probe_provider: ReadinessProbeProvider = _collect_runtime_readiness_probe_reports,
        folder_opener: LocalFolderOpener = _open_local_folder,
    ) -> None:
        self.options = options
        project_root = options.root.resolve(strict=False).parent
        self._workflow_runner = workflow_runner
        self._stage_runner = stage_runner
        self._implementation_stage_runner = (
            run_stage_attempt_command if stage_runner is run_stage_command else stage_runner
        )
        self._stage_interact_runner = stage_interact_runner
        self._readiness_probe_provider = readiness_probe_provider
        self._folder_opener = folder_opener
        self._jobs = UiRunJobStore()
        self._operator_decisions = _UiOperatorDecisionCoordinator(
            jobs=self._jobs,
            attempt_path_resolver=self._job_attempt_path,
        )
        self._shutdown_requested = False
        self._context: UiProjectContext | None = (
            UiProjectContext(
                work_item=options.work_item,
                root=options.root,
                config=options.config,
                project_root=project_root,
            )
            if options.work_item is not None
            else None
        )
        self._recent_project_roots: list[Path] = (
            [project_root] if options.work_item is not None else []
        )
        self._router = OperatorUiRouter(
            get_routes=self._get_routes(),
            post_routes=self._post_routes(),
            static_route_resolver=operator_static_asset_for_route,
            dynamic_get_route=lambda path, params: self._handle_job_get(
                path=path,
                params=params,
            ),
            dynamic_post_route=lambda path, payload: self._handle_job_post(
                path=path,
                payload=payload,
            ),
            remote_mutation_guard=self._remote_mutation_error,
        )

    @property
    def workspace_root(self) -> Path:
        return self._require_context().root

    @property
    def work_item(self) -> str:
        return self._require_context().work_item

    @property
    def config_path(self) -> Path:
        return self._require_context().config

    @property
    def project_root(self) -> Path:
        return self._require_context().project_root

    @property
    def setup_required(self) -> bool:
        return self._context is None

    def _require_context(self) -> UiProjectContext:
        if self._context is None:
            raise ValueError("Complete project setup before using this UI action.")
        return self._context

    def _onboarding_service(self) -> OnboardingService:
        return OnboardingService(
            launch_root=Path.cwd().resolve(strict=False),
            workspace_root=self.options.root,
        )

    def _remember_recent_project(self, project_root: Path) -> None:
        resolved = project_root.resolve(strict=False)
        self._recent_project_roots = [
            path for path in self._recent_project_roots if path != resolved
        ]
        self._recent_project_roots.insert(0, resolved)
        del self._recent_project_roots[8:]

    def _context_config_path(self, project_root: Path) -> Path:
        config = self.options.config
        return config if config.is_absolute() else project_root / config

    def _activate_context(
        self,
        *,
        project_root: Path,
        workspace_root: Path,
        work_item: str,
    ) -> None:
        if self._jobs.has_active_jobs():
            raise ValueError("Cannot switch project while a UI runtime job is active.")
        resolved_project_root = project_root.resolve(strict=False)
        self._context = UiProjectContext(
            work_item=work_item,
            root=workspace_root.resolve(strict=False),
            config=self._context_config_path(resolved_project_root),
            project_root=resolved_project_root,
        )
        self._remember_recent_project(resolved_project_root)

    def _project_set_from_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[OnboardingProjectDeclaration, ...]:
        raw_projects = payload.get("project_set") or payload.get("projects") or ()
        if raw_projects in (None, "") or raw_projects == ():
            return ()
        if not isinstance(raw_projects, list):
            raise ValueError("project_set must be an array.")
        projects: list[OnboardingProjectDeclaration] = []
        for index, raw_project in enumerate(raw_projects):
            if not isinstance(raw_project, dict):
                raise ValueError(f"project_set[{index}] must be an object.")
            project_id = str(raw_project.get("id", "")).strip()
            root = str(raw_project.get("root", "")).strip()
            role = raw_project.get("role")
            if not project_id:
                raise ValueError(f"project_set[{index}].id is required.")
            if not root:
                raise ValueError(f"project_set[{index}].root is required.")
            projects.append(
                OnboardingProjectDeclaration(
                    id=project_id,
                    root=Path(root),
                    role=None if role is None else str(role).strip() or None,
                )
            )
        return tuple(projects)

    def _onboarding_state(self) -> dict[str, object]:
        context = self._context
        return {
            "app_version": __version__,
            "setup_required": context is None,
            "context": None
            if context is None
            else {
                "project_root": context.project_root,
                "workspace_root": context.root,
                "work_item": context.work_item,
                "config": context.config,
            },
            "recent_projects": tuple(
                path.as_posix() for path in self._recent_project_roots if path.exists()
            ),
            "active_jobs": self._jobs.has_active_jobs(),
        }

    def _project_home(self, params: dict[str, list[str]]) -> object:
        selected_work_item = _first_param(params, "work_item")
        return {
            "app_version": __version__,
            "project_home": resolve_operator_project_home_view(
                project_root=self.project_root,
                workspace_root=self.workspace_root,
                selected_work_item=selected_work_item,
                recent_project_roots=tuple(self._recent_project_roots),
            ),
        }

    def _task_view(self, params: dict[str, list[str]]) -> object:
        run_id = _first_param(params, "run_id")
        task_id = _first_param(params, "task_id")
        model = resolve_task_read_model(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=run_id,
        )
        tasks = list(cast(list[dict[str, object]], model["tasks"]))
        if task_id is not None:
            tasks = [task for task in tasks if task.get("id") == task_id]
        if task_id is not None and not tasks:
            raise ValueError(f"Unknown task id `{task_id}`.")
        return {**model, "tasks": tasks}

    def _start_task_job(self, payload: dict[str, Any]) -> object:
        task_id = str(payload.get("task_id", "")).strip()
        run_id = str(payload.get("run_id", "")).strip()
        runtime = str(payload.get("runtime", "")).strip()
        if not task_id:
            raise ValueError("task_id is required.")
        if not run_id:
            raise ValueError("run_id is required.")
        if not runtime:
            raise ValueError("runtime is required.")
        lease = acquire_run_mutation_lease_handle(
            run_root(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                run_id=run_id,
            ),
            operation=f"ui-task:{task_id}",
        )
        try:
            self._validate_implementation_runtime(run_id=run_id, runtime=runtime)
        except Exception:
            release_run_mutation_lease(lease)
            raise

        def _target(job_id: str) -> object:
            try:
                with use_transferred_run_mutation_lease(lease):
                    service = self._implementation_service(
                        runtime=runtime,
                        run_id=run_id,
                        job_id=job_id,
                    )
                    result = service.run_task(
                        self._implementation_request(run_id=run_id),
                        task_id=task_id,
                    )
                    ledger = result.ledger
            except Exception:
                release_run_mutation_lease(lease)
                raise
            if ledger.entry(task_id).status.value != "succeeded":
                raise ValueError(f"Implementation task `{task_id}` did not succeed.")
            return {
                "task_id": task_id,
                "run_id": run_id,
                "status": ledger.entry(task_id).status.value,
            }

        try:
            return self._start_job(kind="task", stage="implement", target=_target)
        except Exception:
            release_run_mutation_lease(lease)
            raise

    def _start_task_finalize_job(self, payload: dict[str, Any]) -> object:
        run_id = str(payload.get("run_id", "")).strip()
        runtime = str(payload.get("runtime", "")).strip()
        if not run_id:
            raise ValueError("run_id is required.")
        if not runtime:
            raise ValueError("runtime is required.")
        lease = acquire_run_mutation_lease_handle(
            run_root(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                run_id=run_id,
            ),
            operation="ui-task:finalize",
        )
        try:
            self._validate_implementation_runtime(run_id=run_id, runtime=runtime)
        except Exception:
            release_run_mutation_lease(lease)
            raise

        def _target(job_id: str) -> object:
            try:
                with use_transferred_run_mutation_lease(lease):
                    service = self._implementation_service(
                        runtime=runtime,
                        run_id=run_id,
                        job_id=job_id,
                    )
                    ledger = service.finalize(self._implementation_request(run_id=run_id)).ledger
            except Exception:
                release_run_mutation_lease(lease)
                raise
            return {
                "run_id": run_id,
                "status": ledger.finalization.status.value,
            }

        try:
            return self._start_job(kind="task-finalize", stage="implement", target=_target)
        except Exception:
            release_run_mutation_lease(lease)
            raise

    def _implementation_request(self, *, run_id: str) -> ImplementationExecutionRequest:
        return ImplementationExecutionRequest(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=run_id,
            project_root=self.project_root,
        )

    def _validate_implementation_runtime(self, *, run_id: str, runtime: str) -> None:
        path = run_manifest_path(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=run_id,
        )
        if not path.is_file():
            raise ValueError(f"Run manifest does not exist for run `{run_id}`.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest_runtime = payload.get("runtime_id") if isinstance(payload, dict) else None
        if manifest_runtime != runtime:
            raise ValueError(
                f"Runtime `{runtime}` does not match run manifest runtime "
                f"`{manifest_runtime or ''}`."
            )

    def _implementation_service(
        self,
        *,
        runtime: str,
        run_id: str,
        job_id: str,
    ) -> ImplementationExecutionService:
        def _execute(context: TaskExecutionContext) -> TaskAttemptOutcome:
            try:
                self._implementation_stage_runner(
                    StageRunOptions(
                        stage="implement",
                        work_item=self.work_item,
                        runtime=runtime,
                        run_id=run_id,
                        root=self.workspace_root,
                        config=self.config_path,
                        log_follow=True,
                        runtime_chunk_sink=lambda stream, text: self._jobs.append_chunk(
                            job_id,
                            stream=stream,
                            text=text,
                        ),
                        runtime_operator_decision_provider=(
                            _UiRuntimeOperatorDecisionProvider(service=self, job_id=job_id)
                        ),
                        cancel_requested=lambda: self._jobs.cancel_requested(job_id),
                        defer_success_publication=True,
                        validation_finding_provider=lambda execution_state, discovery: (
                            task_validation_findings(
                                context=context,
                                workspace_root=self.workspace_root,
                                work_item=self.work_item,
                                project_root=self.project_root,
                                execution_state=execution_state,
                                discovery=discovery,
                            )
                        ),
                    )
                )
            except typer.Exit as exc:
                return TaskAttemptOutcome(
                    succeeded=False,
                    blocker=f"implement stage stopped with exit code {exc.exit_code}.",
                )
            return TaskAttemptOutcome(succeeded=True)

        return ImplementationExecutionService(
            task_executor=_execute,
            aggregate_finalizer=cast(
                AggregateFinalizer,
                aggregate_finalization_port(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=run_id,
                ),
            ),
        )

    def _work_item_resume_context(self, params: dict[str, list[str]]) -> object:
        work_item = _first_param(params, "work_item")
        if not work_item:
            raise ValueError("work_item is required.")
        return {
            "app_version": __version__,
            "resume": resolve_operator_project_home_view(
                project_root=self.project_root,
                workspace_root=self.workspace_root,
                selected_work_item=work_item,
                recent_project_roots=tuple(self._recent_project_roots),
            ).selected_work_item_resume,
        }

    def _active_onboarding_project_summary(self) -> OnboardingProjectSummary:
        home = resolve_operator_project_home_view(
            project_root=self.project_root,
            workspace_root=self.workspace_root,
            selected_work_item=self.work_item,
            recent_project_roots=tuple(self._recent_project_roots),
        )
        return OnboardingProjectSummary(
            project_root=home.project_root,
            workspace_root=home.workspace_root,
            workspace_exists=home.workspace_exists,
            work_items=tuple(
                OnboardingWorkItemSummary(
                    work_item=item.work_item,
                    has_request_context=item.has_request_context,
                )
                for item in home.work_items
            ),
        )

    def _inspect_onboarding_project(self, payload: dict[str, Any]) -> object:
        project_root = _text_from_payload(payload, "project_root", default=".")
        summary = self._onboarding_service().inspect_project(project_root)
        self._remember_recent_project(summary.project_root)
        config_path = self._context_config_path(summary.project_root)
        return {
            "project": summary,
            "config_path": config_path,
            "readiness": self._runtime_readiness_for_config(config_path),
            "recent_projects": self._onboarding_state()["recent_projects"],
        }

    def _validate_onboarding_project_set(self, payload: dict[str, Any]) -> object:
        project_root = _text_from_payload(payload, "project_root", default=".")
        project_set = self._project_set_from_payload(payload)
        resolved = self._onboarding_service().resolve_project_set(
            raw_project_root=project_root,
            project_set=project_set,
        )
        return {"project_set": resolved}

    def _setup_onboarding_work_item(self, payload: dict[str, Any]) -> object:
        project_root = _text_from_payload(payload, "project_root", default=".")
        work_item = _text_from_payload(payload, "work_item")
        action = _text_from_payload(payload, "action", default="create")
        if action not in {"create", "resume"}:
            raise ValueError("action must be create or resume.")
        service = self._onboarding_service()
        if action == "resume":
            if self._context is not None:
                resolve_operator_project_home_view(
                    project_root=self.project_root,
                    workspace_root=self.workspace_root,
                    selected_work_item=work_item,
                    recent_project_roots=tuple(self._recent_project_roots),
                )
                self._activate_context(
                    project_root=self.project_root,
                    workspace_root=self.workspace_root,
                    work_item=work_item,
                )
                return {
                    "project": self._active_onboarding_project_summary(),
                    "work_item": work_item,
                    "context": self._onboarding_state()["context"],
                }
            project = service.inspect_project(project_root)
            if work_item not in {item.work_item for item in project.work_items}:
                raise ValueError(f"Work item '{work_item}' does not exist in selected project.")
            self._activate_context(
                project_root=project.project_root,
                workspace_root=project.workspace_root,
                work_item=work_item,
            )
            return {
                "project": project,
                "work_item": work_item,
                "context": self._onboarding_state()["context"],
            }

        created = service.create_work_item(
            raw_project_root=project_root,
            work_item=work_item,
            request_text=_text_from_payload(payload, "request", default=""),
            force_context=bool(payload.get("force_context", False)),
            project_set=self._project_set_from_payload(payload),
        )
        self._activate_context(
            project_root=created.project.project_root,
            workspace_root=created.project.workspace_root,
            work_item=created.work_item,
        )
        return {"created": created, "context": self._onboarding_state()["context"]}

    def _selected_run_id_from_params(self, params: dict[str, list[str]]) -> str:
        run_id = _first_param(params, "run_id")
        if run_id:
            return run_id
        latest = resolve_latest_run_id(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
        )
        if latest is None:
            raise ValueError(f"No run found for work item '{self.work_item}'.")
        return latest

    def _run_timeline(self, params: dict[str, list[str]]) -> object:
        stage = _first_param(params, "stage")
        return resolve_operator_run_timeline(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self._selected_run_id_from_params(params),
            stage=stage,
        )

    def _run_accountability(self, params: dict[str, list[str]]) -> object:
        return resolve_run_accountability(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self._selected_run_id_from_params(params),
        )

    def _run_comparison(self, params: dict[str, list[str]]) -> object:
        baseline_run_id = _first_param(params, "baseline_run_id")
        target_run_id = _first_param(params, "target_run_id")
        if not baseline_run_id:
            raise ValueError("baseline_run_id is required.")
        if not target_run_id:
            raise ValueError("target_run_id is required.")
        return resolve_run_comparison(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            baseline_run_id=baseline_run_id,
            target_run_id=target_run_id,
        )

    def _repository_diff(self, params: dict[str, list[str]]) -> object:
        stage = _first_param(params, "stage", "implement")
        if stage != "implement":
            raise ValueError("Repository diff is currently available for implement stage only.")
        _ = self._selected_run_id_from_params(params)
        return resolve_repository_diff(
            project_root=self.project_root,
            workspace_root=self.workspace_root,
            work_item=self.work_item,
        )

    def _implementation_evidence(self, _params: dict[str, list[str]]) -> object:
        return resolve_implementation_evidence(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
        )

    def _review_findings(self, _params: dict[str, list[str]]) -> object:
        return resolve_review_findings(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
        )

    def _qa_verdict(self, _params: dict[str, list[str]]) -> object:
        return resolve_qa_verdict(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
        )

    def _remediation_requests(self, params: dict[str, list[str]]) -> object:
        run_id = self._selected_run_id_from_params(params)
        return {
            "run_id": run_id,
            "requests": list_remediation_requests(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                run_id=run_id,
            ),
        }

    def _remediation_status(self, params: dict[str, list[str]]) -> object:
        return load_remediation_status(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self._selected_run_id_from_params(params),
        )

    def _validated_remediation_source_ids(
        self,
        *,
        source_stage: str,
        source_ids: tuple[str, ...],
        allow_operator_audit_source_ids: bool = False,
    ) -> tuple[str, ...]:
        if source_stage == "review":
            valid_ids = tuple(
                finding.finding_id
                for finding in resolve_review_findings(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                ).findings
            )
        elif source_stage == "qa":
            verdict = resolve_qa_verdict(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
            )
            valid_ids = tuple(
                f"risk-{index}" for index, _ in enumerate(verdict.residual_risks, 1)
            ) + tuple(f"issue-{index}" for index, _ in enumerate(verdict.known_issues, 1))
        else:
            return source_ids
        valid_lookup = {item.lower(): item for item in valid_ids}
        missing = tuple(
            item
            for item in source_ids
            if item.lower() not in valid_lookup
            and not (
                allow_operator_audit_source_ids
                and item.startswith("OP-")
                and re.fullmatch(r"OP-[A-Za-z0-9_.-]+", item) is not None
            )
        )
        if missing:
            raise ValueError(
                f"source_ids do not match {source_stage} report: {', '.join(missing)}."
            )
        return tuple(valid_lookup.get(item.lower(), item) for item in source_ids)

    def _create_remediation_request(self, payload: dict[str, Any]) -> object:
        source_stage = _text_from_payload(payload, "source_stage")
        source_ids = self._validated_remediation_source_ids(
            source_stage=source_stage,
            source_ids=_remediation_source_ids_from_payload(payload),
            allow_operator_audit_source_ids=bool(payload.get("allow_operator_audit_source_ids")),
        )
        return create_remediation_request(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=_source_run_id_from_payload(payload),
            source_stage=source_stage,
            source_ids=source_ids,
            operator_note=_text_from_payload(payload, "operator_note"),
            target_stage=_text_from_payload(payload, "target_stage", default="implement"),
        )

    def _launch_remediation(self, payload: dict[str, Any]) -> object:
        runtime = _runtime_from_payload(payload)
        _validate_runtime(runtime)
        source_stage = _text_from_payload(payload, "source_stage")
        source_ids = self._validated_remediation_source_ids(
            source_stage=source_stage,
            source_ids=_remediation_source_ids_from_payload(payload),
            allow_operator_audit_source_ids=bool(payload.get("allow_operator_audit_source_ids")),
        )
        request = create_remediation_request(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=_source_run_id_from_payload(payload),
            source_stage=source_stage,
            source_ids=source_ids,
            operator_note=_text_from_payload(payload, "operator_note"),
            target_stage=_text_from_payload(payload, "target_stage", default="implement"),
        )
        log_follow = bool(payload.get("log_follow", True))

        def _target(job_id: str) -> object:
            with acquire_run_mutation_lease(
                run_root(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=request.run_id,
                ),
                operation="ui-remediation:reopen",
            ):
                self._implementation_service(
                    runtime=runtime,
                    run_id=request.run_id,
                    job_id=job_id,
                ).reopen_for_remediation(
                    self._implementation_request(run_id=request.run_id),
                    remediation_id=request.request_id,
                )
            result = self._run_stage(
                stage="implement",
                runtime=runtime,
                run_id=request.run_id,
                log_follow=log_follow,
                job_id=job_id,
            )
            completed = bool(
                result.get("completed", False) if isinstance(result, Mapping) else False
            )
            finalization_blocker = implementation_finalization_blocker(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                run_id=request.run_id,
            )
            completed = completed and finalization_blocker is None
            status = (
                mark_downstream_stale(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=request.run_id,
                    invalidated_by=request.request_id,
                    target_stage=request.target_stage,
                )
                if completed
                else load_remediation_status(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=request.run_id,
                )
            )
            return {
                "request": request,
                "stage_result": result,
                "status": status,
                "exit_code": result.get("exit_code", 0) if isinstance(result, Mapping) else 1,
                "completed": completed,
                "finalization_blocker": finalization_blocker,
            }

        job = cast(
            dict[str, object],
            self._start_job(kind="remediation", stage="implement", target=_target),
        )
        job["request"] = request
        job["run_id"] = request.run_id
        job["runtime"] = runtime
        return job

    def _stale_downstream_stages(self, run_id: str) -> tuple[str, ...]:
        status = load_remediation_status(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=run_id,
        )
        stale = {entry.stage for entry in status.stale_stages}
        return tuple(stage for stage in STAGES if stage in stale)

    def _rerun_stale_downstream(self, payload: dict[str, Any]) -> object:
        runtime = _runtime_from_payload(payload)
        _validate_runtime(runtime)
        run_id = _source_run_id_from_payload(payload)
        stale_stages = self._stale_downstream_stages(run_id)
        if not stale_stages:
            raise ValueError("No stale downstream stages found for this run.")
        log_follow = bool(payload.get("log_follow", True))

        def _target(job_id: str) -> object:
            results: list[object] = []
            completed_stages: list[str] = []
            exit_code = 0
            completed = True
            for stage in stale_stages:
                result = self._run_stage(
                    stage=stage,
                    runtime=runtime,
                    run_id=run_id,
                    log_follow=log_follow,
                    job_id=job_id,
                )
                results.append(result)
                result_exit = int(result.get("exit_code", 1)) if isinstance(result, Mapping) else 1
                if result_exit != 0:
                    exit_code = result_exit
                    completed = False
                    break
                completed_stages.append(stage)
            status = (
                clear_stale_stages(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=run_id,
                    stages=tuple(completed_stages),
                )
                if completed_stages
                else load_remediation_status(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=run_id,
                )
            )
            return {
                "run_id": run_id,
                "runtime": runtime,
                "rerun_stages": stale_stages,
                "stage_results": tuple(results),
                "status": status,
                "exit_code": exit_code,
                "completed": completed,
            }

        job = cast(
            dict[str, object],
            self._start_job(kind="remediation-rerun", stage=None, target=_target),
        )
        job["run_id"] = run_id
        job["runtime"] = runtime
        job["rerun_stages"] = stale_stages
        return job

    def _rerun_remediation_stage(self, payload: dict[str, Any]) -> object:
        runtime = _runtime_from_payload(payload)
        _validate_runtime(runtime)
        run_id = _source_run_id_from_payload(payload)
        stage = _text_from_payload(payload, "stage")
        stale_stages = self._stale_downstream_stages(run_id)
        if stage not in stale_stages:
            raise ValueError(f"Stage '{stage}' is not stale for run '{run_id}'.")
        log_follow = bool(payload.get("log_follow", True))

        def _target(job_id: str) -> object:
            exit_code = 0
            completed = True
            result: object
            try:
                result = self._run_stage(
                    stage=stage,
                    runtime=runtime,
                    run_id=run_id,
                    log_follow=log_follow,
                    job_id=job_id,
                )
                exit_code = int(result.get("exit_code", 1)) if isinstance(result, Mapping) else 1
                completed = exit_code == 0
            except typer.Exit as exc:
                exit_code = int(exc.exit_code or 1)
                completed = False
                result = {"exit_code": exit_code, "completed": False}
            status = (
                clear_stale_stages(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=run_id,
                    stages=(stage,),
                )
                if completed
                else load_remediation_status(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=run_id,
                )
            )
            return {
                "run_id": run_id,
                "runtime": runtime,
                "rerun_stage": stage,
                "stage_result": result,
                "status": status,
                "exit_code": exit_code,
                "completed": completed,
            }

        job = cast(
            dict[str, object],
            self._start_job(kind="remediation-rerun-stage", stage=stage, target=_target),
        )
        job["run_id"] = run_id
        job["runtime"] = runtime
        job["rerun_stage"] = stage
        return job

    def _get_routes(self) -> dict[str, Callable[[dict[str, list[str]]], UiResponse]]:
        return {
            "/api/onboarding/state": lambda params: _json_response(
                self._onboarding_state()
            ),
            "/api/project-home": lambda params: _json_response(
                self._project_home(params)
            ),
            "/api/work-item/resume": lambda params: _json_response(
                self._work_item_resume_context(params)
            ),
            "/api/run": self._get_run,
            "/api/dashboard": self._get_dashboard,
            "/api/run/timeline": lambda params: _json_response(
                self._run_timeline(params)
            ),
            "/api/run/accountability": lambda params: _json_response(
                self._run_accountability(params)
            ),
            "/api/run/comparison": lambda params: _json_response(
                self._run_comparison(params)
            ),
            "/api/repository/diff": lambda params: _json_response(
                self._repository_diff(params)
            ),
            "/api/implement/evidence": lambda params: _json_response(
                self._implementation_evidence(params)
            ),
            "/api/tasks": lambda params: _json_response(self._task_view(params)),
            "/api/review/findings": lambda params: _json_response(
                self._review_findings(params)
            ),
            "/api/qa/verdict": lambda params: _json_response(
                self._qa_verdict(params)
            ),
            "/api/remediation/requests": lambda params: _json_response(
                self._remediation_requests(params)
            ),
            "/api/remediation/status": lambda params: _json_response(
                self._remediation_status(params)
            ),
            "/api/next-flow/source-findings": self._get_next_flow_source_findings,
            "/api/runtime-readiness": lambda params: _json_response(
                self._runtime_readiness()
            ),
            "/api/stage": self._get_stage,
            "/api/questions": self._get_questions,
            "/api/logs": self._get_logs,
            "/api/artifacts": self._get_artifacts,
            "/api/stage/workbench": self._get_stage_workbench,
            "/api/artifacts/evidence-graph": self._get_evidence_graph,
            "/api/artifacts/document": self._get_artifact_document,
        }

    def _get_run(self, params: dict[str, list[str]]) -> UiResponse:
        try:
            return _json_response(
                resolve_operator_run_view(
                    workspace_root=self.workspace_root,
                    work_item=self.work_item,
                    run_id=_first_param(params, "run_id"),
                )
            )
        except ValueError as exc:
            message = str(exc)
            if message.startswith("No runs found for work item "):
                return _json_response({"metadata": None, "message": message})
            raise

    def _get_dashboard(self, params: dict[str, list[str]]) -> UiResponse:
        requested_stage = _first_param(params, "stage")
        stage = requested_stage or STAGES[0]
        return _json_response(
            {
                "app_version": __version__,
                "active_job": self._jobs.active_job(),
                "dashboard": self._dashboard_view(
                    stage=stage,
                    run_id=_first_param(params, "run_id"),
                    use_terminal_default=requested_stage is None,
                ),
            }
        )

    def _get_next_flow_source_findings(
        self,
        params: dict[str, list[str]],
    ) -> UiResponse:
        dashboard = resolve_operator_dashboard_view(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            active_stage="qa",
            run_id=_first_param(params, "run_id"),
            project_root=self.project_root,
        )
        return _json_response(_next_flow_source_findings_payload(dashboard))

    def _get_stage(self, params: dict[str, list[str]]) -> UiResponse:
        stage = _first_param(params, "stage") or STAGES[0]
        return _json_response(
            resolve_operator_stage_view(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                stage=stage,
                run_id=_first_param(params, "run_id"),
            )
        )

    def _get_questions(self, params: dict[str, list[str]]) -> UiResponse:
        stage = _first_param(params, "stage") or STAGES[0]
        return _json_response(
            resolve_operator_questions_view(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                stage=stage,
            )
        )

    def _get_logs(self, params: dict[str, list[str]]) -> UiResponse:
        stage = _first_param(params, "stage") or STAGES[0]
        run_id = _first_param(params, "run_id")
        attempt_number = _optional_attempt(params)
        try:
            summary = resolve_operator_run_log_view(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                stage=stage,
                run_id=run_id,
                attempt_number=attempt_number,
                tail_bytes=_optional_positive_int_param(params, "tail"),
                limit_bytes=_optional_positive_int_param(params, "limit"),
            )
        except ValueError as exc:
            message = str(exc)
            if _is_runtime_log_not_available(message):
                return _json_response(
                    _missing_runtime_log_payload(
                        stage=stage,
                        run_id=run_id,
                        attempt_number=attempt_number,
                        message="Runtime log is not available yet.",
                    )
                )
            raise
        return _json_response(
            {
                "summary": summary.summary,
                "text": summary.text,
                "byte_size": summary.byte_size,
                "start_byte": summary.start_byte,
                "end_byte": summary.end_byte,
                "requested_bytes": summary.requested_bytes,
                "max_bytes": summary.max_bytes,
                "truncated": summary.truncated,
                "truncated_head": summary.truncated_head,
                "truncated_tail": summary.truncated_tail,
                "available": True,
                "message": None,
            }
        )

    def _get_artifacts(self, params: dict[str, list[str]]) -> UiResponse:
        stage = _first_param(params, "stage") or STAGES[0]
        return _json_response(
            resolve_operator_artifacts_view(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                stage=stage,
                run_id=_first_param(params, "run_id"),
                attempt_number=_optional_attempt(params),
            )
        )

    def _get_stage_workbench(self, params: dict[str, list[str]]) -> UiResponse:
        stage = _first_param(params, "stage") or STAGES[0]
        return _json_response(
            resolve_operator_stage_document_workbench(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                stage=stage,
                key=_first_param(params, "key"),
                run_id=_first_param(params, "run_id"),
                attempt_number=_optional_attempt(params),
                preview_limit_bytes=_optional_positive_int_param(
                    params,
                    "preview_limit",
                ),
                source_limit_bytes=_optional_positive_int_param(
                    params,
                    "source_limit",
                ),
            )
        )

    def _get_evidence_graph(self, params: dict[str, list[str]]) -> UiResponse:
        stage = _first_param(params, "stage") or STAGES[0]
        return _json_response(
            resolve_operator_evidence_graph_view(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                stage=stage,
                run_id=_first_param(params, "run_id"),
                attempt_number=_optional_attempt(params),
            )
        )

    def _get_artifact_document(self, params: dict[str, list[str]]) -> UiResponse:
        stage = _first_param(params, "stage") or STAGES[0]
        key = _first_param(params, "key")
        if key is None:
            raise ValueError("key is required.")
        return _json_response(
            resolve_operator_artifact_document_content(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                stage=stage,
                key=key,
                run_id=_first_param(params, "run_id"),
                attempt_number=_optional_attempt(params),
                mode=_first_param(params, "mode", "preview") or "preview",
                limit_bytes=_optional_positive_int_param(params, "limit"),
            )
        )

    def handle_get(self, path: str, params: dict[str, list[str]]) -> UiResponse:
        return self._router.handle_get(path, params)

    def _dashboard_view(
        self,
        *,
        stage: str,
        run_id: str | None,
        use_terminal_default: bool,
    ) -> object:
        dashboard = resolve_operator_dashboard_view(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            active_stage=stage,
            run_id=run_id,
            project_root=self.project_root,
        )
        if (
            use_terminal_default
            and dashboard.first_failure is not None
            and dashboard.first_failure.stage
            and dashboard.first_failure.stage != stage
            and any(item.stage == dashboard.first_failure.stage for item in dashboard.stages)
        ):
            return resolve_operator_dashboard_view(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                active_stage=dashboard.first_failure.stage,
                run_id=run_id,
                project_root=self.project_root,
            )
        if (
            use_terminal_default
            and dashboard.terminal_handoff is not None
            and stage != "qa"
            and any(item.stage == "qa" for item in dashboard.stages)
        ):
            return resolve_operator_dashboard_view(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                active_stage="qa",
                run_id=run_id,
                project_root=self.project_root,
            )
        return dashboard

    def _post_routes(self) -> dict[str, Callable[[dict[str, Any]], UiResponse]]:
        return {
            "/api/onboarding/project": lambda payload: _json_response(
                self._inspect_onboarding_project(payload)
            ),
            "/api/onboarding/project-set": lambda payload: _json_response(
                self._validate_onboarding_project_set(payload)
            ),
            "/api/onboarding/work-item": lambda payload: _json_response(
                self._setup_onboarding_work_item(payload)
            ),
            "/api/answers": self._post_answer,
            "/api/stage/run": lambda payload: _json_response(
                self._start_stage_job(payload)
            ),
            "/api/stage/interact": lambda payload: _json_response(
                self._start_stage_interact_job(payload)
            ),
            "/api/tasks/run": lambda payload: _json_response(
                self._start_task_job(payload),
                status=HTTPStatus.ACCEPTED,
            ),
            "/api/tasks/finalize": lambda payload: _json_response(
                self._start_task_finalize_job(payload),
                status=HTTPStatus.ACCEPTED,
            ),
            "/api/remediation/request": lambda payload: _json_response(
                self._create_remediation_request(payload),
                status=HTTPStatus.CREATED,
            ),
            "/api/remediation/launch": lambda payload: _json_response(
                self._launch_remediation(payload),
                status=HTTPStatus.ACCEPTED,
            ),
            "/api/remediation/rerun-downstream": lambda payload: _json_response(
                self._rerun_stale_downstream(payload),
                status=HTTPStatus.ACCEPTED,
            ),
            "/api/remediation/rerun-stage": lambda payload: _json_response(
                self._rerun_remediation_stage(payload),
                status=HTTPStatus.ACCEPTED,
            ),
            "/api/next-flow/preflight": self._next_flow_preflight,
            "/api/next-flow/follow-up-draft": self._next_flow_follow_up_draft,
            "/api/next-flow/follow-up-draft/create": self._next_flow_create_follow_up_draft,
            "/api/next-flow/clone-draft/create": self._next_flow_create_clone_draft,
            "/api/next-flow/launch": self._next_flow_launch,
            "/api/next-flow/archive": self._next_flow_archive,
            "/api/workflow/run": lambda payload: _json_response(
                self._start_workflow_job(payload)
            ),
            "/api/open-folder": lambda payload: _json_response(
                self._open_folder(payload)
            ),
            "/api/server/stop": lambda payload: _json_response(
                self._request_server_stop()
            ),
        }

    def _post_answer(self, payload: dict[str, Any]) -> UiResponse:
        stage = str(payload.get("stage", STAGES[0])).strip() or STAGES[0]
        question_id = str(payload.get("question_id", "")).strip()
        text = str(payload.get("text", "")).strip()
        raw_resolution = str(
            payload.get("resolution", AnswerResolution.RESOLVED)
        ).strip()
        if not question_id:
            return _error_response("question_id is required.")
        if not text:
            return _error_response("text is required.")
        return _json_response(
            persist_operator_answer(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                stage=stage,
                question_id=question_id,
                text=text,
                resolution=AnswerResolution(raw_resolution),
            )
        )

    def handle_post(self, path: str, payload: dict[str, Any]) -> UiResponse:
        return self._router.handle_post(path, payload)

    def consume_shutdown_requested(self) -> bool:
        if not self._shutdown_requested:
            return False
        self._shutdown_requested = False
        return True

    def _handle_job_get(self, *, path: str, params: dict[str, list[str]]) -> UiResponse:
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["api", "jobs"]:
            return _json_response(self._jobs.view(parts[2]))
        if len(parts) == 4 and parts[:2] == ["api", "jobs"] and parts[3] == "logs":
            return _json_response(self._jobs.logs(parts[2], cursor=_cursor_param(params)))
        if len(parts) == 4 and parts[:2] == ["api", "jobs"] and parts[3] == "operator-requests":
            return _json_response(self._job_operator_requests(parts[2]))
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)

    def _handle_job_post(self, *, path: str, payload: dict[str, Any]) -> UiResponse:
        parts = path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "jobs"] and parts[3] == "cancel":
            return _json_response(self._operator_decisions.cancel(parts[2]))
        if (
            len(parts) == 6
            and parts[:2] == ["api", "jobs"]
            and parts[3] == "operator-requests"
            and parts[5] == "decision"
        ):
            if not _is_loopback_host(self.options.host) and not self.options.allow_remote_approvals:
                return _error_response(
                    "remote approval decisions require --allow-remote-approvals.",
                    status=HTTPStatus.FORBIDDEN,
                )
            return _json_response(
                self._record_operator_decision(
                    job_id=parts[2],
                    request_id=parts[4],
                    payload=payload,
                )
            )
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)

    def _remote_mutation_error(self, path: str) -> UiResponse | None:
        if _is_loopback_host(self.options.host):
            return None
        if (
            self.options.allow_remote_approvals
            and path.startswith("/api/jobs/")
            and path.endswith("/decision")
        ):
            return None
        return _error_response(
            "remote UI mutations require loopback host; bind to 127.0.0.1 or use a local tunnel with explicit operator controls.",
            status=HTTPStatus.FORBIDDEN,
        )

    def _job_attempt_path(self, job_id: str) -> Path | None:
        job = self._jobs.view(job_id)
        raw_attempt_path = job.get("attempt_path")
        if isinstance(raw_attempt_path, str) and raw_attempt_path:
            return Path(raw_attempt_path)
        result = job.get("result")
        stage = job.get("stage")
        run_id: object = None
        if isinstance(result, Mapping):
            stage = result.get("stage") or stage
            run_id = result.get("run_id")
        if not isinstance(stage, str):
            return None
        selected_run_id = (
            run_id
            if isinstance(run_id, str) and run_id
            else resolve_latest_run_id(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
            )
        )
        if selected_run_id is None:
            return None
        return _latest_attempt_path(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=selected_run_id,
            stage=stage,
        )

    def _job_operator_requests(self, job_id: str) -> dict[str, object]:
        self._jobs.view(job_id)
        return _operator_request_view(self._job_attempt_path(job_id))

    def _wait_for_operator_decision(
        self,
        *,
        job_id: str,
        request: RuntimeOperatorRequest,
        attempt_path: Path,
    ) -> RuntimeOperatorDecision | None:
        return self._operator_decisions.wait(
            job_id=job_id,
            request=request,
            attempt_path=attempt_path,
        )

    def _record_operator_decision(
        self,
        *,
        job_id: str,
        request_id: str,
        payload: dict[str, Any],
    ) -> dict[str, object]:
        attempt_path = self._job_attempt_path(job_id)
        if attempt_path is None:
            raise ValueError("job has no attempt operator request context.")
        requests = load_operator_requests(attempt_path / OPERATOR_REQUESTS_FILENAME)
        if request_id not in {request.id for request in requests}:
            raise ValueError(f"Unknown operator request '{request_id}'.")
        raw_action = str(payload.get("action", "")).strip()
        if not raw_action:
            raise ValueError("action is required.")
        decision = RuntimeOperatorDecision(
            request_id=request_id,
            action=RuntimeOperatorDecisionAction(raw_action),
            source=RuntimeOperatorDecisionSource.UI,
            reason=None if payload.get("reason") is None else str(payload.get("reason")),
        )
        self._operator_decisions.decide(
            job_id=job_id,
            attempt_path=attempt_path,
            decision=decision,
        )
        return _operator_request_view(attempt_path)

    def _start_stage_job(self, payload: dict[str, Any]) -> object:
        stage = _stage_from_payload(payload)
        runtime = _runtime_from_payload(payload)
        _validate_runtime(runtime)
        log_follow = bool(payload.get("log_follow", True))
        run_id = str(payload.get("run_id", "")).strip() or None

        def _target(job_id: str) -> object:
            return self._run_stage(
                stage=stage,
                runtime=runtime,
                run_id=run_id,
                log_follow=log_follow,
                job_id=job_id,
            )

        return self._start_job(kind="stage", stage=stage, target=_target)

    def _target_documents_from_payload(self, payload: dict[str, Any]) -> tuple[str, ...]:
        raw_targets = payload.get("target_documents", ())
        if raw_targets is None:
            return ()
        if not isinstance(raw_targets, list):
            raise ValueError("target_documents must be an array.")
        targets: list[str] = []
        for item in raw_targets:
            if not isinstance(item, str):
                raise ValueError("target_documents entries must be strings.")
            normalized = item.strip()
            if normalized:
                targets.append(normalized)
        return tuple(targets)

    def _start_stage_interact_job(self, payload: dict[str, Any]) -> object:
        stage = _stage_from_payload(payload)
        runtime = _runtime_from_payload(payload)
        _validate_runtime(runtime)
        raw_request = payload.get("request")
        if not isinstance(raw_request, str) or not raw_request.strip():
            raise ValueError("request is required.")
        target_documents = self._target_documents_from_payload(payload)
        log_follow = bool(payload.get("log_follow", True))
        run_id = str(payload.get("run_id", "")).strip() or None

        def _target(job_id: str) -> object:
            return self._run_stage_interact(
                stage=stage,
                runtime=runtime,
                run_id=run_id,
                request=raw_request.strip(),
                target_documents=target_documents,
                log_follow=log_follow,
                job_id=job_id,
            )

        return self._start_job(kind="intervention", stage=stage, target=_target)

    def _run_stage(
        self,
        *,
        stage: str,
        runtime: str,
        run_id: str | None,
        log_follow: bool,
        job_id: str,
    ) -> object:
        selected_run_id = run_id
        try:
            self._stage_runner(
                StageRunOptions(
                    stage=stage,
                    work_item=self.work_item,
                    runtime=runtime,
                    run_id=run_id,
                    root=self.workspace_root,
                    config=self.config_path,
                    log_follow=log_follow,
                    runtime_chunk_sink=lambda stream, text: self._jobs.append_chunk(
                        job_id,
                        stream=stream,
                        text=text,
                    ),
                    runtime_operator_decision_provider=_UiRuntimeOperatorDecisionProvider(
                        service=self,
                        job_id=job_id,
                    ),
                    cancel_requested=lambda: self._jobs.cancel_requested(job_id),
                )
            )
        except typer.Exit as exc:
            exit_code = int(exc.exit_code or 0)
            selected_run_id = selected_run_id or resolve_latest_run_id(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
            )
            operator_view = (
                _operator_request_view(
                    _latest_attempt_path(
                        workspace_root=self.workspace_root,
                        work_item=self.work_item,
                        run_id=selected_run_id,
                        stage=stage,
                    )
                )
                if selected_run_id is not None
                else _operator_request_view(None)
            )
            return {
                "stage": stage,
                "runtime": runtime,
                "run_id": selected_run_id,
                "exit_code": exit_code,
                "completed": exit_code == 0,
                "waiting_for_operator": bool(operator_view["pending_request_ids"]),
            }
        selected_run_id = selected_run_id or resolve_latest_run_id(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
        )
        return {
            "stage": stage,
            "runtime": runtime,
            "run_id": selected_run_id,
            "exit_code": 0,
            "completed": True,
        }

    def _run_stage_interact(
        self,
        *,
        stage: str,
        runtime: str,
        run_id: str | None,
        request: str,
        target_documents: tuple[str, ...],
        log_follow: bool,
        job_id: str,
    ) -> object:
        try:
            self._stage_interact_runner(
                StageInteractOptions(
                    stage=stage,
                    work_item=self.work_item,
                    runtime=runtime,
                    run_id=run_id,
                    root=self.workspace_root,
                    config=self.config_path,
                    request=request,
                    request_file=None,
                    target_documents=target_documents,
                    log_follow=log_follow,
                    runtime_chunk_sink=lambda stream, text: self._jobs.append_chunk(
                        job_id,
                        stream=stream,
                        text=text,
                    ),
                    cancel_requested=lambda: self._jobs.cancel_requested(job_id),
                )
            )
        except typer.Exit as exc:
            exit_code = int(exc.exit_code or 0)
            return {
                "stage": stage,
                "runtime": runtime,
                "run_id": run_id,
                "target_documents": target_documents,
                "exit_code": exit_code,
                "completed": exit_code == 0,
            }
        return {
            "stage": stage,
            "runtime": runtime,
            "run_id": run_id,
            "target_documents": target_documents,
            "exit_code": 0,
            "completed": True,
        }

    def _start_workflow_job(self, payload: dict[str, Any]) -> object:
        self._require_context()
        runtime = _runtime_from_payload(payload)
        _validate_runtime(runtime)
        stage_start, stage_end = _workflow_bounds_from_payload(payload)
        requested_run_id = _optional_run_id_from_payload(payload)
        run_id = requested_run_id or allocate_workflow_run_id(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
        )
        log_follow = bool(payload.get("log_follow", True))
        prepared_payload = dict(payload)
        prepared_payload["runtime"] = runtime
        prepared_payload["from_stage"] = stage_start
        prepared_payload["to_stage"] = stage_end
        prepared_payload["run_id"] = run_id
        prepared_payload["continuation"] = requested_run_id is not None
        prepared_payload["log_follow"] = log_follow
        lease = acquire_run_mutation_lease_handle(
            run_root(
                workspace_root=self.workspace_root,
                work_item=self.work_item,
                run_id=run_id,
            ),
            operation="ui-workflow",
        )

        def _target(job_id: str) -> object:
            with use_transferred_run_mutation_lease(lease):
                return self._run_workflow(prepared_payload, job_id=job_id)

        try:
            return self._start_job(kind="workflow", stage=None, target=_target)
        except Exception:
            release_run_mutation_lease(lease)
            raise

    def _next_flow_preflight(self, payload: dict[str, Any]) -> UiResponse:
        result = validate_next_flow_launch_preflight(
            NextFlowLaunchPreflightRequest(
                workspace_root=self.workspace_root,
                source_work_item=_source_work_item_from_payload(
                    payload,
                    default=self.work_item,
                ),
                source_run_id=_source_run_id_from_payload(payload),
                runtime_id=_runtime_from_payload(payload),
                contracts_root=_contracts_root_from_payload(payload),
                baseline_id=_optional_baseline_id_from_payload(payload),
            )
        )
        if result.status == "blocked":
            return _json_response(result.error_payload, status=HTTPStatus.CONFLICT)
        return _json_response({"preflight": result})

    def _next_flow_follow_up_draft(self, payload: dict[str, Any]) -> UiResponse:
        dashboard = resolve_operator_dashboard_view(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            active_stage="qa",
            run_id=_source_run_id_from_payload(payload),
            project_root=self.project_root,
        )
        return _json_response(
            _next_flow_follow_up_draft_payload(
                dashboard=dashboard,
                selected_source_ids=_selected_source_ids_from_payload(payload),
            )
        )

    def _next_flow_create_follow_up_draft(self, payload: dict[str, Any]) -> UiResponse:
        source_work_item = _source_work_item_from_payload(
            payload,
            default=self.work_item,
        )
        source_run_id = _source_run_id_from_payload(payload)
        selected_source_ids = _selected_source_ids_from_payload(payload)
        dashboard = resolve_operator_dashboard_view(
            workspace_root=self.workspace_root,
            work_item=source_work_item,
            active_stage="qa",
            run_id=source_run_id,
            project_root=self.project_root,
        )
        draft_payload = _next_flow_follow_up_draft_payload(
            dashboard=dashboard,
            selected_source_ids=selected_source_ids,
            new_work_item=_text_from_payload(
                payload,
                "new_work_item",
                default=f"{source_work_item}-FOLLOW-UP",
            ),
            title=_text_from_payload(
                payload,
                "title",
                default=f"Follow-up for {source_work_item} from {source_run_id}",
            ),
        )
        draft = cast(dict[str, object], draft_payload["draft"])
        selected_sources = cast(
            tuple[dict[str, object], ...],
            draft["selected_sources"],
        )
        first_stage_input = (
            _optional_text_from_payload(payload, "first_stage_input")
            or _optional_text_from_payload(payload, "first_stage_input_preview")
            or str(draft["first_stage_input_preview"]).strip()
        )
        acceptance_criteria = _optional_string_tuple_from_payload(
            payload,
            "acceptance_criteria",
        )
        required_evidence = _optional_string_tuple_from_payload(
            payload,
            "required_evidence",
        )
        inherited_context = _optional_string_tuple_from_payload(
            payload,
            "inherited_context",
        )
        resolved_acceptance_criteria = (
            acceptance_criteria
            if acceptance_criteria is not None
            else _draft_string_tuple(draft, "acceptance_criteria")
        )
        resolved_required_evidence = (
            required_evidence
            if required_evidence is not None
            else _draft_string_tuple(draft, "required_evidence")
        )
        resolved_inherited_context = (
            inherited_context
            if inherited_context is not None
            else _draft_inherited_context_lines(draft)
        )
        draft["first_stage_input_preview"] = first_stage_input
        draft["acceptance_criteria"] = resolved_acceptance_criteria
        draft["required_evidence"] = resolved_required_evidence
        draft["inherited_context_lines"] = resolved_inherited_context
        result = create_follow_up_work_item_draft(
            FollowUpDraftRequest(
                workspace_root=self.workspace_root,
                source_work_item=source_work_item,
                source_run_id=source_run_id,
                new_work_item=str(draft["new_work_item"]),
                title=str(draft["title"]),
                selections=_follow_up_source_selections_from_items(selected_sources),
                first_stage_input=first_stage_input,
                acceptance_criteria=resolved_acceptance_criteria,
                required_evidence=resolved_required_evidence,
                inherited_context=resolved_inherited_context,
                project_root=self.project_root,
            )
        )
        return _json_response(
            {
                "draft": draft,
                "created": _follow_up_creation_payload(
                    workspace_root=self.workspace_root,
                    result=result,
                ),
            },
            status=HTTPStatus.CREATED,
        )

    def _next_flow_create_clone_draft(self, payload: dict[str, Any]) -> UiResponse:
        source_work_item = _source_work_item_from_payload(
            payload,
            default=self.work_item,
        )
        source_run_id = _source_run_id_from_payload(payload)
        new_work_item = _text_from_payload(
            payload,
            "new_work_item",
            default=f"{source_work_item}-CLONE",
        )
        title = _text_from_payload(
            payload,
            "title",
            default=f"Clone {source_work_item} from {source_run_id}",
        )
        result = create_clone_flow_draft(
            CloneFlowDraftRequest(
                workspace_root=self.workspace_root,
                source_work_item=source_work_item,
                source_run_id=source_run_id,
                new_work_item=new_work_item,
                title=title,
                project_root=self.project_root,
            )
        )
        return _json_response(
            {
                "draft": {
                    "source_work_item": source_work_item,
                    "source_run_id": source_run_id,
                    "new_work_item": result.work_item,
                    "title": title,
                },
                "created": _clone_creation_payload(
                    workspace_root=self.workspace_root,
                    result=result,
                ),
            },
            status=HTTPStatus.CREATED,
        )

    def _next_flow_launch(self, payload: dict[str, Any]) -> UiResponse:
        source_work_item = _source_work_item_from_payload(
            payload,
            default=self.work_item,
        )
        source_run_id = _source_run_id_from_payload(payload)
        new_work_item = _text_from_payload(payload, "new_work_item")
        runtime = _runtime_from_payload(payload)
        _validate_runtime(runtime)
        preflight = validate_next_flow_launch_preflight(
            NextFlowLaunchPreflightRequest(
                workspace_root=self.workspace_root,
                source_work_item=source_work_item,
                source_run_id=source_run_id,
                runtime_id=runtime,
                contracts_root=_contracts_root_from_payload(payload),
                baseline_id=_optional_baseline_id_from_payload(payload),
            )
        )
        if preflight.status == "blocked":
            return _json_response(preflight.error_payload, status=HTTPStatus.CONFLICT)
        lineage = _next_flow_launch_lineage(
            source_work_item=source_work_item,
            source_run_id=source_run_id,
            baseline_id=preflight.resolved_baseline_id,
            relationship=_text_from_payload(
                payload,
                "relationship",
                default="follow-up",
            ),
        )
        prepared_payload = dict(payload)
        prepared_payload["runtime"] = runtime
        prepared_payload["log_follow"] = bool(payload.get("log_follow", True))

        def _target(job_id: str) -> object:
            return self._run_workflow(
                prepared_payload,
                job_id=job_id,
                work_item=new_work_item,
                config_snapshot_extra={
                    "mode": "ui-next-flow-launch",
                    "source_work_item": source_work_item,
                    "source_run_id": source_run_id,
                    "new_work_item": new_work_item,
                },
                lineage=lineage,
            )

        job = cast(
            dict[str, object],
            self._start_job(kind="next-flow-launch", stage=None, target=_target),
        )
        job["work_item"] = new_work_item
        job["source_work_item"] = source_work_item
        job["source_run_id"] = source_run_id
        job["lineage"] = lineage
        job["preflight"] = preflight
        return _json_response(job, status=HTTPStatus.ACCEPTED)

    def _next_flow_archive(self, payload: dict[str, Any]) -> UiResponse:
        run_id = _source_run_id_from_payload(payload)
        work_item = _source_work_item_from_payload(
            payload,
            default=self.work_item,
        )
        reason = payload.get("reason")
        if reason is not None and not isinstance(reason, str):
            raise ValueError("reason must be a string.")
        dashboard = resolve_operator_dashboard_view(
            workspace_root=self.workspace_root,
            work_item=work_item,
            active_stage="qa",
            run_id=run_id,
            project_root=self.project_root,
        )
        if dashboard.terminal_handoff is None:
            raise ValueError("archive decision requires a terminal QA run.")
        archive = persist_run_archive_decision(
            workspace_root=self.workspace_root,
            work_item=work_item,
            run_id=run_id,
            reason=reason,
            source="ui",
        )
        updated_dashboard = resolve_operator_dashboard_view(
            workspace_root=self.workspace_root,
            work_item=work_item,
            active_stage="qa",
            run_id=run_id,
            project_root=self.project_root,
        )
        return _json_response(
            {
                "archive": archive,
                "dashboard": updated_dashboard,
            }
        )

    def _start_job(
        self,
        *,
        kind: str,
        stage: str | None,
        target: Callable[[str], object],
    ) -> object:
        job_id = self._jobs.create(kind=kind, stage=stage)

        def _run() -> None:
            self._jobs.append_chunk(
                job_id,
                stream="system",
                text=f"AIDD UI {kind} job started.\n",
            )
            try:
                result = target(job_id)
                exit_code = _exit_code_from_result(result)
                if isinstance(result, Mapping) and bool(result.get("waiting_for_operator")):
                    self._jobs.wait_for_operator(
                        job_id,
                        result=result,
                        exit_code=exit_code,
                        message="waiting for operator decision",
                    )
                    return
                self._jobs.complete(
                    job_id,
                    result=result,
                    exit_code=exit_code,
                    message="completed" if exit_code == 0 else "stopped",
                )
            except Exception as exc:  # pragma: no cover - defensive job boundary
                self._jobs.append_chunk(
                    job_id,
                    stream="system",
                    text=f"AIDD UI {kind} job failed: {exc}\n",
                )
                self._jobs.fail(job_id, message=str(exc), exit_code=1)

        threading.Thread(target=_run, name=f"aidd-ui-{kind}-{job_id}", daemon=True).start()
        return {"job_id": job_id, "stage": stage, "kind": kind}

    def _run_workflow(
        self,
        payload: dict[str, Any],
        *,
        job_id: str,
        work_item: str | None = None,
        config_snapshot_extra: Mapping[str, Any] | None = None,
        lineage: Mapping[str, Any] | None = None,
    ) -> object:
        runtime = _runtime_from_payload(payload)
        stage_start, stage_end = _workflow_bounds_from_payload(payload)
        run_id = _optional_run_id_from_payload(payload)
        log_follow = bool(payload.get("log_follow", True))
        target_work_item = work_item or self.work_item
        cfg = load_config(self.config_path)
        runtime_command = _runtime_command_for_runtime(runtime=runtime, cfg=cfg)
        runtime_execution_mode = _runtime_execution_mode_for_runtime(runtime=runtime, cfg=cfg)
        runtime_config = cfg.runtime_config(runtime)
        config_snapshot: dict[str, Any] = {
            "config_path": self.config_path.as_posix(),
            "workspace_root": self.workspace_root.as_posix(),
            "runtime_command": runtime_command,
            "runtime_execution_mode": runtime_execution_mode.value,
            "runtime_permission_policy": runtime_config.permission_policy.value,
            "runtime_interaction_mode": runtime_config.interaction_mode.value,
            "runtime_auto_approval_preset": runtime_config.auto_approval_preset.value,
            "log_follow": log_follow,
            "mode": "ui-workflow",
        }
        if config_snapshot_extra is not None:
            config_snapshot.update(config_snapshot_extra)

        def _stage_executor(request: WorkflowStageExecutionRequest) -> None:
            try:
                self._stage_runner(
                    StageRunOptions(
                        stage=request.stage,
                        work_item=request.work_item,
                        runtime=request.runtime_id,
                        run_id=request.run_id,
                        root=request.workspace_root,
                        config=request.config_path,
                        log_follow=request.log_follow,
                        runtime_chunk_sink=lambda stream, text: self._jobs.append_chunk(
                            job_id,
                            stream=stream,
                            text=text,
                        ),
                        runtime_operator_decision_provider=_UiRuntimeOperatorDecisionProvider(
                            service=self,
                            job_id=job_id,
                        ),
                        cancel_requested=lambda: self._jobs.cancel_requested(job_id),
                    )
                )
            except typer.Exit as exc:
                if exc.exit_code in (None, 0):
                    return
                raise WorkflowStageExecutionError(
                    stage=request.stage,
                    exit_code=int(exc.exit_code),
                ) from exc

        return self._workflow_runner(
            request=WorkflowRunRequest(
                work_item=target_work_item,
                runtime_id=runtime,
                workspace_root=self.workspace_root,
                config_path=self.config_path,
                config_snapshot=config_snapshot,
                lineage=lineage,
                run_id=run_id,
                continuation=bool(payload.get("continuation", False)),
                stage_start=stage_start,
                stage_end=stage_end,
                log_follow=log_follow,
            ),
            stage_executor=_stage_executor,
            emit=lambda event: self._jobs.append_chunk(
                job_id,
                stream="system",
                text=(
                    f"workflow {event.kind}: {event.stage}\n"
                    if event.stage is not None
                    else f"workflow {event.kind}\n"
                ),
            ),
        )

    def _runtime_readiness_for_config(self, config_path: Path) -> object:
        cfg = load_config(config_path)
        return resolve_runtime_readiness(
            config=cfg,
            probe_reports=self._readiness_probe_provider(cfg),
            command_sources=_runtime_command_sources_from_config(config_path),
        )

    def _runtime_readiness(self) -> object:
        return self._runtime_readiness_for_config(self.config_path)

    def _ensure_local_only_action(self) -> None:
        if not _is_loopback_host(self.options.host):
            raise ValueError("Local-only UI action is available only on loopback hosts.")

    def _open_folder(self, payload: dict[str, Any]) -> object:
        self._ensure_local_only_action()
        raw_target = payload.get("target")
        if not isinstance(raw_target, str):
            raise ValueError("target is required.")
        target = raw_target.strip()
        if target == "workspace":
            folder = self.workspace_root
        elif target == "stage":
            stage = str(payload.get("stage", "")).strip()
            if not is_valid_stage(stage):
                raise ValueError(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}.")
            folder = self.workspace_root / "workitems" / self.work_item / "stages" / stage
        elif target == "artifact":
            raw_path = payload.get("path")
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise ValueError("path is required for artifact folder target.")
            relative_path = Path(raw_path.strip())
            if relative_path.is_absolute():
                raise ValueError("artifact path must be workspace-relative.")
            workspace = self.workspace_root.resolve(strict=False)
            resolved = (self.workspace_root / relative_path).resolve(strict=False)
            if not resolved.is_relative_to(workspace):
                raise ValueError("artifact path escapes workspace root.")
            folder = resolved if resolved.is_dir() else resolved.parent
        else:
            raise ValueError(
                "unsupported folder target. Expected one of: workspace, stage, artifact."
            )

        resolved_workspace = self.workspace_root.resolve(strict=False)
        resolved_folder = folder.resolve(strict=False)
        if not resolved_folder.is_relative_to(resolved_workspace):
            raise ValueError("folder path escapes workspace root.")
        if not resolved_folder.exists() or not resolved_folder.is_dir():
            raise ValueError(f"folder does not exist: {resolved_folder.as_posix()}.")
        self._folder_opener(resolved_folder)
        return {"opened": resolved_folder.as_posix(), "target": target}

    def _request_server_stop(self) -> object:
        self._ensure_local_only_action()
        self._shutdown_requested = True
        return {
            "status": "stopping",
            "runtime_job_cancellation": False,
            "message": "Stopping the local UI server only; active runtime jobs are not cancelled.",
        }


def run_ui_server(options: UiServerOptions) -> None:
    service = OperatorUiService(options)
    server = ThreadingHTTPServer(
        (options.host, options.port),
        handler_for(router=service._router, shutdown_service=service),
    )
    host, port = cast(tuple[str, int], server.server_address[:2])
    _warn_if_non_loopback_host(options.host)
    console.print(f"AIDD UI: http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("AIDD UI stopped.")
    finally:
        server.server_close()


def ui_command(
    work_item: Annotated[str | None, typer.Option("--work-item", help="Work item id")] = None,
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to an AIDD TOML config file."),
    ] = Path("aidd.example.toml"),
    host: Annotated[
        str,
        typer.Option("--host", help="Local bind host for the operator UI."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", help="Local bind port; use 0 to allocate one."),
    ] = 0,
    allow_remote_approvals: Annotated[
        bool,
        typer.Option(
            "--allow-remote-approvals",
            help="Enable runtime approval decisions when the UI is bound off loopback.",
        ),
    ] = False,
) -> None:
    """Start the local operator UI."""
    workspace_root = root.resolve(strict=False) if work_item is not None else root
    run_ui_server(
        UiServerOptions(
            work_item=work_item,
            root=workspace_root,
            config=config,
            host=host,
            port=port,
            allow_remote_approvals=allow_remote_approvals,
        )
    )


__all__ = [
    "OperatorUiService",
    "UiServerOptions",
    "run_ui_server",
    "ui_command",
]
