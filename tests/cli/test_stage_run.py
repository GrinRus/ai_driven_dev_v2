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
    assert "Live-log follow prefix mode enabled for multi-stream output." in result.stdout
    assert "stdout prefix preview:" in result.stdout
    assert "[generic-cli:plan:stdout] runtime-output-line" in result.stdout
    assert "stderr prefix preview:" in result.stdout
    assert "[generic-cli:plan:stderr] runtime-error-line" in result.stdout
    assert "Stage execution is not implemented yet." in result.stdout


def test_stage_run_without_log_follow_omits_stream_prefix_preview() -> None:
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
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0
    assert "log_follow=False" in result.stdout
    assert "Live-log follow prefix mode enabled for multi-stream output." not in result.stdout
