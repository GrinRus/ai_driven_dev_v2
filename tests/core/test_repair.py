from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.models.run import RepairHistoryEntry
from aidd.core.repair import (
    RepairBudgetPolicy,
    count_stage_attempts,
    default_repair_budget,
    effective_repair_budget,
    evaluate_stage_repair_counter,
    generate_repair_brief,
    parse_validator_report_findings,
    persist_repair_history_snapshot,
    remaining_repair_attempts,
    render_repair_brief,
    render_stage_result_with_repair_history,
    repair_attempts_used,
    write_repair_brief,
)
from aidd.core.run_store import create_run_manifest, load_stage_metadata, persist_stage_status
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


def test_render_repair_brief_adds_actionable_list_format_hint() -> None:
    report_markdown = render_validator_report(
        findings=(
            ValidationFinding(
                code="SEM-INCOMPLETE-SECTION",
                message=(
                    "Required section `Open questions` must use bullet items "
                    "(or `- none`) so downstream stages can parse constraints "
                    "and open questions deterministically."
                ),
                severity="medium",
                location=ValidationIssueLocation(
                    workspace_relative_path=(
                        "workitems/WI-001/stages/idea/idea-brief.md"
                    ),
                    line_number=20,
                ),
            ),
        )
    )

    repair_brief = render_repair_brief(
        validator_report_markdown=report_markdown,
        validator_report_path="workitems/WI-001/stages/idea/validator-report.md",
        prior_stage_artifacts=(),
        stage_attempt_count=2,
        max_repair_attempts=2,
    )

    assert "Required section `Open questions` must use bullet items" in repair_brief
    assert "Render the section as top-level Markdown bullet items" in repair_brief
    assert "write exactly `- none`" in repair_brief


def test_render_repair_brief_adds_interview_document_answer_hint() -> None:
    report_markdown = render_validator_report(
        findings=(
            ValidationFinding(
                code="INTERVIEW-MALFORMED-DOCUMENT",
                message=(
                    "Malformed interview document `answers.md`: Invalid answer entry "
                    "at line 3: expected `- <QID> [resolved|partial|deferred] <text>`."
                ),
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path="workitems/WI-001/stages/plan/answers.md",
                    line_number=3,
                ),
            ),
        )
    )

    repair_brief = render_repair_brief(
        validator_report_markdown=report_markdown,
        validator_report_path="workitems/WI-001/stages/plan/validator-report.md",
        prior_stage_artifacts=("workitems/WI-001/stages/plan/answers.md",),
        stage_attempt_count=2,
        max_repair_attempts=2,
    )

    assert "`- Q1 [resolved]: text`" in repair_brief
    assert "`- Q1 [resolved] text`" in repair_brief
    assert "`- Q1: [resolved] text`" in repair_brief
    assert "`A1` answer ids" in repair_brief
    assert "write exactly `- none`" in repair_brief


def test_render_repair_brief_adds_interview_document_question_hint() -> None:
    report_markdown = render_validator_report(
        findings=(
            ValidationFinding(
                code="INTERVIEW-MALFORMED-DOCUMENT",
                message=(
                    "Malformed interview document `questions.md`: Invalid question entry "
                    "at line 4: expected `- <QID> [blocking|non-blocking] <text>`."
                ),
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path="workitems/WI-001/stages/plan/questions.md",
                    line_number=4,
                ),
            ),
        )
    )

    repair_brief = render_repair_brief(
        validator_report_markdown=report_markdown,
        validator_report_path="workitems/WI-001/stages/plan/validator-report.md",
        prior_stage_artifacts=("workitems/WI-001/stages/plan/questions.md",),
        stage_attempt_count=1,
        max_repair_attempts=2,
    )

    assert "`- Q1 [blocking] text`" in repair_brief
    assert "`- Q1 [non-blocking] text`" in repair_brief
    assert "non-bullet continuation prose" in repair_brief
    assert "nested bullets" in repair_brief


