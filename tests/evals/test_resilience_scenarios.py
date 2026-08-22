from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aidd.evals.resilience_scenarios import (
    DEFAULT_RESILIENCE_FIXTURE_ROOT,
    ResilienceScenarioError,
    load_resilience_scenarios,
    run_provider_free_resilience_scenarios,
    validate_resilience_result,
)


def test_resilience_manifest_covers_the_provider_free_scope() -> None:
    suite_id, definitions = load_resilience_scenarios()

    assert suite_id == "w43-e5-s1-t1-provider-free-resilience-v1"
    assert [definition.scenario_id for definition in definitions] == [
        "ownership-missing-runtime-draft",
        "ownership-contradictory-runtime-draft",
        "service-placeholder-content",
        "interview-resume-malformed-question",
        "interview-safe-question-variant",
        "tasklist-safe-presentation",
        "tasklist-eleven-malformed-cards",
        "tasklist-one-malformed-card",
        "tasklist-root-cause-repair",
        "interview-resume-non-repair-accounting",
    ]
    assert DEFAULT_RESILIENCE_FIXTURE_ROOT.is_dir()


def test_provider_free_resilience_suite_retains_lifecycle_and_raw_evidence() -> None:
    report = run_provider_free_resilience_scenarios()

    assert report.all_passed is True
    assert len(report.scenarios) == 10
    for scenario in report.scenarios:
        assert scenario.terminal_state
        assert scenario.attempt_modes
        assert (
            scenario.automatic_repair_budget["consumed"]
            <= scenario.automatic_repair_budget["max"]
        )
        assert scenario.canonical_records
        assert scenario.workflow_records
        assert scenario.raw_evidence
        assert scenario.semantic_omissions == ()


@pytest.mark.parametrize(
    ("scenario_id", "expected_issue_count", "expected_terminal"),
    (
        ("tasklist-eleven-malformed-cards", 11, "blocked"),
        ("tasklist-one-malformed-card", 1, "blocked"),
        ("interview-resume-malformed-question", 1, "blocked"),
    ),
)
def test_malformed_inputs_preserve_locations_and_fail_closed(
    scenario_id: str,
    expected_issue_count: int,
    expected_terminal: str,
) -> None:
    report = run_provider_free_resilience_scenarios()
    scenario = next(item for item in report.scenarios if item.scenario_id == scenario_id)

    assert scenario.parse_issue_count == expected_issue_count
    assert scenario.terminal_state == expected_terminal
    assert scenario.root_findings
    assert scenario.raw_evidence
    assert scenario.passed is True


def test_safe_variants_do_not_change_executable_meaning() -> None:
    report = run_provider_free_resilience_scenarios()

    for scenario_id in ("interview-safe-question-variant", "tasklist-safe-presentation"):
        scenario = next(item for item in report.scenarios if item.scenario_id == scenario_id)
        assert scenario.terminal_state.startswith("ready")
        assert scenario.root_findings == ()
        assert scenario.observed_signals == ()


def test_result_validation_rejects_missing_raw_evidence_instead_of_inferencing_it() -> None:
    suite_id, definitions = load_resilience_scenarios()
    del suite_id
    report = run_provider_free_resilience_scenarios()
    result = report.scenarios[0]
    definition = definitions[0]

    incomplete = replace(result, raw_evidence=())

    assert "raw_evidence" in validate_resilience_result(incomplete, definition)


def test_manifest_rejects_fixture_path_escape(tmp_path: Path) -> None:
    root = tmp_path / "fixtures"
    root.mkdir()
    (root / "resilience-scenarios.json").write_text(
        '{"schema_version": 1, "suite_id": "xx", '
        '"source": {"credentials_removed": true}, '
        '"scenarios": [{"scenario_id": "xx", "category": "x", "stage": "plan", '
        '"terminal_state": "blocked", "attempt_modes": ["initial"], '
        '"automatic_repair_budget": {"max": 0, "consumed": 0}, '
        '"canonical_records": ["x"], "workflow_records": ["x"], '
        '"expected_root_findings": ["x"], "required_evidence": ["../outside"], '
        '"fixtures": ["../outside"]}]}',
        encoding="utf-8",
    )

    with pytest.raises(ResilienceScenarioError, match="missing or escapes"):
        load_resilience_scenarios(root)
