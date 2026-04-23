from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from aidd.cli import main as cli_main
from aidd.core.run_store import persist_stage_status, run_manifest_path, work_item_runs_root
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState

runner = CliRunner()
_RUNTIME_COMMANDS: dict[str, str] = {
    "generic-cli": "python-generic",
    "claude-code": "claude-fake",
    "codex": "codex-fake",
    "opencode": "opencode-fake",
}


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "aidd.test.toml"
    config_path.write_text(
        (
            "[workspace]\n"
            "root = \".aidd\"\n\n"
            "[runtime.generic_cli]\n"
            f"command = \"{_RUNTIME_COMMANDS['generic-cli']}\"\n\n"
            "[runtime.claude_code]\n"
            f"command = \"{_RUNTIME_COMMANDS['claude-code']}\"\n\n"
            "[runtime.codex]\n"
            f"command = \"{_RUNTIME_COMMANDS['codex']}\"\n\n"
            "[runtime.opencode]\n"
            f"command = \"{_RUNTIME_COMMANDS['opencode']}\"\n"
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


@pytest.mark.parametrize("selected_runtime", ("claude-code", "codex", "opencode"))
def test_run_dispatches_workflow_for_supported_non_generic_runtimes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selected_runtime: str,
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
        assert runtime == selected_runtime
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
            "WI-012",
            "--runtime",
            selected_runtime,
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert executed_stages == list(STAGES)
    assert f"AIDD run: work_item=WI-012 runtime={selected_runtime}" in result.stdout
    assert "Workflow run completed:" in result.stdout


def test_run_rejects_unsupported_runtime_with_nonzero_exit() -> None:
    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-013",
            "--runtime",
            "unsupported-runtime",
        ],
    )

    assert result.exit_code == 2, result.output
    assert "AIDD run: work_item=WI-013 runtime=unsupported-runtime" in result.stdout
    assert "Unsupported runtime 'unsupported-runtime' for workflow execution." in result.stdout
    assert "Failure classification: unsupported-runtime" in result.stdout


@pytest.mark.parametrize("selected_runtime", ("generic-cli", "claude-code", "codex", "opencode"))
def test_run_manifest_persists_runtime_specific_command_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selected_runtime: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_config(tmp_path)

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
        assert runtime == selected_runtime
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
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
            "WI-014",
            "--runtime",
            selected_runtime,
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    run_ids = sorted(
        path.name
        for path in work_item_runs_root(
            workspace_root=workspace_root,
            work_item="WI-014",
        ).iterdir()
    )
    assert run_ids
    manifest = json.loads(
        run_manifest_path(
            workspace_root=workspace_root,
            work_item="WI-014",
            run_id=run_ids[-1],
        ).read_text(encoding="utf-8")
    )
    assert manifest["runtime_id"] == selected_runtime
    assert manifest["config_snapshot"]["runtime_command"] == _RUNTIME_COMMANDS[selected_runtime]
