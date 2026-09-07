from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.core.run_store import (
    create_run_manifest,
    load_stage_metadata,
    persist_stage_status,
)

runner = CliRunner()


def _prepare_stage(workspace_root: Path, *, status: str = "executing") -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-CLI-RECONCILE",
        run_id="run-cli-reconcile",
        runtime_id="generic-cli",
        stage_target="idea",
        config_snapshot={"runtime_command": "runtime"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-CLI-RECONCILE",
        run_id="run-cli-reconcile",
        stage="idea",
        status=status,
    )


def _command(workspace_root: Path, *, expected_state: str = "executing") -> list[str]:
    return [
        "stage",
        "reconcile-terminal",
        "idea",
        "--work-item",
        "WI-CLI-RECONCILE",
        "--run-id",
        "run-cli-reconcile",
        "--expected-state",
        expected_state,
        "--reason",
        "provider-no-progress",
        "--root",
        workspace_root.as_posix(),
    ]


def test_stage_reconcile_terminal_cli_is_public_and_idempotent(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_stage(workspace_root)

    first = runner.invoke(app, _command(workspace_root))
    assert first.exit_code == 0
    payload = json.loads(first.stdout)
    assert payload["disposition"] == "reconciled"
    assert payload["reconciled"] is True
    metadata = load_stage_metadata(
        workspace_root,
        "WI-CLI-RECONCILE",
        "run-cli-reconcile",
        "idea",
    )
    assert metadata is not None
    assert [entry.status for entry in metadata.status_history] == ["executing", "failed"]
    metadata_path = Path(str(payload["metadata_path"]))
    evidence_path = Path(str(payload["evidence_path"]))
    stable_bytes = (metadata_path.read_bytes(), evidence_path.read_bytes())

    second = runner.invoke(app, _command(workspace_root))

    assert second.exit_code == 0
    assert json.loads(second.stdout) == payload
    assert (metadata_path.read_bytes(), evidence_path.read_bytes()) == stable_bytes


def test_stage_reconcile_terminal_cli_handles_validating_state(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_stage(workspace_root, status="validating")

    result = runner.invoke(
        app,
        _command(workspace_root, expected_state="validating"),
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["expected_state"] == "validating"
    assert payload["disposition"] == "reconciled"
    assert payload["reconciled"] is True
    metadata = load_stage_metadata(
        workspace_root,
        "WI-CLI-RECONCILE",
        "run-cli-reconcile",
        "idea",
    )
    assert metadata is not None
    assert [entry.status for entry in metadata.status_history] == [
        "validating",
        "failed",
    ]


def test_stage_reconcile_terminal_cli_rejects_terminal_expected_state(
    tmp_path: Path,
) -> None:
    command = _command(tmp_path / ".aidd")
    command[command.index("executing")] = "failed"

    result = runner.invoke(app, command)

    assert result.exit_code == 2
    assert "must be non-terminal" in result.stdout


def test_stage_reconcile_terminal_cli_rejects_non_inflight_expected_state(
    tmp_path: Path,
) -> None:
    command = _command(tmp_path / ".aidd", expected_state="preparing")

    result = runner.invoke(app, command)

    assert result.exit_code == 2
    assert "executing" in result.stdout
    assert "validating" in result.stdout
