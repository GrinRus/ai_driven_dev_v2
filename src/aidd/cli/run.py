from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from aidd.cli.stage_run import run_stage_attempt_command
from aidd.cli.support import (
    _WORKFLOW_RUN_SUPPORTED_RUNTIMES,
    _path_summary,
    _print_workflow_run_summary,
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    _tail_lines,
    console,
)
from aidd.config import load_config
from aidd.core.run_inspection import (
    resolve_run_artifacts_summary,
    resolve_run_log_summary,
    resolve_run_metadata_summary,
)
from aidd.core.stage_graph import StageAdvancementSummary
from aidd.core.stages import STAGES
from aidd.core.workflow_service import (
    WorkflowRunEvent,
    WorkflowRunRequest,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
    run_workflow,
)


def _invoke_stage_run(
    *,
    stage: str,
    work_item: str,
    runtime: str,
    run_id: str,
    root: Path,
    config: Path,
    log_follow: bool,
) -> None:
    from aidd.cli import main as cli_main

    cli_main.stage_run(
        stage=stage,
        work_item=work_item,
        runtime=runtime,
        run_id=run_id,
        root=root,
        config=config,
        log_follow=log_follow,
    )


def _select_next_runnable_stage(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage_start: str,
    stage_end: str,
) -> str | None:
    from aidd.cli import main as cli_main

    return cli_main.select_next_runnable_stage(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage_start=stage_start,
        stage_end=stage_end,
    )


def _summarize_workflow_advancement(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage_start: str,
    stage_end: str,
) -> tuple[StageAdvancementSummary, ...]:
    from aidd.cli import main as cli_main

    return cli_main.summarize_workflow_advancement(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage_start=stage_start,
        stage_end=stage_end,
    )


def _run_stage_from_workflow(request: WorkflowStageExecutionRequest) -> None:
    try:
        if request.stage == "implement":
            from aidd.cli.task import execute_all_tasks

            execute_all_tasks(
                work_item=request.work_item,
                run_id=request.run_id,
                runtime=request.runtime_id,
                root=request.workspace_root,
                config=request.config_path,
                log_follow=request.log_follow,
                stage_runner=_run_implementation_attempt_from_workflow,
            )
            return
        _invoke_stage_run(
            stage=request.stage,
            work_item=request.work_item,
            runtime=request.runtime_id,
            run_id=request.run_id,
            root=request.workspace_root,
            config=request.config_path,
            log_follow=request.log_follow,
        )
    except typer.Exit as exc:
        if exc.exit_code in (None, 0):
            return
        raise WorkflowStageExecutionError(
            stage=request.stage,
            exit_code=int(exc.exit_code),
        ) from exc


def _run_implementation_attempt_from_workflow(options: object) -> None:
    from aidd.cli import main as cli_main
    from aidd.cli.stage import stage_run as registered_stage_run
    from aidd.cli.stage_run import StageRunOptions

    if not isinstance(options, StageRunOptions):
        raise TypeError("Expected StageRunOptions.")
    if cli_main.stage_run is registered_stage_run:
        run_stage_attempt_command(options)
        return
    _invoke_stage_run(
        stage=options.stage,
        work_item=options.work_item,
        runtime=options.runtime,
        run_id=options.run_id or "",
        root=options.root or Path(".aidd"),
        config=options.config,
        log_follow=options.log_follow,
    )


def _print_workflow_event(
    event: WorkflowRunEvent,
    *,
    work_item: str,
    runtime: str,
    from_stage: str,
    to_stage: str,
) -> None:
    if event.kind == "started":
        console.print(
            "AIDD run: "
            f"work_item={work_item} runtime={runtime} run_id={event.run_id} "
            f"stage_bounds={from_stage}->{to_stage}"
        )
    elif event.kind == "next-stage" and event.stage is not None:
        console.print(f"Workflow next stage: {event.stage}")
    elif event.kind == "stage-succeeded" and event.stage is not None:
        console.print(f"Workflow progress: stage={event.stage} status=succeeded")
    elif event.kind == "stopped" and event.stage is not None:
        console.print(f"Workflow stopped at stage '{event.stage}'.")


