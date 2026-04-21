from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.repair import (
    RepairBudgetPolicy,
    count_stage_attempts,
    default_repair_budget,
    effective_repair_budget,
    evaluate_stage_repair_counter,
    generate_repair_brief,
    parse_validator_report_findings,
    remaining_repair_attempts,
    render_repair_brief,
    repair_attempts_used,
    write_repair_brief,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.reports import render_validator_report


def _make_attempt_dir(root: Path, name: str) -> None:
    (root / name).mkdir(parents=True, exist_ok=True)


def test_default_repair_budget_is_two_attempts() -> None:
    assert default_repair_budget() == 2


def test_repair_budget_policy_validates_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        RepairBudgetPolicy(default_max_repair_attempts=-1)

    with pytest.raises(ValueError, match="Stage override key must not be empty"):
        RepairBudgetPolicy(stage_max_repair_attempts={"": 1})

    with pytest.raises(ValueError, match="non-negative"):
        RepairBudgetPolicy(stage_max_repair_attempts={"plan": -1})


def test_effective_repair_budget_uses_stage_override() -> None:
    policy = RepairBudgetPolicy(
        default_max_repair_attempts=2,
        stage_max_repair_attempts={"qa": 1},
    )

    assert effective_repair_budget(stage="plan", policy=policy) == 2
    assert effective_repair_budget(stage="qa", policy=policy) == 1


def test_count_stage_attempts_ignores_non_attempt_directories(tmp_path: Path) -> None:
    attempts_root = (
        tmp_path
        / ".aidd"
        / "reports"
        / "runs"
        / "WI-001"
        / "run-001"
        / "stages"
        / "plan"
        / "attempts"
    )
    _make_attempt_dir(attempts_root, "attempt-0001")
    _make_attempt_dir(attempts_root, "attempt-0002")
    _make_attempt_dir(attempts_root, "attempt-final")
    _make_attempt_dir(attempts_root, "misc")

    assert count_stage_attempts(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    ) == 2


def test_repair_attempts_used_treats_initial_attempt_as_non_repair() -> None:
    assert repair_attempts_used(stage_attempt_count=0) == 0
    assert repair_attempts_used(stage_attempt_count=1) == 0
    assert repair_attempts_used(stage_attempt_count=3) == 2


def test_remaining_repair_attempts_clamps_at_zero() -> None:
    assert remaining_repair_attempts(repair_attempts_used=0, max_repair_attempts=2) == 2
    assert remaining_repair_attempts(repair_attempts_used=2, max_repair_attempts=2) == 0
    assert remaining_repair_attempts(repair_attempts_used=4, max_repair_attempts=2) == 0


def test_evaluate_stage_repair_counter_reports_budget_state(tmp_path: Path) -> None:
    attempts_root = (
        tmp_path
        / ".aidd"
        / "reports"
        / "runs"
        / "WI-001"
        / "run-001"
        / "stages"
        / "plan"
        / "attempts"
    )
    _make_attempt_dir(attempts_root, "attempt-0001")
    _make_attempt_dir(attempts_root, "attempt-0002")
    _make_attempt_dir(attempts_root, "attempt-0003")

    counter = evaluate_stage_repair_counter(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        policy=RepairBudgetPolicy(default_max_repair_attempts=2),
    )

    assert counter.stage == "plan"
    assert counter.stage_attempt_count == 3
    assert counter.repair_attempts_used == 2
    assert counter.max_repair_attempts == 2
    assert counter.remaining_repair_attempts == 0
    assert counter.budget_exhausted is True


def test_parse_validator_report_findings_extracts_codes_and_locations() -> None:
    report_markdown = render_validator_report(
        findings=(
            ValidationFinding(
                code="STRUCT-MISSING-REQUIRED-DOCUMENT",
                message="Missing required document.",
                severity="critical",
                location=ValidationIssueLocation(
                    workspace_relative_path="workitems/WI-001/stages/plan/stage-result.md"
                ),
            ),
            ValidationFinding(
                code="SEM-PLACEHOLDER-CONTENT",
                message="Placeholder text remains in required section.",
                severity="medium",
                location=ValidationIssueLocation(
                    workspace_relative_path="workitems/WI-001/stages/plan/plan.md",
                    line_number=15,
                ),
            ),
        )
    )

    findings = parse_validator_report_findings(validator_report_markdown=report_markdown)

    assert len(findings) == 2
    assert findings[0].code == "STRUCT-MISSING-REQUIRED-DOCUMENT"
    assert findings[0].severity == "critical"
    assert findings[0].source_path == "workitems/WI-001/stages/plan/stage-result.md"
    assert findings[1].code == "SEM-PLACEHOLDER-CONTENT"
    assert findings[1].severity == "medium"
    assert findings[1].source_path == "workitems/WI-001/stages/plan/plan.md"


def test_render_repair_brief_includes_required_sections_and_budget_context(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    validator_report_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "validator-report.md"
    )
    report_markdown = render_validator_report(
        findings=(
            ValidationFinding(
                code="STRUCT-MISSING-REQUIRED-SECTION",
                message="Missing required section `Dependencies`.",
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path="workitems/WI-001/stages/plan/plan.md",
                ),
            ),
            ValidationFinding(
                code="CROSS-REFERENCE-MISMATCH",
                message="Stage result status conflicts with validator verdict.",
                severity="low",
                location=ValidationIssueLocation(
                    workspace_relative_path="workitems/WI-001/stages/plan/stage-result.md",
                ),
            ),
        )
    )

    repair_brief = render_repair_brief(
        validator_report_markdown=report_markdown,
        validator_report_path=validator_report_path,
        prior_stage_artifacts=(
            workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "questions.md",
            workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "answers.md",
            "workitems/WI-001/stages/research/output/research-notes.md",
        ),
        stage_attempt_count=1,
        max_repair_attempts=2,
        workspace_root=workspace_root,
    )

    assert "# Failed checks" in repair_brief
    assert "# Required corrections" in repair_brief
    assert "# Relevant upstream docs" in repair_brief
    assert (
        "- `STRUCT-MISSING-REQUIRED-SECTION` `high` in "
        "`workitems/WI-001/stages/plan/plan.md`" in repair_brief
    )
    assert (
        "- [`STRUCT-MISSING-REQUIRED-SECTION`] Update "
        "`workitems/WI-001/stages/plan/plan.md`" in repair_brief
    )
    assert "## Mandatory fixes" in repair_brief
    assert "## Optional quality improvements" in repair_brief
    assert "- `workitems/WI-001/stages/plan/validator-report.md`" in repair_brief
    assert "- `workitems/WI-001/stages/plan/questions.md`" in repair_brief
    assert "- `workitems/WI-001/stages/research/output/research-notes.md`" in repair_brief
    assert "attempt `2` of max `3`" in repair_brief
    assert "remaining retries after this attempt: `1`" in repair_brief
    assert "Repair budget status: `repair-budget-available`." in repair_brief


