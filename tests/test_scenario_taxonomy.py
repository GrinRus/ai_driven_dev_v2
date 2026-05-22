from __future__ import annotations

from pathlib import Path

import yaml

from aidd.core.contracts import repo_root_from
from aidd.harness.scenarios import Scenario, load_scenario


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _scenario_entries() -> list[tuple[Path, Scenario]]:
    scenario_root = _repo_root() / "harness" / "scenarios"
    return [
        (path, load_scenario(path))
        for path in sorted(scenario_root.rglob("*.yaml"))
        if path.is_file()
    ]


def test_all_scenarios_expose_required_taxonomy_metadata() -> None:
    entries = _scenario_entries()
    assert entries

    for path, scenario in entries:
        assert scenario.scenario_class
        assert scenario.feature_size
        assert scenario.automation_lane
        assert scenario.canonical_runtime
        assert scenario.canonical_runtime in scenario.runtime_targets, path.as_posix()
        assert scenario.feature_source is not None, path.as_posix()


def test_live_scenarios_are_manual_only() -> None:
    for path, scenario in _scenario_entries():
        if scenario.is_live:
            assert scenario.automation_lane == "manual", path.as_posix()
            assert scenario.scenario_class in {
                "live-full-flow",
                "live-full-flow-interview",
            }, path.as_posix()
            assert scenario.live_flow is not None, path.as_posix()
            assert scenario.live_flow.driver == "stepwise-black-box", path.as_posix()
            assert scenario.live_flow.checkpoint_policy == "after-each-step", path.as_posix()
            assert scenario.live_flow.frontend_checkpoints is True, path.as_posix()
            assert scenario.live_flow.answer_policy == "agent-decides", path.as_posix()


def test_live_scenarios_do_not_mask_setup_or_pytest_failures_with_shell_fallbacks() -> None:
    def _commands(section_name: str, scenario: Scenario) -> tuple[str, ...]:
        section = scenario.raw.get(section_name)
        if not isinstance(section, dict):
            return tuple()
        raw_commands = section.get("commands", [])
        if not isinstance(raw_commands, list):
            return tuple()
        return tuple(str(command) for command in raw_commands)

    for path, scenario in _scenario_entries():
        if not scenario.is_live:
            continue
        commands = (
            *_commands("setup", scenario),
            *_commands("verify", scenario),
            *_commands("quality", scenario),
        )
        assert all("||" not in command for command in commands), path.as_posix()


def test_ci_eligible_scenarios_are_deterministic_only() -> None:
    for path, scenario in _scenario_entries():
        if scenario.automation_lane == "ci":
            assert scenario.is_live is False, path.as_posix()
            assert scenario.scenario_class in {
                "deterministic-stage",
                "deterministic-workflow",
            }, path.as_posix()


def test_representative_matrix_buckets_exist_in_manifest_set() -> None:
    observed = {
        (scenario.scenario_class, scenario.feature_size, scenario.automation_lane)
        for _path, scenario in _scenario_entries()
    }
    required = {
        ("deterministic-stage", "small", "ci"),
        ("deterministic-workflow", "medium", "ci"),
        ("deterministic-workflow", "large", "manual"),
        ("live-full-flow", "tiny", "manual"),
        ("live-full-flow", "small", "manual"),
        ("live-full-flow", "medium", "manual"),
        ("live-full-flow-interview", "large", "manual"),
        ("live-full-flow-interview", "xlarge", "manual"),
    }
    assert required.issubset(observed)


