from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from aidd import __version__
from aidd.adapters.base import CapabilityReport
from aidd.adapters.runtime_registry import RuntimeDefinition, runtime_definitions
from aidd.cli.support import (
    _capability_summary,
    _execution_command_available,
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    console,
)
from aidd.config import load_config


def _runtime_probe_report(*, definition: RuntimeDefinition) -> CapabilityReport:
    from aidd.cli import main as cli_main

    probe_by_runtime = {
        "generic-cli": cli_main.probe_generic_cli,
        "claude-code": cli_main.probe_claude_code,
        "codex": cli_main.probe_codex,
        "opencode": cli_main.probe_opencode,
        "qwen": cli_main.probe_qwen,
    }
    try:
        probe_runtime = probe_by_runtime[definition.runtime_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported runtime id: {definition.runtime_id}") from exc
    return probe_runtime(definition.probe_command)


def doctor(
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to an AIDD TOML config file."),
    ] = Path("aidd.example.toml"),
) -> None:
    """Inspect the local bootstrap environment."""
    cfg = load_config(config)

    table = Table(title="AIDD doctor")
    table.add_column("Check")
    table.add_column("Value")
    table.add_row("Version", __version__)
    table.add_row("Config path", str(config.resolve()))
    table.add_row("Workspace root", str(cfg.workspace_root))
    for definition in runtime_definitions():
        runtime_command = _runtime_command_for_runtime(runtime=definition.runtime_id, cfg=cfg)
        execution_mode = _runtime_execution_mode_for_runtime(
            runtime=definition.runtime_id,
            cfg=cfg,
        )
        report = _runtime_probe_report(definition=definition)
        table.add_row(f"{definition.runtime_id} support tier", definition.support_tier)
        table.add_row(f"{definition.runtime_id} provider probe command", report.command)
        table.add_row(
            f"{definition.runtime_id} provider available",
            "yes" if report.available else "no",
        )
        table.add_row(
            f"{definition.runtime_id} execution command",
            runtime_command,
        )
        table.add_row(f"{definition.runtime_id} execution mode", execution_mode.value)
        table.add_row(
            f"{definition.runtime_id} execution command available",
            "yes" if _execution_command_available(runtime_command) else "no",
        )
        table.add_row(f"{definition.runtime_id} version", report.version_text or "unknown")
        table.add_row(f"{definition.runtime_id} capabilities", _capability_summary(report))
    table.add_row("log mode", cfg.log_mode)
    table.add_row("max repair attempts", str(cfg.max_repair_attempts))

    console.print(table)
    console.print(
        "Provider probe checks raw runtime availability; execution readiness checks "
        "the configured AIDD command and mode."
    )
