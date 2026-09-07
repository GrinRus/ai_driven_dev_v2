from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class FrontendProbeContext(Protocol):
    run_id: str
    work_item: str


PRIMARY_STAGE_OUTPUTS: dict[str, str] = {
    "idea": "idea-brief.md",
    "research": "research-notes.md",
    "plan": "plan.md",
    "review-spec": "review-spec-report.md",
    "tasklist": "tasklist.md",
    "implement": "implementation-report.md",
    "review": "review-report.md",
    "qa": "qa-report.md",
}


def http_probe(url: str, *, timeout_seconds: float = 10.0) -> dict[str, object]:
    """Read a public UI/API endpoint and retain bounded diagnostic evidence."""
    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            body = response.read(1048576).decode("utf-8", errors="replace")
            payload: dict[str, object] = {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "body_preview": body[:1000],
            }
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                payload["json_payload"] = parsed
            return payload
    except HTTPError as exc:
        body = exc.read(1048576).decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "body_preview": body[:1000],
            "error": str(exc),
        }
    except (OSError, URLError) as exc:
        return {"ok": False, "status": None, "body_preview": "", "error": str(exc)}


def http_post_json(
    url: str,
    payload: dict[str, object],
    *,
    timeout_seconds: float = 10.0,
) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(1048576).decode("utf-8", errors="replace")
            result: dict[str, object] = {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "body_preview": body[:1000],
            }
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                result["json_payload"] = parsed
            return result
    except HTTPError as exc:
        body = exc.read(1048576).decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "body_preview": body[:1000],
            "error": str(exc),
        }
    except (OSError, URLError) as exc:
        return {"ok": False, "status": None, "body_preview": "", "error": str(exc)}


def frontend_probe_targets(
    ctx: FrontendProbeContext,
    stage: str,
    *,
    primary_stage_outputs: Mapping[str, str] = PRIMARY_STAGE_OUTPUTS,
) -> tuple[tuple[str, str], ...]:
    stage_query = urlencode({"stage": stage, "run_id": ctx.run_id})
    run_query = urlencode({"run_id": ctx.run_id})
    targets = [
        ("page", "/"),
        ("dashboard-api", f"/api/dashboard?{stage_query}"),
        ("run-api", f"/api/run?{run_query}"),
        ("stage-api", f"/api/stage?{stage_query}"),
        ("questions-api", f"/api/questions?{urlencode({'stage': stage})}"),
        ("logs-api", f"/api/logs?{stage_query}"),
        ("artifacts-api", f"/api/artifacts?{stage_query}"),
    ]
    rich_tasklist = False
    prepared = getattr(ctx, "prepared_working_copy", None)
    working_copy_path = getattr(prepared, "working_copy_path", None)
    if stage == "implement" and isinstance(working_copy_path, Path):
        tasklist_path = (
            working_copy_path
            / ".aidd"
            / "workitems"
            / ctx.work_item
            / "stages"
            / "tasklist"
            / "output"
            / "tasklist.md"
        )
        try:
            rich_tasklist = bool(
                re.search(
                    r"(?m)^###\s+[A-Za-z0-9][\w.-]*\b",
                    tasklist_path.read_text(),
                )
            )
        except OSError:
            rich_tasklist = False
    if stage == "implement" and rich_tasklist:
        targets.append(("tasks-api", f"/api/tasks?{run_query}"))
    return tuple(targets)


def frontend_running_probe_targets(
    ctx: FrontendProbeContext,
    stage: str,
) -> tuple[tuple[str, str], ...]:
    stage_query = urlencode({"stage": stage, "run_id": ctx.run_id})
    run_query = urlencode({"run_id": ctx.run_id})
    return (
        ("page", "/"),
        ("dashboard-api", f"/api/dashboard?{stage_query}"),
        ("run-api", f"/api/run?{run_query}"),
        ("stage-api", f"/api/stage?{stage_query}"),
        ("logs-api", f"/api/logs?{stage_query}"),
    )


def frontend_checkpoint_timeout_seconds(
    phase: str,
    *,
    startup_timeout_seconds: float = 30.0,
    probe_timeout_seconds: float = 10.0,
) -> float:
    probe_count = 5 if phase == "running-stage" else 7
    return startup_timeout_seconds + probe_count * probe_timeout_seconds


