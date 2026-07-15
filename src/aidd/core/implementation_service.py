from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from aidd.core.task_execution import (
    TaskExecutionContext,
    TaskFinalizationContext,
    complete_task_execution,
    complete_task_finalization,
    load_task_execution_plan,
    prepare_task_execution,
    prepare_task_finalization,
    reconcile_task_execution_state,
)
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    ensure_task_ledger,
    load_task_ledger,
)


class ImplementationExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    STOPPED = "stopped"


class ImplementationNextTarget(StrEnum):
    TASK = "task"
    FINALIZATION = "finalization"
    COMPLETE = "complete"


class ImplementationExecutionError(ValueError):
    code = "implementation-execution-error"

    def __init__(self, message: str, *, ledger: TaskLedger | None = None) -> None:
        self.ledger = ledger
        super().__init__(message)


class ImplementationSourceMismatchError(ImplementationExecutionError):
    code = "implementation-source-mismatch"


class ImplementationTaskSelectionError(ImplementationExecutionError):
    code = "implementation-task-selection"


class ImplementationNoReadyTaskError(ImplementationExecutionError):
    code = "implementation-no-ready-task"


class ImplementationFinalizationError(ImplementationExecutionError):
    code = "implementation-finalization"


class ImplementationPortError(ImplementationExecutionError):
    code = "implementation-port-error"


@dataclass(frozen=True, slots=True)
class ImplementationExecutionRequest:
    workspace_root: Path
    work_item: str
    run_id: str
    project_root: Path


@dataclass(frozen=True, slots=True)
class TaskAttemptOutcome:
    succeeded: bool
    blocker: str | None = None


@dataclass(frozen=True, slots=True)
class AggregateFinalizationOutcome:
    succeeded: bool
    published: bool = False
    blocker: str | None = None


@dataclass(frozen=True, slots=True)
class ImplementationExecutionResult:
    ledger: TaskLedger
    status: ImplementationExecutionStatus
    next_target: ImplementationNextTarget
    next_task_id: str | None = None
    published: bool = False


class TaskAttemptExecutor(Protocol):
    def __call__(self, context: TaskExecutionContext) -> TaskAttemptOutcome: ...


class AggregateFinalizer(Protocol):
    def __call__(
        self, context: TaskFinalizationContext
    ) -> AggregateFinalizationOutcome: ...