def test_render_repair_brief_marks_exhausted_budget() -> None:
    report_markdown = render_validator_report(
        findings=(
            ValidationFinding(
                code="SEM-PLACEHOLDER-CONTENT",
                message="Placeholder text remains in required section.",
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path="workitems/WI-001/stages/qa/qa-report.md",
                ),
            ),
        )
    )

    repair_brief = render_repair_brief(
        validator_report_markdown=report_markdown,
        validator_report_path="workitems/WI-001/stages/qa/validator-report.md",
        prior_stage_artifacts=(),
        stage_attempt_count=2,
        max_repair_attempts=2,
    )

    assert "remaining retries after this attempt: `0`" in repair_brief
    assert "Rerun allowed after this attempt: `no`." in repair_brief
    assert "Repair budget status: `repair-budget-exhausted`." in repair_brief


def test_generate_and_write_repair_brief_roundtrip(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    validator_report_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "validator-report.md"
    )
    validator_report_path.parent.mkdir(parents=True, exist_ok=True)
    validator_report_path.write_text(
        render_validator_report(
            findings=(
                ValidationFinding(
                    code="STRUCT-MISSING-REQUIRED-DOCUMENT",
                    message="Missing required document.",
                    severity="critical",
                    location=ValidationIssueLocation(
                        workspace_relative_path="workitems/WI-001/stages/plan/stage-result.md"
                    ),
                ),
            )
        ),
        encoding="utf-8",
    )

    repair_brief = generate_repair_brief(
        validator_report_path=validator_report_path,
        prior_stage_artifacts=(),
        stage_attempt_count=0,
        max_repair_attempts=2,
        workspace_root=workspace_root,
    )
    assert "attempt `1` of max `3`" in repair_brief

    brief_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "repair-brief.md"
    write_repair_brief(path=brief_path, repair_brief_markdown=repair_brief)

    assert brief_path.exists()
    assert "# Failed checks" in brief_path.read_text(encoding="utf-8")
