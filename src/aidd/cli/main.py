from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.console import Console
from rich.table import Table

from aidd import __version__
from aidd.adapters.base import CapabilityReport
from aidd.adapters.claude_code import probe as probe_claude_code
from aidd.adapters.claude_code.runner import (
    ClaudeCodeCommandContext,
    ClaudeCodeExitClassification,
)
from aidd.adapters.claude_code.runner import (
    build_subprocess_spec as build_claude_code_subprocess_spec,
)
from aidd.adapters.claude_code.runner import (
    persist_attempt_runtime_log as persist_claude_code_runtime_log,
)
from aidd.adapters.claude_code.runner import (
    run_subprocess_with_streaming as run_claude_code_subprocess_with_streaming,
)
from aidd.adapters.codex import probe as probe_codex
from aidd.adapters.codex.runner import (
    CodexCommandContext,
    CodexExitClassification,
)
from aidd.adapters.codex.runner import (
    build_subprocess_spec as build_codex_subprocess_spec,
)
from aidd.adapters.codex.runner import (
    persist_attempt_runtime_log as persist_codex_runtime_log,
)
from aidd.adapters.codex.runner import (
    run_subprocess_with_streaming as run_codex_subprocess_with_streaming,
)
from aidd.adapters.generic_cli import probe as probe_generic_cli
from aidd.adapters.generic_cli.runner import (
    GenericCliExitClassification,
    GenericCliStageContext,
    build_subprocess_spec,
    persist_attempt_runtime_artifacts,
    run_subprocess_with_streaming,
)
from aidd.adapters.opencode import probe as probe_opencode
from aidd.adapters.opencode.runner import (
    OpenCodeCommandContext,
    OpenCodeExitClassification,
)
from aidd.adapters.opencode.runner import (
    build_subprocess_spec as build_opencode_subprocess_spec,
)
from aidd.adapters.opencode.runner import (
    persist_attempt_runtime_log as persist_opencode_runtime_log,
)
from aidd.adapters.opencode.runner import (
    run_subprocess_with_streaming as run_opencode_subprocess_with_streaming,
)
from aidd.cli.run_lookup import (
    resolve_run_artifacts_summary,
    resolve_run_log_summary,
    resolve_run_metadata_summary,
    resolve_stage_result_summary,
)
from aidd.config import AiddConfig, load_config
from aidd.core.interview import (
    load_answers_document,
    load_questions_document,
    resolved_question_ids,
    stage_has_unresolved_blocking_questions,
)
from aidd.core.repair import RepairBudgetPolicy, generate_repair_brief, write_repair_brief
from aidd.core.run_lookup import latest_run_id
from aidd.core.run_store import (
    RUN_RUNTIME_LOG_FILENAME,
    create_run_manifest,
    load_stage_metadata,
    work_item_runs_root,
)
from aidd.core.stage_graph import select_next_runnable_stage, summarize_workflow_advancement
from aidd.core.stage_registry import (
    resolve_prompt_pack_file_paths,
)
from aidd.core.stage_runner import (
    AdapterExecutionOutcome,
    AdapterInvocationBundle,
    PostValidationAction,
    StageExecutionState,
    StageOrchestrationResult,
    run_single_stage_orchestration,
    update_stage_unblock_state,
)
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.state_machine import StageState
from aidd.core.workspace import WorkspaceBootstrapService
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.evals.reporting import resolve_latest_eval_summary_report_path
from aidd.harness.eval_runner import run_eval_scenario

console = Console(no_color=True)
_STAGE_RUN_SUPPORTED_RUNTIMES: tuple[str, ...] = (
    "generic-cli",
    "claude-code",
    "codex",
    "opencode",
)
_WORKFLOW_RUN_SUPPORTED_RUNTIMES: tuple[str, ...] = _STAGE_RUN_SUPPORTED_RUNTIMES

app = typer.Typer(
    help="Runtime-agnostic orchestration for document-first AI software delivery.",
    add_completion=False,
    no_args_is_help=True,
)
stage_app = typer.Typer(help="Stage-level commands.", add_completion=False)
eval_app = typer.Typer(help="Eval and harness commands.", add_completion=False)
run_app = typer.Typer(help="Run-level commands.", add_completion=False, invoke_without_command=True)

