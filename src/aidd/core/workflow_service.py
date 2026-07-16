from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidd.core.mutation_lease import acquire_run_mutation_lease
from aidd.core.run_store import (
    create_run_manifest,
    load_stage_metadata,
    run_manifest_path,
    run_root,
    work_item_runs_root,
)
from aidd.core.stage_graph import (
    StageAdvancementSummary,
    evaluate_stage_eligibility,
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
    continuation: bool = False


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


def _continuation_blockers(
    *,
    request: WorkflowRunRequest,
    selected_run_id: str,
) -> tuple[str, ...]:
    blockers: list[str] = []
    for stage in STAGES[: STAGES.index(request.stage_start)]:
        metadata = load_stage_metadata(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=selected_run_id,
            stage=stage,
        )
        if metadata is None or metadata.status.strip().lower() != StageState.SUCCEEDED.value:
            blockers.append(f"upstream stage '{stage}' is not succeeded")

    eligibility = evaluate_stage_eligibility(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=selected_run_id,
        stage=request.stage_start,
    )
    if eligibility.missing_prerequisites:
        blockers.append("missing prerequisites: " + ", ".join(eligibility.missing_prerequisites))
    if eligibility.blocked_upstream_stages:
        blockers.append(
            "blocked upstream stages: " + ", ".join(eligibility.blocked_upstream_stages)
        )
    if eligibility.failed_upstream_stages:
        blockers.append("failed upstream stages: " + ", ".join(eligibility.failed_upstream_stages))
    if eligibility.missing_input_documents:
        blockers.append(
            "missing required inputs: " + ", ".join(eligibility.missing_input_documents)
        )
    return tuple(dict.fromkeys(blockers))


def validate_workflow_continuation(
    *,
    request: WorkflowRunRequest,
) -> None:
    """Validate an explicit workflow continuation without mutating durable state."""
    _validate_stage_bounds(stage_start=request.stage_start, stage_end=request.stage_end)
    if not request.continuation:
        if request.stage_start != STAGES[0]:
            raise ValueError(
                f"Workflow continuation from '{request.stage_start}' requires an explicit run_id."
            )
        return
    if request.run_id is None:
        raise ValueError("Workflow continuation requires an explicit run_id.")

    manifest_path = run_manifest_path(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
    )
    if not manifest_path.is_file():
        raise ValueError(
            f"Workflow continuation run '{request.run_id}' does not exist for work item "
            f"'{request.work_item}'."
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Workflow continuation manifest for run '{request.run_id}' is not valid JSON."
        ) from exc
    if not isinstance(manifest, dict):
        raise ValueError(
            f"Workflow continuation manifest for run '{request.run_id}' must be an object."
        )
    if (
        manifest.get("run_id") != request.run_id
        or manifest.get("work_item_id") != request.work_item
    ):
        raise ValueError(
            f"Workflow continuation manifest identity does not match run '{request.run_id}' "
            f"and work item '{request.work_item}'."
        )

    raw_bounds = manifest.get("workflow_bounds")
    if not isinstance(raw_bounds, dict):
        raise ValueError(
            f"Workflow continuation run '{request.run_id}' has no canonical workflow bounds."
        )
    original_start = raw_bounds.get("start")
    original_end = raw_bounds.get("end")
    if original_start not in STAGES or original_end not in STAGES:
        raise ValueError(
            f"Workflow continuation run '{request.run_id}' has invalid workflow bounds."
        )
    if STAGES.index(request.stage_start) < STAGES.index(original_start) or STAGES.index(
        request.stage_end
    ) > STAGES.index(original_end):
        raise ValueError(
            f"Requested workflow bounds {request.stage_start}->{request.stage_end} are outside "
            f"run '{request.run_id}' bounds {original_start}->{original_end}."
        )

    original_target = str(manifest.get("stage_target", "")).strip()
    create_run_manifest(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        runtime_id=request.runtime_id,
        stage_target=original_target,
        config_snapshot=dict(request.config_snapshot),
        workflow_stage_start=original_start,
        workflow_stage_end=original_end,
    )
    terminal_metadata = load_stage_metadata(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage=original_end,
    )
    if (
        terminal_metadata is not None
        and terminal_metadata.status.strip().lower() == StageState.SUCCEEDED.value
    ):
        raise ValueError(f"Workflow continuation run '{request.run_id}' is already closed.")

    blockers = _continuation_blockers(request=request, selected_run_id=request.run_id)
    if blockers:
        raise ValueError(
            f"Workflow continuation run '{request.run_id}' is not eligible: "
            + "; ".join(blockers)
            + "."
        )


def _run_workflow_without_lease(
    *,
    request: WorkflowRunRequest,
    stage_executor: WorkflowStageExecutor,
    emit: WorkflowEventSink | None = None,
    stage_selector: WorkflowStageSelector | None = None,
    advancement_summarizer: WorkflowAdvancementSummarizer | None = None,
    continuation: bool = False,
) -> WorkflowRunResult:
    _validate_stage_bounds(stage_start=request.stage_start, stage_end=request.stage_end)
    selected_run_id = request.run_id or allocate_workflow_run_id(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
    )
    if continuation:
        validate_workflow_continuation(request=request)
    else:
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
    validate_workflow_continuation(request=request)
    continuation = request.continuation
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
            continuation=continuation,
        )


__all__ = [
    "WorkflowRunEvent",
    "WorkflowRunRequest",
    "WorkflowRunResult",
    "WorkflowStageExecutionError",
    "WorkflowStageExecutionRequest",
    "allocate_workflow_run_id",
    "run_workflow",
    "validate_workflow_continuation",
]
