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
    assert any("No touched files" in warning for warning in implementation.warnings)
    assert any(
        "No executable verification commands" in warning for warning in implementation.warnings
    )
    assert review.findings == ()
    assert "No structured review findings" in review.warnings[-1]
    assert qa.quality_verdict is None
    assert "No QA verdict" in qa.warnings[-1]


def test_parse_implementation_report_warns_when_verification_commands_are_missing() -> None:
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
                "",
                "## Verification",
                "",
                "- skipped browser smoke: no browser available.",
            )
        )
    )

    assert view.touched_files == ("src/app.py",)
    assert view.verification_commands == ()
    assert view.skipped_checks == ("skipped browser smoke: no browser available.",)
    assert any("No executable verification commands" in warning for warning in view.warnings)


def test_parse_implementation_report_keeps_non_passing_outcomes_unverified() -> None:
    view = parse_implementation_report_text(
        "\n".join(
            (
                "# Implementation Report",
                "",
                "## Verification",
                "",
                "- `uv run pytest -q` — not-run: provider unavailable.",
                "- `uv run ruff check .` -> exit 1.",
            )
        )
    )

    assert view.verification_status == "failed"
    assert view.verification_commands == (
        "`uv run pytest -q` — not-run: provider unavailable.",
        "`uv run ruff check .` -> exit 1.",
    )
    assert [item["status"] for item in view.verification_results] == ["not-run", "fail"]
    assert any("non-passing" in warning for warning in view.warnings)


def test_parse_implementation_report_does_not_treat_command_claim_without_result_as_pass() -> None:
    view = parse_implementation_report_text(
        "\n".join(
            (
                "# Implementation Report",
                "",
                "## Verification",
                "",
                "- `uv run pytest -q` was executed successfully.",
            )
        )
    )

    assert view.verification_status == "unverifiable"
    assert view.verification_results[0]["status"] == "missing"
    assert view.verification_commands == ("`uv run pytest -q` was executed successfully.",)
    assert any("non-passing" in warning for warning in view.warnings)


def test_parse_implementation_report_ignores_result_word_in_command_argument() -> None:
    view = parse_implementation_report_text(
        "\n".join(
            (
                "# Implementation Report",
                "",
                "## Verification",
                "",
                "- `uv run pytest -k passed`.",
            )
        )
    )

    assert view.verification_status == "unverifiable"
    assert view.verification_results == (
        {"command": "`uv run pytest -k passed`.", "status": "missing"},
    )
    assert any("non-passing" in warning for warning in view.warnings)


def test_parse_implementation_report_requires_command_and_outcome_on_one_item() -> None:
    view = parse_implementation_report_text(
        "\n".join(
            (
                "# Implementation Report",
                "",
                "## Verification",
                "",
                "- Command: `uv run pytest -q`.",
                "- Outcome: `12 passed`, exit code `0` -> pass.",
            )
        )
    )

    assert view.verification_status == "unverifiable"
    assert view.verification_results == (
        {"command": "Command: `uv run pytest -q`.", "status": "missing"},
        {
            "command": "Outcome: `12 passed`, exit code `0` -> pass.",
            "status": "unverifiable",
            "kind": "claim",
        },
    )
    assert any("non-passing" in warning for warning in view.warnings)


def test_parse_implementation_report_blocks_mixed_outcome_only_claims() -> None:
    view = parse_implementation_report_text(
        "\n".join(
            (
                "# Implementation Report",
                "",
                "## Verification",
                "",
                "- `uv run pytest -q` -> pass.",
                "- Full test suite passed.",
            )
        )
    )

    assert view.verification_status == "unverifiable"
    assert view.verification_commands == ("`uv run pytest -q` -> pass.",)
    assert view.verification_results == (
        {"command": "`uv run pytest -q` -> pass.", "status": "pass"},
        {"command": "Full test suite passed.", "status": "unverifiable", "kind": "claim"},
    )
    assert any("non-passing" in warning for warning in view.warnings)


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
                "  - Evidence: EV-1 shows `src/app.py` lacks AC-1 boundary handling.",
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
    assert view.findings[0].acceptance_ids == ("AC-1",)


def test_parse_review_findings_extracts_inline_severity_and_disposition() -> None:
    view = parse_review_report_text(
        "\n".join(
            (
                "# Review Report",
                "",
                "## Approval status",
                "",
                "- `rejected`",
                "",
                "## Findings",
                "",
                "- RV-1 (`high`, `must-fix`): Missing remediation proof",
                "  - Evidence: EV-1 shows `src/app.py` is not rerun.",
            )
        )
    )

    assert view.approval_status == "rejected"
    assert view.findings[0].severity == "high"
    assert view.findings[0].disposition == "must-fix"


def test_parse_review_findings_accepts_none_marker_without_warning() -> None:
    view = parse_review_report_text(
        "\n".join(
            (
                "# Review Report",
                "",
                "## Verdict",
                "",
                "- Status: `approved`",
                "",
                "## Findings",
                "",
                "- none",
                "",
                "Evidence: `implementation-report.md` records AC-1 coverage.",
                "",
                "## Risks",
                "",
                "- No material review risk remains.",
                "",
                "## Required follow-up",
                "",
                "- none",
            )
        )
    )

    assert view.approval_status == "approved"
    assert view.findings == ()
    assert view.warnings == ()


def test_parse_qa_verdict_extracts_risks_issues_and_evidence() -> None:
    view = parse_qa_report_text(
        "\n".join(
            (
                "# QA Report",
                "",
                "- Quality verdict: `not-ready`",
                "- Release recommendation: `hold`",
                "- Evidence: EV-1, EV-2, `verification.md`, AC-2",
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
    assert view.evidence_references == ("EV-1", "EV-2", "verification.md")
    assert view.acceptance_ids == ("AC-2",)
    assert view.residual_risks == ("Retry path unverified.",)
    assert view.known_issues == ("QAI-1 missing production smoke.",)


def test_parse_qa_verdict_ignores_known_issues_none_marker() -> None:
    view = parse_qa_report_text(
        "\n".join(
            (
                "# QA Report",
                "",
                "## Verification summary",
                "",
                "- Quality verdict: `ready`.",
                "",
                "## Release recommendation",
                "",
                "- `proceed`",
                "",
                "## Evidence",
                "",
                "- EV-1: `implementation-report.md` records remediation.",
                "",
                "## Known issues",
                "",
                "- Known issues: none.",
                "",
                "## Readiness",
                "",
                "- Ready.",
            )
        )
    )

    assert view.quality_verdict == "ready"
    assert view.known_issues == ()
