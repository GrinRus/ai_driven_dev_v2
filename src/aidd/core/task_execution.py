from __future__ import annotations

import json
import shutil
from pathlib import Path

from aidd.core.implementation_finalization import (
    TaskFinalizationContext,
    complete_task_finalization,
    prepare_task_finalization,
    render_aggregate_implementation_report,
)
from aidd.core.run_store import (
    load_stage_metadata,
    next_attempt_number,
    persist_stage_status,
    run_attempt_root,
)
from aidd.core.state_machine import StageState
from aidd.core.task_attempt_lifecycle import (
    TaskExecutionContext,
    TaskResumeBlockedError,
    complete_task_attempt,
    copy_interview_evidence,
    load_task_execution_plan,
    prepare_task_attempt,
    published_tasklist_path,
    reconcile_task_execution_state,
    write_task_selection_context,
)
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskLedger,
)
from aidd.core.task_repository_evidence import (
    capture_repository_snapshot,
    repository_snapshot_payload,
    task_diff_evidence,
    write_repository_snapshot,
)


def prepare_task_execution(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_id: str,
    project_root: Path,
) -> TaskExecutionContext:
    return prepare_task_attempt(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        task_id=task_id,
        project_root=project_root,
        repository_baseline=repository_snapshot_payload,
    )


def _snapshot_global_attempts(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> None:
    end = next_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
    )
    for attempt_number in range(context.global_attempt_start, end):
        source = run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
            attempt_number=attempt_number,
        )
        if source.exists():
            destination = context.task_attempt_path / f"stage-attempt-{attempt_number:04d}"
            shutil.copytree(source, destination)
            input_bundle = destination / "input-bundle.md"
            if (
                input_bundle.exists()
                and not (context.task_attempt_path / "input-bundle.md").exists()
            ):
                shutil.copy2(input_bundle, context.task_attempt_path / "input-bundle.md")
            runtime_log = destination / "runtime.log"
            if runtime_log.exists():
                shutil.copy2(runtime_log, context.task_attempt_path / "runtime.log")
            repair_context = destination / "repair-context.md"
            if repair_context.exists():
                shutil.copy2(repair_context, context.task_attempt_path / "repair-context.md")


def complete_task_execution(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    project_root: Path,
    succeeded: bool,
    blocker: str | None = None,
) -> TaskLedger:
    _snapshot_global_attempts(
        context=context,
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    implementation_report = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    implementation_report_text: str | None = None
    if implementation_report.exists():
        implementation_report_text = implementation_report.read_text(encoding="utf-8")
        shutil.copy2(
            implementation_report,
            context.task_attempt_path / "implementation-report.md",
        )
    implement_stage_root = implementation_report.parent
    copy_interview_evidence(implement_stage_root, context.task_attempt_path)
    final_status = capture_repository_snapshot(
        project_root=project_root,
        task_id=context.task.id,
    )
    write_repository_snapshot(
        context.task_attempt_path / "repository-final.json",
        final_status,
    )
    task_diff, task_diff_issues = task_diff_evidence(
        context=context,
        workspace_root=workspace_root,
        work_item=work_item,
        project_root=project_root,
        report=implementation_report_text,
    )
    (context.task_attempt_path / "task-diff.json").write_text(
        json.dumps(task_diff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if succeeded and task_diff_issues:
        succeeded = False
        blocker = " ".join(task_diff_issues)
    status = TaskExecutionStatus.SUCCEEDED if succeeded else TaskExecutionStatus.FAILED
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
    )
    if not succeeded and metadata is not None and metadata.status == StageState.BLOCKED.value:
        status = TaskExecutionStatus.BLOCKED
    ledger = complete_task_attempt(
        context=context,
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        status=status,
        blocker=blocker,
    )
    if not ledger.all_succeeded():
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
            status=(StageState.PENDING.value if succeeded else StageState.BLOCKED.value),
        )
    return ledger


__all__ = [
    "TaskExecutionContext",
    "TaskFinalizationContext",
    "TaskResumeBlockedError",
    "complete_task_finalization",
    "complete_task_execution",
    "load_task_execution_plan",
    "prepare_task_execution",
    "prepare_task_finalization",
    "published_tasklist_path",
    "reconcile_task_execution_state",
    "render_aggregate_implementation_report",
    "write_task_selection_context",
]