app.add_typer(stage_app, name="stage")
app.add_typer(eval_app, name="eval")
app.add_typer(run_app, name="run")


def _capability_summary(report: CapabilityReport) -> str:
    capability_pairs = (
        ("raw-log", report.supports_raw_log_stream),
        ("structured-log", report.supports_structured_log_stream),
        ("questions", report.supports_questions),
        ("resume", report.supports_resume),
        ("subagents", report.supports_subagents),
        ("non-interactive", report.supports_non_interactive_mode),
        ("cwd-control", report.supports_working_directory_control),
        ("env-injection", report.supports_env_injection),
    )
    enabled = [name for name, is_enabled in capability_pairs if is_enabled]
    return ", ".join(enabled) if enabled else "none"


def _path_summary(paths: tuple[str, ...]) -> str:
    if not paths:
        return "none"
    return "\n".join(paths)


def _runtime_command_for_runtime(*, runtime: str, cfg: AiddConfig) -> str:
    if runtime == "generic-cli":
        return cfg.generic_cli_command
    if runtime == "claude-code":
        return cfg.claude_code_command
    if runtime == "codex":
        return cfg.codex_command
    if runtime == "opencode":
        return cfg.opencode_command
    raise ValueError(f"Unsupported runtime id: {runtime}")


def _tail_lines(text: str, *, line_count: int) -> str:
    lines = text.splitlines()
    if line_count >= len(lines):
        return text
    return "\n".join(lines[-line_count:]) + "\n"


def _stream_prefix(*, runtime: str, stage: str, stream: Literal["stdout", "stderr"]) -> str:
    return f"[{runtime}:{stage}:{stream}]"


def _prefix_stream_chunk(
    *,
    runtime: str,
    stage: str,
    stream: Literal["stdout", "stderr"],
    chunk: str,
    multi_stream: bool,
) -> str:
    if not multi_stream:
        return chunk

    prefix = _stream_prefix(runtime=runtime, stage=stage, stream=stream)
    lines = chunk.splitlines(keepends=True)
    if not lines:
        return f"{prefix} "
    return "".join(f"{prefix} {line}" for line in lines)


def _allocate_stage_run_id(*, workspace_root: Path, work_item: str) -> str:
    base_run_id = f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    candidate = base_run_id
    suffix = 2
    while (runs_root / candidate).exists():
        candidate = f"{base_run_id}-{suffix:02d}"
        suffix += 1
    return candidate


def _print_workflow_run_summary(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage_start: str | None = None,
    stage_end: str | None = None,
) -> None:
    summary = resolve_run_metadata_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    normalized_stage_start = stage_start or summary.workflow_stage_start or STAGES[0]
    normalized_stage_end = stage_end or summary.workflow_stage_end or summary.stage_target
    console.print(
        "Workflow summary: "
        f"run_id={summary.run_id} runtime={summary.runtime_id} "
        f"stage_bounds={normalized_stage_start}->{normalized_stage_end}"
    )
    if not summary.stages:
        console.print("- no stage metadata recorded")
        return
    for stage_summary in summary.stages:
        console.print(
            f"- {stage_summary.stage}: "
            f"status={stage_summary.status} attempts={stage_summary.attempt_count}"
        )


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"aidd {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the AIDD version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    _ = version


