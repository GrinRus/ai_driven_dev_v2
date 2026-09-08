from __future__ import annotations

import pytest

from aidd.core.evidence_freshness import (
    EvidenceFreshness,
    EvidenceFreshnessRequest,
    EvidenceFreshnessStatus,
    classify_evidence_freshness,
)
from aidd.evals.reporting import build_scenario_summary_row, render_eval_summary_markdown
from aidd.evals.verdicts import build_scenario_verdict, render_scenario_verdict_markdown


def _freshness(status: EvidenceFreshnessStatus) -> EvidenceFreshness:
    request = EvidenceFreshnessRequest(
        candidate_sha="a" * 40,
        evidence_sha="a" * 40,
        evidence_schema_version=1,
        target_pin="pin-a",
        evidence_target_pin="pin-a",
        locator="reports/evals/run-report/verdict.md",
    )
    if status is EvidenceFreshnessStatus.STALE:
        request = EvidenceFreshnessRequest(
            candidate_sha=request.candidate_sha,
            evidence_sha="b" * 40,
            evidence_schema_version=request.evidence_schema_version,
            target_pin=request.target_pin,
            evidence_target_pin=request.evidence_target_pin,
            locator=request.locator,
        )
    elif status is EvidenceFreshnessStatus.INCOMPATIBLE:
        request = EvidenceFreshnessRequest(
            candidate_sha=request.candidate_sha,
            evidence_sha=request.evidence_sha,
            evidence_schema_version=2,
            target_pin=request.target_pin,
            evidence_target_pin=request.evidence_target_pin,
            locator=request.locator,
        )
    elif status is EvidenceFreshnessStatus.UNAVAILABLE:
        request = EvidenceFreshnessRequest(
            candidate_sha=None,
            evidence_sha=request.evidence_sha,
            evidence_schema_version=request.evidence_schema_version,
            target_pin=request.target_pin,
            evidence_target_pin=request.evidence_target_pin,
            locator=request.locator,
        )
    return classify_evidence_freshness(request)


@pytest.mark.parametrize("status", tuple(EvidenceFreshnessStatus))
def test_report_and_verdict_preserve_each_freshness_state_and_reason(
    status: EvidenceFreshnessStatus,
) -> None:
    freshness = _freshness(status)
    verdict = build_scenario_verdict(
        scenario_id="DET-FRESHNESS",
        run_id="run-freshness",
        runtime_id="generic-cli",
        status="pass",
        summary="Verdict history remains pass.",
        created_at_utc="2026-09-08T00:00:00Z",
        freshness=freshness,
    )
    row = build_scenario_summary_row(verdict=verdict, duration_seconds=1.0)

    assert verdict.status == "pass"
    assert row.verdict_status == "pass"
    assert row.freshness == freshness
    summary = render_eval_summary_markdown(scenario_rows=(row,))
    verdict_markdown = render_scenario_verdict_markdown(verdict)
    assert "| Freshness | Freshness Reason |" in summary
    assert f"`{status.value}`" in summary
    assert freshness.reason in summary
    assert f"- State: `{status.value}`" in verdict_markdown
    assert f"- Reason: {freshness.reason}" in verdict_markdown
