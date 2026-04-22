from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def test_doctor_runs() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "AIDD doctor" in result.stdout
    assert "generic-cli capabilities" in result.stdout
    assert "claude-code capabilities" in result.stdout
    assert "codex capabilities" in result.stdout
    assert "opencode capabilities" in result.stdout


def test_init_creates_workspace(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["init", "--work-item", "WI-TEST", "--root", str(tmp_path / ".aidd")],
    )
    assert result.exit_code == 0
    assert (tmp_path / ".aidd" / "workitems" / "WI-TEST" / "stages" / "plan").exists()
