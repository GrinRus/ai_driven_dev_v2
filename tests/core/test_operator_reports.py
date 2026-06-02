from __future__ import annotations

from aidd.core.operator_reports import (
    parse_implementation_report_text,
    parse_qa_report_text,
    parse_review_report_text,
)


def test_parse_implementation_report_extracts_claims_and_evidence() -> None:
    view = parse_implementation_report_text(
        "\n".join(
            (
                "# Implementation Report",
                "",
                "- Selected task id: `TASK-42`",
                "",
                "## Touched files",
                "",
                "- `src/app.py` - changed routing.",
                "- `tests/test_app.py` - covered routing.",
                "",
                "## Verification",
                "",
                "- `uv run pytest tests/test_app.py` -> exit 0.",
                "- skipped browser smoke: no browser available.",
                "",
                "## Residual risks",
                "",
                "- Manual visual QA remains.",
            )
        )
    )

    assert view.selected_task_id == "TASK-42"
    assert view.touched_files == ("src/app.py", "tests/test_app.py")
    assert view.verification_commands == ("`uv run pytest tests/test_app.py` -> exit 0.",)
    assert view.skipped_checks == ("skipped browser smoke: no browser available.",)
    assert view.residual_risks == ("Manual visual QA remains.",)
    assert not view.warnings


def test_parse_reports_tolerates_malformed_markdown_with_warnings() -> None:
    implementation = parse_implementation_report_text("plain text without headings")
    review = parse_review_report_text("plain text without structured findings")
    qa = parse_qa_report_text("plain text without verdict")

    assert implementation.touched_files == ()
    assert "No touched files" in implementation.warnings[-1]
    assert review.findings == ()
    assert "No structured review findings" in review.warnings[-1]
    assert qa.quality_verdict is None
    assert "No QA verdict" in qa.warnings[-1]


def test_parse_review_findings_extracts_severity_disposition_and_evidence() -> None:
    view = parse_review_report_text(
        "\n".join(
            (
                "# Review Report",
                "",
                "- Approval status: `rejected`",
                "",
                "## Findings",
                "",
                "- RV-1 Missing test guard",
                "  - Severity: `high`",
                "  - Disposition: `must-fix`",
                "  - Evidence: EV-1 shows `src/app.py` lacks boundary handling.",
                "",
                "- RV-2 Cosmetic follow-up",
                "  - Severity: `low`",
                "  - Disposition: `follow-up`",
            )
        )
    )

    assert view.approval_status == "rejected"
    assert [finding.finding_id for finding in view.findings] == ["RV-1", "RV-2"]
    assert "EV-1" not in [finding.finding_id for finding in view.findings]
    assert view.findings[0].severity == "high"
    assert view.findings[0].disposition == "must-fix"
    assert "src/app.py" in view.findings[0].related_paths


def test_parse_qa_verdict_extracts_risks_issues_and_evidence() -> None:
    view = parse_qa_report_text(
        "\n".join(
            (
                "# QA Report",
                "",
                "- Quality verdict: `not-ready`",
                "- Release recommendation: `hold`",
                "- Evidence: EV-1, EV-2",
                "",
                "## Residual risks",
                "",
                "- Retry path unverified.",
                "",
                "## Known issues",
                "",
                "- QAI-1 missing production smoke.",
            )
        )
    )

    assert view.quality_verdict == "not-ready"
    assert view.release_recommendation == "hold"
    assert view.evidence_ids == ("EV-1", "EV-2")
    assert view.residual_risks == ("Retry path unverified.",)
    assert view.known_issues == ("QAI-1 missing production smoke.",)
