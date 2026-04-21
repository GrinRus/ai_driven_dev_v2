from __future__ import annotations

from pathlib import Path

from aidd.harness.scenarios import load_scenario


def test_live_scenario_loads() -> None:
    path = Path("harness/scenarios/live/typer-styled-help-alignment.yaml")
    scenario = load_scenario(path)
    assert scenario.scenario_id == "AIDD-LIVE-001"
    assert "generic-cli" in scenario.runtime_targets
