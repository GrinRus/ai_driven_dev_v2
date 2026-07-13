from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidd.core.mutation_lease import acquire_run_mutation_lease
from aidd.core.run_store import create_run_manifest, run_root, work_item_runs_root
from aidd.core.stage_graph import (
    StageAdvancementSummary,
    select_next_runnable_stage,
    summarize_workflow_advancement,
)
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState


@dataclass(frozen=True, slots=True)
class WorkflowRunRequest:
    work_item: str
    runtime_id: str
    workspace_root: Path
    config_path: Path
    config_snapshot: Mapping[str, Any]
    lineage: Mapping[str, Any] | None = None
    stage_start: str = STAGES[0]
    stage_end: str = STAGES[-1]
    log_follow: bool = False
    run_id: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowStageExecutionRequest:
    stage: str
    work_item: str
    runtime_id: str
    run_id: str
    workspace_root: Path
    config_path: Path
    log_follow: bool


@dataclass(frozen=True, slots=True)
class WorkflowRunEvent:
    kind: str
    run_id: str
    stage: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowRunResult:
    run_id: str
    executed_stage_count: int
    completed: bool
    incomplete: tuple[StageAdvancementSummary, ...]
    stopped_stage: str | None = None
    exit_code: int = 0


class WorkflowStageExecutionError(RuntimeError):
    def __init__(self, *, stage: str, exit_code: int) -> None:
        super().__init__(f"Workflow stage '{stage}' stopped with exit code {exit_code}.")
        self.stage = stage
        self.exit_code = exit_code


WorkflowStageExecutor = Callable[[WorkflowStageExecutionRequest], None]
WorkflowEventSink = Callable[[WorkflowRunEvent], None]
WorkflowStageSelector = Callable[
    [Path, str, str, str, str],
    str | None,
]
WorkflowAdvancementSummarizer = Callable[
    [Path, str, str, str, str],
    tuple[StageAdvancementSummary, ...],
]


def allocate_workflow_run_id(*, workspace_root: Path, work_item: str) -> str:
    base_run_id = f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    candidate = base_run_id
    suffix = 2
    while (runs_root / candidate).exists():
        candidate = f"{base_run_id}-{suffix:02d}"
        suffix += 1
    return candidate


def _validate_stage_bounds(*, stage_start: str, stage_end: str) -> None:
    if stage_start not in STAGES:
        supported = ", ".join(STAGES)
        raise ValueError(f"Unknown stage '{stage_start}'. Expected one of: {supported}.")
    if stage_end not in STAGES:
        supported = ", ".join(STAGES)
        raise ValueError(f"Unknown stage '{stage_end}'. Expected one of: {supported}.")
    if STAGES.index(stage_start) > STAGES.index(stage_end):
        raise ValueError(
            f"Stage start '{stage_start}' must not come after stage end '{stage_end}'."
        )


