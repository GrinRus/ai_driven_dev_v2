from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from aidd.core.identifiers import contained_component_path
from aidd.core.run_store import run_stage_root
from aidd.core.task_attempt_lifecycle import existing_attempts, reconcile_staging_attempts
from aidd.core.task_ledger import (
    TaskFinalizationStatus,
    TaskLedger,
    persist_task_ledger,
)
from aidd.core.task_plan import TaskPlan


@dataclass(frozen=True, slots=True)
class TaskFinalizationContext:
    ledger: TaskLedger
    attempt_path: Path
    attempt_number: int


def _finalization_attempts_root(*, workspace_root: Path, work_item: str, run_id: str) -> Path:
    finalization_root = contained_component_path(
        run_stage_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        ),
        "finalization",
        boundary_root=workspace_root,
        label="finalization directory",
    )
    return contained_component_path(
        finalization_root,
        "attempts",
        boundary_root=workspace_root,
        label="finalization attempts directory",
    )


def prepare_task_finalization(
    *, workspace_root: Path, work_item: str, run_id: str, ledger: TaskLedger
) -> TaskFinalizationContext:
    if not ledger.all_succeeded():
        raise ValueError("Cannot finalize implementation before every task succeeds.")
    if ledger.finalization.status is TaskFinalizationStatus.SUCCEEDED:
        raise ValueError("Implementation task finalization has already succeeded.")
    if ledger.finalization.status is TaskFinalizationStatus.EXECUTING:
        ledger = ledger.transition_finalization(
            TaskFinalizationStatus.FAILED,
            blocker="Aggregate finalization was interrupted before a terminal result.",
        )
    attempts_root = _finalization_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    reconcile_staging_attempts(attempts_root, task_id="finalization")
    existing = existing_attempts(attempts_root)
    number = max((ledger.finalization.attempt_count, *(item for item, _ in existing))) + 1
    attempts_root.mkdir(parents=True, exist_ok=True)
    staging = attempts_root / f".attempt-{number:04d}-{uuid4().hex}.staging"
    staging.mkdir()
    (staging / "finalization-state.json").write_text(
        json.dumps(
            {"schema_version": 1, "attempt_number": number, "status": "executing"},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    attempt_path = contained_component_path(
        attempts_root,
        f"attempt-{number:04d}",
        boundary_root=workspace_root,
        label="finalization attempt id",
    )
    staging.replace(attempt_path)
    ledger = ledger.transition_finalization(
        TaskFinalizationStatus.EXECUTING,
        attempt_number=number,
        latest_attempt_path=attempt_path.relative_to(workspace_root).as_posix(),
    )
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    return TaskFinalizationContext(
        ledger=ledger,
        attempt_path=attempt_path,
        attempt_number=number,
    )


def complete_task_finalization(
    *,
    context: TaskFinalizationContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    succeeded: bool,
    blocker: str | None = None,
) -> TaskLedger:
    status = TaskFinalizationStatus.SUCCEEDED if succeeded else TaskFinalizationStatus.FAILED
    ledger = context.ledger.transition_finalization(status, blocker=blocker)
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    (context.attempt_path / "finalization-state.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "attempt_number": context.attempt_number,
                "status": status.value,
                "blocker": blocker,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return ledger


def _section(markdown: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        markdown,
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group("body").strip() if match is not None else ""


def render_aggregate_implementation_report(
    *,
    plan: TaskPlan,
    ledger: TaskLedger,
    workspace_root: Path,
) -> str:
    if not ledger.all_succeeded():
        raise ValueError("Cannot aggregate implementation evidence before every task succeeds.")
    summaries: list[str] = []
    touched: list[str] = []
    verification: list[str] = []
    follow_up: list[str] = []
    for task in plan.tasks:
        entry = ledger.entry(task.id)
        if entry.latest_attempt_path is None:
            raise ValueError(f"Task `{task.id}` has no attempt evidence path.")
        report_path = workspace_root / entry.latest_attempt_path / "implementation-report.md"
        report = report_path.read_text(encoding="utf-8")
        summaries.append(
            f"- `{task.id}`: {task.outcome} Evidence: "
            f"`{entry.latest_attempt_path}/implementation-report.md`."
        )
        for line in _section(report, "Touched files").splitlines():
            if line.strip().startswith("-") and line not in touched:
                touched.append(line)
        for line in _section(report, "Verification notes").splitlines():
            if line.strip().startswith("-"):
                verification.append(f"- `{task.id}` {line.strip()[1:].strip()}")
        for criterion in task.acceptance_criteria:
            verification.append(
                f"- `{task.id}` `{criterion.id}` -> covered by "
                f"`{entry.latest_attempt_path}/implementation-report.md`."
            )
        for line in _section(report, "Follow-up notes").splitlines():
            if line.strip().startswith("-") and "none" not in line.casefold():
                follow_up.append(f"- `{task.id}` {line.strip()[1:].strip()}")
    lines = [
        "# Implementation Report",
        "",
        "## Selected task",
        "",
        "- Task ids: " + ", ".join(f"`{task.id}`" for task in plan.tasks),
        "",
        "## Change summary",
        "",
        *summaries,
        "",
        "## Touched files",
        "",
        *(touched or ["- none"]),
        "",
        "## Verification notes",
        "",
        *verification,
        "",
        "## Follow-up notes",
        "",
        *(follow_up or ["- none"]),
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "TaskFinalizationContext",
    "complete_task_finalization",
    "prepare_task_finalization",
    "render_aggregate_implementation_report",
]
