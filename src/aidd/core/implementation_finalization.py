from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aidd.core.attempt_lineage import (
    AttemptKind,
    AttemptLineage,
    AttemptScope,
    FinalizationAttemptState,
)
from aidd.core.identifiers import contained_component_path
from aidd.core.markdown import extract_h2_section
from aidd.core.run_store import load_run_manifest, load_stage_metadata, run_stage_root
from aidd.core.task_attempt_lifecycle import existing_attempts, reconcile_staging_attempts
from aidd.core.task_ledger import (
    TaskFinalizationStatus,
    TaskLedger,
    persist_task_ledger,
)
from aidd.core.task_plan import TaskExecutionMode, TaskPlan


@dataclass(frozen=True, slots=True)
class TaskFinalizationContext:
    ledger: TaskLedger
    attempt_path: Path
    attempt_number: int
    lineage: AttemptLineage | None = None


def aggregate_execution_mode(plan: TaskPlan) -> TaskExecutionMode:
    """Return the effective repository mode for system-owned aggregate evidence."""

    if any(
        task.execution_mode is TaskExecutionMode.REPOSITORY_CHANGE for task in plan.tasks
    ):
        return TaskExecutionMode.REPOSITORY_CHANGE
    return TaskExecutionMode.VERIFICATION_ONLY


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
    load_run_manifest(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    load_stage_metadata(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id, stage="implement"
    )
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
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    lineage = AttemptLineage(
        scope=AttemptScope.FINALIZATION,
        attempt_kind=AttemptKind.FINALIZATION,
        attempt_number=number,
    )
    state = FinalizationAttemptState(
        attempt_number=number,
        status="executing",
        created_at_utc=timestamp,
        updated_at_utc=timestamp,
        lineage=lineage,
    )
    (staging / "finalization-state.json").write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n",
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
        lineage=lineage,
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
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    state_path = context.attempt_path / "finalization-state.json"
    created_at_utc = timestamp
    lineage = AttemptLineage(
        scope=AttemptScope.FINALIZATION,
        attempt_kind=AttemptKind.FINALIZATION,
        attempt_number=context.attempt_number,
    )
    try:
        existing_payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError):
        existing = None
    else:
        existing = FinalizationAttemptState.from_dict(existing_payload)
    if existing is not None:
        if existing.created_at_utc is not None and existing.created_at_utc.strip():
            created_at_utc = existing.created_at_utc
        if existing.lineage is not None:
            lineage = existing.lineage
    state = FinalizationAttemptState(
        attempt_number=context.attempt_number,
        status=status.value,
        blocker=blocker,
        created_at_utc=created_at_utc,
        updated_at_utc=timestamp,
        lineage=lineage,
    )
    (context.attempt_path / "finalization-state.json").write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ledger


def _section_bullets(markdown: str, heading: str) -> tuple[str, ...]:
    """Return top-level bullets with wrapped Markdown lines joined together.

    Runtime-authored implementation reports often wrap a verification item over
    several physical lines.  Treat only column-zero ``- `` markers as new items;
    indented lines remain part of the preceding item so command and result
    evidence cannot be split into unverifiable fragments during aggregation.
    """

    section = extract_h2_section(markdown, heading)
    bullets: list[str] = []
    current: str | None = None
    for raw_line in section.splitlines():
        if raw_line.startswith("- "):
            if current is not None:
                bullets.append(current)
            current = raw_line[2:].strip()
        elif current is not None and raw_line.strip():
            current += " " + raw_line.strip()
    if current is not None:
        bullets.append(current)
    return tuple(bullets)


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
        for line in extract_h2_section(report, "Touched files").splitlines():
            normalized_line = line.strip()
            if (
                normalized_line.startswith("-")
                and normalized_line.casefold() != "- none"
                and normalized_line not in touched
            ):
                touched.append(normalized_line)
        verification_section = (
            "Verification" if extract_h2_section(report, "Verification") else "Verification notes"
        )
        for bullet in _section_bullets(report, verification_section):
            verification.append(f"- `{task.id}` {bullet}")
        for criterion in task.acceptance_criteria:
            verification.append(
                f"- `{task.id}` `{criterion.id}` -> covered by "
                f"`{entry.latest_attempt_path}/implementation-report.md`."
            )
        for line in extract_h2_section(report, "Follow-up notes").splitlines():
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
    "aggregate_execution_mode",
    "complete_task_finalization",
    "prepare_task_finalization",
    "render_aggregate_implementation_report",
]