def run_callback(
    ctx: typer.Context,
    work_item: Annotated[
        str | None,
        typer.Option("--work-item", help="Work item id"),
    ] = None,
    runtime: Annotated[str | None, typer.Option("--runtime", help="Runtime id")] = None,
    from_stage: Annotated[
        str,
        typer.Option("--from-stage", help="First stage to include in the workflow run."),
    ] = STAGES[0],
    to_stage: Annotated[
        str,
        typer.Option("--to-stage", help="Last stage to include in the workflow run."),
    ] = STAGES[-1],
    run_id: Annotated[
        str | None,
        typer.Option(
            "--run-id",
            help="Existing run id to continue; required for non-first --from-stage.",
        ),
    ] = None,
    root: Annotated[
        Path | None,
        typer.Option("--root", help="Root AIDD storage directory. Defaults to config value."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to an AIDD TOML config file."),
    ] = Path("aidd.example.toml"),
    log_follow: Annotated[
        bool,
        typer.Option(
            "--log-follow/--no-log-follow",
            help="Enable explicit live-log follow mode for each stage run.",
        ),
    ] = False,
) -> None:
    """Run the AIDD workflow for a work item."""
    if ctx.invoked_subcommand is not None:
        return
    if work_item is None:
        console.print("Error: Missing option '--work-item'.")
        raise typer.Exit(code=2)
    if runtime is None:
        supported = ", ".join(_WORKFLOW_RUN_SUPPORTED_RUNTIMES)
        console.print(
            "Missing option '--runtime'. Product workflow execution requires an "
            f"explicit runtime id. Supported runtimes: {supported}. Run `aidd doctor` "
            "to check runtime readiness."
        )
        raise typer.Exit(code=2)
    if from_stage not in STAGES:
        supported = ", ".join(STAGES)
        raise typer.BadParameter(f"Unknown stage '{from_stage}'. Expected one of: {supported}")
    if to_stage not in STAGES:
        supported = ", ".join(STAGES)
        raise typer.BadParameter(f"Unknown stage '{to_stage}'. Expected one of: {supported}")
    if STAGES.index(from_stage) > STAGES.index(to_stage):
        raise typer.BadParameter(
            f"Option '--from-stage' ({from_stage}) must not come after '--to-stage' ({to_stage})."
        )
    if from_stage != STAGES[0] and run_id is None:
        raise typer.BadParameter(
            f"Option '--run-id' is required when '--from-stage' is '{from_stage}'."
        )

    if runtime not in _WORKFLOW_RUN_SUPPORTED_RUNTIMES:
        supported = ", ".join(_WORKFLOW_RUN_SUPPORTED_RUNTIMES)
        console.print(f"AIDD run: work_item={work_item} runtime={runtime}")
        console.print(
            f"Unsupported runtime '{runtime}' for workflow execution. "
            f"Supported runtimes: {supported}."
        )
        console.print("Failure classification: unsupported-runtime")
        raise typer.Exit(code=2)

    cfg = load_config(config)
    workspace_root = (root if root is not None else cfg.workspace_root).resolve(strict=False)
    runtime_command = _runtime_command_for_runtime(runtime=runtime, cfg=cfg)
    runtime_execution_mode = _runtime_execution_mode_for_runtime(runtime=runtime, cfg=cfg)
    runtime_config = cfg.runtime_config(runtime)
    config_snapshot = {
        "config_path": config.as_posix(),
        "workspace_root": workspace_root.as_posix(),
        "runtime_command": runtime_command,
        "runtime_execution_mode": runtime_execution_mode.value,
        "runtime_permission_policy": runtime_config.permission_policy.value,
        "runtime_interaction_mode": runtime_config.interaction_mode.value,
        "runtime_auto_approval_preset": runtime_config.auto_approval_preset.value,
        "log_follow": log_follow,
        "mode": "workflow",
    }
    try:
        result = run_workflow(
            request=WorkflowRunRequest(
                work_item=work_item,
                runtime_id=runtime,
                workspace_root=workspace_root,
                config_path=config,
                config_snapshot=config_snapshot,
                stage_start=from_stage,
                stage_end=to_stage,
                log_follow=log_follow,
                run_id=run_id,
                continuation=run_id is not None,
            ),
            stage_executor=_run_stage_from_workflow,
            emit=lambda event: _print_workflow_event(
                event,
                work_item=work_item,
                runtime=runtime,
                from_stage=from_stage,
                to_stage=to_stage,
            ),
            stage_selector=_select_next_runnable_stage,
            advancement_summarizer=_summarize_workflow_advancement,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if result.stopped_stage is not None:
        _print_workflow_run_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=result.run_id,
            stage_start=from_stage,
            stage_end=to_stage,
        )
        raise typer.Exit(code=result.exit_code)

    if not result.completed:
        console.print("Workflow stopped: no runnable stage is currently available.")
        for summary in result.incomplete[:3]:
            console.print(f"- {summary.stage}: {summary.reason}")
        _print_workflow_run_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=result.run_id,
            stage_start=from_stage,
            stage_end=to_stage,
        )
        raise typer.Exit(code=result.exit_code)

    _print_workflow_run_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=result.run_id,
        stage_start=from_stage,
        stage_end=to_stage,
    )
    console.print(
        "Workflow run completed: "
        f"run_id={result.run_id} stages_executed={result.executed_stage_count}"
    )


