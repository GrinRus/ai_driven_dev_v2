from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from aidd.core.identifiers import contained_component_path
from aidd.core.run_store import run_stage_root, write_json_payload
from aidd.core.task_plan import TaskCard, TaskPlan

TASK_LEDGER_FILENAME = "task-ledger.json"
TASKS_DIRNAME = "tasks"


class TaskExecutionStatus(StrEnum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"
    FAILED = "failed"


class TaskFinalizationStatus(StrEnum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[TaskExecutionStatus, frozenset[TaskExecutionStatus]] = {
    TaskExecutionStatus.PENDING: frozenset({TaskExecutionStatus.EXECUTING}),
    TaskExecutionStatus.EXECUTING: frozenset(
        {
            TaskExecutionStatus.SUCCEEDED,
            TaskExecutionStatus.BLOCKED,
            TaskExecutionStatus.FAILED,
        }
    ),
    TaskExecutionStatus.BLOCKED: frozenset({TaskExecutionStatus.EXECUTING}),
    TaskExecutionStatus.FAILED: frozenset({TaskExecutionStatus.EXECUTING}),
    TaskExecutionStatus.SUCCEEDED: frozenset(),
}

_ALLOWED_FINALIZATION_TRANSITIONS: dict[
    TaskFinalizationStatus, frozenset[TaskFinalizationStatus]
] = {
    TaskFinalizationStatus.PENDING: frozenset({TaskFinalizationStatus.EXECUTING}),
    TaskFinalizationStatus.EXECUTING: frozenset(
        {TaskFinalizationStatus.SUCCEEDED, TaskFinalizationStatus.FAILED}
    ),
    TaskFinalizationStatus.FAILED: frozenset({TaskFinalizationStatus.EXECUTING}),
    TaskFinalizationStatus.SUCCEEDED: frozenset(),
}


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class TaskLedgerEntry:
    id: str
    title: str
    dependencies: tuple[str, ...]
    acceptance_ids: tuple[str, ...]
    status: TaskExecutionStatus = TaskExecutionStatus.PENDING
    attempt_count: int = 0
    latest_attempt_path: str | None = None
    blocker: str | None = None
    updated_at_utc: str | None = None

    @classmethod
    def from_card(cls, card: TaskCard) -> TaskLedgerEntry:
        return cls(
            id=card.id,
            title=card.title,
            dependencies=card.dependencies,
            acceptance_ids=tuple(item.id for item in card.acceptance_criteria),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskLedgerEntry:
        return cls(
            id=str(payload["id"]),
            title=str(payload["title"]),
            dependencies=tuple(str(item) for item in payload.get("dependencies", [])),
            acceptance_ids=tuple(str(item) for item in payload.get("acceptance_ids", [])),
            status=TaskExecutionStatus(str(payload.get("status", "pending"))),
            attempt_count=int(payload.get("attempt_count", 0)),
            latest_attempt_path=(
                str(payload["latest_attempt_path"])
                if payload.get("latest_attempt_path") is not None
                else None
            ),
            blocker=(str(payload["blocker"]) if payload.get("blocker") is not None else None),
            updated_at_utc=(
                str(payload["updated_at_utc"])
                if payload.get("updated_at_utc") is not None
                else None
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "dependencies": list(self.dependencies),
            "acceptance_ids": list(self.acceptance_ids),
            "status": self.status.value,
            "attempt_count": self.attempt_count,
            "latest_attempt_path": self.latest_attempt_path,
            "blocker": self.blocker,
            "updated_at_utc": self.updated_at_utc,
        }


@dataclass(frozen=True, slots=True)
class TaskFinalization:
    status: TaskFinalizationStatus = TaskFinalizationStatus.PENDING
    attempt_count: int = 0
    latest_attempt_path: str | None = None
    blocker: str | None = None
    updated_at_utc: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskFinalization:
        return cls(
            status=TaskFinalizationStatus(str(payload.get("status", "pending"))),
            attempt_count=int(payload.get("attempt_count", 0)),
            latest_attempt_path=(
                str(payload["latest_attempt_path"])
                if payload.get("latest_attempt_path") is not None
                else None
            ),
            blocker=(str(payload["blocker"]) if payload.get("blocker") is not None else None),
            updated_at_utc=(
                str(payload["updated_at_utc"])
                if payload.get("updated_at_utc") is not None
                else None
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "attempt_count": self.attempt_count,
            "latest_attempt_path": self.latest_attempt_path,
            "blocker": self.blocker,
            "updated_at_utc": self.updated_at_utc,
        }


@dataclass(frozen=True, slots=True)
class TaskLedger:
    source_tasklist_sha256: str
    tasks: tuple[TaskLedgerEntry, ...]
    created_at_utc: str
    updated_at_utc: str
    finalization: TaskFinalization = TaskFinalization()
    schema_version: int = 2

    @classmethod
    def create(cls, plan: TaskPlan) -> TaskLedger:
        timestamp = _now()
        return cls(
            source_tasklist_sha256=plan.source_sha256,
            tasks=tuple(TaskLedgerEntry.from_card(card) for card in plan.tasks),
            created_at_utc=timestamp,
            updated_at_utc=timestamp,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskLedger:
        finalization_payload = payload.get("finalization", {})
        if not isinstance(finalization_payload, dict):
            finalization_payload = {}
        return cls(
            schema_version=2,
            source_tasklist_sha256=str(payload["source_tasklist_sha256"]),
            tasks=tuple(
                TaskLedgerEntry.from_dict(item)
                for item in payload.get("tasks", [])
                if isinstance(item, dict)
            ),
            created_at_utc=str(payload["created_at_utc"]),
            updated_at_utc=str(payload["updated_at_utc"]),
            finalization=TaskFinalization.from_dict(finalization_payload),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_tasklist_sha256": self.source_tasklist_sha256,
            "tasks": [task.to_dict() for task in self.tasks],
            "finalization": self.finalization.to_dict(),
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }

    def entry(self, task_id: str) -> TaskLedgerEntry:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise ValueError(f"Unknown task id `{task_id}`.")

    def ready_task_ids(self) -> tuple[str, ...]:
        succeeded = {task.id for task in self.tasks if task.status is TaskExecutionStatus.SUCCEEDED}
        return tuple(
            task.id
            for task in self.tasks
            if task.status
            in {
                TaskExecutionStatus.PENDING,
                TaskExecutionStatus.BLOCKED,
                TaskExecutionStatus.FAILED,
            }
            and all(dependency in succeeded for dependency in task.dependencies)
        )

    def all_succeeded(self) -> bool:
        return bool(self.tasks) and all(
            task.status is TaskExecutionStatus.SUCCEEDED for task in self.tasks
        )

    def reopen_last_task_for_remediation(self, *, blocker: str) -> TaskLedger:
        if not self.tasks:
            raise ValueError("Task ledger has no task to remediate.")
        selected = self.tasks[-1]
        if selected.status is not TaskExecutionStatus.SUCCEEDED:
            raise ValueError("Remediation requires the selected task to have succeeded.")
        timestamp = _now()
        reopened = replace(
            selected,
            status=TaskExecutionStatus.PENDING,
            blocker=blocker,
            updated_at_utc=timestamp,
        )
        return replace(
            self,
            tasks=tuple(reopened if task.id == selected.id else task for task in self.tasks),
            finalization=replace(
                self.finalization,
                status=TaskFinalizationStatus.PENDING,
                blocker="Remediation requires aggregate finalization.",
                updated_at_utc=timestamp,
            ),
            updated_at_utc=timestamp,
        )

    def transition(
        self,
        task_id: str,
        status: TaskExecutionStatus,
        *,
        attempt_number: int | None = None,
        latest_attempt_path: str | None = None,
        blocker: str | None = None,
    ) -> TaskLedger:
        current = self.entry(task_id)
        if status not in _ALLOWED_TRANSITIONS[current.status]:
            raise ValueError(
                f"Illegal task transition: {task_id} {current.status.value} -> {status.value}."
            )
        if status is TaskExecutionStatus.EXECUTING:
            succeeded = {
                task.id for task in self.tasks if task.status is TaskExecutionStatus.SUCCEEDED
            }
            missing = [
                dependency for dependency in current.dependencies if dependency not in succeeded
            ]
            if missing:
                raise ValueError(
                    f"Task `{task_id}` has incomplete dependencies: {', '.join(missing)}."
                )
        timestamp = _now()
        updated = replace(
            current,
            status=status,
            attempt_count=(
                attempt_number or current.attempt_count + 1
                if status is TaskExecutionStatus.EXECUTING
                else current.attempt_count
            ),
            latest_attempt_path=latest_attempt_path or current.latest_attempt_path,
            blocker=(
                blocker
                if status in {TaskExecutionStatus.BLOCKED, TaskExecutionStatus.FAILED}
                else None
            ),
            updated_at_utc=timestamp,
        )
        return replace(
            self,
            tasks=tuple(updated if task.id == task_id else task for task in self.tasks),
            updated_at_utc=timestamp,
        )

    def transition_finalization(
        self,
        status: TaskFinalizationStatus,
        *,
        attempt_number: int | None = None,
        latest_attempt_path: str | None = None,
        blocker: str | None = None,
    ) -> TaskLedger:
        current = self.finalization
        if status not in _ALLOWED_FINALIZATION_TRANSITIONS[current.status]:
            raise ValueError(
                "Illegal task finalization transition: "
                f"{current.status.value} -> {status.value}."
            )
        if status is TaskFinalizationStatus.EXECUTING and not self.all_succeeded():
            raise ValueError("Cannot finalize implementation before every task succeeds.")
        timestamp = _now()
        finalization = replace(
            current,
            status=status,
            attempt_count=(
                attempt_number or current.attempt_count + 1
                if status is TaskFinalizationStatus.EXECUTING
                else current.attempt_count
            ),
            latest_attempt_path=latest_attempt_path or current.latest_attempt_path,
            blocker=blocker if status is TaskFinalizationStatus.FAILED else None,
            updated_at_utc=timestamp,
        )
        return replace(self, finalization=finalization, updated_at_utc=timestamp)


def task_ledger_path(*, workspace_root: Path, work_item: str, run_id: str) -> Path:
    return (
        run_stage_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        )
        / TASK_LEDGER_FILENAME
    )


def task_root(*, workspace_root: Path, work_item: str, run_id: str, task_id: str) -> Path:
    tasks_root = (
        run_stage_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        )
        / TASKS_DIRNAME
    )
    return contained_component_path(
        tasks_root,
        task_id,
        boundary_root=workspace_root,
        label="task id",
    )


def load_task_ledger(*, workspace_root: Path, work_item: str, run_id: str) -> TaskLedger | None:
    path = task_ledger_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Task ledger must contain a JSON object.")
    return TaskLedger.from_dict(payload)


def persist_task_ledger(
    *, workspace_root: Path, work_item: str, run_id: str, ledger: TaskLedger
) -> Path:
    path = task_ledger_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    write_json_payload(path, ledger.to_dict())
    return path


def ensure_task_ledger(
    *, workspace_root: Path, work_item: str, run_id: str, plan: TaskPlan
) -> TaskLedger:
    existing = load_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if existing is not None:
        if existing.source_tasklist_sha256 != plan.source_sha256:
            raise ValueError(
                "Published tasklist changed after task execution state was created; "
                "start a new continuation run from tasklist."
            )
        return existing
    ledger = TaskLedger.create(plan)
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    return ledger


__all__ = [
    "TASK_LEDGER_FILENAME",
    "TaskExecutionStatus",
    "TaskFinalization",
    "TaskFinalizationStatus",
    "TaskLedger",
    "TaskLedgerEntry",
    "ensure_task_ledger",
    "load_task_ledger",
    "persist_task_ledger",
    "task_ledger_path",
    "task_root",
]