def frontend_checkpoint_timed_out(
    *,
    failure_reason: str | None,
    probes: Sequence[Mapping[str, object]],
) -> bool:
    evidence = [failure_reason or ""]
    evidence.extend(str(probe.get("error") or "") for probe in probes)
    return any("timed out" in item.lower() for item in evidence)


def json_contains_value(value: object, expected: str) -> bool:
    if isinstance(value, str):
        return value == expected or expected in value
    if isinstance(value, dict):
        return any(json_contains_value(item, expected) for item in value.values())
    if isinstance(value, list | tuple):
        return any(json_contains_value(item, expected) for item in value)
    return False


def json_has_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(json_has_key(item, key) for item in value.values())
    if isinstance(value, list | tuple):
        return any(json_has_key(item, key) for item in value)
    return False


def frontend_probe_semantic_failure(
    *,
    ctx: FrontendProbeContext,
    stage: str,
    name: str,
    probe: Mapping[str, object],
    primary_stage_outputs: Mapping[str, str] = PRIMARY_STAGE_OUTPUTS,
    phase: str = "post-stage",
    observed_stage_status: str | None = None,
) -> str | None:
    if probe.get("ok") is not True:
        return "probe returned non-2xx response"
    if name == "page":
        body = str(probe.get("body_preview") or "")
        return None if body.strip() else "UI page body is empty"
    payload = probe.get("json_payload")
    if not isinstance(payload, dict):
        return "API probe did not return a JSON object"
    if name == "run-api":
        if not json_contains_value(payload, ctx.run_id):
            return "run API response does not include current run_id"
        if not json_contains_value(payload, ctx.work_item):
            return "run API response does not include current work_item"
        return None
    if name == "dashboard-api":
        dashboard = payload.get("dashboard")
        if not isinstance(dashboard, dict):
            return "dashboard API response does not include dashboard object"
        if not json_contains_value(dashboard, ctx.run_id):
            return "dashboard API response does not include current run_id"
        if not json_contains_value(dashboard, ctx.work_item):
            return "dashboard API response does not include current work_item"
        if not json_contains_value(dashboard, stage):
            return "dashboard API response does not include current stage"
        if not any(json_has_key(dashboard, key) for key in ("next_action", "terminal_handoff")):
            return "dashboard API response does not expose next action or terminal handoff"
        if phase == "running-stage":
            next_action = dashboard.get("next_action")
            if not isinstance(next_action, dict):
                return "dashboard API response does not expose running next action"
            if next_action.get("action") != "wait-for-stage":
                return "dashboard next action is not the running-stage wait state"
            if next_action.get("enabled") is not False:
                return "running-stage wait action must be disabled"
            if not json_contains_value(next_action, stage):
                return "running-stage wait action does not include current stage"
        return None
    if name == "stage-api":
        if not json_contains_value(payload, ctx.run_id):
            return "stage API response does not include current run_id"
        if not json_contains_value(payload, stage):
            return "stage API response does not include current stage"
        if not any(
            json_has_key(payload, key) for key in ("status", "state", "stage_state", "final_state")
        ):
            return "stage API response does not include stage status/state"
        if (
            phase == "running-stage"
            and observed_stage_status is not None
            and not json_contains_value(payload, observed_stage_status)
        ):
            return "stage API response does not include observed running status"
        return None
    if name == "questions-api":
        if not json_contains_value(payload, stage):
            return "questions API response does not include current stage"
        if not any(json_has_key(payload, key) for key in ("questions", "items", "state")):
            return "questions API response does not expose question state"
        return None
    if name == "logs-api":
        if not json_contains_value(payload, stage):
            return "logs API response does not include current stage"
        log_keys: tuple[str, ...] = ("logs", "chunks", "text", "lines")
        if phase == "running-stage":
            log_keys = (*log_keys, "available", "message")
        if not any(json_has_key(payload, key) for key in log_keys):
            return "logs API response does not expose log data"
        return None
    if name == "artifacts-api":
        if not json_contains_value(payload, stage):
            return "artifacts API response does not include current stage"
        primary = primary_stage_outputs.get(stage, "")
        if not (
            json_contains_value(payload, primary)
            or json_has_key(payload, "artifacts")
            or json_has_key(payload, "items")
        ):
            return "artifacts API response does not expose artifact list"
        return None
    if name == "tasks-api":
        if not json_contains_value(payload, ctx.run_id):
            return "tasks API response does not include current run_id"
        tasks = payload.get("tasks")
        if not isinstance(tasks, list) or not any(isinstance(item, dict) for item in tasks):
            return "tasks API response does not expose task projection"
        if not any(json_has_key(payload, key) for key in ("tasklist", "next_ready_task")):
            return "tasks API response does not expose task progression state"
    return None