@app.command()
def doctor(
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to an AIDD TOML config file."),
    ] = Path("aidd.example.toml"),
) -> None:
    """Inspect the local bootstrap environment."""
    cfg = load_config(config)
    generic = probe_generic_cli(cfg.generic_cli_command)
    claude = probe_claude_code(cfg.claude_code_command)
    codex = probe_codex(cfg.codex_command)
    opencode = probe_opencode(cfg.opencode_command)

    table = Table(title="AIDD doctor")
    table.add_column("Check")
    table.add_column("Value")
    table.add_row("Version", __version__)
    table.add_row("Config path", str(config.resolve()))
    table.add_row("Workspace root", str(cfg.workspace_root))
    table.add_row("generic-cli command", generic.command)
    table.add_row("generic-cli available", "yes" if generic.available else "no")
    table.add_row("generic-cli version", generic.version_text or "unknown")
    table.add_row("generic-cli capabilities", _capability_summary(generic))
    table.add_row("claude-code command", claude.command)
    table.add_row("claude-code available", "yes" if claude.available else "no")
    table.add_row("claude-code version", claude.version_text or "unknown")
    table.add_row("claude-code capabilities", _capability_summary(claude))
    table.add_row("codex command", codex.command)
    table.add_row("codex available", "yes" if codex.available else "no")
    table.add_row("codex version", codex.version_text or "unknown")
    table.add_row("codex capabilities", _capability_summary(codex))
    table.add_row("opencode command", opencode.command)
    table.add_row("opencode available", "yes" if opencode.available else "no")
    table.add_row("opencode version", opencode.version_text or "unknown")
    table.add_row("opencode capabilities", _capability_summary(opencode))
    table.add_row("log mode", cfg.log_mode)
    table.add_row("max repair attempts", str(cfg.max_repair_attempts))

    console.print(table)
    console.print(
        "Workflow, installed live E2E, and published-package release proof are "
        "available on maintained runtimes."
    )


