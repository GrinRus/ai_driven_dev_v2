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
    assert scenario.raw["verify"]["pass_conditions"] == [
        "Verification command exits with status 0.",
        "Pytest output reports all tests as passed.",
        "No new failing tests are introduced relative to baseline.",
    ]
    assert scenario.raw["reference_run"]["run_id"] == "eval-live-003-reference-20260422T083406Z"
    assert scenario.raw["reference_run"]["runtime"] == "generic-cli"
    assert scenario.raw["reference_run"]["status"] == "harness_fail"
    assert (
        scenario.raw["reference_run"]["resolved_revision"]
        == "b5addb64f0161ff6bfe94c124ef76f6a1fba5254"
    )
    assert (
        scenario.raw["reference_run"]["bundle_root"]
        == ".aidd/reports/evals/eval-live-003-reference-20260422T083406Z"
    )


def test_sqlite_utils_smoke_scenario_exposes_pinned_revision_and_objective() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml")
    )

    assert scenario.scenario_id == "AIDD-LIVE-005"
    assert scenario.repo.url == "https://github.com/simonw/sqlite-utils"
    assert scenario.repo.default_branch == "main"
    assert scenario.repo.revision == "8d74ffc93292c604d5827e2b44fffedca0c28c19"
    assert (
        scenario.raw["objective"]
        == "Keep sqlite-utils smoke lane deterministic by targeting the header-only "
        "detect-types crash with bounded patch scope."
    )
    assert scenario.setup.commands == ("uv sync || pip install -e .[dev]",)
    assert scenario.raw["setup"]["rationale"] == [
        "Install sqlite-utils development dependencies before the smoke run.",
        "Confirm the repository environment is ready for targeted regression verification.",
    ]
    assert scenario.raw["aidd_invocation"]["command"] == ["uv", "run", "aidd", "run"]
    assert scenario.raw["aidd_invocation"]["work_item"] == "WI-LIVE-SQLITE-SMOKE"
    assert scenario.raw["aidd_invocation"]["work_item_flag"] == "--work-item"
    assert scenario.raw["aidd_invocation"]["runtime_flag"] == "--runtime"
    assert scenario.raw["aidd_invocation"]["expected_stage_scope"] == {
        "start": "plan",
        "end": "qa",
    }
    assert scenario.raw["verify"]["pass_conditions"] == [
        "Verification command exits with status 0.",
        "Pytest output reports all tests as passed.",
        "No new failing tests are introduced relative to baseline.",
    ]
    assert scenario.raw["reference_run"]["run_id"] == "eval-live-005-reference-20260422T090823Z"
    assert scenario.raw["reference_run"]["runtime"] == "generic-cli"
    assert scenario.raw["reference_run"]["status"] == "harness_pass"
    assert (
        scenario.raw["reference_run"]["resolved_revision"]
        == "8d74ffc93292c604d5827e2b44fffedca0c28c19"
    )
    assert (
        scenario.raw["reference_run"]["bundle_root"]
        == ".aidd/reports/evals/eval-live-005-reference-20260422T090823Z"
    )


