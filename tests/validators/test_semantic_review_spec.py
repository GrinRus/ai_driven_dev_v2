from __future__ import annotations

from pathlib import Path

from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _write_review_spec_report,
)

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    INCOMPLETE_SECTION_CODE,
    MISSING_EVIDENCE_REF_CODE,
    UNSUPPORTED_CLAIM_CODE,
    validate_semantic_outputs,
)


def test_validate_semantic_outputs_accepts_valid_review_spec_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-spec-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-SEM-REVIEW-SPEC-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_spec_nested_issue_metadata(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-NESTED",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- **State:** `ready`\n\n"
            "## Issue list\n\n"
            "- **OBS-1** - `info` - Plan line numbers are one-off from "
            "`transform` call in prose, but the actual edit target is correct.\n"
            "  - **Severity:** `info`\n"
            "  - **Evidence:** `plan.md` M1 and `cli.py:1179`.\n"
            "  - **Rationale:** The prose says \"edit `cli.py:1179` ... so the "
            "transform call is skipped\" because the edit is scoped to the guard "
            "line and not to unrelated behavior.\n\n"
            "## Strengths\n\n"
            "- The plan is scoped to a minimal regression fix with targeted tests.\n\n"
            "## Recommendation summary\n\n"
            "- Adopt the plan as-is; no remediation is required for OBS-1.\n\n"
            "## Required changes\n\n"
            "None.\n\n"
            "## Decision\n\n"
            "- **Status:** `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-NESTED",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_spec_issue_subsections(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-SUBSECTIONS",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- Readiness: `ready`\n\n"
            "## Issue list\n\n"
            "Each issue is severity-tagged and rationale-backed.\n\n"
            "### I1 - Conditional implementation shape\n\n"
            "- **Severity:** low\n"
            "- **Evidence:** `plan.md` M3.\n"
            "- **Section:** `Milestones > M3`.\n"
            "- **Observation:** The plan keeps two implementation shapes open.\n"
            "- **Rationale:** because the downstream implement stage must record "
            "which shape it chose and why; this is advisory, not blocking.\n\n"
            "### I2 - Test file location remains flexible\n\n"
            "- **Severity:** info\n"
            "- **Evidence:** `plan.md` M1.\n"
            "- **Section:** `Milestones > M1`.\n"
            "- **Observation:** The exact test file is left to implementation.\n"
            "- **Rationale:** because the repo layout is observable at task time "
            "and the recommendation only improves traceability.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "- **(Highest impact, maps to I1)** Record the chosen implementation "
            "shape in `stage-result.md`.\n"
            "- **(Lower impact, maps to I2)** Pin test filenames during task "
            "decomposition.\n\n"
            "## Required changes\n\n"
            "- none\n\n"
            "## Decision\n\n"
            "- Decision: `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-SUBSECTIONS",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_spec_no_issue_markers(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-NO-ISSUES",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- Readiness: `ready`\n\n"
            "## Issue list\n\n"
            "- **I1 - Upstream issue-id discrepancy is advisory.**\n"
            "  - Severity: `low`\n"
            "  - Evidence: `plan.md` M2.\n"
            "  - Rationale: because the plan records the discrepancy and maps "
            "it to a commit-message recommendation.\n"
            "- **I2 - No material defect found that blocks decomposition.**\n"
            "  - Severity: `none`\n"
            "  - Evidence: `plan.md` and `research-notes.md`.\n"
            "  - Rationale: Plan goals, scope, milestones, dependencies, risks, "
            "and verification approach are mutually consistent.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "- **(High priority, maps to I1)** Preserve the documented issue-id "
            "wording in downstream commit text.\n\n"
            "## Required changes\n\n"
            "- none\n\n"
            "## Decision\n\n"
            "- Decision: `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-NO-ISSUES",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_spec_inline_severity_label(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-INLINE-SEVERITY",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- `ready-with-conditions`\n\n"
            "## Issue list\n\n"
            "- I1: Severity: low. Evidence: `plan.md` M2. Rationale: because the "
            "plan should add one delegated constructor smoke check during "
            "downstream tasking.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "1. Add the delegated constructor smoke check before implementation sign-off.\n"
            "2. Proceed with task decomposition after carrying I1 into the tasklist.\n\n"
            "## Required changes\n\n"
            "- Add or assign the I1 smoke check during task decomposition.\n\n"
            "## Decision\n\n"
            "- `approved-with-conditions`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-INLINE-SEVERITY",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_review_spec_no_issue_prose_without_metadata(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-NO-ISSUE-PROSE",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- Readiness: `ready`\n\n"
            "## Issue list\n\n"
            "No material issues identified.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "- Proceed with implementation using the planned verification order.\n\n"
            "## Required changes\n\n"
            "- none\n\n"
            "## Decision\n\n"
            "- Decision: `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-NO-ISSUE-PROSE",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Required section `Issue list` must use bullet items with "
                "severity and rationale."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-REVIEW-SPEC-NO-ISSUE-PROSE/stages/review-spec/"
                    "review-spec-report.md"
                ),
                line_number=7,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_review_spec_ordered_recommendations(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-ORDERED-RECS",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- Readiness: `ready`\n\n"
            "## Issue list\n\n"
            "- **I1 - Memory command assertion can be stronger.**\n"
            "  - Severity: `low`\n"
            "  - Evidence: `plan.md` Verification notes.\n"
            "  - Rationale: because adding an output assertion would tighten "
            "the regression without changing scope.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "1. **Approve and proceed.** The plan is coherent and bounded.\n"
            "2. **Optionally tighten memory assertions.** Confirm no "
            "`AssertionError` appears in command output.\n\n"
            "## Required changes\n\n"
            "- none\n\n"
            "## Decision\n\n"
            "- Decision: `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-ORDERED-RECS",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_review_spec_issue_without_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-MISSING-EVIDENCE",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- `ready-with-conditions`\n\n"
            "## Issue list\n\n"
            "- I1: Severity: low. Rationale: because task decomposition should "
            "preserve the verification note.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded.\n\n"
            "## Recommendation summary\n\n"
            "- Carry I1 into task decomposition.\n\n"
            "## Required changes\n\n"
            "- Preserve the verification note.\n\n"
            "## Decision\n\n"
            "- `approved-with-conditions`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-MISSING-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert any(finding.code == MISSING_EVIDENCE_REF_CODE for finding in findings)


def test_validate_semantic_outputs_flags_review_spec_high_claim_without_direct_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-UNSUPPORTED-HIGH",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- `not-ready`\n\n"
            "## Issue list\n\n"
            "- I1: Severity: high. Evidence: source inspection. Rationale: because "
            "source inspection shows the parser behavior is missing.\n\n"
            "## Strengths\n\n"
            "- The plan names the target parser area.\n\n"
            "## Recommendation summary\n\n"
            "- Provide direct source evidence before blocking decomposition.\n\n"
            "## Required changes\n\n"
            "- Add direct source evidence or downgrade I1.\n\n"
            "## Decision\n\n"
            "- `rejected`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-UNSUPPORTED-HIGH",
        workspace_root=workspace_root,
    )

    assert any(finding.code == UNSUPPORTED_CLAIM_CODE for finding in findings)


def test_validate_semantic_outputs_flags_review_spec_contradiction_without_reconciliation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-CONTRADICTION",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- `not-ready`\n\n"
            "## Issue list\n\n"
            "### I1 - Plan contradiction blocker\n\n"
            "- Severity: high\n"
            "- Evidence: `src/importer/reader.py` and `plan.md`.\n"
            "- Rationale: because source inspection contradicts the plan's claim "
            "that the importer already rejects malformed rows.\n\n"
            "## Strengths\n\n"
            "- The plan identifies importer validation as important.\n\n"
            "## Recommendation summary\n\n"
            "- Reconcile the contradiction with upstream research before proceeding.\n\n"
            "## Required changes\n\n"
            "- Add reconciliation or remove I1.\n\n"
            "## Decision\n\n"
            "- `rejected`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-CONTRADICTION",
        workspace_root=workspace_root,
    )

    assert any(finding.code == UNSUPPORTED_CLAIM_CODE for finding in findings)


def test_validate_semantic_outputs_accepts_review_spec_contradiction_with_reconciliation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-CONTRADICTION-RECONCILED",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- `not-ready`\n\n"
            "## Issue list\n\n"
            "### I1 - Plan contradiction blocker\n\n"
            "- Severity: high\n"
            "- Evidence: `src/importer/reader.py`, `plan.md`, and F7.\n"
            "- Reconciliation: F7 is superseded by the direct failing probe "
            "`repo-cli validate-import fixtures/bad.csv`.\n"
            "- Rationale: because source inspection contradicts the plan's claim "
            "that the importer already rejects malformed rows.\n\n"
            "## Strengths\n\n"
            "- The plan identifies importer validation as important.\n\n"
            "## Recommendation summary\n\n"
            "- Update the plan with the reconciled importer evidence.\n\n"
            "## Required changes\n\n"
            "- Add the failing importer probe before task decomposition.\n\n"
            "## Decision\n\n"
            "- `rejected`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-CONTRADICTION-RECONCILED",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_review_spec_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-spec-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-SEM-REVIEW-SPEC-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each `Issue list` item must include explicit severity "
                "(critical/high/medium/low/info/none)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each `Issue list` item must include rationale "
                "(for example `because ...`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=MISSING_EVIDENCE_REF_CODE,
            message=(
                "Each `Issue list` item must include `Evidence:` naming a concrete "
                "artifact, source id, target file path, or check result."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Recommendation summary` cannot be `none`; "
                "include actionable remediation steps."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=15,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Sections `Readiness state` and `Decision` are inconsistent: "
                "`not-ready` expects `rejected`."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=23,
            ),
        ),
    )