def _run_workflow_without_lease(
    *,
    request: WorkflowRunRequest,
    stage_executor: WorkflowStageExecutor,
    emit: WorkflowEventSink | None = None,
    stage_selector: WorkflowStageSelector | None = None,
    advancement_summarizer: WorkflowAdvancementSummarizer | None = None,
) -> WorkflowRunResult:
    _validate_stage_bounds(stage_start=request.stage_start, stage_end=request.stage_end)
    selected_run_id = request.run_id or allocate_workflow_run_id(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
    )
    create_run_manifest(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=selected_run_id,
        runtime_id=request.runtime_id,
        stage_target=request.stage_end,
        config_snapshot=dict(request.config_snapshot),
        workflow_stage_start=request.stage_start,
        workflow_stage_end=request.stage_end,
        lineage=dict(request.lineage) if request.lineage is not None else None,
    )
    if emit is not None:
        emit(WorkflowRunEvent(kind="started", run_id=selected_run_id))

    executed_stage_count = 0
    while True:
        next_stage = (
            select_next_runnable_stage(
                workspace_root=request.workspace_root,
                work_item=request.work_item,
                run_id=selected_run_id,
                stage_start=request.stage_start,
                stage_end=request.stage_end,
            )
            if stage_selector is None
            else stage_selector(
                request.workspace_root,
                request.work_item,
                selected_run_id,
                request.stage_start,
                request.stage_end,
            )
        )
        if next_stage is None:
            break

        if emit is not None:
            emit(WorkflowRunEvent(kind="next-stage", run_id=selected_run_id, stage=next_stage))
        try:
            stage_executor(
                WorkflowStageExecutionRequest(
                    stage=next_stage,
                    work_item=request.work_item,
                    runtime_id=request.runtime_id,
                    run_id=selected_run_id,
                    workspace_root=request.workspace_root,
                    config_path=request.config_path,
                    log_follow=request.log_follow,
                )
            )
        except WorkflowStageExecutionError as exc:
            advancement = (
                summarize_workflow_advancement(
                    workspace_root=request.workspace_root,
                    work_item=request.work_item,
                    run_id=selected_run_id,
                    stage_start=request.stage_start,
                    stage_end=request.stage_end,
                )
                if advancement_summarizer is None
                else advancement_summarizer(
                    request.workspace_root,
                    request.work_item,
                    selected_run_id,
                    request.stage_start,
                    request.stage_end,
                )
            )
            if emit is not None:
                emit(
                    WorkflowRunEvent(
                        kind="stopped",
                        run_id=selected_run_id,
                        stage=exc.stage,
                    )
                )
            return WorkflowRunResult(
                run_id=selected_run_id,
                executed_stage_count=executed_stage_count,
                completed=False,
                incomplete=tuple(
                    summary
                    for summary in advancement
                    if summary.current_status != StageState.SUCCEEDED.value
                ),
                stopped_stage=exc.stage,
                exit_code=exc.exit_code,
            )
        executed_stage_count += 1
        if emit is not None:
            emit(
                WorkflowRunEvent(
                    kind="stage-succeeded",
                    run_id=selected_run_id,
                    stage=next_stage,
                )
            )

    advancement = (
        summarize_workflow_advancement(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=selected_run_id,
            stage_start=request.stage_start,
            stage_end=request.stage_end,
        )
        if advancement_summarizer is None
        else advancement_summarizer(
            request.workspace_root,
            request.work_item,
            selected_run_id,
            request.stage_start,
            request.stage_end,
        )
    )
    incomplete = tuple(
        summary for summary in advancement if summary.current_status != StageState.SUCCEEDED.value
    )
    if incomplete:
        if emit is not None:
            emit(WorkflowRunEvent(kind="blocked", run_id=selected_run_id))
        return WorkflowRunResult(
            run_id=selected_run_id,
            executed_stage_count=executed_stage_count,
            completed=False,
            incomplete=incomplete,
            exit_code=1,
        )

    if emit is not None:
        emit(WorkflowRunEvent(kind="completed", run_id=selected_run_id))
    return WorkflowRunResult(
        run_id=selected_run_id,
        executed_stage_count=executed_stage_count,
        completed=True,
        incomplete=(),
    )


def run_workflow(
    *,
    request: WorkflowRunRequest,
    stage_executor: WorkflowStageExecutor,
    emit: WorkflowEventSink | None = None,
    stage_selector: WorkflowStageSelector | None = None,
    advancement_summarizer: WorkflowAdvancementSummarizer | None = None,
) -> WorkflowRunResult:
    selected_run_id = request.run_id or allocate_workflow_run_id(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
    )
    selected_request = replace(request, run_id=selected_run_id)
    with acquire_run_mutation_lease(
        run_root(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=selected_run_id,
        ),
        operation="workflow",
    ):
        return _run_workflow_without_lease(
            request=selected_request,
            stage_executor=stage_executor,
            emit=emit,
            stage_selector=stage_selector,
            advancement_summarizer=advancement_summarizer,
        )


__all__ = [
    "WorkflowRunEvent",
    "WorkflowRunRequest",
    "WorkflowRunResult",
    "WorkflowStageExecutionError",
    "WorkflowStageExecutionRequest",
    "allocate_workflow_run_id",
    "run_workflow",
]
