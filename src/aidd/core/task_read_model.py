from __future__ import annotations

import json
from pathlib import Path

from aidd.core.run_store import run_stage_root
from aidd.core.task_attempt_lifecycle import load_task_execution_plan
from aidd.core.task_ledger import TaskLedger, load_task_ledger, task_root


def _attempts(root: Path, *, workspace_root: Path) -> list[dict[str, object]]:
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
        attempts.append(
            {
                "number": int(path.name.removeprefix("attempt-")),
                "path": path.relative_to(workspace_root).as_posix(),
                "status": str(payload.get("status", "unknown")),
                "blocker": payload.get("blocker"),
            }
        )
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
            )
            if run_id is not None
            else []
        )
        tasks.append(
            {
                **entry.to_dict(),
                "outcome": card.outcome,
                "dominant_deliverable": card.dominant_deliverable,
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
                "attempts": attempt_items,
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
    return {
        "run_id": run_id,
        "source_tasklist_sha256": ledger.source_tasklist_sha256,
        "all_succeeded": ledger.all_succeeded(),
        "tasks": tasks,
        "finalization": {
            **ledger.finalization.to_dict(),
            "attempts": finalization_attempts,
        },
    }


__all__ = ["resolve_task_read_model"]
