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
        ("live-full-flow", "small", "manual"),
        ("live-full-flow", "medium", "manual"),
        ("live-full-flow-interview", "large", "manual"),
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
    assert all(
        "claude-code" not in scenario.runtime_targets for scenario in live
    ), "Live rollout must remain off Claude Code in Wave 13."


def test_scenario_matrix_doc_mentions_all_representative_buckets() -> None:
    matrix_doc = (_repo_root() / "docs" / "e2e" / "scenario-matrix.md").read_text(
        encoding="utf-8"
    )

    for needle in (
        "AIDD-SMOKE-001",
        "AIDD-DETERMINISTIC-001",
        "AIDD-DETERMINISTIC-002",
        "AIDD-LIVE-001",
        "AIDD-LIVE-004",
        "AIDD-LIVE-006",
        "live-full-flow-interview",
        "fixture-seed",
        "curated-issue-pool",
    ):
        assert needle in matrix_doc


def test_live_catalog_mentions_manual_matrix_coverage() -> None:
    catalog_doc = (_repo_root() / "docs" / "e2e" / "live-e2e-catalog.md").read_text(
        encoding="utf-8"
    )

    for needle in (
        "manual external-audit lane only",
        "Representative matrix coverage for the live lane",
        "`live-full-flow`",
        "`live-full-flow-interview`",
        "`codex`",
        "`opencode`",
        "AIDD_EVAL_CODEX_COMMAND",
        "AIDD_EVAL_OPENCODE_COMMAND",
    ):
        assert needle in catalog_doc


def test_ci_workflow_does_not_reference_live_scenarios() -> None:
    ci_workflow = (_repo_root() / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "harness/scenarios/live/" not in ci_workflow
    assert "AIDD_EVAL_PUBLISHED_PACKAGE_SPEC" not in ci_workflow
    assert "verify-published-live-e2e" not in ci_workflow


def test_manual_live_workflow_dispatch_is_manual_only() -> None:
    workflow_path = _repo_root() / ".github" / "workflows" / "manual-live-e2e.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    trigger_block = workflow.get("on", workflow.get(True))
    assert isinstance(trigger_block, dict)
    assert set(trigger_block) == {"workflow_dispatch"}
    inputs = trigger_block["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"scenario_id", "runtime_id", "feature_size", "scenario_class"}
    assert inputs["runtime_id"]["options"] == ["codex", "opencode"]

    job_env = workflow["jobs"]["manual-live-e2e"]["env"]
    assert job_env["AIDD_EVAL_CODEX_COMMAND"] == "${{ secrets.AIDD_EVAL_CODEX_COMMAND }}"
    assert job_env["AIDD_EVAL_OPENCODE_COMMAND"] == "${{ secrets.AIDD_EVAL_OPENCODE_COMMAND }}"

    steps = workflow["jobs"]["manual-live-e2e"]["steps"]
    run_blocks = "\n".join(step.get("run", "") for step in steps if isinstance(step, dict))
    assert "harness/scenarios/live" in run_blocks
    assert 'scenario.automation_lane != "manual"' in run_blocks
    assert "uv run aidd eval run \"$SCENARIO_PATH\" --runtime" in run_blocks
    assert "validate_live_runtime_command" in run_blocks
    assert "Validated runtime readiness" in run_blocks
