from __future__ import annotations

from pathlib import Path

from aidd.harness.scenarios import load_scenario


def test_live_scenario_exposes_repo_steps_and_run_config() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/typer-styled-help-alignment.yaml"))

    assert scenario.scenario_id == "AIDD-LIVE-001"
    assert scenario.repo.url == "https://github.com/fastapi/typer"
    assert scenario.repo.default_branch == "master"
    assert scenario.repo.revision == "9ce8e30383ef419c490431caab5a515eca669b1b"
    assert (
        scenario.raw["objective"]
        == "Keep Typer smoke lane deterministic by targeting the styled help alignment "
        "defect with bounded patch scope and regression coverage."
    )
    assert scenario.setup.commands == (
        "uv sync --group tests || uv sync",
        "uv run pytest -q || pytest -q",
    )
    assert scenario.raw["setup"]["rationale"] == [
        "Install Typer dependencies and test extras before the smoke run.",
        "Confirm a clean baseline test pass before AIDD applies changes.",
    ]
    assert scenario.raw["aidd_invocation"]["command"] == ["uv", "run", "aidd", "run"]
    assert scenario.raw["aidd_invocation"]["work_item"] == "WI-LIVE-TYPER-SMOKE"
    assert scenario.raw["aidd_invocation"]["work_item_flag"] == "--work-item"
    assert scenario.raw["aidd_invocation"]["runtime_flag"] == "--runtime"
    assert scenario.raw["aidd_invocation"]["expected_stage_scope"] == {
        "start": "plan",
        "end": "qa",
    }
    assert scenario.verify.commands == ("uv run pytest -q || pytest -q",)
    assert scenario.raw["verify"]["pass_conditions"] == [
        "Verification command exits with status 0.",
        "Pytest output reports all tests as passed.",
        "No new failing tests are introduced relative to baseline.",
    ]
    assert scenario.raw["reference_run"]["run_id"] == "eval-live-001-reference-20260422T081401Z"
    assert scenario.raw["reference_run"]["runtime"] == "generic-cli"
    assert scenario.raw["reference_run"]["status"] == "harness_fail"
    assert (
        scenario.raw["reference_run"]["resolved_revision"]
        == "9ce8e30383ef419c490431caab5a515eca669b1b"
    )
    assert (
        scenario.raw["reference_run"]["bundle_root"]
        == ".aidd/reports/evals/eval-live-001-reference-20260422T081401Z"
    )
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


def test_httpx_smoke_scenario_exposes_pinned_revision_and_objective() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/httpx-invalid-header-message.yaml"))

    assert scenario.scenario_id == "AIDD-LIVE-003"
    assert scenario.repo.url == "https://github.com/encode/httpx"
    assert scenario.repo.default_branch == "master"
    assert scenario.repo.revision == "b5addb64f0161ff6bfe94c124ef76f6a1fba5254"
    assert (
        scenario.raw["objective"]
        == "Keep HTTPX smoke lane deterministic by targeting the invalid-header "
        "diagnostics defect with bounded patch scope."
    )
    assert scenario.setup.commands == ("uv sync || pip install -e .[dev]",)
    assert scenario.raw["setup"]["rationale"] == [
        "Install HTTPX development dependencies before the smoke run.",
        "Confirm the repository environment is ready for targeted regression verification.",
    ]
    assert scenario.raw["aidd_invocation"]["command"] == ["uv", "run", "aidd", "run"]
    assert scenario.raw["aidd_invocation"]["work_item"] == "WI-LIVE-HTTPX-SMOKE"
    assert scenario.raw["aidd_invocation"]["work_item_flag"] == "--work-item"
    assert scenario.raw["aidd_invocation"]["runtime_flag"] == "--runtime"
    assert scenario.raw["aidd_invocation"]["expected_stage_scope"] == {
        "start": "plan",
        "end": "qa",
    }