def test_provider_rollout_policy_matches_manifest_set() -> None:
    entries = _scenario_entries()
    live = [scenario for _path, scenario in entries if scenario.is_live]
    deterministic = [scenario for _path, scenario in entries if not scenario.is_live]

    assert any(
        scenario.canonical_runtime == "generic-cli" for scenario in deterministic
    ), "Expected a generic-cli deterministic baseline scenario."
    assert any(
        scenario.scenario_class == "deterministic-workflow"
        and "opencode" in scenario.runtime_targets
        for scenario in deterministic
    ), "Expected an opencode deterministic workflow lane."
    assert any(
        "claude-code" in scenario.runtime_targets for scenario in deterministic
    ), "Expected at least one deterministic Claude Code lane."
    assert any(
        scenario.canonical_runtime == "codex" and scenario.feature_size == "small"
        for scenario in live
    ), "Expected a small live lane with codex as canonical runtime."
    assert any(
        scenario.canonical_runtime == "codex" and scenario.feature_size == "medium"
        for scenario in live
    ), "Expected a medium live lane with codex as canonical runtime."
    assert any(
        scenario.canonical_runtime == "opencode" for scenario in live
    ), "Expected at least one live opencode lane."
    assert all(
        "generic-cli" not in scenario.runtime_targets for scenario in live
    ), "Live rollout must remain off generic-cli in Wave 13."
    claude_live_targets = [
        scenario.scenario_id for scenario in live if "claude-code" in scenario.runtime_targets
    ]
    assert sorted(claude_live_targets) == [
        "AIDD-LIVE-005",
        "AIDD-LIVE-007",
    ], "Claude Code live rollout must include smoke plus planned medium coverage."


def test_hono_medium_live_scenario_uses_focused_verification_gate() -> None:
    entries = dict(_scenario_entries())
    scenario_path = (
        _repo_root() / "harness" / "scenarios" / "live" / "hono-non-error-throw-handling.yaml"
    )
    scenario = entries[scenario_path]

    focused_command = "./node_modules/.bin/vitest --run src/hono.test.ts src/compose.test.ts"
    assert focused_command in scenario.verify.commands
    assert focused_command in scenario.quality.commands
    assert "./node_modules/.bin/tsc --noEmit" in scenario.verify.commands
    assert "./node_modules/.bin/tsc --noEmit" in scenario.quality.commands
    assert "bun test" not in scenario.verify.commands
    assert "bun test" not in scenario.quality.commands
    assert "bunx vitest run src/hono.test.ts src/compose.test.ts" not in scenario.verify.commands
    task = scenario.feature_source.tasks[0]
    assert "without widening the public error handler" in task.target_change
    assert "preserves the existing public error type contracts" in task.quality_bar


def test_scenario_matrix_doc_mentions_all_representative_buckets() -> None:
    matrix_doc = (_repo_root() / "docs" / "e2e" / "scenario-matrix.md").read_text(
        encoding="utf-8"
    )

    for needle in (
        "AIDD-SMOKE-001",
        "AIDD-INSTALLED-LOCAL-001",
        "AIDD-DETERMINISTIC-001",
        "AIDD-DETERMINISTIC-002",
        "AIDD-LIVE-001",
        "AIDD-LIVE-004",
        "AIDD-LIVE-006",
        "live-full-flow-interview",
        "fixture-seed",
        "authored-task-pool",
        "`tiny`",
        "`xlarge`",
    ):
        assert needle in matrix_doc


def test_live_catalog_mentions_manual_matrix_coverage() -> None:
    catalog_doc = (_repo_root() / "docs" / "e2e" / "live-e2e-catalog.md").read_text(
        encoding="utf-8"
    )

    for needle in (
        "manual local operator audit evidence only",
        "Representative matrix coverage for the live lane",
        "`live-full-flow`",
        "`live-full-flow-interview`",
        "`codex`",
        "`opencode`",
        "AIDD_EVAL_CLAUDE_CODE_COMMAND",
        "AIDD_EVAL_CODEX_COMMAND",
        "AIDD_EVAL_OPENCODE_COMMAND",
        "AIDD_EVAL_PUBLISHED_PACKAGE_SPEC",
        "setup-blocked",
    ):
        assert needle in catalog_doc


def test_ci_workflow_does_not_reference_live_scenarios() -> None:
    ci_workflow = (_repo_root() / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "harness/scenarios/live/" not in ci_workflow
    assert "AIDD_EVAL_PUBLISHED_PACKAGE_SPEC" not in ci_workflow
    assert "verify-published-live-e2e" not in ci_workflow


def test_ci_python_matrix_matches_compatibility_window() -> None:
    workflow_path = _repo_root() / ".github" / "workflows" / "ci.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["lint-type-test"]["strategy"]["matrix"]

    assert matrix["python-version"] == ["3.12", "3.13", "3.14"]


def test_manual_live_github_actions_workflow_is_absent() -> None:
    workflow_path = _repo_root() / ".github" / "workflows" / "manual-live-e2e.yml"
    assert not workflow_path.exists()
