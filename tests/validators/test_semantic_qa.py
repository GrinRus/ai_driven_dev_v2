from __future__ import annotations

from pathlib import Path

from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _write_acceptance_criteria,
    _write_qa_report,
    _write_workspace_baseline,
)

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    INCOMPLETE_SECTION_CODE,
    MISSING_EVIDENCE_REF_CODE,
    RISK_UNDERREPORT_CODE,
    UNSUPPORTED_VERDICT_CODE,
    validate_semantic_outputs,
)


def test_validate_semantic_outputs_accepts_valid_qa_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "qa-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="qa",
        work_item="WI-SEM-QA-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_qa_acceptance_coverage_checklist(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-ACCEPTANCE-COVERAGE"
    _write_acceptance_criteria(
        tmp_path,
        work_item,
        """# Acceptance Criteria

- AC-1: Regression exercises the public CLI behavior.
- AC-2: The tracked diff stays within the selected command module and tests.
""",
    )
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Quality verdict

- QA verdict: ready

## Verification summary

- Verification passed with acceptance evidence tracked by `EV-1`.

## Release recommendation

- proceed

## Evidence

- EV-1: `context/verification-output.md` reports the targeted tests passed.

## Known issues

- Known issues: none.

## Readiness

- AC-1: confirmed. Evidence: EV-1, `context/verification-output.md`.
  The public CLI regression test passed.
- AC-2: confirmed. Evidence: EV-1, `context/verification-output.md`.
  Diff review stayed within the selected files.
- Ready because each acceptance criterion has evidence and no known issue remains.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == ()


