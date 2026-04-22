from __future__ import annotations

from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def test_stage_run_supports_explicit_log_follow_flag() -> None:
    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-001",
            "--runtime",
            "generic-cli",
            "--log-follow",
        ],
    )

    assert result.exit_code == 0
    assert "AIDD stage run: stage=plan work_item=WI-001 runtime=generic-cli log_follow=True" in (
        result.stdout
    )
    assert "Stage execution is not implemented yet." in result.stdout