class ImplementationExecutionService:
    def __init__(
        self,
        *,
        task_executor: TaskAttemptExecutor,
        aggregate_finalizer: AggregateFinalizer,
    ) -> None:
        self._task_executor = task_executor
        self._aggregate_finalizer = aggregate_finalizer

    def _ledger(self, request: ImplementationExecutionRequest) -> TaskLedger:
        plan = load_task_execution_plan(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
        )
        try:
            ledger = ensure_task_ledger(
                workspace_root=request.workspace_root,
                work_item=request.work_item,
                run_id=request.run_id,
                plan=plan,
            )
        except ValueError as exc:
            if "source_tasklist_sha256" in str(exc) or "tasklist changed" in str(exc).lower():
                raise ImplementationSourceMismatchError(str(exc)) from exc
            raise
        return reconcile_task_execution_state(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            ledger=ledger,
        )

    @staticmethod
    def _result(ledger: TaskLedger, *, published: bool = False) -> ImplementationExecutionResult:
        if ledger.finalization.status is TaskFinalizationStatus.SUCCEEDED:
            return ImplementationExecutionResult(
                ledger=ledger,
                status=ImplementationExecutionStatus.SUCCEEDED,
                next_target=ImplementationNextTarget.COMPLETE,
                published=published,
            )
        ready = ledger.ready_task_ids()
        if ready:
            return ImplementationExecutionResult(
                ledger=ledger,
                status=ImplementationExecutionStatus.STOPPED,
                next_target=ImplementationNextTarget.TASK,
                next_task_id=ready[0],
            )
        if ledger.all_succeeded():
            return ImplementationExecutionResult(
                ledger=ledger,
                status=ImplementationExecutionStatus.STOPPED,
                next_target=ImplementationNextTarget.FINALIZATION,
            )
        return ImplementationExecutionResult(
            ledger=ledger,
            status=ImplementationExecutionStatus.STOPPED,
            next_target=ImplementationNextTarget.TASK,
        )

    def run_task(
        self, request: ImplementationExecutionRequest, *, task_id: str
    ) -> ImplementationExecutionResult:
        ledger = self._ledger(request)
        try:
            context = prepare_task_execution(
                workspace_root=request.workspace_root,
                work_item=request.work_item,
                run_id=request.run_id,
                task_id=task_id,
                project_root=request.project_root,
            )
        except ValueError as exc:
            raise ImplementationTaskSelectionError(str(exc), ledger=ledger) from exc
        try:
            outcome = self._task_executor(context)
        except Exception as exc:
            failed = complete_task_execution(
                context=context,
                workspace_root=request.workspace_root,
                work_item=request.work_item,
                run_id=request.run_id,
                project_root=request.project_root,
                succeeded=False,
                blocker=str(exc) or exc.__class__.__name__,
            )
            raise ImplementationPortError(
                "Task attempt executor failed.", ledger=failed
            ) from exc
        ledger = complete_task_execution(
            context=context,
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            project_root=request.project_root,
            succeeded=outcome.succeeded,
            blocker=outcome.blocker,
        )
        return self._result(ledger)

    def finalize(
        self, request: ImplementationExecutionRequest
    ) -> ImplementationExecutionResult:
        ledger = load_task_ledger(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
        )
        if ledger is None:
            raise ImplementationFinalizationError("Task ledger does not exist.")
        try:
            context = prepare_task_finalization(
                workspace_root=request.workspace_root,
                work_item=request.work_item,
                run_id=request.run_id,
                ledger=ledger,
            )
        except ValueError as exc:
            raise ImplementationFinalizationError(str(exc), ledger=ledger) from exc
        try:
            outcome = self._aggregate_finalizer(context)
        except Exception as exc:
            failed = complete_task_finalization(
                context=context,
                workspace_root=request.workspace_root,
                work_item=request.work_item,
                run_id=request.run_id,
                succeeded=False,
                blocker=str(exc) or exc.__class__.__name__,
            )
            raise ImplementationPortError(
                "Aggregate finalizer failed.", ledger=failed
            ) from exc
        ledger = complete_task_finalization(
            context=context,
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            succeeded=outcome.succeeded,
            blocker=outcome.blocker,
        )
        return self._result(ledger, published=outcome.published)

    def run_all(
        self, request: ImplementationExecutionRequest
    ) -> ImplementationExecutionResult:
        ledger = self._ledger(request)
        while not ledger.all_succeeded():
            if any(
                entry.status in {TaskExecutionStatus.BLOCKED, TaskExecutionStatus.FAILED}
                for entry in ledger.tasks
            ):
                return self._result(ledger)
            ready = ledger.ready_task_ids()
            if not ready:
                raise ImplementationNoReadyTaskError(
                    "Task execution has no dependency-ready task.", ledger=ledger
                )
            result = self.run_task(request, task_id=ready[0])
            ledger = result.ledger
            if ledger.entry(ready[0]).status is not TaskExecutionStatus.SUCCEEDED:
                return result
        if ledger.finalization.status is TaskFinalizationStatus.SUCCEEDED:
            return self._result(ledger)
        return self.finalize(request)


__all__ = [
    "AggregateFinalizationOutcome",
    "AggregateFinalizer",
    "ImplementationExecutionError",
    "ImplementationExecutionRequest",
    "ImplementationExecutionResult",
    "ImplementationExecutionService",
    "ImplementationExecutionStatus",
    "ImplementationFinalizationError",
    "ImplementationNextTarget",
    "ImplementationNoReadyTaskError",
    "ImplementationPortError",
    "ImplementationSourceMismatchError",
    "ImplementationTaskSelectionError",
    "TaskAttemptExecutor",
    "TaskAttemptOutcome",
]
