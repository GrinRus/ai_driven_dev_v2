from __future__ import annotations

from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def test_eval_run_command_is_removed() -> None:
    result = runner.invoke(app, ["eval", "run", "harness/scenarios/live/foo.yaml"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_eval_namespace_keeps_doctor_and_summary_only() -> None:
    result = runner.invoke(app, ["eval", "--help"])

    assert result.exit_code == 0
    assert "doctor" in result.stdout
    assert "summary" in result.stdout
    assert " run " not in result.stdout
