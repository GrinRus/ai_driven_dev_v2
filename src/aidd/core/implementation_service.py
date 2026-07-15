from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from aidd.core.implementation_finalization import (
    TaskFinalizationContext,
    complete_task_finalization,
    prepare_task_finalization,
)
from aidd.core.run_store import (
    load_stage_metadata,
    next_attempt_number,
    persist_stage_status,
)
from aidd.core.state_machine import StageState
from aidd.core.task_attempt_evidence import write_task_attempt_references
from aidd.core.task_attempt_lifecycle import (
    TaskExecutionContext,
    complete_task_attempt,
    copy_interview_evidence,
    load_task_execution_plan,
    prepare_task_attempt,
    reconcile_task_execution_state,
)
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    ensure_task_ledger,
    load_task_ledger,
    persist_task_ledger,
)
from aidd.core.task_repository_evidence import (
    capture_repository_snapshot,
    load_repository_snapshot,
    repository_snapshot_payload,
    task_diff_evidence,
    write_repository_snapshot,
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
    def __call__(self, context: TaskFinalizationContext) -> AggregateFinalizationOutcome: ...


def _prepare_task_execution(
    *,
    request: ImplementationExecutionRequest,
    task_id: str,
) -> TaskExecutionContext:
    return prepare_task_attempt(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        task_id=task_id,
        project_root=request.project_root,
        repository_baseline=repository_snapshot_payload,
    )


def _record_global_attempt_references(
    *,
    context: TaskExecutionContext,
    request: ImplementationExecutionRequest,
) -> None:
    end = next_attempt_number(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage="implement",
    )
    write_task_attempt_references(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        task_id=context.task.id,
        task_attempt_number=context.task_attempt_number,
        task_attempt_path=context.task_attempt_path,
        stage_attempt_numbers=tuple(range(context.global_attempt_start, end)),
    )


def _complete_task_execution(
    *,
    context: TaskExecutionContext,
    request: ImplementationExecutionRequest,
    succeeded: bool,
    blocker: str | None = None,
) -> TaskLedger:
    _record_global_attempt_references(context=context, request=request)
    implementation_report = (
        request.workspace_root
        / "workitems"
        / request.work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    report_text: str | None = None
    if implementation_report.exists():
        report_text = implementation_report.read_text(encoding="utf-8")
        shutil.copy2(
            implementation_report,
            context.task_attempt_path / "implementation-report.md",
        )
    copy_interview_evidence(implementation_report.parent, context.task_attempt_path)
    final_snapshot_path = context.task_attempt_path / "repository-final.json"
    if final_snapshot_path.exists():
        final_snapshot = load_repository_snapshot(final_snapshot_path)
    else:
        final_snapshot = capture_repository_snapshot(
            project_root=request.project_root,
            task_id=context.task.id,
        )
        write_repository_snapshot(final_snapshot_path, final_snapshot)
    diff, issues = task_diff_evidence(
        context=context,
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        final_snapshot=final_snapshot,
        report=report_text,
    )
    (context.task_attempt_path / "task-diff.json").write_text(
        json.dumps(diff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if succeeded and issues:
        succeeded = False
        blocker = " ".join(issues)
    status = TaskExecutionStatus.SUCCEEDED if succeeded else TaskExecutionStatus.FAILED
    metadata = load_stage_metadata(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage="implement",
    )
    if not succeeded and metadata is not None and metadata.status == StageState.BLOCKED.value:
        status = TaskExecutionStatus.BLOCKED
    ledger = complete_task_attempt(
        context=context,
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        status=status,
        blocker=blocker,
    )
    if not ledger.all_succeeded():
        persist_stage_status(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage="implement",
            status=(StageState.PENDING.value if succeeded else StageState.BLOCKED.value),
        )
    return ledger


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
            context = _prepare_task_execution(
                request=request,
                task_id=task_id,
            )
        except ValueError as exc:
            raise ImplementationTaskSelectionError(str(exc), ledger=ledger) from exc
        try:
            outcome = self._task_executor(context)
        except Exception as exc:
            failed = _complete_task_execution(
                context=context,
                request=request,
                succeeded=False,
                blocker=str(exc) or exc.__class__.__name__,
            )
            raise ImplementationPortError("Task attempt executor failed.", ledger=failed) from exc
        ledger = _complete_task_execution(
            context=context,
            request=request,
            succeeded=outcome.succeeded,
            blocker=outcome.blocker,
        )
        return self._result(ledger)

    def resolve_next(
        self, request: ImplementationExecutionRequest
    ) -> ImplementationExecutionResult:
        """Resolve the next legal implementation target without executing it."""

        return self._result(self._ledger(request))

    def reopen_for_remediation(
        self,
        request: ImplementationExecutionRequest,
        *,
        remediation_id: str,
    ) -> ImplementationExecutionResult:
        ledger = self._ledger(request).reopen_last_task_for_remediation(
            blocker=f"Remediation `{remediation_id}` requires a new task attempt."
        )
        persist_task_ledger(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            ledger=ledger,
        )
        return self._result(ledger)

    def finalize(self, request: ImplementationExecutionRequest) -> ImplementationExecutionResult:
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
            raise ImplementationPortError("Aggregate finalizer failed.", ledger=failed) from exc
        ledger = complete_task_finalization(
            context=context,
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            succeeded=outcome.succeeded,
            blocker=outcome.blocker,
        )
        return self._result(ledger, published=outcome.published)

    def run_all(self, request: ImplementationExecutionRequest) -> ImplementationExecutionResult:
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