def frontend_probe_by_name(
    probes: Sequence[Mapping[str, object]],
    name: str,
) -> Mapping[str, object]:
    for probe in probes:
        if probe.get("name") == name:
            return probe
    return {}


def frontend_probe_json_payload(
    probes: Sequence[Mapping[str, object]],
    name: str,
) -> dict[str, object]:
    payload = frontend_probe_by_name(probes, name).get("json_payload")
    return payload if isinstance(payload, dict) else {}


def operator_surface_check(*, name: str, ok: bool, detail: str) -> dict[str, object]:
    return {"name": name, "ok": ok, "detail": detail}


def frontend_operator_surface_checks(
    *,
    ctx: FrontendProbeContext,
    stage: str,
    probes: Sequence[Mapping[str, object]],
    primary_stage_outputs: Mapping[str, str] = PRIMARY_STAGE_OUTPUTS,
) -> dict[str, object]:
    page_probe = frontend_probe_by_name(probes, "page")
    page_body = str(page_probe.get("body_preview") or "")
    dashboard_payload = frontend_probe_json_payload(probes, "dashboard-api")
    dashboard_raw = dashboard_payload.get("dashboard")
    dashboard = dashboard_raw if isinstance(dashboard_raw, dict) else {}
    run_payload = frontend_probe_json_payload(probes, "run-api")
    stage_payload = frontend_probe_json_payload(probes, "stage-api")
    logs_payload = frontend_probe_json_payload(probes, "logs-api")
    artifacts_payload = frontend_probe_json_payload(probes, "artifacts-api")
    tasks_payload = frontend_probe_json_payload(probes, "tasks-api")
    primary = primary_stage_outputs.get(stage, "")
    checks = [
        operator_surface_check(
            name="operator-shell-visible",
            ok="AIDD Operator Console" in page_body or "AIDD UI" in page_body,
            detail="page exposes the operator UI shell label",
        ),
        operator_surface_check(
            name="work-item-context-visible",
            ok=json_contains_value(run_payload, ctx.work_item),
            detail="run payload exposes current work item",
        ),
        operator_surface_check(
            name="run-context-visible",
            ok=json_contains_value(run_payload, ctx.run_id),
            detail="run payload exposes current run id",
        ),
        operator_surface_check(
            name="active-stage-visible",
            ok=json_contains_value(stage_payload, stage),
            detail="stage payload exposes active checkpoint stage",
        ),
        operator_surface_check(
            name="stage-status-visible",
            ok=any(
                json_has_key(stage_payload, key)
                for key in ("status", "state", "stage_state", "final_state")
            ),
            detail="stage payload exposes operator-readable stage status",
        ),
        operator_surface_check(
            name="next-action-visible",
            ok=any(json_has_key(dashboard, key) for key in ("next_action", "terminal_handoff")),
            detail="dashboard payload exposes the next operator action or terminal handoff",
        ),
        operator_surface_check(
            name="runtime-log-surface-visible",
            ok=any(
                json_has_key(logs_payload, key)
                for key in ("logs", "chunks", "text", "lines", "message")
            ),
            detail="logs payload exposes saved or pending runtime log state",
        ),
        operator_surface_check(
            name="artifact-surface-visible",
            ok=(
                json_contains_value(artifacts_payload, primary)
                or json_has_key(artifacts_payload, "artifacts")
                or json_has_key(artifacts_payload, "items")
            ),
            detail="artifacts payload exposes primary output or artifact list state",
        ),
    ]
    first_failure = run_payload.get("first_failure")
    blockers = run_payload.get("blockers")
    has_blockers = isinstance(blockers, list) and bool(blockers)
    if first_failure is not None or has_blockers:
        checks.append(
            operator_surface_check(
                name="recovery-action-visible",
                ok=json_has_key(run_payload, "recovery_actions")
                or json_has_key(run_payload, "next_action"),
                detail="blocked or failed run exposes recovery guidance",
            )
        )
    if stage == "implement" and frontend_probe_by_name(probes, "tasks-api"):
        task_items = tasks_payload.get("tasks")
        task_items = task_items if isinstance(task_items, list) else []
        ready_ids = {
            str(item.get("id"))
            for item in task_items
            if isinstance(item, dict) and item.get("ready") is True
        }
        dependency_blocked = [
            item
            for item in task_items
            if isinstance(item, dict)
            and isinstance(item.get("missing_dependencies"), list)
            and item.get("missing_dependencies")
        ]
        actionable_blocked = dependency_blocked if ready_ids else []
        recovery_ok = all(
            isinstance(item.get("action_projection"), dict)
            and isinstance(item["action_projection"].get("recovery"), dict)
            and str(item["action_projection"]["recovery"].get("task_id")) in ready_ids
            for item in actionable_blocked
        )
        checks.append(
            operator_surface_check(
                name="task-recovery-projection-visible",
                ok=bool(tasks_payload) and (not actionable_blocked or recovery_ok),
                detail=(
                    "dependency-blocked tasks expose a core-owned recovery target"
                    if actionable_blocked
                    else "task projection is available; recovery target is not currently required"
                ),
            )
        )
    failed = [str(check["name"]) for check in checks if check.get("ok") is not True]
    return {"ok": not failed, "checks": checks, "failed_checks": failed}


