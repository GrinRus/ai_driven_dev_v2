from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_SCENARIO = REPO_ROOT / "harness/scenarios/smoke/plan-stage-minimal-fixture.yaml"


def test_eval_execute_runs_full_deterministic_lifecycle(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"

    result = CliRunner().invoke(
        app,
        ["eval", "execute", SMOKE_SCENARIO.as_posix(), "--root", root.as_posix()],
    )

    assert result.exit_code == 0, result.output
    assert "Scenario: AIDD-SMOKE-001" in result.output
    assert "Status: pass" in result.output
    bundles = tuple((root / "reports/evals").glob("eval-*"))
    assert len(bundles) == 1
    bundle = bundles[0]
    assert (bundle / "setup-transcript.json").is_file()
    assert (bundle / "run-transcript.json").is_file()
    assert (bundle / "verify-transcript.json").is_file()
    assert (bundle / "teardown-transcript.json").is_file()
    assert (bundle / "verdict.md").is_file()
    metadata = json.loads((bundle / "harness-metadata.json").read_text(encoding="utf-8"))
    selection = json.loads((bundle / "feature-selection.json").read_text(encoding="utf-8"))
    assert metadata["evaluation_run_id"] == bundle.name
    assert metadata["product_run_id"]
    assert metadata["product_run_id"] != metadata["evaluation_run_id"]
    assert metadata["phase_metadata"]["status"] == "pass"
    assert metadata["phase_metadata"]["outcomes"]["execution"] == "succeeded"
    assert selection["evaluation_run_id"] == bundle.name
    assert selection["product_run_id"] == metadata["product_run_id"]
    assert selection["phase_metadata"]["terminal_phase"] == "teardown"


def test_eval_execute_rejects_live_scenario_before_creating_root(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    live_scenario = REPO_ROOT / "harness/scenarios/live/sqlite-yield-per-row.yaml"

    result = CliRunner().invoke(
        app,
        ["eval", "execute", live_scenario.as_posix(), "--root", root.as_posix()],
    )

    assert result.exit_code == 2
    assert not root.exists()
