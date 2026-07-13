from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from aidd.cli.stage_run import StageRunOptions, run_stage_command
from aidd.cli.support import (
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    console,
)
from aidd.config import load_config
from aidd.core.mutation_lease import (
    RunMutationLease,
    acquire_run_mutation_lease,
    use_transferred_run_mutation_lease,
)
from aidd.core.run_store import (
    create_run_manifest,
    persist_stage_status,
    run_manifest_path,
    run_root,
)
from aidd.core.stage_outputs import publish_stage_outputs_after_validation_pass
from aidd.core.state_machine import StageState
from aidd.core.task_execution import (
    complete_task_execution,
    complete_task_finalization,
    load_task_execution_plan,
    prepare_task_execution,
    prepare_task_finalization,
    reconcile_task_execution_state,
    render_aggregate_implementation_report,
    task_validation_findings,
)
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    ensure_task_ledger,
    load_task_ledger,
)
from aidd.core.task_plan import TaskPlan
from aidd.core.task_read_model import resolve_task_read_model
from aidd.validators.reports import write_validator_report
from aidd.validators.semantic import validate_semantic_outputs

StageRunner = Callable[[StageRunOptions], None]


def _workspace_root(root: Path | None, config: Path) -> Path:
    cfg = load_config(config)
    return (root if root is not None else cfg.workspace_root).resolve(strict=False)


def _validate_run_manifest_identity(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    runtime: str,
    config: Path,
) -> None:
    manifest_path = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not manifest_path.exists():
        raise ValueError(f"Run manifest does not exist for run `{run_id}`.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Run manifest must contain a JSON object.")
    manifest_runtime = str(manifest.get("runtime_id", ""))
    if manifest_runtime != runtime:
        raise ValueError(
            f"Runtime `{runtime}` does not match run manifest runtime `{manifest_runtime}`."
        )
    cfg = load_config(config)
    runtime_cfg = cfg.runtime_config(runtime)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id=runtime,
        stage_target="implement",
        config_snapshot={
            "workspace_root": workspace_root.as_posix(),
            "runtime_command": _runtime_command_for_runtime(runtime=runtime, cfg=cfg),
            "runtime_execution_mode": _runtime_execution_mode_for_runtime(
                runtime=runtime, cfg=cfg
            ).value,
            "runtime_permission_policy": runtime_cfg.permission_policy.value,
            "runtime_interaction_mode": runtime_cfg.interaction_mode.value,
            "runtime_auto_approval_preset": runtime_cfg.auto_approval_preset.value,
        },
    )


def _validate_ledger_source(*, plan_hash: str, ledger: TaskLedger | None) -> None:
    if ledger is not None and ledger.source_tasklist_sha256 != plan_hash:
        raise ValueError(
            "Published tasklist changed after task execution state was created; "
            "start a new continuation run from tasklist."
        )


def _display_ledger(
    *, ledger: TaskLedger, plan: TaskPlan | None = None, task_id: str | None = None
) -> None:
    table = Table(title="Implementation tasks")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Dependencies")
    table.add_column("Attempts")
    for entry in ledger.tasks:
        if task_id is not None and entry.id != task_id:
            continue
        table.add_row(
            entry.id,
            entry.status.value,
            ", ".join(entry.dependencies) or "none",
            str(entry.attempt_count),
        )
        if task_id is not None:
            console.print(f"Title: {entry.title}")
            card = plan.by_id().get(entry.id) if plan is not None else None
            if card is not None:
                console.print(f"Outcome: {card.outcome}")
                console.print(f"Dominant deliverable: {card.dominant_deliverable}")
                console.print(f"In scope: {card.in_scope}")
                console.print(f"Verification: {card.verification}")
                for criterion in card.acceptance_criteria:
                    console.print(f"Acceptance {criterion.id}: {criterion.text}")
            else:
                console.print("Acceptance: " + (", ".join(entry.acceptance_ids) or "none"))
            console.print(f"Evidence: {entry.latest_attempt_path or 'none'}")
            console.print(f"Blocker: {entry.blocker or 'none'}")
    console.print(table)
    console.print(
        "Finalization: "
        f"{ledger.finalization.status.value}; attempts={ledger.finalization.attempt_count}; "
        f"blocker={ledger.finalization.blocker or 'none'}"
    )


def task_list(
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id; defaults to tasklist-derived state."),
    ] = None,
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    plan = load_task_execution_plan(workspace_root=root, work_item=work_item)
    ledger = (
        load_task_ledger(workspace_root=root, work_item=work_item, run_id=run_id)
        if run_id is not None
        else None
    )
    _validate_ledger_source(plan_hash=plan.source_sha256, ledger=ledger)
    _display_ledger(ledger=ledger or TaskLedger.create(plan), plan=plan)