def test_validate_semantic_outputs_requires_setup_ignored_residue_evidence_for_ready_qa(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-SETUP-RESIDUE"
    _write_workspace_baseline(tmp_path, work_item)
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Quality verdict

- QA verdict: ready

## Verification summary

- Authored verification passed with evidence tracked by `EV-1` and `EV-2`.

## Release recommendation

- proceed

## Evidence

- EV-1: `./node_modules/.bin/vitest --run --coverage.enabled=false
  tests/runtime-error.test.ts` -> pass.
- EV-2: `./node_modules/.bin/tsc --noEmit` -> pass.

## Known issues

- Known issues: none.

## Readiness

- Ready because authored verification passed and no known issue remains.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert any(
        finding.code == MISSING_EVIDENCE_REF_CODE
        and "git status --ignored --short --untracked-files=all" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_accepts_setup_ignored_residue_evidence_for_ready_qa(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-SETUP-RESIDUE-CLEAN"
    _write_workspace_baseline(tmp_path, work_item)
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Quality verdict

- QA verdict: ready

## Verification summary

- Authored verification passed with evidence tracked by `EV-1`, `EV-2`, and `EV-3`.

## Release recommendation

- proceed

## Evidence

- EV-1: `./node_modules/.bin/vitest --run --coverage.enabled=false
  tests/runtime-error.test.ts` -> pass.
- EV-2: `./node_modules/.bin/tsc --noEmit` -> pass.
- EV-3: `git status --ignored --short --untracked-files=all` -> pass; no new
  `coverage/`, `.coverage*`, `__pycache__/`, build, dist, or dependency-cache
  residue beyond setup baseline.

## Known issues

- Known issues: none.

## Readiness

- Ready because authored verification and ignored workspace residue evidence are clean.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_qa_bundled_acceptance_coverage(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-BUNDLED-ACCEPTANCE"
    _write_acceptance_criteria(
        tmp_path,
        work_item,
        """# Acceptance Criteria

- AC-1: Regression exercises the public CLI behavior.
- AC-2: The tracked diff stays within the selected command module and tests.
- AC-3: Verification transcript captures the targeted command.
""",
    )
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Quality verdict

- QA verdict: ready

## Verification summary

- Verification passed with acceptance evidence tracked by `EV-1`.

## Release recommendation

- proceed

## Evidence

- EV-1: `context/verification-output.md` reports the targeted tests passed.

## Known issues

- Known issues: none.

## Readiness

- AC-1 through AC-3: confirmed. Evidence: EV-1.
- Ready because the authored verification passed.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Acceptance coverage must use a separate top-level bullet for "
                "`AC-1` instead of bundling multiple `AC-N` ids."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-BUNDLED-ACCEPTANCE/stages/qa/qa-report.md"
                ),
                line_number=1,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "QA report must include an acceptance coverage bullet for "
                "`AC-2` from `context/acceptance-criteria.md`."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-BUNDLED-ACCEPTANCE/stages/qa/qa-report.md"
                ),
                line_number=1,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Acceptance coverage must use a separate top-level bullet for "
                "`AC-3` instead of bundling multiple `AC-N` ids."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-BUNDLED-ACCEPTANCE/stages/qa/qa-report.md"
                ),
                line_number=1,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_known_issue_blocks_with_metadata(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-KNOWN-ISSUES"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready-with-risks`.
- Verification passed with residual risks tracked by `EV-1`.

## Release recommendation

- `proceed-with-conditions`

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

### KI-1: sibling command remains out of scope

- Severity: `medium`.
- Disposition: `follow-up`.
- Description: sibling command remains intentionally deferred.
- Mitigation: track a follow-up before broad release.
- Ownership: platform maintainer.
- Evidence: `EV-1`, `context/verification-output.md`.

### KI-2: acceptance branch remains explicit

- Severity: `low`.
- Disposition: `accepted-risk`.
- Description: accepted branch is documented in the regression test.
- Mitigation: keep the test docstring as the change boundary.
- Ownership: QA owner.
- Evidence: `EV-1`.

## Readiness

- Ready with conditions because `EV-1` is clean and known issues have owners.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_flat_known_issue_metadata(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-FLAT-KNOWN-ISSUES"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready-with-risks`.
- Verification passed with residual risks tracked by `EV-1`.

## Release recommendation

- `proceed-with-conditions`

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

- QR-1 (`medium`): release-proof lane validates operator semantics only.
- Mitigation: keep maintained-runtime bugfix runs in nightly checks.
- Owner: platform maintainer.

## Readiness

- Ready with conditions because `EV-1` is clean and known issue ownership is explicit.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == ()


def test_validate_semantic_outputs_isolates_treatment_metadata_per_qa_risk(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-ISOLATED-RISKS"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready-with-risks`.
- Verification passed with residual risks tracked by `EV-1`.

## Release recommendation

- `proceed-with-conditions`

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

- QR-1 (Severity: `medium`): retry telemetry remains partial.
  - Mitigation: keep the retry alert enabled.
  - Owner: platform maintainer.
- QR-2 (Severity: `high`): rollback timing remains unverified.
- QR-3 (Severity: `low`): weekend load coverage remains incomplete.

## Readiness

- Ready with conditions because `EV-1` is clean and risks are explicit.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == (
        ValidationFinding(
            code=RISK_UNDERREPORT_CODE,
            message=(
                "Each residual risk item must include mitigation and/or ownership notes."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-ISOLATED-RISKS/stages/qa/qa-report.md"
                ),
                line_number=21,
            ),
        ),
        ValidationFinding(
            code=RISK_UNDERREPORT_CODE,
            message=(
                "Each residual risk item must include mitigation and/or ownership notes."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-ISOLATED-RISKS/stages/qa/qa-report.md"
                ),
                line_number=22,
            ),
        ),
    )


def test_validate_semantic_outputs_flags_ready_with_residual_risk_entry(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-READY-WITH-RESIDUAL-RISK"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready`.
- Verification passed with residual risk tracked by `EV-1`.

## Release recommendation

- proceed

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

- Known issues: none.
- Residual risk RR-1: Severity: low. Verification is focused rather than full-suite.
  Mitigation/ownership: release operator may run the broader suite if policy requires it.

## Readiness

- Ready because `EV-1` is clean and the residual risk has low severity and owner coverage.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == (
        ValidationFinding(
            code=UNSUPPORTED_VERDICT_CODE,
            message=(
                "Verdict `ready` cannot include residual risk entries; use "
                "`ready-with-risks` or `proceed-with-conditions` for true "
                "residual risk, or move satisfied selected-boundary notes out "
                "of `Known issues`."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-READY-WITH-RESIDUAL-RISK/stages/qa/"
                    "qa-report.md"
                ),
                line_number=16,
            ),
        ),
    )


def test_validate_semantic_outputs_flags_known_issue_block_missing_severity(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-MISSING-SEVERITY"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready-with-risks`.
- Verification passed with residual risks tracked by `EV-1`.

## Release recommendation

- `proceed-with-conditions`

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

### KI-1: sibling command remains out of scope

- Disposition: `follow-up`.
- Description: sibling command remains intentionally deferred.
- Mitigation: track a follow-up before broad release.
- Ownership: platform maintainer.
- Evidence: `EV-1`, `context/verification-output.md`.

## Readiness

- Ready with conditions because `EV-1` is clean and known issues have owners.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == (
        ValidationFinding(
            code=RISK_UNDERREPORT_CODE,
            message=(
                "Each residual risk item must include explicit severity "
                "(critical/high/medium/low)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-MISSING-SEVERITY/stages/qa/qa-report.md"
                ),
                line_number=18,
            ),
        ),
    )


def test_validate_semantic_outputs_flags_invalid_qa_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "qa-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="qa",
        work_item="WI-SEM-QA-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=MISSING_EVIDENCE_REF_CODE,
            message=(
                "Material QA claims and release recommendation must reference "
                "verification artifacts or execution outputs."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-INVALID/stages/qa/qa-report.md"
                ),
                line_number=15,
            ),
        ),
        ValidationFinding(
            code=UNSUPPORTED_VERDICT_CODE,
            message=(
                "Verdicts `ready` or `ready-with-risks` cannot pair with "
                "release recommendation `hold`."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-INVALID/stages/qa/qa-report.md"
                ),
                line_number=11,
            ),
        ),
        ValidationFinding(
            code=UNSUPPORTED_VERDICT_CODE,
            message=(
                "Ready/proceed-style outcomes are unsupported without concrete "
                "verification evidence references."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-INVALID/stages/qa/qa-report.md"
                ),
                line_number=3,
            ),
        ),
    )

