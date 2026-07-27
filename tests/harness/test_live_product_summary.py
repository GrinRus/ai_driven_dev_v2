from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.live_product_summary import derive_live_product_acceptance


def _manual_evidence(
    tmp_path: Path,
    *,
    decision: str,
) -> tuple[tuple[Path, ...], tuple[Path, ...], Path]:
    audit = tmp_path / "stage-quality-audits" / "qa.md"
    audit.parent.mkdir()
    audit.write_text("# Audit\n", encoding="utf-8")
    reports = tuple(
        tmp_path / filename
        for filename in (
            "flow-quality-report.md",
            "code-quality-report.md",
            "quality-report.md",
        )
    )
    for report in reports:
        report.write_text(
            (
                "# Quality\n\n"
                f"- Final decision: {decision}\n"
                if report.name == "quality-report.md"
                else "# Review\n"
            ),
            encoding="utf-8",
        )
    return (audit,), reports, reports[-1]


def test_pre_review_execution_pass_is_not_counted_clean(tmp_path: Path) -> None:
    status = derive_live_product_acceptance(
        flow_status="pass",
        verdict_status="pass",
        grader_status="pass",
        stage_quality_audit_paths=(tmp_path / "missing-audit.md",),
        final_report_paths=(tmp_path / "missing-report.md",),
        quality_report_path=tmp_path / "quality-report.md",
        legacy_degraded=False,
    )

    assert status.execution_pass is True
    assert status.quality_reviewed is False
    assert status.counted_clean is False
    assert status.not_clean_reasons == ("manual quality evidence is incomplete",)


@pytest.mark.parametrize(
    ("decision", "legacy_degraded", "counted_clean", "reason"),
    (
        ("not-counted", False, False, "quality-report.md does not record counted-clean"),
        ("counted-clean", False, True, None),
        ("counted-clean", True, False, "bundle uses legacy degraded evidence"),
    ),
)
def test_post_review_status_is_derived_from_primary_evidence(
    tmp_path: Path,
    decision: str,
    legacy_degraded: bool,
    counted_clean: bool,
    reason: str | None,
) -> None:
    audits, reports, quality_report = _manual_evidence(tmp_path, decision=decision)

    status = derive_live_product_acceptance(
        flow_status="pass",
        verdict_status="pass",
        grader_status="pass",
        stage_quality_audit_paths=audits,
        final_report_paths=reports,
        quality_report_path=quality_report,
        legacy_degraded=legacy_degraded,
    )

    assert status.quality_reviewed is True
    assert status.counted_clean is counted_clean
    if reason is None:
        assert not status.not_clean_reasons
    else:
        assert reason in status.not_clean_reasons


def test_manual_quality_stop_is_independent_from_execution_verdict(
    tmp_path: Path,
) -> None:
    audits, reports, quality_report = _manual_evidence(
        tmp_path,
        decision="counted-clean",
    )

    status = derive_live_product_acceptance(
        flow_status="manual-quality-stop",
        verdict_status=None,
        grader_status=None,
        stage_quality_audit_paths=audits,
        final_report_paths=reports,
        quality_report_path=quality_report,
        legacy_degraded=False,
    )

    assert status.execution_pass is False
    assert status.quality_reviewed is True
    assert status.counted_clean is False
    assert status.manual_quality_stop is True
    assert "manual quality review stopped the run" in status.not_clean_reasons