@app.command()
def init(
    work_item: Annotated[
        str,
        typer.Option("--work-item", help="Work item identifier, for example WI-001."),
    ] = "WI-001",
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    """Create a starter AIDD workspace for one work item."""
    bootstrap_service = WorkspaceBootstrapService(root=root)
    work_item_root = bootstrap_service.bootstrap_work_item(work_item=work_item)
    console.print(f"Initialized workspace: {work_item_root.resolve()}")


@run_app.callback(invoke_without_command=True)
def run_callback(
    ctx: typer.Context,
    work_item: Annotated[
        str | None,
        typer.Option("--work-item", help="Work item id"),
    ] = None,
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")] = "generic-cli",
    from_stage: Annotated[
        str,
        typer.Option("--from-stage", help="First stage to include in the workflow run."),
    ] = STAGES[0],
    to_stage: Annotated[
        str,
        typer.Option("--to-stage", help="Last stage to include in the workflow run."),
    ] = STAGES[-1],
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
        raise typer.BadParameter("Missing option '--work-item'.")
    if from_stage not in STAGES:
        supported = ", ".join(STAGES)
        raise typer.BadParameter(
            f"Unknown stage '{from_stage}'. Expected one of: {supported}"
        )
    if to_stage not in STAGES:
        supported = ", ".join(STAGES)
        raise typer.BadParameter(
            f"Unknown stage '{to_stage}'. Expected one of: {supported}"
        )
    if STAGES.index(from_stage) > STAGES.index(to_stage):
        raise typer.BadParameter(
            f"Option '--from-stage' ({from_stage}) must not come after '--to-stage' ({to_stage})."
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
    run_id = _allocate_stage_run_id(workspace_root=workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id=runtime,
        stage_target=to_stage,
        config_snapshot={
            "config_path": config.as_posix(),
            "workspace_root": workspace_root.as_posix(),
            "runtime_command": runtime_command,
            "log_follow": log_follow,
            "mode": "workflow",
        },
        workflow_stage_start=from_stage,
        workflow_stage_end=to_stage,
    )
    console.print(
        "AIDD run: "
        f"work_item={work_item} runtime={runtime} run_id={run_id} "
        f"stage_bounds={from_stage}->{to_stage}"
    )

    executed_stage_count = 0
    while True:
        next_stage = select_next_runnable_stage(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage_start=from_stage,
            stage_end=to_stage,
        )
        if next_stage is None:
            break

        console.print(f"Workflow next stage: {next_stage}")
        try:
            stage_run(
                stage=next_stage,
                work_item=work_item,
                runtime=runtime,
                run_id=run_id,
                root=workspace_root,
                config=config,
                log_follow=log_follow,
            )
        except typer.Exit as exc:
            if exc.exit_code not in (None, 0):
                console.print(f"Workflow stopped at stage '{next_stage}'.")
                _print_workflow_run_summary(
                    workspace_root=workspace_root,
                    work_item=work_item,
                    run_id=run_id,
                    stage_start=from_stage,
                    stage_end=to_stage,
                )
                raise
        executed_stage_count += 1
        console.print(f"Workflow progress: stage={next_stage} status=succeeded")

    advancement = summarize_workflow_advancement(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage_start=from_stage,
        stage_end=to_stage,
    )
    incomplete = [
        summary for summary in advancement if summary.current_status != StageState.SUCCEEDED.value
    ]
    if incomplete:
        console.print("Workflow stopped: no runnable stage is currently available.")
        for summary in incomplete[:3]:
            console.print(f"- {summary.stage}: {summary.reason}")
        _print_workflow_run_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage_start=from_stage,
            stage_end=to_stage,
        )
        raise typer.Exit(code=1)

    _print_workflow_run_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage_start=from_stage,
        stage_end=to_stage,
    )
    console.print(
        "Workflow run completed: "
        f"run_id={run_id} stages_executed={executed_stage_count}"
    )


@run_app.command("show")
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
    run_table.add_row("stage target", summary.stage_target)
    run_table.add_row(
        "workflow bounds",
        f"{summary.workflow_stage_start or STAGES[0]} -> "
        f"{summary.workflow_stage_end or summary.stage_target}",
    )
    run_table.add_row("repository git sha", summary.repository_git_sha or "unknown")
    run_table.add_row(
        "prompt packs",
        _path_summary(
            tuple(
                f"{entry.path} ({entry.sha256})"
                for entry in summary.prompt_pack_provenance
            )
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


@run_app.command("logs")
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
        "Run log: "
        f"run_id={summary.run_id} stage={summary.stage} attempt={summary.attempt_number}"
    )
    console.print(f"Path: {summary.runtime_log_path.as_posix()}")
    if not log_text:
        console.print("(empty runtime log)")
        return
    console.print(log_text, end="")


@run_app.command("artifacts")
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


@stage_app.command("run")
def stage_run(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")] = "generic-cli",
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id; defaults to latest blocked or new run."),
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
            help="Enable explicit live-log follow mode during stage execution.",
        ),
    ] = False,
) -> None:
    """Run a single AIDD stage."""
    if not is_valid_stage(stage):
        raise typer.BadParameter(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}")
    if runtime not in _STAGE_RUN_SUPPORTED_RUNTIMES:
        supported = ", ".join(_STAGE_RUN_SUPPORTED_RUNTIMES)
        raise typer.BadParameter(
            f"Unsupported runtime '{runtime}'. Supported runtimes: {supported}."
        )

    cfg = load_config(config)
    workspace_root = (root if root is not None else cfg.workspace_root).resolve(strict=False)
    runtime_command = _runtime_command_for_runtime(runtime=runtime, cfg=cfg)
    repair_policy = RepairBudgetPolicy(default_max_repair_attempts=cfg.max_repair_attempts)
    selected_run_id: str | None = None
    if run_id is not None:
        normalized_run_id = run_id.strip()
        if not normalized_run_id:
            raise typer.BadParameter("Option '--run-id' must not be empty.")
        selected_run_id = normalized_run_id
    else:
        latest_existing_run = latest_run_id(workspace_root=workspace_root, work_item=work_item)
        if latest_existing_run is not None:
            latest_stage_metadata = load_stage_metadata(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=latest_existing_run,
                stage=stage,
            )
            if (
                latest_stage_metadata is not None
                and latest_stage_metadata.status.lower() == StageState.BLOCKED.value
            ):
                selected_run_id = latest_existing_run

    is_resume_candidate = False
    if selected_run_id is not None:
        selected_stage_metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=selected_run_id,
            stage=stage,
        )
        is_resume_candidate = (
            selected_stage_metadata is not None
            and selected_stage_metadata.status.lower() == StageState.BLOCKED.value
        )

    run_id = selected_run_id or _allocate_stage_run_id(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id=runtime,
        stage_target=stage,
        config_snapshot={
            "config_path": config.as_posix(),
            "workspace_root": workspace_root.as_posix(),
            "runtime_command": runtime_command,
            "log_follow": log_follow,
        },
    )
    prompt_pack_file_paths = resolve_prompt_pack_file_paths(stage=stage)
    prompt_pack_path = prompt_pack_file_paths[0]

    console.print(
        "AIDD stage run: "
        f"stage={stage} work_item={work_item} runtime={runtime} "
        f"log_follow={log_follow} run_id={run_id}"
    )
    if is_resume_candidate:
        console.print("Detected blocked stage metadata on the latest run; attempting resume.")
    if log_follow:
        console.print("Live-log follow mode enabled for runtime stream output.")

    def _stream_runtime_chunk(
        *,
        stream: Literal["stdout", "stderr"],
        chunk: str,
    ) -> None:
        if not log_follow:
            return
        prefixed_chunk = _prefix_stream_chunk(
            runtime=runtime,
            stage=stage,
            stream=stream,
            chunk=chunk,
            multi_stream=True,
        )
        console.print(prefixed_chunk, end="", markup=False, highlight=False)

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        stage_documents_root = workspace_stage_root(
            root=workspace_root,
            work_item=invocation.work_item,
            stage=invocation.stage,
        )
        stage_documents_root.mkdir(parents=True, exist_ok=True)
        stage_brief_path = stage_documents_root / "stage-brief.md"
        stage_brief_path.write_text(invocation.stage_brief_markdown, encoding="utf-8")

        def _on_stdout(chunk: str) -> None:
            _stream_runtime_chunk(stream="stdout", chunk=chunk)

        def _on_stderr(chunk: str) -> None:
            _stream_runtime_chunk(stream="stderr", chunk=chunk)

        on_stdout = _on_stdout if log_follow else None
        on_stderr = _on_stderr if log_follow else None
        try:
            if runtime == "generic-cli":
                generic_context = GenericCliStageContext(
                    stage=invocation.stage,
                    work_item=invocation.work_item,
                    run_id=invocation.run_id,
                    prompt_pack_path=prompt_pack_path,
                )
                generic_spec = build_subprocess_spec(
                    configured_command=runtime_command,
                    workspace_root=workspace_root,
                    context=generic_context,
                    base_env=dict(os.environ),
                    repository_root=Path.cwd(),
                )
                generic_run_result = run_subprocess_with_streaming(
                    spec=generic_spec,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                )
                persist_attempt_runtime_artifacts(
                    attempt_path=execution_state.attempt_path,
                    run_result=generic_run_result,
                )
                return AdapterExecutionOutcome(
                    succeeded=(
                        generic_run_result.exit_classification
                        is GenericCliExitClassification.SUCCESS
                    ),
                    details=generic_run_result.exit_classification.value,
                )

            prompt_pack_paths_for_runtime = tuple(prompt_pack_file_paths)
            if runtime == "claude-code":
                claude_context = ClaudeCodeCommandContext(
                    stage=invocation.stage,
                    work_item=invocation.work_item,
                    run_id=invocation.run_id,
                    workspace_root=workspace_root,
                    stage_brief_path=stage_brief_path,
                    prompt_pack_paths=prompt_pack_paths_for_runtime,
                )
                claude_spec = build_claude_code_subprocess_spec(
                    configured_command=runtime_command,
                    context=claude_context,
                    base_env=dict(os.environ),
                    repository_root=Path.cwd(),
                )
                claude_run_result = run_claude_code_subprocess_with_streaming(
                    spec=claude_spec,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                )
                persist_claude_code_runtime_log(
                    attempt_path=execution_state.attempt_path,
                    run_result=claude_run_result,
                )
                return AdapterExecutionOutcome(
                    succeeded=(
                        claude_run_result.exit_classification
                        is ClaudeCodeExitClassification.SUCCESS
                    ),
                    details=claude_run_result.exit_classification.value,
                )

            if runtime == "codex":
                codex_context = CodexCommandContext(
                    stage=invocation.stage,
                    work_item=invocation.work_item,
                    run_id=invocation.run_id,
                    workspace_root=workspace_root,
                    stage_brief_path=stage_brief_path,
                    prompt_pack_paths=prompt_pack_paths_for_runtime,
                )
                codex_spec = build_codex_subprocess_spec(
                    configured_command=runtime_command,
                    context=codex_context,
                    base_env=dict(os.environ),
                    repository_root=Path.cwd(),
                )
                codex_run_result = run_codex_subprocess_with_streaming(
                    spec=codex_spec,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                )
                persist_codex_runtime_log(
                    attempt_path=execution_state.attempt_path,
                    run_result=codex_run_result,
                )
                return AdapterExecutionOutcome(
                    succeeded=(
                        codex_run_result.exit_classification is CodexExitClassification.SUCCESS
                    ),
                    details=codex_run_result.exit_classification.value,
                )

            if runtime == "opencode":
                opencode_context = OpenCodeCommandContext(
                    stage=invocation.stage,
                    work_item=invocation.work_item,
                    run_id=invocation.run_id,
                    workspace_root=workspace_root,
                    stage_brief_path=stage_brief_path,
                    prompt_pack_paths=prompt_pack_paths_for_runtime,
                )
                opencode_spec = build_opencode_subprocess_spec(
                    configured_command=runtime_command,
                    context=opencode_context,
                    base_env=dict(os.environ),
                    repository_root=Path.cwd(),
                )
                opencode_run_result = run_opencode_subprocess_with_streaming(
                    spec=opencode_spec,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                )
                persist_opencode_runtime_log(
                    attempt_path=execution_state.attempt_path,
                    run_result=opencode_run_result,
                )
                return AdapterExecutionOutcome(
                    succeeded=(
                        opencode_run_result.exit_classification
                        is OpenCodeExitClassification.SUCCESS
                    ),
                    details=opencode_run_result.exit_classification.value,
                )

            return AdapterExecutionOutcome(
                succeeded=False,
                details=f"unsupported-runtime: {runtime}",
            )
        except OSError as exc:
            return AdapterExecutionOutcome(
                succeeded=False,
                details=f"runtime-launch-error: {exc}",
            )

    def _write_repair_brief_for_retry(
        *,
        orchestration: StageOrchestrationResult,
    ) -> Path:
        if orchestration.validation_result is None:
            raise ValueError("Repair retry requires validator findings from the previous attempt.")

        validator_report_path = orchestration.validation_result.validator_report_path
        repair_brief_path = validator_report_path.parent / "repair-brief.md"
        repair_brief = generate_repair_brief(
            validator_report_path=validator_report_path,
            prior_stage_artifacts=orchestration.adapter_invocation.expected_input_bundle,
            stage_attempt_count=orchestration.execution_state.attempt_number,
            max_repair_attempts=repair_policy.default_max_repair_attempts,
            workspace_root=workspace_root,
        )
        write_repair_brief(path=repair_brief_path, repair_brief_markdown=repair_brief)
        return repair_brief_path

    orchestration: StageOrchestrationResult | None = None
    stage_attempt_count = 0
    while True:
        unblock_state = update_stage_unblock_state(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if unblock_state.was_blocked and not unblock_state.unblocked:
            stage_documents_root = workspace_root / "workitems" / work_item / "stages" / stage
            console.print("Stage run result: action=wait state=blocked")
            if unblock_state.stage_metadata_path is not None:
                console.print(f"Stage metadata: {unblock_state.stage_metadata_path.as_posix()}")
            console.print("Blocking questions are unresolved.")
            console.print(f"Questions: {(stage_documents_root / 'questions.md').as_posix()}")
            console.print(f"Answers: {(stage_documents_root / 'answers.md').as_posix()}")
            raise typer.Exit(code=1)
        if unblock_state.unblocked:
            console.print("Resuming blocked stage after answers were detected.")

        try:
            orchestration = run_single_stage_orchestration(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                adapter_executor=_adapter_executor,
                repair_policy=repair_policy,
            )
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

        stage_attempt_count += 1
        if orchestration.transition.action is not PostValidationAction.REPAIR:
            break
        repair_brief_path = _write_repair_brief_for_retry(orchestration=orchestration)
        console.print(f"Repair brief prepared: {repair_brief_path.as_posix()}")
        console.print(
            "Repair retry scheduled: "
            f"attempt={orchestration.execution_state.attempt_number + 1}"
        )

    assert orchestration is not None

    runtime_log_path = orchestration.execution_state.attempt_path / RUN_RUNTIME_LOG_FILENAME
    console.print(
        "Stage run result: "
        f"action={orchestration.transition.action.value} "
        f"state={orchestration.transition.next_state.value}"
    )
    console.print(f"Stage attempts: {stage_attempt_count}")
    console.print(f"Stage metadata: {orchestration.transition.stage_metadata_path.as_posix()}")
    console.print(f"Runtime log: {runtime_log_path.as_posix()}")
    if orchestration.validation_result is not None:
        console.print(
            "Validator report: "
            f"{orchestration.validation_result.validator_report_path.as_posix()}"
        )
    if orchestration.adapter_outcome.details:
        console.print(f"Adapter outcome: {orchestration.adapter_outcome.details}")
    if orchestration.transition.action is not PostValidationAction.ADVANCE:
        raise typer.Exit(code=1)


@stage_app.command("questions")
def stage_questions(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    """Show pending stage questions and answer guidance."""
    if not is_valid_stage(stage):
        raise typer.BadParameter(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}")

    questions = load_questions_document(
        workspace_root=root,
        work_item=work_item,
        stage=stage,
    )
    if not questions:
        console.print("No stage questions recorded.")
        return

    resolved_ids: set[str] = set()
    answers_path = root / "workitems" / work_item / "stages" / stage / "answers.md"
    if answers_path.exists():
        resolved_ids = set(
            resolved_question_ids(
                answers=load_answers_document(
                    workspace_root=root,
                    work_item=work_item,
                    stage=stage,
                )
            )
        )

    table = Table(title=f"Stage questions: {stage} / {work_item}")
    table.add_column("Question id")
    table.add_column("Policy")
    table.add_column("Status")
    table.add_column("Text")
    for question in questions:
        if question.question_id in resolved_ids:
            status = "resolved"
        elif question.policy.value == "blocking":
            status = "pending-blocking"
        else:
            status = "pending-non-blocking"
        table.add_row(question.question_id, question.policy.value, status, question.text)
    console.print(table)

    if stage_has_unresolved_blocking_questions(
        workspace_root=root,
        work_item=work_item,
        stage=stage,
    ):
        console.print(
            "Blocking questions are unresolved. Add `[resolved]` answers in "
            f"`{answers_path.as_posix()}` before progressing this stage."
        )
        return

    console.print("No unresolved blocking questions. Stage can proceed if other checks pass.")


@stage_app.command("summary")
def stage_summary(
    stage: Annotated[str, typer.Argument(help="Stage name")],
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
    """Show a stage result summary for one work item run."""
    if not is_valid_stage(stage):
        raise typer.BadParameter(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}")

    try:
        summary = resolve_stage_result_summary(
            workspace_root=root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    table = Table(title=f"Stage summary: {stage} / {work_item}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("run id", summary.run_id)
    table.add_row("runtime", summary.runtime_id)
    table.add_row("final state", summary.final_state)
    table.add_row("attempt count", str(summary.attempt_count))
    table.add_row("validator pass count", str(summary.validator_pass_count))
    table.add_row("validator fail count", str(summary.validator_fail_count))
    table.add_row("validator report", summary.validator_report_path)
    table.add_row("log artifacts", _path_summary(summary.log_artifact_paths))
    table.add_row("document artifacts", _path_summary(summary.document_artifact_paths))
    table.add_row("repair outputs", _path_summary(summary.repair_output_paths))
    console.print(table)


@eval_app.command("run")
def eval_run(
    scenario: Annotated[str, typer.Argument(help="Scenario path")],
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")] = "generic-cli",
) -> None:
    """Run an eval scenario."""
    scenario_path = Path(scenario)
    if not scenario_path.exists():
        raise typer.BadParameter(f"Scenario not found: {scenario}")

    try:
        result = run_eval_scenario(
            scenario_path=scenario_path,
            runtime_id=runtime,
            workspace_root=Path(".aidd"),
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    console.print(f"AIDD eval run: scenario={result.scenario_id} runtime={runtime}")
    console.print(f"Status: {result.status}")
    console.print(f"Quality gate: {result.quality_gate}")
    console.print(f"Run id: {result.run_id}")
    console.print(f"Bundle root: {result.bundle_root.as_posix()}")
    console.print(f"Verdict path: {result.verdict_path.as_posix()}")
    console.print(f"Quality report path: {result.quality_report_path.as_posix()}")
    console.print(f"Summary path: {result.summary_path.as_posix()}")


@eval_app.command("summary")
def eval_summary(
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    """Print the latest eval summary report."""
    try:
        summary_path = resolve_latest_eval_summary_report_path(workspace_root=root)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    console.print(f"Latest eval report: {summary_path.as_posix()}")
    console.print(summary_path.read_text(encoding="utf-8").rstrip())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