def test_hono_smoke_scenario_exposes_pinned_revision_and_objective() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/hono-non-error-throw-handling.yaml"))

    assert scenario.scenario_id == "AIDD-LIVE-007"
    assert scenario.repo.url == "https://github.com/honojs/hono"
    assert scenario.repo.default_branch == "main"
    assert scenario.repo.revision == "cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba"
    assert (
        scenario.raw["objective"]
        == "Keep Hono smoke lane deterministic by targeting the non-Error throw "
        "handling defect with bounded patch scope."
    )
    assert scenario.setup.commands == ("bun install",)
    assert scenario.raw["setup"]["rationale"] == [
        "Install Hono development dependencies with Bun before the smoke run.",
        "Confirm the repository workspace is ready for targeted middleware regression "
        "verification.",
    ]
    assert scenario.raw["aidd_invocation"]["command"] == ["uv", "run", "aidd", "run"]
    assert scenario.raw["aidd_invocation"]["work_item"] == "WI-LIVE-HONO-SMOKE"
    assert scenario.raw["aidd_invocation"]["work_item_flag"] == "--work-item"
    assert scenario.raw["aidd_invocation"]["runtime_flag"] == "--runtime"
    assert scenario.raw["aidd_invocation"]["expected_stage_scope"] == {
        "start": "plan",
        "end": "qa",
    }
    assert scenario.raw["verify"]["pass_conditions"] == [
        "Verification commands exit with status 0.",
        "Bun test run reports no failing tests.",
        "TypeScript compile check reports no type errors.",
    ]
    assert scenario.raw["reference_run"]["run_id"] == "eval-live-007-reference-20260422T092510Z"
    assert scenario.raw["reference_run"]["runtime"] == "generic-cli"
    assert scenario.raw["reference_run"]["status"] == "harness_fail"
    assert (
        scenario.raw["reference_run"]["resolved_revision"]
        == "cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba"
    )
    assert (
        scenario.raw["reference_run"]["bundle_root"]
        == ".aidd/reports/evals/eval-live-007-reference-20260422T092510Z"
    )


def test_sqlite_utils_interview_scenario_forces_blocking_question_conditions() -> None:
    scenario = load_scenario(
        Path("harness/scenarios/live/sqlite-utils-yielded-rows-interview.yaml")
    )

    assert scenario.scenario_id == "AIDD-LIVE-006"
    assert scenario.run.interview_required is True
    assert scenario.raw["interview"]["must_ask_at_least_one"] is True
    assert scenario.raw["interview"]["blocking_question_topics"] == [
        "Execution trust boundary for user-provided Python code.",
        "Accepted input form (inline expression, file, or both).",
        "Required documentation updates and examples for the selected form.",
    ]
    assert scenario.raw["interview"]["trigger_conditions"] == [
        "If code execution policy is not explicitly stated, ask a blocking question before "
        "planning.",
        "If accepted input forms are ambiguous, ask a blocking question before task decomposition.",
        "If documentation obligations are unclear, ask a blocking question before implementation.",
    ]
    assert scenario.raw["interview"]["answer_flow"]["mode"] == "answers_markdown_and_stage_rerun"
    assert (
        scenario.raw["interview"]["answer_flow"]["answers_file"]
        == ".aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/idea/answers.md"
    )
    assert scenario.raw["interview"]["answer_flow"]["question_check_command"] == [
        "uv",
        "run",
        "aidd",
        "stage",
        "questions",
        "idea",
        "--work-item",
        "WI-LIVE-SQLITE-INTERVIEW",
    ]
    assert scenario.raw["interview"]["answer_flow"]["resume_command"] == [
        "uv",
        "run",
        "aidd",
        "stage",
        "run",
        "idea",
        "--work-item",
        "WI-LIVE-SQLITE-INTERVIEW",
        "--runtime",
        "generic-cli",
    ]
    assert scenario.verify.commands == (
        "uv run aidd stage questions idea --work-item WI-LIVE-SQLITE-INTERVIEW",
        "test -f .aidd/workitems/WI-LIVE-SQLITE-INTERVIEW/stages/idea/answers.md",
        "uv run pytest -q || pytest -q",
    )
    assert scenario.raw["verify"]["pass_conditions"] == [
        "The first stage-questions check reports at least one pending blocking question.",
        "Answers file resolves each blocking question before stage rerun.",
        "Final verification command exits with status 0 after resume.",
    ]
    assert scenario.raw["verify"]["flow_steps"] == [
        {
            "step": "blocked",
            "evidence": "questions.md exists with at least one blocking question id.",
        },
        {
            "step": "resumed",
            "evidence": "answers.md exists and marks each blocking question as resolved.",
        },
        {
            "step": "completed",
            "evidence": "verification command succeeds after the resolved-answer rerun.",
        },
    ]
    assert scenario.raw["reference_run"]["run_id"] == "eval-live-006-reference-20260422T084432Z"
    assert scenario.raw["reference_run"]["runtime"] == "generic-cli"
    assert scenario.raw["reference_run"]["status"] == "harness_fail"
    assert (
        scenario.raw["reference_run"]["resolved_revision"]
        == "8d74ffc93292c604d5827e2b44fffedca0c28c19"
    )
    assert (
        scenario.raw["reference_run"]["bundle_root"]
        == ".aidd/reports/evals/eval-live-006-reference-20260422T084432Z"
    )


