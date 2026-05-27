from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from aidd.cli.doctor import _runtime_probe_report
from aidd.cli.support import console
from aidd.evals.reporting import resolve_latest_eval_summary_report_path
from aidd.harness.live_runtime_config import validate_live_runtime_command
from aidd.harness.scenarios import load_scenario
from aidd.runtime_catalog import get_runtime_definition


def eval_doctor(
    scenario: Annotated[str, typer.Argument(help="Scenario path")],
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")] = "generic-cli",
) -> None:
    """Inspect eval runtime readiness for a scenario."""
    scenario_path = Path(scenario)
    if not scenario_path.exists():
        raise typer.BadParameter(f"Scenario not found: {scenario}")

    try:
        loaded_scenario = load_scenario(
            scenario_path,
            runtime_id=runtime,
            workspace_root=Path(".aidd"),
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    try:
        definition = get_runtime_definition(runtime)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    report = _runtime_probe_report(definition=definition)
    table = Table(title="AIDD eval doctor")
    table.add_column("Check")
    table.add_column("Value")
    table.add_row("Scenario", loaded_scenario.scenario_id)
    table.add_row("Scenario path", scenario_path.as_posix())
    table.add_row("Runtime", runtime)
    table.add_row("Runtime allowed", "yes" if runtime in loaded_scenario.runtime_targets else "no")
    table.add_row("Runtime targets", ", ".join(loaded_scenario.runtime_targets))
    table.add_row("Provider probe command", report.command)
    table.add_row("Provider available", "yes" if report.available else "no")
    table.add_row("Provider version", report.version_text or "unknown")

    if loaded_scenario.is_live:
        try:
            command_entry = validate_live_runtime_command(
                runtime_id=runtime,
                scenario=loaded_scenario,
            )
        except RuntimeError as exc:
            table.add_row("Execution readiness", "fail")
            table.add_row("Execution issue", str(exc))
        else:
            table.add_row("Execution readiness", "pass")
            table.add_row("Execution command", command_entry.command)
            table.add_row("Execution mode", command_entry.execution_mode.value)
            table.add_row("Execution command source", command_entry.source)
    else:
        table.add_row("Execution readiness", "not-live")
        table.add_row("Execution mode", "scenario invocation")
    console.print(table)


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
