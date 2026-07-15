from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, NoReturn, cast

import typer
from rich.table import Table

from aidd.application.implementation import aggregate_finalization_port
from aidd.cli.stage_run import StageRunOptions, run_stage_attempt_command
from aidd.cli.support import (
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    console,
)
from aidd.config import load_config
from aidd.core.implementation_service import (
    AggregateFinalizer,
    ImplementationExecutionRequest,
    ImplementationExecutionService,
    ImplementationExecutionStatus,
    ImplementationNextTarget,
    ImplementationPortError,
    ImplementationTaskSelectionError,
    TaskAttemptExecutor,
    TaskAttemptOutcome,
)
from aidd.core.mutation_lease import (
    RunMutationLease,
    acquire_run_mutation_lease,
    use_transferred_run_mutation_lease,
)
from aidd.core.run_store import (
    create_run_manifest,
    run_manifest_path,
    run_root,
)
from aidd.core.task_execution import (
    TaskExecutionContext,
    load_task_execution_plan,
    task_validation_findings,
)
from aidd.core.task_ledger import (
    TaskLedger,
    load_task_ledger,
)
from aidd.core.task_plan import TaskPlan
from aidd.core.task_read_model import resolve_task_read_model

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


def _task_attempt_port(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    runtime: str,
    config: Path,
    log_follow: bool,
    project_root: Path,
    stage_runner: StageRunner,
    intervention_request_path: Path | None = None,
) -> Callable[[TaskExecutionContext], TaskAttemptOutcome]:
    def _execute(context: TaskExecutionContext) -> TaskAttemptOutcome:
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
                    intervention_request_path=intervention_request_path,
                )
            )
        except typer.Exit as exc:
            return TaskAttemptOutcome(
                succeeded=False,
                blocker=f"implement stage stopped with exit code {exc.exit_code}.",
            )
        return TaskAttemptOutcome(succeeded=True)

    return _execute


def _implementation_service(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    runtime: str,
    config: Path,
    log_follow: bool,
    project_root: Path,
    stage_runner: StageRunner,
    intervention_request_path: Path | None = None,
) -> ImplementationExecutionService:
    return ImplementationExecutionService(
        task_executor=cast(
            TaskAttemptExecutor,
            _task_attempt_port(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                runtime=runtime,
                config=config,
                log_follow=log_follow,
                project_root=project_root,
                stage_runner=stage_runner,
                intervention_request_path=intervention_request_path,
            ),
        ),
        aggregate_finalizer=cast(
            AggregateFinalizer,
            aggregate_finalization_port(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
            ),
        ),
    )


def _execution_request(
    *, workspace_root: Path, work_item: str, run_id: str, project_root: Path
) -> ImplementationExecutionRequest:
    return ImplementationExecutionRequest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        project_root=project_root,
    )


def _raise_port_cause(exc: ImplementationPortError) -> NoReturn:
    if isinstance(exc.__cause__, Exception):
        raise exc.__cause__.with_traceback(exc.__cause__.__traceback__)
    raise exc


def execute_task_by_id(
    *,
    task_id: str,
    work_item: str,
    run_id: str,
    runtime: str,
    root: Path | None,
    config: Path,
    log_follow: bool,
    stage_runner: StageRunner = run_stage_attempt_command,
    mutation_lease: RunMutationLease | None = None,
    intervention_request_path: Path | None = None,
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
        service = _implementation_service(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            runtime=runtime,
            config=config,
            log_follow=log_follow,
            project_root=project_root,
            stage_runner=stage_runner,
            intervention_request_path=intervention_request_path,
        )
        try:
            result = service.run_task(
                _execution_request(
                    workspace_root=workspace_root,
                    work_item=work_item,
                    run_id=run_id,
                    project_root=project_root,
                ),
                task_id=task_id,
            )
        except ImplementationPortError as exc:
            _raise_port_cause(exc)
        if result.status is not ImplementationExecutionStatus.SUCCEEDED:
            entry = result.ledger.entry(task_id)
            if entry.status.value != "succeeded":
                raise typer.Exit(code=1)
        return result.ledger


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
        service = _implementation_service(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            runtime=runtime,
            config=config,
            log_follow=False,
            project_root=Path.cwd().resolve(strict=True),
            stage_runner=run_stage_attempt_command,
        )
        try:
            return service.finalize(
                _execution_request(
                    workspace_root=workspace_root,
                    work_item=work_item,
                    run_id=run_id,
                    project_root=Path.cwd().resolve(strict=True),
                )
            ).ledger
        except ImplementationPortError as exc:
            _raise_port_cause(exc)


def execute_all_tasks(
    *,
    work_item: str,
    run_id: str,
    runtime: str,
    root: Path,
    config: Path,
    log_follow: bool,
    stage_runner: StageRunner = run_stage_attempt_command,
) -> TaskLedger:
    project_root = Path.cwd().resolve(strict=True)
    _validate_run_manifest_identity(
        workspace_root=root,
        work_item=work_item,
        run_id=run_id,
        runtime=runtime,
        config=config,
    )
    service = _implementation_service(
        workspace_root=root,
        work_item=work_item,
        run_id=run_id,
        runtime=runtime,
        config=config,
        log_follow=log_follow,
        project_root=project_root,
        stage_runner=stage_runner,
    )
    selected_run_root = run_root(workspace_root=root, work_item=work_item, run_id=run_id)
    with acquire_run_mutation_lease(selected_run_root, operation="task:all"):
        try:
            result = service.run_all(
                _execution_request(
                    workspace_root=root,
                    work_item=work_item,
                    run_id=run_id,
                    project_root=project_root,
                )
            )
        except ImplementationPortError as exc:
            _raise_port_cause(exc)
    if result.status is not ImplementationExecutionStatus.SUCCEEDED:
        raise typer.Exit(code=1)
    return result.ledger


def interact_with_implementation(
    *,
    work_item: str,
    run_id: str,
    runtime: str,
    root: Path,
    config: Path,
    log_follow: bool,
    intervention_request_path: Path,
    stage_runner: StageRunner,
) -> TaskLedger:
    project_root = Path.cwd().resolve(strict=True)
    _validate_run_manifest_identity(
        workspace_root=root,
        work_item=work_item,
        run_id=run_id,
        runtime=runtime,
        config=config,
    )
    service = _implementation_service(
        workspace_root=root,
        work_item=work_item,
        run_id=run_id,
        runtime=runtime,
        config=config,
        log_follow=log_follow,
        project_root=project_root,
        stage_runner=stage_runner,
        intervention_request_path=intervention_request_path,
    )
    request = _execution_request(
        workspace_root=root,
        work_item=work_item,
        run_id=run_id,
        project_root=project_root,
    )
    target = service.resolve_next(request)
    if target.next_target is ImplementationNextTarget.TASK:
        ready = target.ledger.ready_task_ids()
        if len(ready) != 1:
            raise ImplementationTaskSelectionError(
                "Implementation interaction requires exactly one ready or resumable task.",
                ledger=target.ledger,
            )
        return execute_task_by_id(
            task_id=ready[0],
            work_item=work_item,
            run_id=run_id,
            runtime=runtime,
            root=root,
            config=config,
            log_follow=log_follow,
            stage_runner=stage_runner,
            intervention_request_path=intervention_request_path,
        )
    if target.next_target is ImplementationNextTarget.FINALIZATION:
        return finalize_implementation(
            work_item=work_item,
            run_id=run_id,
            runtime=runtime,
            root=root,
            config=config,
        )
    raise ImplementationTaskSelectionError(
        "Implementation interaction has no pending task or finalization target.",
        ledger=target.ledger,
    )


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
