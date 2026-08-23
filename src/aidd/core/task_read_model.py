from __future__ import annotations

import json
from pathlib import Path

from aidd.core.implementation_eligibility import implementation_finalization_blocker
from aidd.core.run_store import run_stage_root
from aidd.core.task_attempt_evidence import resolve_task_attempt_evidence
from aidd.core.task_attempt_lifecycle import load_task_execution_plan
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    TaskLedgerEntry,
    load_task_ledger,
    task_root,
)

TASK_WORKSPACE_SCHEMA_VERSION = 1
TASK_ACTION_PROJECTION_SCHEMA_VERSION = 1


def _dependency_graph(ledger: TaskLedger) -> dict[str, dict[str, object]]:
    dependents: dict[str, list[str]] = {entry.id: [] for entry in ledger.tasks}
    for entry in ledger.tasks:
        for dependency in entry.dependencies:
            if dependency in dependents:
                dependents[dependency].append(entry.id)
    ready = set(ledger.ready_task_ids())
    return {
        entry.id: {
            "dependencies": list(entry.dependencies),
            "dependents": dependents[entry.id],
            "dependency_eligible": entry.id in ready,
            "status": entry.status.value,
        }
        for entry in ledger.tasks
    }


def _critical_path(ledger: TaskLedger) -> list[str]:
    """Return an advisory longest remaining dependency chain in plan order."""

    entries = {entry.id: entry for entry in ledger.tasks}
    remaining = {
        entry.id for entry in ledger.tasks if entry.status is not TaskExecutionStatus.SUCCEEDED
    }
    memo: dict[str, list[str]] = {}

    def path(task_id: str) -> list[str]:
        if task_id in memo:
            return memo[task_id]
        entry = entries[task_id]
        candidates = [
            path(dependency)
            for dependency in entry.dependencies
            if dependency in remaining
        ]
        longest = max(candidates, key=len, default=[])
        memo[task_id] = [*longest, task_id]
        return memo[task_id]

    paths = [path(entry.id) for entry in ledger.tasks if entry.id in remaining]
    if not paths:
        return []
    return max(enumerate(paths), key=lambda item: (len(item[1]), -item[0]))[1]


