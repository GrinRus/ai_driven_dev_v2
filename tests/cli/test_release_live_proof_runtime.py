from __future__ import annotations

import sys
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.core.contracts import repo_root_from
from aidd.harness.live_workspace_bootstrap import bootstrap_live_work_item
from aidd.harness.scenarios import load_scenario

runner = CliRunner()


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def test_release_live_proof_runtime_completes_generic_workflow(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = tmp_path / "aidd.release.toml"
    runtime_script = _repo_root() / "scripts" / "release_live_proof_runtime.py"
    scenario = load_scenario(
        _repo_root()
        / "harness"
        / "scenarios"
        / "live"
        / "sqlite-utils-detect-types-header-only.yaml",
        runtime_id="generic-cli",
        workspace_root=workspace_root,
    )
    bootstrap_live_work_item(
        working_copy_path=tmp_path,
        scenario=scenario,
        work_item="WI-RELEASE-LIVE-PROOF",
        selected_issue=scenario.feature_source.issues[0],
        resolved_revision="test-revision",
    )
    config_path.write_text(
        "\n".join(
            (
                "[workspace]",
                f'root = "{workspace_root.as_posix()}"',
                "",
                "[runtime.generic_cli]",
                f'command = "{sys.executable} {runtime_script.as_posix()}"',
                "",
                "[logging]",
                'mode = "both"',
                "",
                "[repair]",
                "max_attempts = 2",
                "",
            )
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            "--work-item",
            "WI-RELEASE-LIVE-PROOF",
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
    assert "Workflow run completed:" in result.stdout
    qa_output_root = (
        workspace_root
        / "workitems"
        / "WI-RELEASE-LIVE-PROOF"
        / "stages"
        / "qa"
        / "output"
    )
    assert (qa_output_root / "qa-report.md").exists()
    assert (qa_output_root / "stage-result.md").exists()
    assert (qa_output_root / "validator-report.md").exists()
