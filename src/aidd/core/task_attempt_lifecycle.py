from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from aidd.core.identifiers import contained_component_path
from aidd.core.interview import stage_has_unresolved_blocking_questions
from aidd.core.run_store import load_stage_metadata, next_attempt_number
from aidd.core.stage_validation import update_stage_unblock_state
from aidd.core.state_machine import StageState
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskLedger,
    ensure_task_ledger,
    persist_task_ledger,
    task_root,
)
from aidd.core.task_plan import TaskCard, TaskPlan, parse_task_plan


@dataclass(frozen=True, slots=True)
class TaskExecutionContext:
    plan: TaskPlan
    ledger: TaskLedger
    task: TaskCard
    global_attempt_start: int
    task_attempt_number: int
    task_attempt_path: Path


class TaskResumeBlockedError(ValueError):
    """Raised when a blocked task still requires operator input."""


class RepositoryBaselineProvider(Protocol):
    def __call__(self, *, project_root: Path, task_id: str) -> dict[str, object]: ...


def published_tasklist_path(*, workspace_root: Path, work_item: str) -> Path:
    return (
        workspace_root / "workitems" / work_item / "stages" / "tasklist" / "output" / "tasklist.md"
    )


def load_task_execution_plan(*, workspace_root: Path, work_item: str) -> TaskPlan:
    path = published_tasklist_path(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    if not path.exists():
        raise ValueError(f"Published tasklist is missing: {path.as_posix()}.")
    return parse_task_plan(path.read_text(encoding="utf-8"))


def _task_selection_path(*, workspace_root: Path, work_item: str) -> Path:
    return workspace_root / "workitems" / work_item / "context" / "task-selection.md"


def _selected_task_id(*, workspace_root: Path, work_item: str) -> str | None:
    path = _task_selection_path(workspace_root=workspace_root, work_item=work_item)
    if not path.exists():
        return None
    match = re.search(r"Task id\s*:\s*`([^`]+)`", path.read_text(encoding="utf-8"))
    return match.group(1).upper() if match is not None else None


def write_task_selection_context(*, workspace_root: Path, work_item: str, task: TaskCard) -> Path:
    path = _task_selection_path(workspace_root=workspace_root, work_item=work_item)
    lines = [
        "# Task Selection",
        "",
        "## Selected task",
        "",
        f"- Task id: `{task.id}`",
        f"- Title: {task.title}",
        f"- Outcome: {task.outcome}",
        f"- Dominant deliverable: {task.dominant_deliverable}",
        f"- In scope: {task.in_scope}",
        "",
        "## Acceptance criteria",
        "",
    ]
    lines.extend(f"- `{criterion.id}`: {criterion.text}" for criterion in task.acceptance_criteria)
    lines.extend(
        [
            "",
            "## Dependencies",
            "",
            "- " + (", ".join(f"`{item}`" for item in task.dependencies) or "none"),
            "",
            "## Verification",
            "",
            f"- {task.verification}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _attempt_state_path(attempt_path: Path) -> Path:
    return attempt_path / "attempt-state.json"


def _write_attempt_state(
    attempt_path: Path,
    *,
    task_id: str,
    attempt_number: int,
    status: str,
    blocker: str | None = None,
) -> None:
    _attempt_state_path(attempt_path).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": task_id,
                "attempt_number": attempt_number,
                "status": status,
                "blocker": blocker,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def task_attempts_root(*, workspace_root: Path, work_item: str, run_id: str, task_id: str) -> Path:
    return contained_component_path(
        task_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            task_id=task_id,
        ),
        "attempts",
        boundary_root=workspace_root,
        label="task attempts directory",
    )


def existing_attempts(attempts_root: Path) -> tuple[tuple[int, Path], ...]:
    attempts: list[tuple[int, Path]] = []
    if not attempts_root.exists():
        return ()
    for path in attempts_root.glob("attempt-[0-9][0-9][0-9][0-9]"):
        try:
            number = int(path.name.removeprefix("attempt-"))
        except ValueError:
            continue
        attempts.append((number, path))
    return tuple(sorted(attempts))


def reconcile_staging_attempts(
    attempts_root: Path,
    *,
    task_id: str,
) -> None:
    if not attempts_root.exists():
        return
    for staging in sorted(attempts_root.glob(".attempt-*-*.staging")):
        match = re.match(r"^\.attempt-(\d+)-", staging.name)
        if match is None:
            continue
        number = int(match.group(1))
        target = attempts_root / f"attempt-{number:04d}"
        if target.exists():
            shutil.rmtree(staging, ignore_errors=True)
            continue
        staging.replace(target)
        _write_attempt_state(
            target,
            task_id=task_id,
            attempt_number=number,
            status="abandoned",
            blocker="Task attempt was abandoned during atomic preparation.",
        )


def reconcile_task_execution_state(
    *, workspace_root: Path, work_item: str, run_id: str, ledger: TaskLedger
) -> TaskLedger:
    """Terminalize abandoned task attempts after the run lease has been acquired."""

    reconciled = ledger
    for entry in ledger.tasks:
        attempts_root = task_attempts_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            task_id=entry.id,
        )
        reconcile_staging_attempts(attempts_root, task_id=entry.id)
        attempts = existing_attempts(attempts_root)
        for number, path in attempts:
            if number > entry.attempt_count:
                _write_attempt_state(
                    path,
                    task_id=entry.id,
                    attempt_number=number,
                    status="abandoned",
                    blocker="Task attempt was abandoned before ledger commit.",
                )
        if entry.status is not TaskExecutionStatus.EXECUTING:
            continue
        if entry.latest_attempt_path is not None:
            attempt_path = workspace_root / entry.latest_attempt_path
            if attempt_path.exists():
                _write_attempt_state(
                    attempt_path,
                    task_id=entry.id,
                    attempt_number=entry.attempt_count,
                    status="abandoned",
                    blocker="Task execution was interrupted before a terminal result.",
                )
        reconciled = reconciled.transition(
            entry.id,
            TaskExecutionStatus.FAILED,
            blocker="Task execution was interrupted; resume creates a new attempt.",
        )
    if reconciled != ledger:
        persist_task_ledger(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            ledger=reconciled,
        )
    return reconciled


def copy_interview_evidence(stage_root: Path, attempt_path: Path) -> None:
    for name in ("questions.md", "answers.md"):
        source = stage_root / name
        if source.exists():
            shutil.copy2(source, attempt_path / name)


def prepare_task_attempt(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_id: str,
    project_root: Path,
    repository_baseline: RepositoryBaselineProvider,
) -> TaskExecutionContext:
    plan = load_task_execution_plan(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    ledger = ensure_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        plan=plan,
    )
    ledger = reconcile_task_execution_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    task = plan.by_id().get(task_id)
    if task is None:
        raise ValueError(f"Unknown task id `{task_id}`.")
    entry = ledger.entry(task_id)
    if entry.status is TaskExecutionStatus.SUCCEEDED:
        raise ValueError(f"Task `{task_id}` has already succeeded.")
    resume_blocked_task = entry.status is TaskExecutionStatus.BLOCKED
    if resume_blocked_task:
        unblock = update_stage_unblock_state(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        )
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        )
        resumed_preparing = (
            metadata is not None
            and metadata.status == StageState.PREPARING.value
            and any(change.status == StageState.BLOCKED.value for change in metadata.status_history)
            and not stage_has_unresolved_blocking_questions(
                workspace_root=workspace_root,
                work_item=work_item,
                stage="implement",
            )
        )
        if not unblock.unblocked and not resumed_preparing:
            raise TaskResumeBlockedError(
                f"Task `{task_id}` is still blocked by unresolved questions or approvals."
            )
    attempts_root = task_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        task_id=task_id,
    )
    reconcile_staging_attempts(attempts_root, task_id=task_id)
    task_attempt_number = (
        max((entry.attempt_count, *(number for number, _ in existing_attempts(attempts_root)))) + 1
    )
    attempts_root.mkdir(parents=True, exist_ok=True)
    staging_path = attempts_root / f".attempt-{task_attempt_number:04d}-{uuid4().hex}.staging"
    staging_path.mkdir()
    baseline = repository_baseline(project_root=project_root, task_id=task_id)
    (staging_path / "repository-baseline.json").write_text(
        json.dumps(baseline, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_attempt_state(
        staging_path,
        task_id=task_id,
        attempt_number=task_attempt_number,
        status="preparing",
    )
    task_attempt_path = contained_component_path(
        attempts_root,
        f"attempt-{task_attempt_number:04d}",
        boundary_root=workspace_root,
        label="task attempt id",
    )
    staging_path.replace(task_attempt_path)
    implement_stage_root = workspace_root / "workitems" / work_item / "stages" / "implement"
    for document_name in (
        "implementation-report.md",
        "stage-result.md",
        "validator-report.md",
        "repair-brief.md",
    ):
        (implement_stage_root / document_name).unlink(missing_ok=True)
    preserve_interview = (
        resume_blocked_task
        or _selected_task_id(
            workspace_root=workspace_root,
            work_item=work_item,
        )
        == task_id
    )
    if preserve_interview:
        copy_interview_evidence(implement_stage_root, task_attempt_path)
    else:
        for document_name in ("questions.md", "answers.md"):
            (implement_stage_root / document_name).unlink(missing_ok=True)
    write_task_selection_context(
        workspace_root=workspace_root,
        work_item=work_item,
        task=task,
    )
    ledger = ledger.transition(
        task_id,
        TaskExecutionStatus.EXECUTING,
        attempt_number=task_attempt_number,
        latest_attempt_path=task_attempt_path.relative_to(workspace_root).as_posix(),
    )
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    _write_attempt_state(
        task_attempt_path,
        task_id=task_id,
        attempt_number=task_attempt_number,
        status="executing",
    )
    return TaskExecutionContext(
        plan=plan,
        ledger=ledger,
        task=task,
        global_attempt_start=next_attempt_number(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        ),
        task_attempt_number=task_attempt_number,
        task_attempt_path=task_attempt_path,
    )


def complete_task_attempt(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    status: TaskExecutionStatus,
    blocker: str | None,
) -> TaskLedger:
    ledger = context.ledger.transition(
        context.task.id,
        status,
        latest_attempt_path=context.task_attempt_path.relative_to(workspace_root).as_posix(),
        blocker=blocker,
    )
    _write_attempt_state(
        context.task_attempt_path,
        task_id=context.task.id,
        attempt_number=ledger.entry(context.task.id).attempt_count,
        status=status.value,
        blocker=blocker,
    )
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    return ledger


__all__ = [
    "RepositoryBaselineProvider",
    "TaskExecutionContext",
    "TaskResumeBlockedError",
    "complete_task_attempt",
    "copy_interview_evidence",
    "existing_attempts",
    "load_task_execution_plan",
    "prepare_task_attempt",
    "published_tasklist_path",
    "reconcile_staging_attempts",
    "reconcile_task_execution_state",
    "task_attempts_root",
    "write_task_selection_context",
]
