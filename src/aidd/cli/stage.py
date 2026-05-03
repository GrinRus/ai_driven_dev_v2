from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from aidd.cli.stage_inspection import (
    StageQuestionsOptions,
    StageSummaryOptions,
    show_stage_questions,
    show_stage_summary,
)
from aidd.cli.stage_run import StageRunOptions, run_stage_command


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
    run_stage_command(
        StageRunOptions(
            stage=stage,
            work_item=work_item,
            runtime=runtime,
            run_id=run_id,
            root=root,
            config=config,
            log_follow=log_follow,
        )
    )


def stage_questions(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    """Show pending stage questions and answer guidance."""
    show_stage_questions(
        StageQuestionsOptions(stage=stage, work_item=work_item, root=root)
    )


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
    show_stage_summary(
        StageSummaryOptions(
            stage=stage,
            work_item=work_item,
            root=root,
            run_id=run_id,
        )
    )
