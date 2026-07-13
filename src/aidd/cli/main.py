from __future__ import annotations

from typing import Annotated

import typer

from aidd import __version__
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.cli.doctor import _runtime_probe_report, doctor
from aidd.cli.eval import eval_doctor, eval_summary
from aidd.cli.init_command import init
from aidd.cli.run import run_artifacts, run_callback, run_logs, run_show
from aidd.cli.stage import stage_interact, stage_questions, stage_run, stage_summary
from aidd.cli.support import (
    _active_prompt_pack_paths,
    _allocate_stage_run_id,
    _path_summary,
    _prefix_stream_chunk,
    _print_workflow_run_summary,
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    _runtime_timeout_for_runtime,
    _tail_lines,
    console,
)
from aidd.cli.task import task_finalize, task_list, task_run, task_show
from aidd.cli.ui import ui_command
from aidd.core.stage_graph import select_next_runnable_stage, summarize_workflow_advancement

__all__ = [
    "_active_prompt_pack_paths",
    "_allocate_stage_run_id",
    "_path_summary",
    "_prefix_stream_chunk",
    "_print_workflow_run_summary",
    "_runtime_command_for_runtime",
    "_runtime_execution_mode_for_runtime",
    "_runtime_probe_report",
    "_runtime_timeout_for_runtime",
    "_tail_lines",
    "app",
    "doctor",
    "eval_doctor",
    "eval_summary",
    "init",
    "main",
    "probe_claude_code",
    "probe_codex",
    "probe_generic_cli",
    "probe_opencode",
    "probe_qwen",
    "run_artifacts",
    "run_callback",
    "run_logs",
    "run_show",
    "stage_interact",
    "select_next_runnable_stage",
    "stage_questions",
    "stage_run",
    "stage_summary",
    "summarize_workflow_advancement",
    "task_list",
    "task_finalize",
    "task_run",
    "task_show",
    "ui_command",
]

probe_generic_cli = get_runtime_adapter_surface("generic-cli").probe
probe_claude_code = get_runtime_adapter_surface("claude-code").probe
probe_codex = get_runtime_adapter_surface("codex").probe
probe_opencode = get_runtime_adapter_surface("opencode").probe
probe_qwen = get_runtime_adapter_surface("qwen").probe

app = typer.Typer(
    help="Runtime-agnostic orchestration for document-first AI software delivery.",
    add_completion=False,
    no_args_is_help=True,
)
stage_app = typer.Typer(help="Stage-level commands.", add_completion=False)
eval_app = typer.Typer(help="Eval and harness commands.", add_completion=False)
run_app = typer.Typer(
    help="Run-level commands.",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
)
task_app = typer.Typer(help="Task-level implementation commands.", add_completion=False)

app.add_typer(stage_app, name="stage")
app.add_typer(eval_app, name="eval")
app.add_typer(run_app, name="run")
app.add_typer(task_app, name="task")


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


app.command()(doctor)
app.command()(init)
app.command("ui")(ui_command)
run_app.callback(invoke_without_command=True)(run_callback)
run_app.command("show")(run_show)
run_app.command("logs")(run_logs)
run_app.command("artifacts")(run_artifacts)
stage_app.command("run")(stage_run)
stage_app.command("interact")(stage_interact)
stage_app.command("questions")(stage_questions)
stage_app.command("summary")(stage_summary)
eval_app.command("doctor")(eval_doctor)
eval_app.command("summary")(eval_summary)
task_app.command("list")(task_list)
task_app.command("show")(task_show)
task_app.command("run")(task_run)
task_app.command("finalize")(task_finalize)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
