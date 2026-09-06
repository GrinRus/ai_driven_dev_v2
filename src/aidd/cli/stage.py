from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from aidd.application.stage_reconciliation import (
    TerminalStageReconciliationRequest,
    reconcile_terminal_stage,
)
from aidd.cli.stage_inspection import (
    StageQuestionsOptions,
    StageSummaryOptions,
    show_stage_questions,
    show_stage_summary,
)
from aidd.cli.stage_run import (
    StageInteractOptions,
    StageRepairExtensionOptions,
    StageRunOptions,
    run_stage_command,
    run_stage_interact_command,
    run_stage_repair_extension_command,
)
from aidd.cli.support import console


def stage_run(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    runtime: Annotated[str | None, typer.Option("--runtime", help="Runtime id")] = None,
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
    if runtime is None:
        console.print(
            "Missing option '--runtime'. Product stage execution requires an explicit "
            "runtime id. Run `aidd doctor` to check runtime readiness."
        )
        raise typer.Exit(code=2)
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


def stage_interact(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    runtime: Annotated[str | None, typer.Option("--runtime", help="Runtime id")] = None,
    request: Annotated[
        str | None,
        typer.Option("--request", help="Inline operator request for this stage."),
    ] = None,
    request_file: Annotated[
        Path | None,
        typer.Option("--request-file", help="Markdown file containing the operator request."),
    ] = None,
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id; defaults to the latest run."),
    ] = None,
    target_documents: Annotated[
        list[str] | None,
        typer.Option(
            "--target-document",
            help="Stage-scoped target Markdown document; may be repeated.",
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
            help="Enable explicit live-log follow mode during intervention execution.",
        ),
    ] = True,
) -> None:
    """Run a stage-scoped operator intervention in the current run."""
    if runtime is None:
        console.print(
            "Missing option '--runtime'. Operator intervention requires an explicit "
            "runtime id. Run `aidd doctor` to check runtime readiness."
        )
        raise typer.Exit(code=2)
    run_stage_interact_command(
        StageInteractOptions(
            stage=stage,
            work_item=work_item,
            runtime=runtime,
            run_id=run_id,
            root=root,
            config=config,
            request=request,
            request_file=request_file,
            target_documents=tuple(target_documents or ()),
            log_follow=log_follow,
        )
    )


def stage_repair_extension(
    stage: Annotated[str, typer.Argument(help="Exhausted stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    run_id: Annotated[str, typer.Option("--run-id", help="Exact exhausted run id")],
    runtime: Annotated[str | None, typer.Option("--runtime", help="Runtime id")] = None,
    root: Annotated[
        Path | None,
        typer.Option("--root", help="Root AIDD storage directory. Defaults to config value."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to an AIDD TOML config file."),
    ] = Path("aidd.example.toml"),
    author: Annotated[
        str | None,
        typer.Option("--author", help="Operator identity recorded in the durable grant."),
    ] = None,
    reason: Annotated[
        str,
        typer.Option("--reason", help="Reason recorded in the durable grant."),
    ] = "Apply one bounded correction after automatic repair exhaustion.",
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            help="Explicitly authorize the command without an interactive confirmation.",
        ),
    ] = False,
    log_follow: Annotated[
        bool,
        typer.Option(
            "--log-follow/--no-log-follow",
            help="Enable explicit live-log follow mode during the extension attempt.",
        ),
    ] = True,
) -> None:
    """Authorize and run exactly one guarded repair-extension attempt."""
    if runtime is None:
        console.print(
            "Missing option '--runtime'. Repair extension requires an explicit runtime id."
        )
        raise typer.Exit(code=2)
    run_stage_repair_extension_command(
        StageRepairExtensionOptions(
            stage=stage,
            work_item=work_item,
            runtime=runtime,
            run_id=run_id,
            root=root,
            config=config,
            author=author,
            reason=reason,
            non_interactive=non_interactive,
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


def stage_reconcile_terminal(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Canonical work item id")],
    run_id: Annotated[str, typer.Option("--run-id", help="Canonical run id")],
    expected_state: Annotated[
        str,
        typer.Option(
            "--expected-state",
            help="Abandoned in-flight state that must still be current: executing or validating.",
        ),
    ],
    reason: Annotated[
        str,
        typer.Option(
            "--reason",
            help="Canonical reconciliation reason.",
        ),
    ],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    """Fail an abandoned stage through an idempotent compare-and-set operation."""
    try:
        result = reconcile_terminal_stage(
            TerminalStageReconciliationRequest(
                workspace_root=root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                expected_state=expected_state,
                reason=reason,
            )
        )
    except ValueError as exc:
        console.print(f"Terminal reconciliation rejected: {exc}")
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result.to_payload(), sort_keys=True))
