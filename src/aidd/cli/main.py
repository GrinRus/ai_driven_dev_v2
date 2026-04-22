from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.console import Console
from rich.table import Table

from aidd import __version__
from aidd.adapters.base import CapabilityReport
from aidd.adapters.claude_code import probe as probe_claude_code
from aidd.adapters.generic_cli import probe as probe_generic_cli
from aidd.cli.run_lookup import (
    resolve_run_artifacts_summary,
    resolve_run_log_summary,
    resolve_run_metadata_summary,
    resolve_stage_result_summary,
)
from aidd.config import load_config
from aidd.core.interview import (
    load_answers_document,
    load_questions_document,
    resolved_question_ids,
    stage_has_unresolved_blocking_questions,
)
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.workspace import WorkspaceBootstrapService
from aidd.harness.scenarios import load_scenario

console = Console(no_color=True)

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
    table.add_row("log mode", cfg.log_mode)
    table.add_row("max repair attempts", str(cfg.max_repair_attempts))

    console.print(table)
    console.print(
        "Bootstrap commands are functional. Stage execution, validators, adapters, and harness "
        "orchestration are still roadmap work."
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
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")] = "claude-code",
) -> None:
    """Run the AIDD workflow for a work item."""
    if ctx.invoked_subcommand is not None:
        return
    if work_item is None:
        raise typer.BadParameter("Missing option '--work-item'.")
    console.print(f"AIDD run: work_item={work_item} runtime={runtime}")
    console.print(
        "Workflow execution is not implemented yet. "
        "See docs/backlog/roadmap.md for the next implementation slices."
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

    console.print(
        "AIDD stage run: "
        f"stage={stage} work_item={work_item} runtime={runtime} log_follow={log_follow}"
    )
    if log_follow:
        stdout_preview = _prefix_stream_chunk(
            runtime=runtime,
            stage=stage,
            stream="stdout",
            chunk="runtime-output-line\n",
            multi_stream=True,
        ).rstrip("\n")
        stderr_preview = _prefix_stream_chunk(
            runtime=runtime,
            stage=stage,
            stream="stderr",
            chunk="runtime-error-line\n",
            multi_stream=True,
        ).rstrip("\n")
        console.print("Live-log follow prefix mode enabled for multi-stream output.")
        console.print(f"stdout prefix preview: {stdout_preview}", markup=False)
        console.print(f"stderr prefix preview: {stderr_preview}", markup=False)
    console.print(
        "Stage execution is not implemented yet. "
        "See contracts/stages/ and docs/architecture/document-contracts.md."
    )


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

    loaded = load_scenario(scenario_path)
    console.print(f"AIDD eval run: scenario={loaded.scenario_id} runtime={runtime}")
    console.print(f"Task: {loaded.task}")
    console.print(
        "Harness execution is not implemented yet. "
        "See docs/architecture/eval-harness-integration.md."
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