def test_render_repair_brief_adds_review_evidence_reference_hint() -> None:
    report_markdown = render_validator_report(
        findings=(
            ValidationFinding(
                code="SEM-UNSUPPORTED-CLAIM",
                message=(
                    "Finding is missing evidence reference to implementation output "
                    "or acceptance criteria."
                ),
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path=(
                        "workitems/WI-001/stages/review/review-report.md"
                    ),
                    line_number=9,
                ),
            ),
        )
    )

    repair_brief = render_repair_brief(
        validator_report_markdown=report_markdown,
        validator_report_path="workitems/WI-001/stages/review/validator-report.md",
        prior_stage_artifacts=(
            "workitems/WI-001/stages/implement/output/implementation-report.md",
            "workitems/WI-001/context/acceptance-criteria.md",
        ),
        stage_attempt_count=2,
        max_repair_attempts=2,
    )

    assert "Finding is missing evidence reference" in repair_brief
    assert "Add an explicit `Evidence:` line" in repair_brief
    assert "`implementation-report.md`" in repair_brief
    assert "acceptance-criteria id such as `AC-1`" in repair_brief
    assert "remove or mark the finding `invalid`" in repair_brief


def test_render_repair_brief_adds_review_workspace_hygiene_hint() -> None:
    report_markdown = render_validator_report(
        findings=(
            ValidationFinding(
                code="SEM-UNVERIFIABLE-CHECK-CLAIM",
                message=(
                    "Live review cannot declare approved/no findings or cleanup passed "
                    "while non-baseline ignored workspace residue exists after review: "
                    "coverage/raw/default."
                ),
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path=(
                        "workitems/WI-001/stages/review/review-report.md"
                    ),
                    line_number=7,
                ),
            ),
        )
    )

    repair_brief = render_repair_brief(
        validator_report_markdown=report_markdown,
        validator_report_path="workitems/WI-001/stages/review/validator-report.md",
        prior_stage_artifacts=("workitems/WI-001/stages/review/review-report.md",),
        stage_attempt_count=1,
        max_repair_attempts=2,
    )

    assert "Check ignored residue after all review commands" in repair_brief
    assert "post-cleanup evidence" in repair_brief
    assert "active `RV-*` finding" in repair_brief
    assert "Do not write `Findings: none` while residue exists" in repair_brief


def test_render_repair_brief_marks_final_repair_attempt() -> None:
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
    assert "Repair budget status: `repair-budget-final-attempt`." in repair_brief
    assert "repair-budget-exhausted" not in repair_brief


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


def test_render_stage_result_with_repair_history_includes_attempt_lines() -> None:
    stage_result = render_stage_result_with_repair_history(
        stage="review",
        work_item="WI-001",
        status="failed",
        repair_history=(
            RepairHistoryEntry(
                attempt_number=1,
                trigger="initial",
                outcome="failed validation",
                recorded_at_utc="2026-04-22T10:00:00Z",
                validator_report_path="workitems/WI-001/stages/review/validator-report.md",
            ),
            RepairHistoryEntry(
                attempt_number=2,
                trigger="repair",
                outcome="failed validation",
                recorded_at_utc="2026-04-22T10:05:00Z",
                validator_report_path="workitems/WI-001/stages/review/validator-report.md",
                repair_brief_path="workitems/WI-001/stages/review/repair-brief.md",
            ),
        ),
        validator_report_path="workitems/WI-001/stages/review/validator-report.md",
        repair_brief_path="workitems/WI-001/stages/review/repair-brief.md",
    )

    assert "## Attempt history" in stage_result
    assert "- Attempt `1` (`initial`) -> failed validation." in stage_result
    assert "- Attempt `2` (`repair`) -> failed validation." in stage_result
    assert "`workitems/WI-001/stages/review/repair-brief.md`" in stage_result


def test_persist_repair_history_snapshot_updates_metadata_and_stage_result(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status="repair-needed",
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    validator_report_path = stage_root / "validator-report.md"
    repair_brief_path = stage_root / "repair-brief.md"
    stage_root.mkdir(parents=True, exist_ok=True)
    validator_report_path.write_text("# Validator Report\n", encoding="utf-8")
    repair_brief_path.write_text("# Failed checks\n", encoding="utf-8")

    result = persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
        trigger="initial",
        outcome="failed validation",
        stage_status="failed",
        validator_report_path=validator_report_path,
        repair_brief_path=repair_brief_path,
    )

    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert metadata is not None
    assert len(metadata.repair_history) == 1
    assert metadata.repair_history[0].attempt_number == 1
    assert metadata.repair_history[0].trigger == "initial"
    assert result.stage_result_path.exists()

    stage_result_text = result.stage_result_path.read_text(encoding="utf-8")
    assert "- Attempt `1` (`initial`) -> failed validation." in stage_result_text
    assert "`workitems/WI-001/stages/plan/validator-report.md`" in stage_result_text
    assert "`workitems/WI-001/stages/plan/repair-brief.md`" in stage_result_text
