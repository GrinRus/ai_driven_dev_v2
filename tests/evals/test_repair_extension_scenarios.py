from __future__ import annotations

from pathlib import Path

import pytest

from aidd.evals.repair_extension_scenarios import (
    DEFAULT_REPAIR_EXTENSION_FIXTURE_ROOT,
    RepairExtensionScenarioError,
    load_repair_extension_scenarios,
    run_repair_extension_scenarios,
)


def test_repair_extension_manifest_covers_all_terminal_paths() -> None:
    suite_id, definitions = load_repair_extension_scenarios()

    assert suite_id == "w43-e5-s1-t2-repair-extension-v1"
    assert [item.scenario_id for item in definitions] == [
        "extension-success",
        "extension-repeated-failure",
        "manual-fix-prevalidation",
        "stale-evidence",
        "downstream-success",
        "second-grant",
        "request-change-separation",
        "immutable-history",
    ]
    assert DEFAULT_REPAIR_EXTENSION_FIXTURE_ROOT.is_dir()


def test_repair_extension_scenarios_preserve_grant_history_budget_and_lineage() -> None:
    report = run_repair_extension_scenarios()

    assert report.all_passed is True
    assert len(report.scenarios) == 8
    for scenario in report.scenarios:
        assert scenario.passed is True
        assert scenario.grant_count <= 1
        assert scenario.automatic_repair_attempts_used == 2
        assert scenario.automatic_repair_attempts_max == 2
        assert scenario.automatic_loop_scheduled is False
        assert scenario.downstream_artifacts_unchanged is True
        assert scenario.report_lineage
        assert scenario.raw_evidence
        assert scenario.semantic_omissions == ()


def test_repair_extension_success_and_failure_keep_distinct_attempt_modes() -> None:
    report = run_repair_extension_scenarios()
    success = next(item for item in report.scenarios if item.scenario_id == "extension-success")
    failure = next(
        item for item in report.scenarios if item.scenario_id == "extension-repeated-failure"
    )

    assert success.action == "reopened"
    assert success.terminal_state == "succeeded"
    assert success.attempt_modes == ("initial", "repair", "repair", "repair-extension")
    assert success.repair_history_triggers[-1] == "repair-extension"
    assert failure.terminal_state == "failed"
    assert failure.attempt_modes == ("initial", "repair", "repair", "repair-extension")
    assert failure.repair_history_triggers[-1] == "repair-extension"


def test_grant_evidence_is_exact_and_durable_for_success() -> None:
    report = run_repair_extension_scenarios()
    scenario = next(item for item in report.scenarios if item.scenario_id == "extension-success")
    grant = scenario.grant_content

    assert grant is not None
    assert grant["work_item_id"] == "WI-REPAIR-EXTENSION"
    assert grant["run_id"] == "run-repair-extension"
    assert grant["stage"] == "plan"
    assert grant["configuration_identity"] == "fixture:repair-extension-v1"
    assert len(str(grant["validator_report_sha256"])) == 64
    assert len(str(grant["repair_brief_sha256"])) == 64
    assert scenario.grant_count == 1


@pytest.mark.parametrize(
    ("scenario_id", "reason"),
    (
        ("stale-evidence", "stale"),
        ("downstream-success", "downstream"),
        ("second-grant", "already used"),
    ),
)
def test_blocked_repair_extension_paths_keep_literal_disabled_reasons(
    scenario_id: str,
    reason: str,
) -> None:
    report = run_repair_extension_scenarios()
    scenario = next(item for item in report.scenarios if item.scenario_id == scenario_id)

    assert scenario.action == "blocked"
    assert reason in (scenario.disabled_reason or "").lower()
    assert scenario.grant_count <= 1


def test_request_change_remains_a_distinct_operator_action() -> None:
    report = run_repair_extension_scenarios()
    scenario = next(
        item for item in report.scenarios if item.scenario_id == "request-change-separation"
    )

    assert scenario.request_change_separate is True
    assert scenario.action == "blocked"


def test_immutable_history_scenario_retains_prior_attempts() -> None:
    report = run_repair_extension_scenarios()
    scenario = next(item for item in report.scenarios if item.scenario_id == "immutable-history")

    assert scenario.immutable_history is True
    assert scenario.repair_history_triggers[:3] == ("initial", "repair", "repair")
    assert scenario.repair_history_triggers[-1] == "repair-extension"


def test_repair_extension_manifest_rejects_duplicate_ids(tmp_path: Path) -> None:
    root = tmp_path / "fixtures"
    root.mkdir()
    (root / "repair-extension-scenarios.json").write_text(
        '{"schema_version": 1, "suite_id": "xx", '
        '"source": {"credentials_removed": true}, '
        '"scenarios": [{"scenario_id": "duplicate", "expected_action": "blocked", '
        '"expected_terminal": "failed"}, {"scenario_id": "duplicate", '
        '"expected_action": "blocked", "expected_terminal": "failed"}]}',
        encoding="utf-8",
    )

    with pytest.raises(RepairExtensionScenarioError, match="unique"):
        load_repair_extension_scenarios(root)
