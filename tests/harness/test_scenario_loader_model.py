from __future__ import annotations

from pathlib import Path

from aidd.core.stages import STAGES
from aidd.harness.scenarios import load_scenario


def _assert_live_contract(scenario) -> None:
    assert scenario.is_live is True
    assert scenario.run.stage_start == STAGES[0]
    assert scenario.run.stage_end == STAGES[-1]
    assert scenario.feature_source is not None
    assert scenario.feature_source.mode == "curated-issue-pool"
    assert scenario.feature_source.selection_policy == "first-listed"
    assert scenario.feature_source.issues
    assert scenario.quality is not None
    assert scenario.quality.rubric_profile == "live-full"
    assert scenario.quality.code_review_required is True
    assert "ready" in scenario.quality.allowed_qa_verdicts
    assert "ready-with-risks" in scenario.quality.allowed_qa_verdicts


def test_live_scenario_exposes_full_flow_repo_steps_and_quality_contract() -> None:
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
    assert scenario.task.startswith("Run the installed AIDD full-flow live audit")
    assert scenario.setup.commands == (
        "uv sync --group tests || uv sync",
        "uv run pytest -q || pytest -q",
    )
    assert scenario.verify.commands == (
        "uv run pytest -q || pytest -q",
        "test -f .aidd/workitems/WI-LIVE-TYPER-SMOKE/stages/qa/output/stage-result.md",
        "test -f .aidd/workitems/WI-LIVE-TYPER-SMOKE/stages/qa/output/validator-report.md",
    )
    _assert_live_contract(scenario)
    first_issue = scenario.feature_source.issues[0]
    assert first_issue.issue_id == "1159"
    assert first_issue.title == "styled help alignment bugfix"
    assert first_issue.url == "https://github.com/fastapi/typer/issues/1159"
    assert "regression coverage" in first_issue.summary
    assert scenario.quality.commands == ("uv run pytest -q || pytest -q",)
    assert scenario.quality.require_review_status == "approved"


def test_all_live_scenarios_load_as_valid_full_flow_manifests() -> None:
    live_root = Path("harness/scenarios/live")
    scenario_files = sorted(live_root.glob("*.yaml"))
    assert scenario_files

    for scenario_file in scenario_files:
        scenario = load_scenario(scenario_file)
        assert scenario.scenario_id
        assert scenario.task
        _assert_live_contract(scenario)


def test_sqlite_utils_canonical_live_scenario_declares_installed_full_flow_bundle() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml")
    )

    assert scenario.scenario_id == "AIDD-LIVE-005"
    assert scenario.repo.url == "https://github.com/simonw/sqlite-utils"
    assert scenario.repo.default_branch == "main"
    assert scenario.repo.revision == "8d74ffc93292c604d5827e2b44fffedca0c28c19"
    _assert_live_contract(scenario)
    assert scenario.raw["operator_execution"] == {
        "install_channel": "uv-tool",
        "artifact_source": "local-wheel",
        "execution_cwd": "repository-root",
        "workspace_root": ".aidd",
        "resource_source": "packaged-assets",
    }
    assert scenario.raw["workflow_bundle"]["lane"] == "installed-live-full-flow-audit"
    assert "quality-report.md" in scenario.raw["workflow_bundle"]["required_artifacts"]
    assert scenario.runtime_targets == ("generic-cli", "codex", "opencode")


def test_sqlite_utils_interview_scenario_forces_blocking_question_conditions() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/live/sqlite-utils-yielded-rows-interview.yaml")
    )

    _assert_live_contract(scenario)
    assert scenario.scenario_id == "AIDD-LIVE-006"
    assert scenario.run.interview_required is True
    assert scenario.raw["interview"]["must_ask_at_least_one"] is True
    assert scenario.quality.require_review_status == "approved-with-conditions"
    assert scenario.feature_source.issues[0].issue_id == "694"
    assert scenario.raw["interview"]["blocking_question_topics"] == [
        "Execution trust boundary for user-provided Python code.",
        "Accepted input form (inline expression, file, or both).",
        "Required documentation updates and examples for the selected form.",
    ]
    assert (
        scenario.raw["interview"]["answer_flow"]["answers_file"]
        == ".aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/idea/answers.md"
    )
    assert scenario.verify.commands == (
        "uv run aidd stage questions idea --work-item WI-LIVE-SQLITE-INTERVIEW",
        "test -f .aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/idea/answers.md",
        "uv run pytest -q || pytest -q",
        "test -f .aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/qa/output/stage-result.md",
        "test -f .aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/qa/output/validator-report.md",
    )


def test_hono_interview_scenario_forces_blocking_question_conditions() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/hono-router-double-star-parity.yaml"))

    _assert_live_contract(scenario)
    assert scenario.scenario_id == "AIDD-LIVE-008"
    assert scenario.run.interview_required is True
    assert scenario.feature_source.issues[0].issue_id == "4633"
    assert scenario.quality.require_review_status == "approved-with-conditions"
    assert scenario.raw["interview"]["must_ask_at_least_one"] is True
    assert (
        scenario.raw["interview"]["answer_flow"]["answers_file"]
        == ".aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/idea/answers.md"
    )
    assert scenario.verify.commands == (
        "uv run aidd stage questions idea --work-item WI-LIVE-HONO-INTERVIEW",
        "test -f .aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/idea/answers.md",
        "bun test",
        "bunx tsc --noEmit",
        "test -f .aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/qa/output/stage-result.md",
        "test -f .aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/qa/output/validator-report.md",
    )


def test_smoke_plan_stagepack_scenario_declares_cross_runtime_output_checks() -> None:
    scenario = load_scenario(Path("harness/scenarios/smoke/plan-stagepack-smoke.yaml"))

    assert scenario.is_live is False
    assert scenario.scenario_id == "AIDD-STAGEPACK-PLAN-SMOKE-001"
    assert scenario.raw["aidd_invocation"]["command"] == ["uv", "run", "aidd", "run"]
    assert scenario.run.stage_start == "plan"
    assert scenario.run.stage_end == "plan"
    assert scenario.runtime_targets == (
        "generic-cli",
        "claude-code",
        "codex",
        "opencode",
    )
    assert scenario.verify.commands == (
        "test -f .aidd/workitems/WI-STAGE-PLAN-SMOKE/stages/plan/output/plan.md",
        "test -f .aidd/workitems/WI-STAGE-PLAN-SMOKE/stages/plan/output/stage-result.md",
        "test -f .aidd/workitems/WI-STAGE-PLAN-SMOKE/stages/plan/output/validator-report.md",
    )
