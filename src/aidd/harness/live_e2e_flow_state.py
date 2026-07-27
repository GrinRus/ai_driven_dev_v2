from __future__ import annotations

import fcntl
import json
import os
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from aidd.core.identifiers import SafeIdentifier, contained_component_path
from aidd.core.stages import STAGES
from aidd.harness.install_artifact import HarnessInstallResult
from aidd.harness.live_flow_timing import (
    finish_stale_owner_segment,
    format_segment_timestamp,
    process_segments_payload,
    update_process_segments,
)
from aidd.harness.repo_prep import PreparedRepository, PreparedWorkingCopy
from aidd.harness.scenarios import Scenario

FLOW_STATE_FILENAME = "flow-state.json"
TERMINAL_STATUSES = frozenset({"pass", "fail", "infra-fail"})
TERMINAL_MANUAL_STATUSES = frozenset({"manual-quality-stop"})
RESUMABLE_STATUSES = frozenset({"blocked", "interrupted-resumable", "awaiting-quality-review"})
PRESERVED_STATE_EXTRA_KEYS = (
    "error",
    "interruption",
    "no_progress",
    "no_progress_details",
    "no_progress_reconciliation",
    "operator_action_request_json",
    "operator_action_request_markdown",
    "remediation_evidence",
    "remediation_terminal_evidence",
    "stage_exit_code",
    "error_classification",
    "target_readiness_evidence",
)


class FlowStateContext(Protocol):
    scenario_path: Path
    scenario: Scenario
    run_id: str
    runtime_id: str
    workspace_root: Path
    report_root: Path
    bundle_root: Path
    work_item: str
    prepared_repository: PreparedRepository | None
    prepared_working_copy: PreparedWorkingCopy | None
    install_result: HarnessInstallResult | None
    preserved_install_payload: dict[str, object] | None
    config_path: Path | None
    installed_command: tuple[str, ...]
    target_workspace_baseline_snapshot: dict[str, object] | None
    enable_next_flow_follow_up_proof: bool
    manual_frontend_evidence: Path | None


@dataclass(frozen=True, slots=True)
class StaleOwnerObservation:
    durable_status: str | None
    read_status: str | None
    evaluator_pid: int | None
    owner_alive: bool
    stale_owner: bool
    active_step: dict[str, object] | None
    observed_at_utc: str

    def to_payload(self) -> dict[str, object]:
        return {
            "durable_status": self.durable_status,
            "read_status": self.read_status,
            "evaluator_pid": self.evaluator_pid,
            "owner_alive": self.owner_alive,
            "stale_owner": self.stale_owner,
            "active_step": self.active_step,
            "observed_at_utc": self.observed_at_utc,
        }


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_path(bundle_root: Path) -> Path:
    return bundle_root / FLOW_STATE_FILENAME


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path.as_posix()}.")
    return payload


def write_json_atomic(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)
    return path


def load_flow_state(bundle_root: Path) -> dict[str, Any]:
    path = state_path(bundle_root)
    if not path.exists():
        return {}
    return read_json_object(path)


