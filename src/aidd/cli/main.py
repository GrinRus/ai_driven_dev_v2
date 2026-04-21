from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from aidd import __version__
from aidd.adapters.claude_code import probe as probe_claude_code
from aidd.adapters.generic_cli import probe as probe_generic_cli
from aidd.config import load_config
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.workspace import init_workspace
from aidd.harness.scenarios import load_scenario

console = Console(no_color=True)

app = typer.Typer(
    help="Runtime-agnostic orchestration for document-first AI software delivery.",
    add_completion=False,
    no_args_is_help=True,
)
stage_app = typer.Typer(help="Stage-level commands.", add_completion=False)
eval_app = typer.Typer(help="Eval and harness commands.", add_completion=False)

app.add_typer(stage_app, name="stage")
app.add_typer(eval_app, name="eval")


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
    table.add_row("claude-code command", claude.command)
    table.add_row("claude-code available", "yes" if claude.available else "no")
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
    work_item_root = init_workspace(root=root, work_item=work_item)
    console.print(f"Initialized workspace: {work_item_root.resolve()}")


@app.command()
def run(
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")] = "claude-code",
) -> None:
    """Run the AIDD workflow for a work item."""
    console.print(f"AIDD run: work_item={work_item} runtime={runtime}")
    console.print(
        "Workflow execution is not implemented yet. "
        "See docs/backlog/roadmap.md for the next implementation slices."
    )


@stage_app.command("run")
def stage_run(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")] = "generic-cli",
) -> None:
    """Run a single AIDD stage."""
    if not is_valid_stage(stage):
        raise typer.BadParameter(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}")

    console.print(f"AIDD stage run: stage={stage} work_item={work_item} runtime={runtime}")
    console.print(
        "Stage execution is not implemented yet. "
        "See contracts/stages/ and docs/architecture/document-contracts.md."
    )


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