def frontend_running_stage_surface_checks(
    *,
    ctx: FrontendProbeContext,
    stage: str,
    observed_stage_status: str,
    probes: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    page_probe = frontend_probe_by_name(probes, "page")
    page_body = str(page_probe.get("body_preview") or "")
    dashboard_payload = frontend_probe_json_payload(probes, "dashboard-api")
    dashboard_raw = dashboard_payload.get("dashboard")
    dashboard = dashboard_raw if isinstance(dashboard_raw, dict) else {}
    run_payload = frontend_probe_json_payload(probes, "run-api")
    stage_payload = frontend_probe_json_payload(probes, "stage-api")
    logs_payload = frontend_probe_json_payload(probes, "logs-api")
    next_action_raw = dashboard.get("next_action")
    next_action = next_action_raw if isinstance(next_action_raw, dict) else {}
    checks = [
        operator_surface_check(
            name="operator-shell-visible",
            ok="AIDD Operator Console" in page_body or "AIDD UI" in page_body,
            detail="page exposes the operator UI shell label",
        ),
        operator_surface_check(
            name="work-item-context-visible",
            ok=json_contains_value(run_payload, ctx.work_item),
            detail="run payload exposes current work item",
        ),
        operator_surface_check(
            name="run-context-visible",
            ok=json_contains_value(run_payload, ctx.run_id),
            detail="run payload exposes current run id",
        ),
        operator_surface_check(
            name="running-stage-visible",
            ok=json_contains_value(dashboard, stage)
            and json_contains_value(stage_payload, observed_stage_status),
            detail="dashboard and stage payloads expose the active running stage",
        ),
        operator_surface_check(
            name="running-wait-action-visible",
            ok=next_action.get("action") == "wait-for-stage"
            and next_action.get("enabled") is False
            and json_contains_value(next_action, stage),
            detail="dashboard exposes a disabled wait action for the running stage",
        ),
        operator_surface_check(
            name="runtime-log-affordance-visible",
            ok=any(
                json_has_key(logs_payload, key)
                for key in ("logs", "chunks", "text", "lines", "available", "message")
            ),
            detail="logs payload exposes either live log data or a pending-log message",
        ),
    ]
    failed = [str(check["name"]) for check in checks if check.get("ok") is not True]
    return {"ok": not failed, "checks": checks, "failed_checks": failed}


__all__ = [
    "FrontendProbeContext",
    "PRIMARY_STAGE_OUTPUTS",
    "frontend_checkpoint_timed_out",
    "frontend_checkpoint_timeout_seconds",
    "frontend_operator_surface_checks",
    "frontend_probe_by_name",
    "frontend_probe_json_payload",
    "frontend_probe_semantic_failure",
    "frontend_probe_targets",
    "frontend_running_probe_targets",
    "frontend_running_stage_surface_checks",
    "http_post_json",
    "http_probe",
    "json_contains_value",
    "json_has_key",
    "operator_surface_check",
]
