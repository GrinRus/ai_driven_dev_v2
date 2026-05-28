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
from aidd.cli.ui_assets import operator_static_asset_for_route
from aidd.cli.ui_http import (
    UiRequestBodyTooLarge,
    UiResponse,
    _error_response,
    _json_response,
    _read_json_body,
)
from aidd.config import AiddConfig, load_config
from aidd.core.interview import AnswerResolution
from aidd.core.next_flow import (
    CloneFlowDraftRequest,
    FollowUpDraftRequest,
    FollowUpSourceSelection,
    NextFlowLaunchPreflightRequest,
    create_clone_flow_draft,
    create_follow_up_work_item_draft,
    validate_next_flow_launch_preflight,
)
from aidd.core.operator_frontend import (
    persist_operator_answer,
    resolve_operator_artifact_document_content,
    resolve_operator_artifacts_view,
    resolve_operator_dashboard_view,
    resolve_operator_evidence_graph_view,
    resolve_operator_questions_view,
    resolve_operator_run_log_view,
    resolve_operator_run_view,
    resolve_operator_stage_document_workbench,
    resolve_operator_stage_view,
)
from aidd.core.run_lookup import latest_run_id as resolve_latest_run_id
from aidd.core.run_store import (
    next_attempt_number,
    persist_run_archive_decision,
    run_attempt_root,
)
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
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.workflow_service import (
    WorkflowRunRequest,
    WorkflowRunResult,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
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


def _next_flow_source_findings_payload(dashboard: Any) -> dict[str, object]:
    run = dashboard.run
    handoff = dashboard.terminal_handoff
    final_artifacts = tuple(handoff.final_artifacts) if handoff is not None else ()
    qa_items = [
        _next_flow_source_item(
            item_id=f"qa-finding:{artifact.stage}:{artifact.key}",
            kind="qa-finding",
            title=f"QA artifact: {artifact.key}",
            detail="Use this final QA artifact as follow-up source context.",
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
            detail="Carry forward review-stage notes or accepted risks.",
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
            detail=blocker.detail,
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
            detail="Add a scoped operator note in the follow-up definition step.",
        )
    ]
    groups = (
        _next_flow_source_group(
            group_id="qa-findings",
            label="QA findings",
            detail="Final QA outputs that can become follow-up source selections.",
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
    return {
        "source_work_item": dashboard.work_item,
        "source_run_id": run.run_id,
        "source_runtime_id": run.runtime_id,
        "groups": groups,
        "counts": {
            "total_items": len(all_items),
            "selected_defaults": sum(1 for item in all_items if item["selected"]),
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
            "Selected source findings do not match this source run: "
            f"{', '.join(missing_ids)}."
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
                raise ValueError(
                    f"Selected source '{item_id}' has no source artifact path."
                )
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
            if static_asset := operator_static_asset_for_route(path):
                return UiResponse(
                    status=int(HTTPStatus.OK),
                    content_type=static_asset.content_type,
                    body=static_asset.text.encode("utf-8"),
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
            if path == "/api/next-flow/source-findings":
                dashboard = resolve_operator_dashboard_view(
                    workspace_root=self.workspace_root,
                    work_item=self.options.work_item,
                    active_stage="qa",
                    run_id=_first_param(params, "run_id"),
                    project_root=Path.cwd(),
                )
                return _json_response(_next_flow_source_findings_payload(dashboard))
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
            if path == "/api/stage/workbench":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    resolve_operator_stage_document_workbench(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                        key=_first_param(params, "key"),
                        run_id=_first_param(params, "run_id"),
                        attempt_number=_optional_attempt(params),
                        preview_limit_bytes=_optional_positive_int_param(
                            params, "preview_limit"
                        ),
                        source_limit_bytes=_optional_positive_int_param(
                            params, "source_limit"
                        ),
                    )
                )
            if path == "/api/artifacts/evidence-graph":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    resolve_operator_evidence_graph_view(
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
            remote_mutation_error = self._remote_mutation_error(path)
            if remote_mutation_error is not None:
                return remote_mutation_error
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
            if path == "/api/next-flow/preflight":
                return self._next_flow_preflight(payload)
            if path == "/api/next-flow/follow-up-draft":
                return self._next_flow_follow_up_draft(payload)
            if path == "/api/next-flow/follow-up-draft/create":
                return self._next_flow_create_follow_up_draft(payload)
            if path == "/api/next-flow/clone-draft/create":
                return self._next_flow_create_clone_draft(payload)
            if path == "/api/next-flow/launch":
                return self._next_flow_launch(payload)
            if path == "/api/next-flow/archive":
                return self._next_flow_archive(payload)
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
        run_id = _optional_run_id_from_payload(payload)
        log_follow = bool(payload.get("log_follow", True))
        prepared_payload = dict(payload)
        prepared_payload["runtime"] = runtime
        prepared_payload["from_stage"] = stage_start
        prepared_payload["to_stage"] = stage_end
        prepared_payload["run_id"] = run_id
        prepared_payload["log_follow"] = log_follow

        def _target(job_id: str) -> object:
            return self._run_workflow(prepared_payload, job_id=job_id)

        return self._start_job(kind="workflow", stage=None, target=_target)

    def _next_flow_preflight(self, payload: dict[str, Any]) -> UiResponse:
        result = validate_next_flow_launch_preflight(
            NextFlowLaunchPreflightRequest(
                workspace_root=self.workspace_root,
                source_work_item=_source_work_item_from_payload(
                    payload,
                    default=self.options.work_item,
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
            work_item=self.options.work_item,
            active_stage="qa",
            run_id=_source_run_id_from_payload(payload),
            project_root=Path.cwd(),
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
            default=self.options.work_item,
        )
        source_run_id = _source_run_id_from_payload(payload)
        selected_source_ids = _selected_source_ids_from_payload(payload)
        dashboard = resolve_operator_dashboard_view(
            workspace_root=self.workspace_root,
            work_item=source_work_item,
            active_stage="qa",
            run_id=source_run_id,
            project_root=Path.cwd(),
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
        result = create_follow_up_work_item_draft(
            FollowUpDraftRequest(
                workspace_root=self.workspace_root,
                source_work_item=source_work_item,
                source_run_id=source_run_id,
                new_work_item=str(draft["new_work_item"]),
                title=str(draft["title"]),
                selections=_follow_up_source_selections_from_items(selected_sources),
                project_root=Path.cwd(),
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
            default=self.options.work_item,
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
                project_root=Path.cwd(),
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
            default=self.options.work_item,
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
            default=self.options.work_item,
        )
        reason = payload.get("reason")
        if reason is not None and not isinstance(reason, str):
            raise ValueError("reason must be a string.")
        dashboard = resolve_operator_dashboard_view(
            workspace_root=self.workspace_root,
            work_item=work_item,
            active_stage="qa",
            run_id=run_id,
            project_root=Path.cwd(),
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
            project_root=Path.cwd(),
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
        target_work_item = work_item or self.options.work_item
        cfg = load_config(self.options.config)
        runtime_command = _runtime_command_for_runtime(runtime=runtime, cfg=cfg)
        runtime_execution_mode = _runtime_execution_mode_for_runtime(runtime=runtime, cfg=cfg)
        config_snapshot: dict[str, Any] = {
            "config_path": self.options.config.as_posix(),
            "workspace_root": self.workspace_root.as_posix(),
            "runtime_command": runtime_command,
            "runtime_execution_mode": runtime_execution_mode.value,
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
                config_path=self.options.config,
                config_snapshot=config_snapshot,
                lineage=lineage,
                run_id=run_id,
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