def test_hono_interview_scenario_forces_blocking_question_conditions() -> None:
    scenario = load_scenario(Path("harness/scenarios/live/hono-router-double-star-parity.yaml"))

    assert scenario.scenario_id == "AIDD-LIVE-008"
    assert scenario.run.interview_required is True
    assert scenario.raw["interview"]["must_ask_at_least_one"] is True
    assert scenario.raw["interview"]["blocking_question_topics"] == [
        "Expected `/**` behavior relative to existing wildcard routing semantics.",
        "Whether router parity should be implemented or explicitly documented as an "
        "intentional divergence.",
        "Required compatibility notes and release-facing documentation updates for the "
        "chosen behavior.",
    ]
    assert scenario.raw["interview"]["trigger_conditions"] == [
        "If expected `/**` matching behavior is not explicitly defined, ask a blocking "
        "question before planning.",
        "If parity-vs-divergence decision is ambiguous, ask a blocking question before "
        "task decomposition.",
        "If documentation and compatibility obligations are unclear, ask a blocking "
        "question before implementation.",
    ]
    assert scenario.raw["interview"]["answer_flow"]["mode"] == "answers_markdown_and_stage_rerun"
    assert (
        scenario.raw["interview"]["answer_flow"]["answers_file"]
        == ".aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/idea/answers.md"
    )
    assert scenario.raw["interview"]["answer_flow"]["question_check_command"] == [
        "uv",
        "run",
        "aidd",
        "stage",
        "questions",
        "idea",
        "--work-item",
        "WI-LIVE-HONO-INTERVIEW",
    ]
    assert scenario.raw["interview"]["answer_flow"]["resume_command"] == [
        "uv",
        "run",
        "aidd",
        "stage",
        "run",
        "idea",
        "--work-item",
        "WI-LIVE-HONO-INTERVIEW",
        "--runtime",
        "generic-cli",
    ]
    assert scenario.verify.commands == (
        "uv run aidd stage questions idea --work-item WI-LIVE-HONO-INTERVIEW",
        "test -f .aidd/workitems/WI-LIVE-HONO-INTERVIEW/stages/idea/answers.md",
        "bun test",
        "bunx tsc --noEmit",
    )
    assert scenario.raw["verify"]["pass_conditions"] == [
        "The first stage-questions check reports at least one pending blocking question.",
        "Answers file resolves each blocking question before stage rerun.",
        "Verification commands exit with status 0 after resume.",
    ]
    assert scenario.raw["verify"]["flow_steps"] == [
        {
            "step": "blocked",
            "evidence": "questions.md exists with at least one blocking question id.",
        },
        {
            "step": "resumed",
            "evidence": "answers.md exists and marks each blocking question as resolved.",
        },
        {
            "step": "completed",
            "evidence": "verification commands succeed after the resolved-answer rerun.",
        },
    ]
    assert scenario.raw["reference_run"]["run_id"] == "eval-live-008-reference-20260422T094912Z"
    assert scenario.raw["reference_run"]["runtime"] == "generic-cli"
    assert scenario.raw["reference_run"]["status"] == "harness_fail"
    assert (
        scenario.raw["reference_run"]["resolved_revision"]
        == "cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba"
    )
    assert (
        scenario.raw["reference_run"]["bundle_root"]
        == ".aidd/reports/evals/eval-live-008-reference-20260422T094912Z"
    )
