from __future__ import annotations

from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from aidd.cli import main as cli_main
from aidd.core.run_store import persist_stage_status
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState

runner = CliRunner()


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "aidd.test.toml"
    config_path.write_text(
        (
            "[workspace]\n"
            "root = \".aidd\"\n\n"
            "[runtime.generic_cli]\n"
            "command = \"python\"\n"
        ),
        encoding="utf-8",
    )
    return config_path


def test_run_executes_runnable_stages_in_dependency_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_config(tmp_path)
    executed_stages: list[str] = []

    def _fake_stage_run(
        *,
        stage: str,
        work_item: str,
        runtime: str,
        run_id: str | None,
        root: Path | None,
        config: Path,
        log_follow: bool,
    ) -> None:
        assert runtime == "generic-cli"
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
        executed_stages.append(stage)
        persist_stage_status(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            status=StageState.SUCCEEDED.value,
        )

    monkeypatch.setattr(cli_main, "stage_run", _fake_stage_run)

    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-010",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert executed_stages == list(STAGES)
    assert "Workflow progress: stage=qa status=succeeded" in result.stdout
    assert "Workflow summary:" in result.stdout
    assert "- qa: status=succeeded attempts=0" in result.stdout
    assert "Workflow run completed:" in result.stdout


def test_run_stops_when_stage_execution_returns_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_config(tmp_path)
    executed_stages: list[str] = []

    def _fake_stage_run(
        *,
        stage: str,
        work_item: str,
        runtime: str,
        run_id: str | None,
        root: Path | None,
        config: Path,
        log_follow: bool,
    ) -> None:
        assert runtime == "generic-cli"
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
        executed_stages.append(stage)
        if stage == "idea":
            persist_stage_status(
                workspace_root=root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                status=StageState.SUCCEEDED.value,
            )
            return
        persist_stage_status(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            status=StageState.FAILED.value,
        )
        raise typer.Exit(code=1)

    monkeypatch.setattr(cli_main, "stage_run", _fake_stage_run)

    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-011",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 1, result.output
    assert executed_stages == ["idea", "research"]
    assert "Workflow stopped at stage 'research'." in result.stdout
    assert "Workflow summary:" in result.stdout
    assert "- research: status=failed attempts=0" in result.stdout
