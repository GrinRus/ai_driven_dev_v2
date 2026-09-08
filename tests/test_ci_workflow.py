from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _ci_workflow() -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load(
        (repository_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    assert isinstance(workflow, dict)
    return workflow


def test_ci_build_is_a_required_upstream_result_gate() -> None:
    build_job = _ci_workflow()["jobs"]["build"]

    assert build_job["if"] == "${{ always() && !cancelled() }}"
    assert build_job["needs"] == [
        "lint-type-test",
        "critical-coverage",
        "adapter-conformance",
        "deterministic-scenarios",
        "packaged-ui-browser",
    ]

    gate_step = next(
        step for step in build_job["steps"] if step.get("name") == "Require upstream CI lanes"
    )
    assert gate_step["env"] == {
        "ADAPTER_CONFORMANCE_RESULT": "${{ needs.adapter-conformance.result }}",
        "CRITICAL_COVERAGE_RESULT": "${{ needs.critical-coverage.result }}",
        "DETERMINISTIC_SCENARIOS_RESULT": "${{ needs.deterministic-scenarios.result }}",
        "LINT_TYPE_TEST_RESULT": "${{ needs.lint-type-test.result }}",
        "PACKAGED_UI_BROWSER_RESULT": "${{ needs.packaged-ui-browser.result }}",
    }
    assert 'if [ "${result}" != "success" ]; then' in gate_step["run"]
    assert "exit 1" in gate_step["run"]


def test_ci_lint_lane_checks_byte_stable_traceability_view() -> None:
    lint_job = _ci_workflow()["jobs"]["lint-type-test"]

    traceability_step = next(
        step for step in lint_job["steps"] if step.get("name") == "User-story traceability view"
    )

    assert "scripts/generate_user_story_traceability.py --check" in traceability_step["run"]


def test_ci_lint_lane_enforces_formatter_baseline() -> None:
    lint_job = _ci_workflow()["jobs"]["lint-type-test"]

    format_step = next(step for step in lint_job["steps"] if step.get("name") == "Format")

    assert "ruff format --check ." in format_step["run"]


def test_ci_critical_coverage_lane_enforces_reviewed_module_baseline() -> None:
    workflow = _ci_workflow()
    coverage_job = workflow["jobs"]["critical-coverage"]

    assert coverage_job["needs"] == "lint-type-test"
    setup_python = next(
        step
        for step in coverage_job["steps"]
        if step.get("uses", "").startswith("actions/setup-python")
    )
    assert setup_python["with"]["python-version"] == "3.13"

    measure_step = next(
        step
        for step in coverage_job["steps"]
        if step.get("name") == "Measure critical module coverage"
    )
    assert "--cov-branch" in measure_step["run"]
    assert "--cov-report=json:coverage-critical.json" in measure_step["run"]
    assert "tests/core/test_task_attempt_lifecycle.py" in measure_step["run"]

    enforce_step = next(
        step
        for step in coverage_job["steps"]
        if step.get("name") == "Enforce critical coverage baseline"
    )
    assert "scripts/check_critical_coverage.py" in enforce_step["run"]
    assert "critical-coverage" in workflow["jobs"]["build"]["needs"]


def test_ci_lint_lane_enforces_complexity_baseline() -> None:
    lint_job = _ci_workflow()["jobs"]["lint-type-test"]

    complexity_step = next(
        step for step in lint_job["steps"] if step.get("name") == "Complexity baseline"
    )

    assert "scripts/check_complexity.py" in complexity_step["run"]