def task_show(
    task_id: Annotated[str, typer.Argument(help="Task id, for example TL-1")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id."),
    ] = None,
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    plan = load_task_execution_plan(workspace_root=root, work_item=work_item)
    ledger = (
        load_task_ledger(workspace_root=root, work_item=work_item, run_id=run_id)
        if run_id is not None
        else None
    ) or TaskLedger.create(plan)
    _validate_ledger_source(plan_hash=plan.source_sha256, ledger=ledger)
    ledger.entry(task_id)
    _display_ledger(ledger=ledger, plan=plan, task_id=task_id)
    model = resolve_task_read_model(
        workspace_root=root,
        work_item=work_item,
        run_id=run_id,
    )
    tasks = model.get("tasks", [])
    if isinstance(tasks, list):
        selected = next(
            (item for item in tasks if isinstance(item, dict) and item.get("id") == task_id),
            None,
        )
        if selected is not None:
            attempts = selected.get("attempts", [])
            if isinstance(attempts, list):
                for attempt in attempts:
                    if isinstance(attempt, dict):
                        console.print(
                            "Attempt "
                            f"{attempt.get('number')}: {attempt.get('status')} "
                            f"{attempt.get('path')}"
                        )


def _copy_finalization_artifacts(stage_root: Path, attempt_path: Path) -> None:
    for name in ("implementation-report.md", "validator-report.md", "stage-result.md"):
        source = stage_root / name
        if source.exists():
            shutil.copy2(source, attempt_path / name)


def _finalize_implementation_without_lease(
    *, workspace_root: Path, work_item: str, run_id: str, ledger: TaskLedger
) -> TaskLedger:
    context = prepare_task_finalization(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    stage_root = workspace_root / "workitems" / work_item / "stages" / "implement"
    diagnostics_path = context.attempt_path / "publication-diagnostics.json"
    try:
        plan = load_task_execution_plan(workspace_root=workspace_root, work_item=work_item)
        report = render_aggregate_implementation_report(
            plan=plan,
            ledger=context.ledger,
            workspace_root=workspace_root,
        )
        report_path = stage_root / "implementation-report.md"
        report_path.write_text(report, encoding="utf-8")
        findings = validate_semantic_outputs(
            stage="implement",
            work_item=work_item,
            workspace_root=workspace_root,
        )
        validator_report_path = stage_root / "validator-report.md"
        write_validator_report(path=validator_report_path, findings=findings)
        _copy_finalization_artifacts(stage_root, context.attempt_path)
        if findings:
            raise ValueError("Aggregate implementation report failed validation.")
        publish_stage_outputs_after_validation_pass(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        )
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
            status=StageState.SUCCEEDED.value,
        )
        diagnostics_path.write_text(
            json.dumps({"status": "succeeded"}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return complete_task_finalization(
            context=context,
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            succeeded=True,
        )
    except Exception as exc:
        blocker = str(exc) or exc.__class__.__name__
        diagnostics_path.write_text(
            json.dumps(
                {"status": "failed", "error": blocker}, indent=2, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
        _copy_finalization_artifacts(stage_root, context.attempt_path)
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
            status=StageState.FAILED.value,
        )
        complete_task_finalization(
            context=context,
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            succeeded=False,
            blocker=blocker,
        )
        raise


def execute_task_by_id(
    *,
    task_id: str,
    work_item: str,
    run_id: str,
    runtime: str,
    root: Path | None,
    config: Path,
    log_follow: bool,
    stage_runner: StageRunner = run_stage_command,
    mutation_lease: RunMutationLease | None = None,
) -> TaskLedger:
    workspace_root = _workspace_root(root, config)
    project_root = Path.cwd().resolve(strict=True)
    _validate_run_manifest_identity(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime=runtime,
        config=config,
    )
    selected_run_root = run_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    lease_context = (
        use_transferred_run_mutation_lease(mutation_lease)
        if mutation_lease is not None
        else acquire_run_mutation_lease(
            selected_run_root,
            operation=f"task:{task_id}",
        )
    )
    with lease_context:
        context = prepare_task_execution(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            task_id=task_id,
            project_root=project_root,
        )
        succeeded = False
        blocker: str | None = None
        unexpected_error: Exception | None = None
        try:
            stage_runner(
                StageRunOptions(
                    stage="implement",
                    work_item=work_item,
                    runtime=runtime,
                    run_id=run_id,
                    root=workspace_root,
                    config=config,
                    log_follow=log_follow,
                    defer_success_publication=True,
                    validation_finding_provider=lambda execution_state, discovery: (
                        task_validation_findings(
                            context=context,
                            workspace_root=workspace_root,
                            work_item=work_item,
                            project_root=project_root,
                            execution_state=execution_state,
                            discovery=discovery,
                        )
                    ),
                )
            )
            succeeded = True
        except typer.Exit as exc:
            blocker = f"implement stage stopped with exit code {exc.exit_code}."
        except Exception as exc:  # preserve durable task failure before surfacing the error
            blocker = str(exc) or exc.__class__.__name__
            unexpected_error = exc
        ledger = complete_task_execution(
            context=context,
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            project_root=project_root,
            succeeded=succeeded,
            blocker=blocker,
        )
        task_succeeded = (
            succeeded and ledger.entry(task_id).status is TaskExecutionStatus.SUCCEEDED
        )
        if task_succeeded and ledger.all_succeeded():
            ledger = _finalize_implementation_without_lease(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                ledger=ledger,
            )
        if not task_succeeded:
            if unexpected_error is not None:
                raise unexpected_error
            raise typer.Exit(code=1)
        return ledger


def finalize_implementation(
    *,
    work_item: str,
    run_id: str,
    runtime: str,
    root: Path | None,
    config: Path,
    mutation_lease: RunMutationLease | None = None,
) -> TaskLedger:
    workspace_root = _workspace_root(root, config)
    _validate_run_manifest_identity(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime=runtime,
        config=config,
    )
    ledger = load_task_ledger(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id
    )
    if ledger is None:
        raise ValueError(f"Task ledger does not exist for run `{run_id}`.")
    selected_run_root = run_root(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id
    )
    lease_context = (
        use_transferred_run_mutation_lease(mutation_lease)
        if mutation_lease is not None
        else acquire_run_mutation_lease(selected_run_root, operation="task:finalize")
    )
    with lease_context:
        return _finalize_implementation_without_lease(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            ledger=ledger,
        )


def execute_all_tasks(
    *,
    work_item: str,
    run_id: str,
    runtime: str,
    root: Path,
    config: Path,
    log_follow: bool,
    stage_runner: StageRunner = run_stage_command,
) -> TaskLedger:
    plan = load_task_execution_plan(workspace_root=root, work_item=work_item)
    ledger = ensure_task_ledger(
        workspace_root=root,
        work_item=work_item,
        run_id=run_id,
        plan=plan,
    )
    ledger = reconcile_task_execution_state(
        workspace_root=root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    while not ledger.all_succeeded():
        blocked_or_failed = next(
            (
                entry
                for entry in ledger.tasks
                if entry.status in {TaskExecutionStatus.BLOCKED, TaskExecutionStatus.FAILED}
            ),
            None,
        )
        if blocked_or_failed is not None:
            raise typer.Exit(code=1)
        ready = ledger.ready_task_ids()
        if not ready:
            raise ValueError("Task execution has no dependency-ready task.")
        ledger = execute_task_by_id(
            task_id=ready[0],
            work_item=work_item,
            run_id=run_id,
            runtime=runtime,
            root=root,
            config=config,
            log_follow=log_follow,
            stage_runner=stage_runner,
        )
    if ledger.finalization.status is not TaskFinalizationStatus.SUCCEEDED:
        selected_run_root = run_root(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
        )
        with acquire_run_mutation_lease(selected_run_root, operation="task:finalize"):
            ledger = _finalize_implementation_without_lease(
                workspace_root=root,
                work_item=work_item,
                run_id=run_id,
                ledger=ledger,
            )
    return ledger


def task_run(
    task_id: Annotated[str, typer.Argument(help="Task id, for example TL-1")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    run_id: Annotated[str, typer.Option("--run-id", help="Existing run id")],
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")],
    root: Annotated[
        Path | None,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to an AIDD TOML config file."),
    ] = Path("aidd.example.toml"),
    log_follow: Annotated[
        bool,
        typer.Option("--log-follow/--no-log-follow"),
    ] = False,
) -> None:
    ledger = execute_task_by_id(
        task_id=task_id,
        work_item=work_item,
        run_id=run_id,
        runtime=runtime,
        root=root,
        config=config,
        log_follow=log_follow,
    )
    plan = load_task_execution_plan(
        workspace_root=_workspace_root(root, config), work_item=work_item
    )
    _display_ledger(ledger=ledger, plan=plan, task_id=task_id)


def task_finalize(
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    run_id: Annotated[str, typer.Option("--run-id", help="Existing run id")],
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")],
    root: Annotated[
        Path | None, typer.Option("--root", help="Root AIDD storage directory.")
    ] = None,
    config: Annotated[
        Path, typer.Option("--config", help="Path to an AIDD TOML config file.")
    ] = Path("aidd.example.toml"),
) -> None:
    ledger = finalize_implementation(
        work_item=work_item,
        run_id=run_id,
        runtime=runtime,
        root=root,
        config=config,
    )
    _display_ledger(ledger=ledger)


__all__ = [
    "execute_all_tasks",
    "execute_task_by_id",
    "finalize_implementation",
    "task_list",
    "task_finalize",
    "task_run",
    "task_show",
]
