from __future__ import annotations

from typing import Annotated

import typer

from aidd import __version__
from aidd.cli.doctor import doctor
from aidd.cli.eval import eval_doctor, eval_execute, eval_summary
from aidd.cli.init_command import init
from aidd.cli.run import run_artifacts, run_callback, run_logs, run_show
from aidd.cli.stage import (
    stage_interact,
    stage_questions,
    stage_reconcile_terminal,
    stage_repair_extension,
    stage_run,
    stage_summary,
)
from aidd.cli.support import console
from aidd.cli.task import task_finalize, task_list, task_run, task_show
from aidd.cli.ui import ui_command

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
stage_app.command("repair-extension")(stage_repair_extension)
stage_app.command("questions")(stage_questions)
stage_app.command("summary")(stage_summary)
stage_app.command("reconcile-terminal")(stage_reconcile_terminal)
eval_app.command("doctor")(eval_doctor)
eval_app.command("execute")(eval_execute)
eval_app.command("summary")(eval_summary)
task_app.command("list")(task_list)
task_app.command("show")(task_show)
task_app.command("run")(task_run)
task_app.command("finalize")(task_finalize)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
