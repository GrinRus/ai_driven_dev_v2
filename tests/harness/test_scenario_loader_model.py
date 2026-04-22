from __future__ import annotations

from pathlib import Path

from aidd.harness.scenarios import load_scenario


def test_live_scenario_exposes_repo_steps_and_run_config() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/typer-styled-help-alignment.yaml"))

    assert scenario.scenario_id == "AIDD-LIVE-001"
    assert scenario.repo.url == "https://github.com/fastapi/typer"
    assert scenario.repo.default_branch == "master"
    assert scenario.setup.commands == (
        "uv sync --group tests || uv sync",
        "uv run pytest -q || pytest -q",
    )
    assert scenario.verify.commands == ("uv run pytest -q || pytest -q",)
    assert scenario.run.stage_start == "plan"
    assert scenario.run.stage_end == "qa"
    assert scenario.run.patch_budget_files == 8
    assert scenario.run.timeout_minutes == 20
    assert scenario.run.interview_required is False
    assert scenario.run.runtime_targets == ("claude-code", "generic-cli")


def test_all_live_scenarios_load_as_valid_manifests() -> None:
    live_root = Path("harness/scenarios/live")
    scenario_files = sorted(live_root.glob("*.yaml"))
    assert scenario_files

    for scenario_file in scenario_files:
        scenario = load_scenario(scenario_file)
        assert scenario.scenario_id
        assert scenario.task