def run_show(
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id; defaults to the latest run."),
    ] = None,
) -> None:
    """Show stored metadata for a run and its stages."""
    try:
        summary = resolve_run_metadata_summary(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    run_table = Table(title=f"Run metadata: {summary.run_id} / {summary.work_item}")
    run_table.add_column("Field")
    run_table.add_column("Value")
    run_table.add_row("run id", summary.run_id)
    run_table.add_row("work item", summary.work_item)
    run_table.add_row("runtime", summary.runtime_id)
    run_table.add_row("adapter", summary.adapter_id or summary.runtime_id)
    run_table.add_row("stage target", summary.stage_target)
    run_table.add_row(
        "workflow bounds",
        f"{summary.workflow_stage_start or STAGES[0]} -> "
        f"{summary.workflow_stage_end or summary.stage_target}",
    )
    run_table.add_row("repository git sha", summary.repository_git_sha or "unknown")
    run_table.add_row("resource revision", summary.resource_revision or "unknown")
    run_table.add_row(
        "prompt packs",
        _path_summary(
            tuple(f"{entry.path} ({entry.sha256})" for entry in summary.prompt_pack_provenance)
        ),
    )
    run_table.add_row("created at (UTC)", summary.created_at_utc or "unknown")
    run_table.add_row("updated at (UTC)", summary.updated_at_utc or "unknown")
    console.print(run_table)

    stage_table = Table(title=f"Run stages: {summary.run_id}")
    stage_table.add_column("Stage")
    stage_table.add_column("Status")
    stage_table.add_column("Attempts")
    stage_table.add_column("Updated at (UTC)")
    if summary.stages:
        for stage_summary in summary.stages:
            stage_table.add_row(
                stage_summary.stage,
                stage_summary.status,
                str(stage_summary.attempt_count),
                stage_summary.updated_at_utc or "unknown",
            )
    else:
        stage_table.add_row("none", "none", "0", "none")
    console.print(stage_table)


def run_logs(
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    stage: Annotated[str, typer.Option("--stage", help="Stage id, for example plan")],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id; defaults to the latest run."),
    ] = None,
    attempt: Annotated[
        int | None,
        typer.Option("--attempt", help="Optional attempt number; defaults to the latest attempt."),
    ] = None,
    tail: Annotated[
        bool,
        typer.Option("--tail/--no-tail", help="Print only the last N lines of the runtime log."),
    ] = False,
    lines: Annotated[
        int,
        typer.Option("--lines", help="Number of lines to print with --tail."),
    ] = 40,
) -> None:
    """Print or tail the persisted runtime log for a selected run attempt."""
    if lines <= 0:
        raise typer.BadParameter("--lines must be greater than zero.")

    try:
        summary = resolve_run_log_summary(
            workspace_root=root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
            attempt_number=attempt,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    log_text = summary.runtime_log_path.read_text(encoding="utf-8")
    if tail:
        log_text = _tail_lines(log_text, line_count=lines)

    console.print(
        f"Run log: run_id={summary.run_id} stage={summary.stage} attempt={summary.attempt_number}"
    )
    console.print(f"Path: {summary.runtime_log_path.as_posix()}")
    if not log_text:
        console.print("(empty runtime log)")
        return
    console.print(log_text, end="", markup=False, highlight=False)


def run_artifacts(
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    stage: Annotated[str, typer.Option("--stage", help="Stage id, for example plan")],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id; defaults to the latest run."),
    ] = None,
    attempt: Annotated[
        int | None,
        typer.Option("--attempt", help="Optional attempt number; defaults to the latest attempt."),
    ] = None,
) -> None:
    """List document and log artifact paths for a selected run attempt."""
    try:
        summary = resolve_run_artifacts_summary(
            workspace_root=root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
            attempt_number=attempt,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    console.print(
        "Run artifacts: "
        f"run_id={summary.run_id} stage={summary.stage} attempt={summary.attempt_number}"
    )
    console.print("Document artifacts:")
    if summary.documents:
        for name, path in summary.documents.items():
            console.print(f"- {name}: {path}")
    else:
        console.print("- none")

    console.print("Log artifacts:")
    if summary.logs:
        for name, path in summary.logs.items():
            console.print(f"- {name}: {path}")
    else:
        console.print("- none")