def build_flow_state_payload(
    *,
    ctx: FlowStateContext,
    status: str,
    next_action: str,
    current_stage: str | None,
    completed_stages: tuple[str, ...],
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    previous_state = load_flow_state(ctx.bundle_root)
    observed_at_utc = format_segment_timestamp()
    install_home = None
    if ctx.install_result is not None:
        install_home = ctx.install_result.install_home.as_posix()
    elif ctx.preserved_install_payload is not None:
        preserved_install_home = ctx.preserved_install_payload.get("install_home")
        if isinstance(preserved_install_home, str):
            install_home = preserved_install_home

    payload: dict[str, object] = {
        "schema_version": 3,
        "updated_at_utc": observed_at_utc,
        "scenario_path": ctx.scenario_path.resolve(strict=False).as_posix(),
        "scenario_id": ctx.scenario.scenario_id,
        "runtime_id": ctx.runtime_id,
        "run_id": ctx.run_id,
        "work_item": ctx.work_item,
        "status": status,
        "next_action": next_action,
        "current_stage": current_stage,
        "completed_stages": list(completed_stages),
        "completed_stage_runs": previous_state.get("completed_stage_runs", []),
        "current_iteration": previous_state.get("current_iteration", 1),
        "handled_quality_stage_run_ids": previous_state.get(
            "handled_quality_stage_run_ids",
            [],
        ),
        "remediation_cycles": previous_state.get("remediation_cycles", 0),
        "stale_downstream_stages": previous_state.get("stale_downstream_stages", []),
        "evaluator_pid": os.getpid(),
        "bundle_root": ctx.bundle_root.as_posix(),
        "work_root": ctx.workspace_root.as_posix(),
        "run_work_root": (ctx.workspace_root / ctx.run_id).as_posix(),
        "report_root": ctx.report_root.as_posix(),
        "source_snapshot": (
            ctx.install_result.source_snapshot_path.as_posix()
            if ctx.install_result is not None
            and ctx.install_result.source_snapshot_path is not None
            else (
                ctx.preserved_install_payload.get("source_snapshot")
                if ctx.preserved_install_payload is not None
                else None
            )
        ),
        "target_repo_root": (
            None
            if ctx.prepared_working_copy is None
            else ctx.prepared_working_copy.working_copy_path.as_posix()
        ),
        "target_workspace_root": (
            None
            if ctx.prepared_working_copy is None
            else (ctx.prepared_working_copy.working_copy_path / ".aidd").as_posix()
        ),
        "working_copy_path": (
            None
            if ctx.prepared_working_copy is None
            else ctx.prepared_working_copy.working_copy_path.as_posix()
        ),
        "config_path": None if ctx.config_path is None else ctx.config_path.as_posix(),
        "install_home": install_home,
        "installed_command": list(ctx.installed_command),
        "target_workspace_baseline_snapshot": ctx.target_workspace_baseline_snapshot,
        "next_flow_follow_up_proof_enabled": ctx.enable_next_flow_follow_up_proof,
        "manual_frontend_evidence_source": (
            None
            if ctx.manual_frontend_evidence is None
            else ctx.manual_frontend_evidence.resolve(strict=False).as_posix()
        ),
    }
    raw_interruption = extra.get("interruption") if extra is not None else None
    interruption_reason = (
        raw_interruption.get("reason")
        if isinstance(raw_interruption, Mapping)
        else None
    )
    payload["process_segments"] = process_segments_payload(
        update_process_segments(
            previous_state.get("process_segments"),
            owner_pid=os.getpid(),
            observed_at_utc=observed_at_utc,
            status=status,
            interruption_reason=interruption_reason,
        )
    )
    if ctx.install_result is not None:
        payload["install"] = {
            "artifact_identity": ctx.install_result.artifact_identity,
            "artifact_source": ctx.install_result.artifact_source,
            "install_channel": ctx.install_result.install_channel,
            "install_home": ctx.install_result.install_home.as_posix(),
            "tool_bin_dir": ctx.install_result.tool_bin_dir.as_posix(),
            "uv_cache_dir": (
                None
                if ctx.install_result.uv_cache_dir is None
                else ctx.install_result.uv_cache_dir.as_posix()
            ),
            "source_snapshot": (
                None
                if ctx.install_result.source_snapshot_path is None
                else ctx.install_result.source_snapshot_path.as_posix()
            ),
            "build_dist": (
                None
                if ctx.install_result.build_dist_path is None
                else ctx.install_result.build_dist_path.as_posix()
            ),
            "source_revision": ctx.install_result.source_revision,
        }
    elif ctx.preserved_install_payload is not None:
        payload["install"] = dict(ctx.preserved_install_payload)
    if ctx.prepared_repository is not None:
        payload["prepared_repository"] = {
            "action": ctx.prepared_repository.action,
            "repo_path": ctx.prepared_repository.repo_path.as_posix(),
            "resolved_revision": ctx.prepared_repository.resolved_revision,
        }
    if ctx.prepared_working_copy is not None:
        payload["prepared_working_copy"] = {
            "action": ctx.prepared_working_copy.action,
            "resolved_revision": ctx.prepared_working_copy.resolved_revision,
            "working_copy_path": ctx.prepared_working_copy.working_copy_path.as_posix(),
        }
    if "pending_remediation" in previous_state:
        payload["pending_remediation"] = previous_state["pending_remediation"]
    if extra:
        if "completed_stage_runs" in extra and "completed_stages" not in extra:
            raw_stage_runs = extra.get("completed_stage_runs")
            if isinstance(raw_stage_runs, list):
                payload["completed_stages"] = [
                    item.get("stage")
                    for item in raw_stage_runs
                    if isinstance(item, dict) and isinstance(item.get("stage"), str)
                ]
        payload.update(extra)
    return payload


def persist_flow_state(
    *,
    ctx: FlowStateContext,
    status: str,
    next_action: str,
    current_stage: str | None,
    completed_stages: tuple[str, ...],
    extra: Mapping[str, object] | None = None,
) -> None:
    payload = build_flow_state_payload(
        ctx=ctx,
        status=status,
        next_action=next_action,
        current_stage=current_stage,
        completed_stages=completed_stages,
        extra=extra,
    )
    write_json_atomic(state_path(ctx.bundle_root), payload)


def completed_stages(bundle_root: Path) -> tuple[str, ...]:
    payload = load_flow_state(bundle_root)
    raw_stage_runs = payload.get("completed_stage_runs")
    if isinstance(raw_stage_runs, list) and raw_stage_runs:
        stages = [
            item.get("stage")
            for item in raw_stage_runs
            if isinstance(item, dict) and isinstance(item.get("stage"), str)
        ]
        return tuple(str(stage) for stage in stages)
    raw = payload.get("completed_stages")
    if not isinstance(raw, list):
        return tuple()
    return tuple(str(item) for item in raw if isinstance(item, str))


def completed_stage_runs(bundle_root: Path) -> tuple[dict[str, Any], ...]:
    payload = load_flow_state(bundle_root)
    raw_stage_runs = payload.get("completed_stage_runs")
    if isinstance(raw_stage_runs, list) and raw_stage_runs:
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(raw_stage_runs, start=1):
            if not isinstance(item, dict):
                continue
            stage = item.get("stage")
            if not isinstance(stage, str) or not stage:
                continue
            stage_run_id = item.get("stage_run_id")
            if not isinstance(stage_run_id, str) or not stage_run_id:
                stage_run_id = f"stage-{index:04d}-{stage}"
            normalized.append({**item, "stage": stage, "stage_run_id": stage_run_id})
        return tuple(normalized)
    raw_stages = payload.get("completed_stages")
    if not isinstance(raw_stages, list):
        return tuple()
    return tuple(
        {
            "stage_run_id": str(stage),
            "stage": str(stage),
            "stage_run_index": index,
            "iteration": 1,
            "legacy_stage_run": True,
        }
        for index, stage in enumerate(raw_stages, start=1)
        if isinstance(stage, str) and stage
    )


def handled_quality_stage_run_ids(bundle_root: Path) -> set[str]:
    raw = load_flow_state(bundle_root).get("handled_quality_stage_run_ids")
    if not isinstance(raw, list):
        return set()
    return {str(item) for item in raw if isinstance(item, str) and item}


def stale_downstream_stages(bundle_root: Path) -> tuple[str, ...]:
    raw = load_flow_state(bundle_root).get("stale_downstream_stages")
    if not isinstance(raw, list):
        return tuple()
    return tuple(str(item) for item in raw if isinstance(item, str) and item in STAGES)


def remediation_cycles(bundle_root: Path) -> int:
    raw = load_flow_state(bundle_root).get("remediation_cycles")
    return raw if isinstance(raw, int) and raw >= 0 else 0


def current_stage(bundle_root: Path) -> str | None:
    raw = load_flow_state(bundle_root).get("current_stage")
    return raw if isinstance(raw, str) and raw else None


def state_status(bundle_root: Path) -> str | None:
    raw = load_flow_state(bundle_root).get("status")
    return raw if isinstance(raw, str) else None


def preserved_state_extras(bundle_root: Path) -> dict[str, object]:
    state = load_flow_state(bundle_root)
    return {key: state[key] for key in PRESERVED_STATE_EXTRA_KEYS if key in state}


def _pid_is_alive(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def detect_stale_owner(
    state: Mapping[str, object],
    *,
    pid_is_alive: Callable[[object], bool] = _pid_is_alive,
    observed_at_utc: str | None = None,
) -> StaleOwnerObservation:
    durable_status = state.get("status")
    normalized_status = durable_status if isinstance(durable_status, str) else None
    raw_pid = state.get("evaluator_pid")
    evaluator_pid = raw_pid if isinstance(raw_pid, int) else None
    owner_alive = pid_is_alive(raw_pid)
    stale_owner = normalized_status == "running" and not owner_alive
    raw_active_step = state.get("active_step")
    active_step = (
        {str(key): value for key, value in raw_active_step.items()}
        if isinstance(raw_active_step, dict)
        else None
    )
    return StaleOwnerObservation(
        durable_status=normalized_status,
        read_status="stale-owner" if stale_owner else normalized_status,
        evaluator_pid=evaluator_pid,
        owner_alive=owner_alive,
        stale_owner=stale_owner,
        active_step=active_step,
        observed_at_utc=observed_at_utc or utc_now(),
    )


def stale_owner_read_model(
    state_path_value: Path,
    *,
    pid_is_alive: Callable[[object], bool] = _pid_is_alive,
) -> dict[str, Any]:
    payload = read_json_object(state_path_value)
    observation = detect_stale_owner(payload, pid_is_alive=pid_is_alive)
    read_model = dict(payload)
    read_model["durable_status"] = observation.durable_status
    read_model["status"] = observation.read_status
    read_model["owner_observation"] = observation.to_payload()
    return read_model


@contextmanager
def _flow_state_reconciliation_lock(state_path_value: Path) -> Iterator[None]:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(state_path_value.parent, flags)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


_RESUME_IDENTITY_KEYS = (
    "run_id",
    "scenario_id",
    "scenario_path",
    "runtime_id",
    "work_item",
    "report_root",
    "work_root",
    "run_work_root",
    "bundle_root",
)


def _resume_identity(state: Mapping[str, object]) -> dict[str, object]:
    return {key: state.get(key) for key in _RESUME_IDENTITY_KEYS}


def reconcile_stale_owner_for_resume(
    state_path_value: Path,
    *,
    expected_identity: Mapping[str, object],
    changed_at_utc: str | None = None,
) -> dict[str, Any]:
    with _flow_state_reconciliation_lock(state_path_value):
        payload = read_json_object(state_path_value)
        if _resume_identity(payload) != dict(expected_identity):
            raise ValueError(
                "Resume flow-state identity changed during stale-owner reconciliation."
            )
        observation = detect_stale_owner(payload)
        if not observation.stale_owner:
            return payload
        reconciled_at = changed_at_utc or utc_now()
        previous_updated_at = payload.get("updated_at_utc")
        interruption = {
            "created_at_utc": reconciled_at,
            "reason": "stale-owner",
            "previous_status": "running",
            "previous_evaluator_pid": observation.evaluator_pid,
            "active_step": observation.active_step,
            "cleanup": "no active evaluator process was found",
            "provider_completion_used_as_stage_verdict": False,
        }
        payload["status"] = "interrupted-resumable"
        payload["next_action"] = "run-stage"
        payload["updated_at_utc"] = reconciled_at
        payload["interruption"] = interruption
        active_step = observation.active_step or {}
        payload["process_segments"] = process_segments_payload(
            finish_stale_owner_segment(
                payload.get("process_segments"),
                owner_pid=observation.evaluator_pid,
                finished_at_utc=reconciled_at,
                fallback_started_at_utc=(
                    active_step.get("started_at_utc")
                    or previous_updated_at
                ),
            )
        )
        write_json_atomic(state_path_value, payload)
        return payload


def _identity_path(value: object, *, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Resume flow state is missing canonical `{field}` identity.")
    raw_path = Path(value)
    if not raw_path.is_absolute():
        raise ValueError(f"Resume flow-state `{field}` identity must be absolute.")
    resolved = raw_path.resolve(strict=False)
    if raw_path != resolved:
        raise ValueError(f"Resume flow-state `{field}` identity must be canonical.")
    return resolved


def _assert_resume_identity(
    *,
    state: Mapping[str, object],
    run_id: str,
    scenario_path: Path,
    scenario_id: str,
    runtime_id: str,
    work_item: str,
    report_root: Path,
    work_root: Path,
    run_root: Path,
) -> None:
    scalar_fields = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "runtime_id": runtime_id,
        "work_item": work_item,
    }
    for field, expected in scalar_fields.items():
        if state.get(field) != expected:
            raise ValueError(
                f"Resume flow-state `{field}` identity does not match the requested run."
            )

    resolved_report_root = report_root.resolve(strict=False)
    resolved_work_root = work_root.resolve(strict=False)
    path_fields = {
        "scenario_path": scenario_path.resolve(strict=False),
        "report_root": resolved_report_root,
        "work_root": resolved_work_root,
        "run_work_root": (resolved_work_root / run_id).resolve(strict=False),
        "bundle_root": run_root.resolve(strict=False),
    }
    for path_field, expected_path in path_fields.items():
        if _identity_path(state.get(path_field), field=path_field) != expected_path:
            raise ValueError(
                f"Resume flow-state `{path_field}` identity does not match the requested run."
            )


def _contained_required_quality_path(*, raw_path: str, run_root: Path) -> Path:
    required = Path(raw_path)
    if not required.is_absolute():
        required = run_root / required
    resolved_run_root = run_root.resolve(strict=False)
    resolved_required = required.resolve(strict=False)
    if not resolved_required.is_relative_to(resolved_run_root):
        raise ValueError(
            "Quality-review evidence path must stay inside the canonical run bundle."
        )
    if required.is_symlink():
        raise ValueError("Quality-review evidence path must not be a symlink.")
    return required


def find_resume_state(
    *,
    report_root: Path,
    run_id: str | None,
    scenario_path: Path,
    scenario_id: str,
    runtime_id: str,
    work_item: str,
    work_root: Path,
) -> Path | None:
    if run_id is None:
        return None
    normalized_run_id = SafeIdentifier.parse(run_id, label="run_id").value
    run_root = contained_component_path(
        report_root,
        normalized_run_id,
        boundary_root=report_root,
        label="run_id",
    )
    if run_root.is_symlink():
        raise ValueError("Resume run root must not be a symlink.")
    candidate = contained_component_path(
        run_root,
        FLOW_STATE_FILENAME,
        boundary_root=report_root,
        label="flow-state filename",
    )
    if candidate.is_symlink():
        raise ValueError("Resume flow-state file must not be a symlink.")
    if not candidate.exists():
        raise ValueError(
            "Explicit --run-id can only resume or refresh an existing black-box live "
            f"E2E run. State file not found: {candidate.as_posix()}."
        )
    state = read_json_object(candidate)
    _assert_resume_identity(
        state=state,
        run_id=normalized_run_id,
        scenario_path=scenario_path,
        scenario_id=scenario_id,
        runtime_id=runtime_id,
        work_item=work_item,
        report_root=report_root,
        work_root=work_root,
        run_root=run_root,
    )
    owner_observation = detect_stale_owner(state)
    if owner_observation.stale_owner:
        state = reconcile_stale_owner_for_resume(
            candidate,
            expected_identity=_resume_identity(state),
        )
    status = state.get("status")
    if status == "awaiting-quality-review":
        required_path = state.get("quality_review_required_path")
        required = (
            _contained_required_quality_path(raw_path=required_path, run_root=run_root)
            if isinstance(required_path, str) and required_path
            else None
        )
        if required is None or not required.exists():
            raise ValueError(
                "Run "
                f"'{normalized_run_id}' is awaiting quality review. Resume requires "
                "the launching operator-agent audit file: "
                f"{required_path if isinstance(required_path, str) else 'missing'}."
            )
    if status not in {
        *RESUMABLE_STATUSES,
        *TERMINAL_STATUSES,
        *TERMINAL_MANUAL_STATUSES,
    }:
        raise ValueError(
            "Explicit --run-id can only resume a blocked or interrupted-resumable "
            "run, resume an awaiting-quality-review run with its required audit "
            "file, or refresh terminal execution reporting. "
            f"Run '{normalized_run_id}' has status `{status}`."
        )
    return candidate


__all__ = [
    "FLOW_STATE_FILENAME",
    "PRESERVED_STATE_EXTRA_KEYS",
    "RESUMABLE_STATUSES",
    "TERMINAL_MANUAL_STATUSES",
    "TERMINAL_STATUSES",
    "StaleOwnerObservation",
    "build_flow_state_payload",
    "completed_stage_runs",
    "completed_stages",
    "current_stage",
    "detect_stale_owner",
    "find_resume_state",
    "handled_quality_stage_run_ids",
    "load_flow_state",
    "persist_flow_state",
    "preserved_state_extras",
    "read_json_object",
    "reconcile_stale_owner_for_resume",
    "remediation_cycles",
    "stale_owner_read_model",
    "stale_downstream_stages",
    "state_path",
    "state_status",
    "write_json_atomic",
]
