from __future__ import annotations

import subprocess
import sys
import threading
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ruff: noqa: E501
from ipaddress import ip_address
from pathlib import Path
from typing import Annotated, Any, cast
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import typer

from aidd import __version__
from aidd.adapters.runtime_registry import runtime_definitions
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.cli.stage_run import (
    StageInteractOptions,
    StageRunOptions,
    run_stage_command,
    run_stage_interact_command,
)
from aidd.cli.support import (
    _execution_command_available,
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    console,
)
from aidd.cli.ui_assets import _INDEX_HTML, _OPERATOR_CSS, _OPERATOR_JS
from aidd.cli.ui_http import (
    UiRequestBodyTooLarge,
    UiResponse,
    _error_response,
    _json_response,
    _read_json_body,
)
from aidd.config import AiddConfig, load_config
from aidd.core.interview import AnswerResolution
from aidd.core.operator_frontend import (
    persist_operator_answer,
    resolve_operator_artifact_document_content,
    resolve_operator_artifacts_view,
    resolve_operator_dashboard_view,
    resolve_operator_questions_view,
    resolve_operator_run_log_view,
    resolve_operator_run_view,
    resolve_operator_stage_view,
)
from aidd.core.run_lookup import latest_run_id as resolve_latest_run_id
from aidd.core.run_store import next_attempt_number, run_attempt_root
from aidd.core.runtime_operator import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    RuntimeOperatorDecision,
    RuntimeOperatorRequest,
    append_operator_decision,
    load_operator_decisions,
    load_operator_requests,
    unapproved_operator_request_ids,
)
from aidd.core.runtime_readiness import (
    RuntimeCommandSource,
    RuntimeReadinessProbeReport,
    resolve_runtime_readiness,
)
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.workflow_service import (
    WorkflowRunRequest,
    WorkflowRunResult,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
    run_workflow,
)
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


@dataclass(frozen=True, slots=True)
class UiServerOptions:
    work_item: str
    root: Path
    config: Path
    host: str
    port: int
    allow_remote_approvals: bool = False


@dataclass(slots=True)
class _UiRunJob:
    job_id: str
    kind: str
    stage: str | None
    status: str
    created_at_utc: str
    updated_at_utc: str
    exit_code: int | None = None
    message: str = ""
    result: object | None = None
    attempt_path: str | None = None
    cancel_requested_at_utc: str | None = None
    cancelled_at_utc: str | None = None
    chunks: list[dict[str, object]] = field(default_factory=list)


class UiRunJobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, _UiRunJob] = {}

    def create(self, *, kind: str, stage: str | None) -> str:
        job_id = f"job-{uuid4().hex}"
        timestamp = _utc_now()
        with self._lock:
            self._jobs[job_id] = _UiRunJob(
                job_id=job_id,
                kind=kind,
                stage=stage,
                status="running",
                created_at_utc=timestamp,
                updated_at_utc=timestamp,
            )
        return job_id

    def append_chunk(self, job_id: str, *, stream: str, text: str) -> None:
        if not text:
            return
        with self._lock:
            job = self._require_job(job_id)
            self._append_chunk_locked(job, stream=stream, text=text)
            job.updated_at_utc = _utc_now()

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
            job.updated_at_utc = _utc_now()

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
            job.updated_at_utc = _utc_now()

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
            job.updated_at_utc = _utc_now()

    def mark_running(self, job_id: str, *, message: str = "running") -> None:
        with self._lock:
            job = self._require_job(job_id)
            if job.status in {"cancelling", *_TERMINAL_JOB_STATUSES}:
                return
            job.status = "running"
            job.exit_code = None
            job.result = None
            job.message = message
            job.updated_at_utc = _utc_now()

    def set_attempt_path(self, job_id: str, attempt_path: Path) -> None:
        with self._lock:
            job = self._require_job(job_id)
            job.attempt_path = attempt_path.as_posix()
            job.updated_at_utc = _utc_now()

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

            timestamp = _utc_now()
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
            return payload

    def cancel_requested(self, job_id: str) -> bool:
        with self._lock:
            job = self._require_job(job_id)
            return job.cancel_requested_at_utc is not None

    def view(self, job_id: str) -> dict[str, object]:
        with self._lock:
            job = self._require_job(job_id)
            return self._view_locked(job)

    def logs(self, job_id: str, *, cursor: int) -> dict[str, object]:
        with self._lock:
            job = self._require_job(job_id)
            safe_cursor = min(max(cursor, 0), len(job.chunks))
            return {
                "job_id": job.job_id,
                "cursor": len(job.chunks),
                "chunks": tuple(job.chunks[safe_cursor:]),
            }

    def _require_job(self, job_id: str) -> _UiRunJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise ValueError(f"Unknown UI job '{job_id}'.") from exc

    def _append_chunk_locked(self, job: _UiRunJob, *, stream: str, text: str) -> None:
        job.chunks.append(
            {
                "sequence": len(job.chunks) + 1,
                "stream": stream,
                "text": text,
            }
        )

    def _mark_cancelled_locked(self, job: _UiRunJob, *, message: str) -> None:
        timestamp = _utc_now()
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
            "cancel_requested": job.cancel_requested_at_utc is not None,
            "cancel_requested_at_utc": job.cancel_requested_at_utc,
            "cancelled_at_utc": job.cancelled_at_utc,
            "cancel_state": cancel_state,
        }


