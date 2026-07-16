from __future__ import annotations

from pathlib import Path

from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _git,
    _write_review_report,
    _write_workspace_baseline,
)

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    INCOMPLETE_SECTION_CODE,
    UNSUPPORTED_CLAIM_CODE,
    UNVERIFIABLE_CHECK_CLAIM_CODE,
    validate_semantic_outputs,
)


def test_validate_semantic_outputs_accepts_valid_review_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_explicit_no_review_findings(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NO-FINDINGS",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "No review findings were identified.\n\n"
            "Evidence: `implementation-report.md` records AC-1 and AC-2 coverage.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NO-FINDINGS",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_none_review_findings_bullet(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NONE-FINDINGS-BULLET",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NONE-FINDINGS-BULLET",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_none_review_findings_with_evidence_note(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NONE-FINDINGS-EVIDENCE",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "Evidence: `implementation-report.md` records AC-1 coverage.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NONE-FINDINGS-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_review_clean_approval_with_setup_residue(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-SETUP-RESIDUE"
    (tmp_path / "coverage" / "raw" / "default").mkdir(parents=True)
    _write_workspace_baseline(workspace_root, work_item)
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert any(
        finding.code == UNVERIFIABLE_CHECK_CLAIM_CODE
        and "coverage/raw/default" in finding.message
        and "after all review commands" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_ignores_review_tracked_build_source_directory(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "aidd@example.test")
    _git(tmp_path, "config", "user.name", "AIDD Test")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "build.ts").write_text("export {}\n", encoding="utf-8")
    _git(tmp_path, "add", "build/build.ts")
    _git(tmp_path, "commit", "-m", "track build source")

    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-SETUP-TRACKED-BUILD"
    _write_workspace_baseline(workspace_root, work_item)
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_condition_with_setup_residue_finding(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-SETUP-RESIDUE-FINDING"
    (tmp_path / "coverage" / "raw" / "default").mkdir(parents=True)
    _write_workspace_baseline(workspace_root, work_item)
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved-with-conditions\n\n"
            "## Findings\n\n"
            "### RV-1 - ignored residue remains after review\n\n"
            "- Severity: `high`\n"
            "- Disposition: `must-fix`\n"
            "- Evidence: `coverage/raw/default` remains visible after "
            "`git status --ignored --short --untracked-files=all`.\n"
            "- Rationale: because ignored coverage residue is workspace pollution "
            "unless it is removed or selected as deliverable output.\n\n"
            "## Risks\n\n"
            "- Review is conditional on cleanup.\n\n"
            "## Required follow-up\n\n"
            "- RV-1: remove `coverage/raw/default` or document it as selected deliverable.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_review_cleanup_claim_with_setup_residue(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-SETUP-CLEANUP-CLAIM"
    (tmp_path / "coverage" / "raw" / "default").mkdir(parents=True)
    _write_workspace_baseline(workspace_root, work_item)
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved\n\n"
            "## Findings\n\n"
            "### RV-1 - scoped implementation evidence reviewed\n\n"
            "- Severity: `low`\n"
            "- Disposition: `accepted-risk`\n"
            "- Evidence: `implementation-report.md` records focused verification.\n"
            "- Rationale: because the selected behavior is covered by targeted tests.\n\n"
            "## Risks\n\n"
            "- Cleanup passed after verification; workspace hygiene is clean.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert any(
        finding.code == UNVERIFIABLE_CHECK_CLAIM_CODE
        and "cleanup passed" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_ignores_review_residue_without_setup_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-NO-BASELINE-RESIDUE"
    (tmp_path / "coverage" / "raw" / "default").mkdir(parents=True)
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_subheading_findings(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-SUBHEADINGS",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "**Status:** `approved`\n\n"
            "## Findings\n\n"
            "### REV-001 - memory residual no such table path\n\n"
            "- **Severity:** low\n"
            "- **Disposition:** accepted-risk\n"
            "- **Rationale:** the implemented guard is acceptable because it prevents the "
            "header-only memory crash without changing populated imports.\n"
            "- **Evidence:** `implementation-report.md` TL-4 and `tests/test_cli_memory.py`.\n\n"
            "### REV-002 - kwarg forwarding drift risk\n\n"
            "- **Severity:** low\n"
            "- **Disposition:** follow-up\n"
            "- **Rationale:** forwarding table creation kwargs remains reviewable because the "
            "current change preserves insert option behavior.\n"
            "- **Evidence:** `data_tool/cli.py:1189-1196` and AC-2.\n\n"
            "## Risks\n\n"
            "- Low residual risk is bounded by targeted regression tests.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-SUBHEADINGS",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_none_severity_findings(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NONE-SEVERITY",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "### RV-1 - Patch shape matches requested scope\n\n"
            "- Severity: `none`\n"
            "- Disposition: `accepted-risk`\n"
            "- Evidence: `data_tool/cli.py:1179` and AC-2.\n"
            "- Rationale: because the finding records a verified non-defect "
            "with bounded residual risk.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NONE-SEVERITY",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_does_not_infer_review_severity_from_prose(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-SEVERITY-PROSE",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "### RV-1 - Patch shape is bounded\n\n"
            "- Disposition: `accepted-risk`\n"
            "- Evidence: `data_tool/cli.py:1179` and AC-2.\n"
            "- Rationale: because none of the observed checks indicate scope creep.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-SEVERITY-PROSE",
        workspace_root=workspace_root,
    )

    assert any(
        finding.code == INCOMPLETE_SECTION_CODE
        and "explicit severity" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_requires_review_finding_evidence_reference(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NO-EVIDENCE",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "### RV-1 - Plausible but uncited claim\n\n"
            "- Severity: `low`\n"
            "- Disposition: `accepted-risk`\n"
            "- Rationale: because the implementation appears small and bounded.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NO-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=UNSUPPORTED_CLAIM_CODE,
            message=(
                "Finding is missing evidence reference to implementation output "
                "or acceptance criteria."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-NO-EVIDENCE/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_compact_review_finding_severity(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-COMPACT-SEVERITY",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved-with-conditions`\n\n"
            "## Findings\n\n"
            "- `RV-1` `medium` `accepted-risk` Evidence: "
            "`implementation-report.md` records the scoped no-op boundary. "
            "Rationale: The boundary is acceptable because release-proof "
            "execution is intentionally non-destructive.\n"
            "- `RV-2` `low` `follow-up` Evidence: AC-2 and "
            "`implementation-report.md`. Rationale: Follow-up remains "
            "bounded to maintained-runtime task completion.\n\n"
            "## Risks\n\n"
            "- Medium residual release-proof risk is explicitly accepted.\n\n"
            "## Required follow-up\n\n"
            "- Re-run the maintained runtime scenario separately.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-COMPACT-SEVERITY",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_ignores_non_disposition_must_fix_mentions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-MUST-FIX-MENTION",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "### RV-1 [low] [accepted-risk] Bounded flag asymmetry\n\n"
            "- Severity: `low`\n"
            "- Disposition: `accepted-risk`\n"
            "- Evidence: `data_tool/cli.py:1179-1183` and AC-2.\n"
            "- Rationale: because the behaviour is bounded to the agreed "
            "scope and should remain accepted-risk rather than `must-fix`.\n\n"
            "### RV-2 [low] [follow-up] Deferred sibling site\n\n"
            "- Severity: `low`\n"
            "- Disposition: `follow-up`\n"
            "- Evidence: `data_tool/cli.py:2029-2040` and AC-3.\n"
            "- Rationale: because the sibling path is documented out of scope.\n\n"
            "## Risks\n\n"
            "- No unresolved `must-fix` findings remain.\n\n"
            "## Required follow-up\n\n"
            "- Track RV-2 separately.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-MUST-FIX-MENTION",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_review_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each finding must include explicit severity "
                "(critical/high/medium/low/info/none)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each finding must include rationale "
                "(for example `Rationale:` or `because ...`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=UNSUPPORTED_CLAIM_CODE,
            message=(
                "Finding is missing evidence reference to implementation output "
                "or acceptance criteria."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each finding must include explicit disposition "
                "(`must-fix`, `follow-up`, `accepted-risk`, or `invalid`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each finding must include rationale "
                "(for example `Rationale:` or `because ...`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=UNSUPPORTED_CLAIM_CODE,
            message=(
                "Finding is missing evidence reference to implementation output "
                "or acceptance criteria."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Approval status cannot be `approved` while unresolved "
                "`must-fix` findings remain."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=12,
            ),
        ),
    )

