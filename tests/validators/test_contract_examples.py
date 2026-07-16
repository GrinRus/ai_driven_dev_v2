from pathlib import Path

import pytest
from contract_fixtures import (
    EXAMPLES_ROOT,
    SUCCESS_EXAMPLES,
    run_contract_fixture,
)


@pytest.mark.parametrize(("stage", "example_root"), SUCCESS_EXAMPLES.items())
def test_success_examples_pass_the_full_validator_stack(
    tmp_path: Path,
    stage: str,
    example_root: Path,
) -> None:
    result = run_contract_fixture(
        tmp_path=tmp_path,
        stage=stage,
        example_root=example_root,
    )

    assert result.finding_codes == ()
    for report in (result.source_report, result.generated_report):
        assert report.verdict == "pass"
        assert report.findings == ()
        total_issues = report.field("total_issues")
        assert total_issues is not None
        assert total_issues.value == "0"


@pytest.mark.parametrize(
    ("stage", "example_root", "expected_codes"),
    (
        (
            "research",
            EXAMPLES_ROOT / "research" / "unresolved",
            ("CROSS-BLOCKING-UNANSWERED",),
        ),
        (
            "plan",
            EXAMPLES_ROOT / "plan" / "invalid",
            (
                "SEM-INCOMPLETE-SECTION",
                "SEM-INCOMPLETE-SECTION",
                "CROSS-BLOCKING-UNANSWERED",
            ),
        ),
        (
            "implement",
            EXAMPLES_ROOT / "implement" / "repair-needed",
            (
                "SEM-INCOMPLETE-EXECUTION-SUMMARY",
                "SEM-INCOMPLETE-EXECUTION-SUMMARY",
                "SEM-MISSING-DIFF-EVIDENCE",
                "SEM-UNVERIFIABLE-CHECK-CLAIM",
            ),
        ),
        (
            "review",
            EXAMPLES_ROOT / "review" / "repair-needed",
            (
                "SEM-INCOMPLETE-SECTION",
                "SEM-INCOMPLETE-SECTION",
                "SEM-INCOMPLETE-SECTION",
                "SEM-UNSUPPORTED-CLAIM",
            ),
        ),
        (
            "qa",
            EXAMPLES_ROOT / "qa" / "repair-needed",
            (
                "SEM-RISK-UNDERREPORT",
                "SEM-RISK-UNDERREPORT",
                "SEM-MISSING-EVIDENCE-REF",
                "SEM-UNSUPPORTED-VERDICT",
            ),
        ),
    ),
)
def test_invalid_and_repair_examples_emit_exact_codes(
    tmp_path: Path,
    stage: str,
    example_root: Path,
    expected_codes: tuple[str, ...],
) -> None:
    result = run_contract_fixture(
        tmp_path=tmp_path,
        stage=stage,
        example_root=example_root,
    )

    assert result.finding_codes == expected_codes
    for report in (result.source_report, result.generated_report):
        assert report.verdict == "fail"
        assert tuple(finding.code for finding in report.findings) == expected_codes
        total_issues = report.field("total_issues")
        assert total_issues is not None
        assert total_issues.value == str(len(expected_codes))