def _task_durable_events(
    *,
    entry: TaskLedgerEntry,
    attempts: list[dict[str, object]],
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for attempt in attempts:
        status = attempt.get("status")
        if status is None:
            continue
        events.append(
            {
                "kind": "task-attempt",
                "status": status,
                "attempt_number": attempt.get("number"),
                "path": attempt.get("path"),
            }
        )
    if entry.updated_at_utc is not None:
        events.append(
            {
                "kind": "task-ledger",
                "status": entry.status.value,
                "recorded_at_utc": entry.updated_at_utc,
                "path": entry.latest_attempt_path,
            }
        )
    return events


def _task_group(*, task_id: str, status: TaskExecutionStatus, ready: set[str]) -> str:
    if status is TaskExecutionStatus.SUCCEEDED:
        return "Done"
    if status is TaskExecutionStatus.EXECUTING:
        return "Running"
    if task_id in ready:
        return "Ready"
    return "Blocked"


def _action_state(
    *, action: str, eligible: bool, disabled_reason: str | None = None
) -> dict[str, object]:
    if eligible and disabled_reason is not None:
        raise ValueError(f"Eligible task action `{action}` cannot have a disabled reason.")
    if not eligible and not (disabled_reason or "").strip():
        raise ValueError(f"Disabled task action `{action}` must have a literal reason.")
    return {
        "action": action,
        "eligible": eligible,
        "disabled_reason": disabled_reason,
    }


def _task_action_projection(
    *,
    entry: TaskLedgerEntry,
    missing_dependencies: list[str],
    ready: set[str],
    ledger: TaskLedger,
) -> dict[str, object]:
    """Project mutually exclusive task mutations from the authoritative ledger.

    The projection deliberately contains no runtime-specific values.  The UI service adds
    the selected Runner readiness before exposing a mutation affordance; the browser never
    needs to infer this policy from status or group labels.
    """

    dependency_reason = (
        "Task dependencies are incomplete: " + ", ".join(missing_dependencies) + "."
        if missing_dependencies
        else None
    )
    run_eligible = entry.status is TaskExecutionStatus.PENDING and entry.id in ready
    run_reason = (
        None
        if run_eligible
        else dependency_reason
        if dependency_reason is not None
        else "Task is not eligible for a new run."
    )
    resume_eligible = entry.status in {
        TaskExecutionStatus.BLOCKED,
        TaskExecutionStatus.FAILED,
    } and entry.id in ready
    resume_reason = (
        None
        if resume_eligible
        else "Task has no interrupted attempt to resume."
        if entry.status is TaskExecutionStatus.PENDING
        else "Task attempt is already running; inspect the active attempt."
        if entry.status is TaskExecutionStatus.EXECUTING
        else dependency_reason
        if dependency_reason is not None
        else "Task already succeeded; preserved success cannot be resumed."
    )
    finalization_status = ledger.finalization.status
    finalize_eligible = (
        entry.status is TaskExecutionStatus.SUCCEEDED
        and ledger.all_succeeded()
        and finalization_status
        in {TaskFinalizationStatus.PENDING, TaskFinalizationStatus.FAILED}
    )
    finalize_reason = (
        None
        if finalize_eligible
        else "Implementation finalization is already running."
        if finalization_status is TaskFinalizationStatus.EXECUTING
        else "Implementation is already finalized."
        if finalization_status is TaskFinalizationStatus.SUCCEEDED
        else "Every task must succeed before finalization."
        if not ledger.all_succeeded()
        else "Selected task must succeed before finalization."
    )
    recommended: str | None
    if run_eligible:
        recommended = "run"
    elif resume_eligible:
        recommended = "resume"
    elif finalize_eligible:
        recommended = "finalize"
    else:
        recommended = None
    return {
        "schema_version": TASK_ACTION_PROJECTION_SCHEMA_VERSION,
        "recommended": recommended,
        "core_recommended": recommended,
        "states": {
            "run": _action_state(action="run", eligible=run_eligible, disabled_reason=run_reason),
            "resume": _action_state(
                action="resume", eligible=resume_eligible, disabled_reason=resume_reason
            ),
            "finalize": _action_state(
                action="finalize", eligible=finalize_eligible, disabled_reason=finalize_reason
            ),
        },
        "runner": {
            "required": recommended is not None,
            "eligible": None,
            "disabled_reason": "Runner readiness must be revalidated by the service.",
        },
    }


def _attempts(
    root: Path,
    *,
    workspace_root: Path,
    task_evidence_identity: tuple[str, str, str] | None = None,
) -> list[dict[str, object]]:
    attempts: list[dict[str, object]] = []
    if not root.exists():
        return attempts
    for path in sorted(root.glob("attempt-[0-9][0-9][0-9][0-9]")):
        state_path = path / "attempt-state.json"
        if not state_path.exists():
            state_path = path / "finalization-state.json"
        payload: dict[str, object] = {}
        if state_path.exists():
            try:
                loaded = json.loads(state_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    payload = loaded
            except (OSError, ValueError, TypeError):
                payload = {"status": "unknown"}
        item: dict[str, object] = {
            "number": int(path.name.removeprefix("attempt-")),
            "path": path.relative_to(workspace_root).as_posix(),
            "status": str(payload.get("status", "unknown")),
            "blocker": payload.get("blocker"),
        }
        if task_evidence_identity is not None:
            work_item, run_id, task_id = task_evidence_identity
            evidence = resolve_task_attempt_evidence(
                task_attempt_path=path,
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                task_id=task_id,
                task_attempt_number=int(path.name.removeprefix("attempt-")),
            )
            item["runtime_evidence"] = {
                "layout": evidence.layout,
                "stage_attempts": [reference.to_dict() for reference in evidence.stage_attempts],
            }
        attempts.append(item)
    return attempts


def resolve_task_read_model(
    *, workspace_root: Path, work_item: str, run_id: str | None = None
) -> dict[str, object]:
    plan = load_task_execution_plan(workspace_root=workspace_root, work_item=work_item)
    ledger = (
        load_task_ledger(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )
        if run_id is not None
        else None
    ) or TaskLedger.create(plan)
    if ledger.source_tasklist_sha256 != plan.source_sha256:
        raise ValueError(
            "Published tasklist changed after task execution state was created; "
            "start a new continuation run from tasklist."
        )
    cards = plan.by_id()
    ready = set(ledger.ready_task_ids())
    tasks: list[dict[str, object]] = []
    groups: dict[str, list[str]] = {name: [] for name in ("Ready", "Running", "Blocked", "Done")}
    graph = _dependency_graph(ledger)
    finalization_eligible = ledger.all_succeeded()
    for entry in ledger.tasks:
        card = cards[entry.id]
        attempt_items = (
            _attempts(
                task_root(
                    workspace_root=workspace_root,
                    work_item=work_item,
                    run_id=run_id,
                    task_id=entry.id,
                )
                / "attempts",
                workspace_root=workspace_root,
                task_evidence_identity=(work_item, run_id, entry.id),
            )
            if run_id is not None
            else []
        )
        group = _task_group(task_id=entry.id, status=entry.status, ready=ready)
        groups[group].append(entry.id)
        missing_dependencies = [
            dependency
            for dependency in entry.dependencies
            if ledger.entry(dependency).status is not TaskExecutionStatus.SUCCEEDED
        ]
        evidence_links: list[str] = []
        if entry.latest_attempt_path is not None:
            evidence_links.append(entry.latest_attempt_path)
        for attempt in attempt_items:
            runtime_evidence = attempt.get("runtime_evidence")
            if isinstance(runtime_evidence, dict):
                stage_attempts = runtime_evidence.get("stage_attempts", [])
                if isinstance(stage_attempts, list):
                    evidence_links.extend(
                        str(reference["path"])
                        for reference in stage_attempts
                        if isinstance(reference, dict) and isinstance(reference.get("path"), str)
                    )
        task_events = _task_durable_events(entry=entry, attempts=attempt_items)
        action_projection = _task_action_projection(
            entry=entry,
            missing_dependencies=missing_dependencies,
            ready=ready,
            ledger=ledger,
        )
        tasks.append(
            {
                **entry.to_dict(),
                "outcome": card.outcome,
                "dominant_deliverable": card.dominant_deliverable,
                "execution_mode": card.execution_mode.value,
                "in_scope": card.in_scope,
                "scope_paths": list(card.scope_paths),
                "context": card.context,
                "implementation_constraints": card.implementation_constraints,
                "out_of_scope": card.out_of_scope,
                "acceptance_criteria": [
                    {"id": item.id, "text": item.text} for item in card.acceptance_criteria
                ],
                "verification": card.verification,
                "ready": entry.id in ready,
                "group": group,
                "dependency_eligible": entry.id in ready,
                "missing_dependencies": missing_dependencies,
                "dependency_state": {
                    "satisfied": not missing_dependencies,
                    "missing": missing_dependencies,
                },
                "preserved_success": entry.status is TaskExecutionStatus.SUCCEEDED,
                "evidence_links": list(dict.fromkeys(evidence_links)),
                "durable_events": task_events,
                "last_durable_event": task_events[-1] if task_events else None,
                "attempts": attempt_items,
                "action_projection": action_projection,
            }
        )
    finalization_attempts = []
    if run_id is not None:
        finalization_attempts = _attempts(
            run_stage_root(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage="implement",
            )
            / "finalization"
            / "attempts",
            workspace_root=workspace_root,
        )
    finalization_blocker = (
        implementation_finalization_blocker(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )
        if run_id is not None
        else "No implementation run is selected."
    )
    next_ready_task = next(
        (task_id for task_id in ledger.ready_task_ids() if task_id in ready),
        None,
    )
    review_eligible = finalization_blocker is None
    return {
        "schema_version": TASK_WORKSPACE_SCHEMA_VERSION,
        "run_id": run_id,
        "status": "ready",
        "source_tasklist_sha256": ledger.source_tasklist_sha256,
        "tasklist": {
            "ledger_sha256": ledger.source_tasklist_sha256,
            "published_sha256": plan.source_sha256,
            "matches": True,
        },
        "all_succeeded": ledger.all_succeeded(),
        "finalization_eligible": finalization_eligible,
        "finalization_eligibility": {
            "eligible": finalization_eligible,
            "reason": (
                None
                if finalization_eligible
                else "Every task must succeed before finalization."
            ),
        },
        "review_eligible": review_eligible,
        "review_eligibility": {
            "eligible": review_eligible,
            "reason": finalization_blocker,
        },
        "review_blocker": finalization_blocker,
        "groups": groups,
        "dependency_graph": graph,
        "next_ready_task": next_ready_task,
        "next_ready": (
            {
                "task_id": next_ready_task,
                "reason": "First dependency-eligible task in canonical tasklist order.",
            }
            if next_ready_task is not None
            else None
        ),
        "critical_path": _critical_path(ledger),
        "preserved_successes": [
            entry.id
            for entry in ledger.tasks
            if entry.status is TaskExecutionStatus.SUCCEEDED
        ],
        "tasks": tasks,
        "finalization": {
            **ledger.finalization.to_dict(),
            "attempts": finalization_attempts,
        },
    }


__all__ = ["resolve_task_read_model"]
