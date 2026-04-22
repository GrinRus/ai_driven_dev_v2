from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
)

runner = CliRunner()


def test_run_artifacts_lists_document_and_log_paths(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-777",
        run_id="run-777",
        runtime_id="claude-code",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-777",
        run_id="run-777",
        stage="plan",
    )

    result = runner.invoke(
        app,
        [
            "run",
            "artifacts",
            "--work-item",
            "WI-777",
            "--stage",
            "plan",
            "--root",
            str(workspace_root),
            "--run-id",
            "run-777",
            "--attempt",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert "Run artifacts: run_id=run-777 stage=plan attempt=1" in result.stdout
    assert "Document artifacts:" in result.stdout
    assert "Log artifacts:" in result.stdout
    assert "stage_result" in result.stdout
    assert "runtime_log" in result.stdout
    assert "workitems/WI-777/stages/plan/stage-result.md" in result.stdout
    assert (
        "reports/runs/WI-777/run-777/stages/plan/attempts/attempt-0001/runtime.log"
        in result.stdout
    )
