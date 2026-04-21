from __future__ import annotations

from pathlib import Path

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.reports import render_validator_report, write_validator_report


def test_render_validator_report_handles_empty_findings() -> None:
    report = render_validator_report(findings=())

    assert "# Validator Report" in report
    assert "- Total issues: 0" in report
    assert "- Blocking issues: no" in report
    assert "- Dominant failure categories: none" in report
    assert "## Structural checks" in report and "- none" in report
    assert "## Semantic checks" in report and "- none" in report
    assert "## Cross-document checks" in report and "- none" in report
    assert "- Verdict: `pass`" in report
    assert "- Repair required for progression: no" in report


def test_render_validator_report_groups_findings_and_renders_location() -> None:
    findings = (
        ValidationFinding(
            code="STRUCT-MISSING-REQUIRED-DOCUMENT",
            message="Missing required document: workitems/WI-001/stages/qa/stage-result.md",
            severity="critical",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/qa/stage-result.md",
            ),
        ),
        ValidationFinding(
            code="SEM-PLACEHOLDER-CONTENT",
            message="Placeholder text remains in required section.",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/qa/qa-report.md",
                line_number=14,
            ),
        ),
        ValidationFinding(
            code="CROSS-REFERENCE-MISMATCH",
            message="Stage result status conflicts with validator verdict.",
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/qa/stage-result.md",
            ),
        ),
    )

    report = render_validator_report(findings=findings)

    assert "- Total issues: 3" in report
    assert "- Blocking issues: yes" in report
    assert (
        "- Affected documents: "
        "`workitems/WI-001/stages/qa/qa-report.md`, "
        "`workitems/WI-001/stages/qa/stage-result.md`"
    ) in report
    assert (
        "- `SEM-PLACEHOLDER-CONTENT` (`high`) in "
        "`workitems/WI-001/stages/qa/qa-report.md`:14"
    ) in report
    assert "- Verdict: `fail`" in report
    assert "- Repair required for progression: yes" in report


def test_write_validator_report_writes_rendered_markdown(tmp_path: Path) -> None:
    report_path = tmp_path / "validator-report.md"
    findings = (
        ValidationFinding(
            code="STRUCT-MISSING-REQUIRED-SECTION",
            message=(
                "Missing required section `Status` in "
                "workitems/WI-001/stages/qa/stage-result.md"
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/qa/stage-result.md",
            ),
        ),
    )

    write_validator_report(path=report_path, findings=findings)

    content = report_path.read_text(encoding="utf-8")
    assert content.startswith("# Validator Report")
    assert "- Total issues: 1" in content
    assert "- Verdict: `fail`" in content