@dataclass(slots=True)
class _UiOperatorDecisionWaiter:
    condition: threading.Condition = field(default_factory=threading.Condition)
    decision: RuntimeOperatorDecision | None = None


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


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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
        }
    requests_path = attempt_path / OPERATOR_REQUESTS_FILENAME
    decisions_path = attempt_path / OPERATOR_DECISIONS_FILENAME
    requests = load_operator_requests(requests_path)
    decisions = load_operator_decisions(decisions_path)
    decided_ids = {decision.request_id for decision in decisions}
    return {
        "attempt_path": attempt_path.as_posix(),
        "requests_path": requests_path.as_posix() if requests_path.exists() else None,
        "decisions_path": decisions_path.as_posix() if decisions_path.exists() else None,
        "requests": tuple(request.to_dict() for request in requests),
        "pending_request_ids": tuple(
            request.id for request in requests if request.id not in decided_ids
        ),
        "unapproved_request_ids": unapproved_operator_request_ids(attempt_path=attempt_path),
        "decisions": tuple(decision.to_dict() for decision in decisions),
    }


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
    for definition in runtime_definitions():
        provider_report = get_runtime_adapter_surface(definition.runtime_id).probe(
            definition.probe_command
        )
        runtime_config = cfg.runtime_config(definition.runtime_id)
        reports[definition.runtime_id] = RuntimeReadinessProbeReport(
            provider_available=provider_report.available,
            execution_command_available=_execution_command_available(runtime_config.command),
            provider_version=provider_report.version_text,
            provider_command=provider_report.command,
        )
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
        self._workflow_runner = workflow_runner
        self._stage_runner = stage_runner
        self._stage_interact_runner = stage_interact_runner
        self._readiness_probe_provider = readiness_probe_provider
        self._folder_opener = folder_opener
        self._jobs = UiRunJobStore()
        self._shutdown_requested = False
        self._operator_waiters_lock = threading.Lock()
        self._operator_waiters: dict[str, _UiOperatorDecisionWaiter] = {}

    @property
    def workspace_root(self) -> Path:
        return self.options.root

    def handle_get(self, path: str, params: dict[str, list[str]]) -> UiResponse:
        try:
            if path == "/":
                return UiResponse(
                    status=int(HTTPStatus.OK),
                    content_type="text/html; charset=utf-8",
                    body=_INDEX_HTML.encode("utf-8"),
                )
            if path == "/operator.js":
                return UiResponse(
                    status=int(HTTPStatus.OK),
                    content_type="text/javascript; charset=utf-8",
                    body=_OPERATOR_JS.encode("utf-8"),
                )
            if path == "/operator.css":
                return UiResponse(
                    status=int(HTTPStatus.OK),
                    content_type="text/css; charset=utf-8",
                    body=_OPERATOR_CSS.encode("utf-8"),
                )
            if path == "/favicon.ico":
                return UiResponse(
                    status=int(HTTPStatus.NO_CONTENT),
                    content_type="image/x-icon",
                    body=b"",
                )
            if path == "/api/run":
                try:
                    return _json_response(
                        resolve_operator_run_view(
                            workspace_root=self.workspace_root,
                            work_item=self.options.work_item,
                            run_id=_first_param(params, "run_id"),
                        )
                    )
                except ValueError as exc:
                    message = str(exc)
                    if message.startswith("No runs found for work item "):
                        return _json_response({"metadata": None, "message": message})
                    raise
            if path == "/api/dashboard":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    {
                        "app_version": __version__,
                        "dashboard": resolve_operator_dashboard_view(
                            workspace_root=self.workspace_root,
                            work_item=self.options.work_item,
                            active_stage=stage,
                            run_id=_first_param(params, "run_id"),
                            project_root=Path.cwd(),
                        ),
                    }
                )
            if path == "/api/runtime-readiness":
                return _json_response(self._runtime_readiness())
            if path == "/api/stage":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    resolve_operator_stage_view(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                        run_id=_first_param(params, "run_id"),
                    )
                )
            if path == "/api/questions":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    resolve_operator_questions_view(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                    )
                )
            if path == "/api/logs":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                summary = resolve_operator_run_log_view(
                    workspace_root=self.workspace_root,
                    work_item=self.options.work_item,
                    stage=stage,
                    run_id=_first_param(params, "run_id"),
                    attempt_number=_optional_attempt(params),
                    tail_bytes=_optional_positive_int_param(params, "tail"),
                    limit_bytes=_optional_positive_int_param(params, "limit"),
                )
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
                    }
                )
            if path == "/api/jobs":
                return _error_response("job id is required.", status=HTTPStatus.NOT_FOUND)
            if path.startswith("/api/jobs/"):
                return self._handle_job_get(path=path, params=params)
            if path == "/api/artifacts":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    resolve_operator_artifacts_view(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                        run_id=_first_param(params, "run_id"),
                        attempt_number=_optional_attempt(params),
                    )
                )
            if path == "/api/artifacts/document":
                stage = _first_param(params, "stage", STAGES[0])
                key = _first_param(params, "key")
                assert stage is not None
                if key is None:
                    raise ValueError("key is required.")
                return _json_response(
                    resolve_operator_artifact_document_content(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                        key=key,
                        run_id=_first_param(params, "run_id"),
                        attempt_number=_optional_attempt(params),
                        mode=_first_param(params, "mode", "preview") or "preview",
                        limit_bytes=_optional_positive_int_param(params, "limit"),
                    )
                )
        except ValueError as exc:
            return _error_response(str(exc))
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)

    def handle_post(self, path: str, payload: dict[str, Any]) -> UiResponse:
        try:
            if path.startswith("/api/jobs/"):
                return self._handle_job_post(path=path, payload=payload)
            if path == "/api/answers":
                stage = str(payload.get("stage", STAGES[0])).strip() or STAGES[0]
                question_id = str(payload.get("question_id", "")).strip()
                text = str(payload.get("text", "")).strip()
                raw_resolution = str(payload.get("resolution", AnswerResolution.RESOLVED)).strip()
                if not question_id:
                    return _error_response("question_id is required.")
                if not text:
                    return _error_response("text is required.")
                return _json_response(
                    persist_operator_answer(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                        question_id=question_id,
                        text=text,
                        resolution=AnswerResolution(raw_resolution),
                    )
                )
            if path == "/api/stage/run":
                return _json_response(self._start_stage_job(payload))
            if path == "/api/stage/interact":
                return _json_response(self._start_stage_interact_job(payload))
            if path == "/api/workflow/run":
                return _json_response(self._start_workflow_job(payload))
            if path == "/api/open-folder":
                return _json_response(self._open_folder(payload))
            if path == "/api/server/stop":
                return _json_response(self._request_server_stop())
        except ValueError as exc:
            return _error_response(str(exc))
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)

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
        if (
            len(parts) == 4
            and parts[:2] == ["api", "jobs"]
            and parts[3] == "operator-requests"
        ):
            return _json_response(self._job_operator_requests(parts[2]))
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)

    def _handle_job_post(self, *, path: str, payload: dict[str, Any]) -> UiResponse:
        parts = path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "jobs"] and parts[3] == "cancel":
            return _json_response(self._jobs.cancel(parts[2]))
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
                work_item=self.options.work_item,
            )
        )
        if selected_run_id is None:
            return None
        return _latest_attempt_path(
            workspace_root=self.workspace_root,
            work_item=self.options.work_item,
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
        waiter = _UiOperatorDecisionWaiter()
        with self._operator_waiters_lock:
            self._operator_waiters[request.id] = waiter
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
                    waiter.condition.wait(timeout=0.25)
                return waiter.decision
        finally:
            with self._operator_waiters_lock:
                self._operator_waiters.pop(request.id, None)
            self._jobs.mark_running(job_id, message="runtime resumed after operator decision")

    def _deliver_operator_decision(self, decision: RuntimeOperatorDecision) -> None:
        with self._operator_waiters_lock:
            waiter = self._operator_waiters.get(decision.request_id)
        if waiter is None:
            return
        with waiter.condition:
            waiter.decision = decision
            waiter.condition.notify_all()

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
        append_operator_decision(
            path=attempt_path / OPERATOR_DECISIONS_FILENAME,
            decision=decision,
        )
        self._deliver_operator_decision(decision)
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
                    work_item=self.options.work_item,
                    runtime=runtime,
                    run_id=run_id,
                    root=self.workspace_root,
                    config=self.options.config,
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
                work_item=self.options.work_item,
            )
            operator_view = (
                _operator_request_view(
                    _latest_attempt_path(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
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
            work_item=self.options.work_item,
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
                    work_item=self.options.work_item,
                    runtime=runtime,
                    run_id=run_id,
                    root=self.workspace_root,
                    config=self.options.config,
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
        runtime = _runtime_from_payload(payload)
        _validate_runtime(runtime)
        stage_start, stage_end = _workflow_bounds_from_payload(payload)
        log_follow = bool(payload.get("log_follow", True))
        prepared_payload = dict(payload)
        prepared_payload["runtime"] = runtime
        prepared_payload["from_stage"] = stage_start
        prepared_payload["to_stage"] = stage_end
        prepared_payload["log_follow"] = log_follow

        def _target(job_id: str) -> object:
            return self._run_workflow(prepared_payload, job_id=job_id)

        return self._start_job(kind="workflow", stage=None, target=_target)

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

    def _run_workflow(self, payload: dict[str, Any], *, job_id: str) -> object:
        runtime = _runtime_from_payload(payload)
        stage_start, stage_end = _workflow_bounds_from_payload(payload)
        log_follow = bool(payload.get("log_follow", True))
        cfg = load_config(self.options.config)
        runtime_command = _runtime_command_for_runtime(runtime=runtime, cfg=cfg)
        runtime_execution_mode = _runtime_execution_mode_for_runtime(runtime=runtime, cfg=cfg)

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
                work_item=self.options.work_item,
                runtime_id=runtime,
                workspace_root=self.workspace_root,
                config_path=self.options.config,
                config_snapshot={
                    "config_path": self.options.config.as_posix(),
                    "workspace_root": self.workspace_root.as_posix(),
                    "runtime_command": runtime_command,
                    "runtime_execution_mode": runtime_execution_mode.value,
                    "log_follow": log_follow,
                    "mode": "ui-workflow",
                },
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

    def _runtime_readiness(self) -> object:
        cfg = load_config(self.options.config)
        return resolve_runtime_readiness(
            config=cfg,
            probe_reports=self._readiness_probe_provider(cfg),
            command_sources=_runtime_command_sources_from_config(self.options.config),
        )

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
            folder = self.workspace_root / "workitems" / self.options.work_item / "stages" / stage
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


def _handler_for(service: OperatorUiService) -> type[BaseHTTPRequestHandler]:
    class OperatorUiHandler(BaseHTTPRequestHandler):
        def _send(self, response: UiResponse) -> None:
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            self.wfile.write(response.body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            self._send(service.handle_get(parsed.path, parse_qs(parsed.query)))

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = _read_json_body(self)
            except UiRequestBodyTooLarge as exc:
                self._send(_error_response(str(exc), status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE))
                return
            except ValueError as exc:
                self._send(_error_response(str(exc)))
                return
            self._send(service.handle_post(parsed.path, payload))
            if service.consume_shutdown_requested():
                threading.Thread(
                    target=self.server.shutdown,
                    name="aidd-ui-server-stop",
                    daemon=True,
                ).start()

        def log_message(self, format: str, *args: object) -> None:
            return

    return OperatorUiHandler


def run_ui_server(options: UiServerOptions) -> None:
    service = OperatorUiService(options)
    server = ThreadingHTTPServer((options.host, options.port), _handler_for(service))
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
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
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
    run_ui_server(
        UiServerOptions(
            work_item=work_item,
            root=root.resolve(strict=False),
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
