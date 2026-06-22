from __future__ import annotations

from pathlib import Path

from aidd.harness.scenarios import load_scenario


def test_live_scenario_loads() -> None:
    path = Path("harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml")
    scenario = load_scenario(path)
    assert scenario.scenario_id == "AIDD-LIVE-005"
    assert scenario.scenario_class == "live-full-flow"
    assert scenario.feature_size == "small"
    assert scenario.live_matrix_role == "flow-regression"
    assert scenario.automation_lane == "manual"
    assert scenario.canonical_runtime == "codex"
    assert "codex" in scenario.runtime_targets
