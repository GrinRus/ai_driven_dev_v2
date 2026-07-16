from __future__ import annotations

import json
import os
import threading
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from aidd.core.stages import STAGES
from aidd.harness.install_artifact import HarnessInstallResult
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
    "stage_exit_code",
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
    install_home = None
    if ctx.install_result is not None:
        install_home = ctx.install_result.install_home.as_posix()
    elif ctx.preserved_install_payload is not None:
        preserved_install_home = ctx.preserved_install_payload.get("install_home")
        if isinstance(preserved_install_home, str):
            install_home = preserved_install_home

    payload: dict[str, object] = {
        "schema_version": 2,
        "updated_at_utc": utc_now(),
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


def mark_stale_running_state_interrupted(state_path_value: Path) -> dict[str, Any]:
    payload = read_json_object(state_path_value)
    if payload.get("status") != "running" or _pid_is_alive(payload.get("evaluator_pid")):
        return payload
    interruption = {
        "created_at_utc": utc_now(),
        "reason": "stale-running-state",
        "previous_status": "running",
        "previous_evaluator_pid": payload.get("evaluator_pid"),
        "cleanup": "no active evaluator process was found",
    }
    payload["status"] = "interrupted-resumable"
    payload["next_action"] = "run-stage"
    payload["updated_at_utc"] = interruption["created_at_utc"]
    payload["interruption"] = interruption
    write_json_atomic(state_path_value, payload)
    return payload


def find_resume_state(*, report_root: Path, run_id: str | None) -> Path | None:
    normalized_run_id = run_id.strip() if run_id is not None else None
    if normalized_run_id == "":
        raise ValueError("run_id must be non-empty when provided.")
    if normalized_run_id is None:
        return None
    candidate = report_root / normalized_run_id / FLOW_STATE_FILENAME
    if not candidate.exists():
        raise ValueError(
            "Explicit --run-id can only resume or refresh an existing black-box live "
            f"E2E run. State file not found: {candidate.as_posix()}."
        )
    state = mark_stale_running_state_interrupted(candidate)
    status = state.get("status")
    if status == "awaiting-quality-review":
        required_path = state.get("quality_review_required_path")
        if not isinstance(required_path, str) or not Path(required_path).exists():
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
    "build_flow_state_payload",
    "completed_stage_runs",
    "completed_stages",
    "current_stage",
    "find_resume_state",
    "handled_quality_stage_run_ids",
    "load_flow_state",
    "mark_stale_running_state_interrupted",
    "persist_flow_state",
    "preserved_state_extras",
    "read_json_object",
    "remediation_cycles",
    "stale_downstream_stages",
    "state_path",
    "state_status",
    "write_json_atomic",
]
