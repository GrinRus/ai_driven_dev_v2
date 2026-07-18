from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.journey_support import configure_sleeping_fixture_runtime
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "review-qa"


def _open_gate(page: Page, detail: str) -> None:
    page.evaluate(
        "async (detail) => {"
        "  state.activeTab = 'work';"
        "  state.workDetail = detail;"
        "  if (detail === 'review-findings') await renderReviewFindings();"
        "  else await renderQaVerdict();"
        "}",
        detail,
    )
    page.locator('[data-studio-quality-gate="review"], [data-studio-quality-gate="qa"]')\
        .wait_for(state="visible")


def _journey_url(base: str, work_item: str, run_id: str) -> str:
    return (
        f"{base}?ui=studio&mode=studio&work_item={work_item}"
        f"&run_id={run_id}&stage=qa"
    )


def test_review_qa_gate_blocks_rejected_and_not_ready_evidence_across_viewports(
    tmp_path: Path,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / "review-qa-rejected",
        "review-qa-rejected",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness:
        for viewport in VIEWPORTS:
            with harness.open_page(viewport) as browser_page:
                page = browser_page.page
                page.goto(
                    _journey_url(harness.url, fixture.work_item or "", fixture.run_id or ""),
                    wait_until="networkidle",
                )
                _open_gate(page, "review-findings")
                review = page.locator('[data-studio-quality-gate="review"]')
                assert review.get_attribute("data-review-status") == "rejected"
                assert review.locator('[data-review-finding="RV-1"]').count() == 1
                assert "TL-2-AC1" in review.inner_text()
                assert "EV-1" in review.inner_text()
                assert review.get_by_role("button", name="Proceed to QA").is_disabled()

                _open_gate(page, "qa-verdict")
                qa = page.locator('[data-studio-quality-gate="qa"]')
                assert qa.get_attribute("data-qa-verdict") == "not-ready"
                assert "QA-RISK-1" in qa.inner_text()
                assert "QA-ISSUE-1" in qa.inner_text()
                assert qa.get_by_role("button", name="Accept complete").is_disabled()
                dashboard = page.evaluate(
                    "async () => (await (await fetch('/api/dashboard?run_id=run-browser')).json())"
                )
                assert dashboard.get("terminal_handoff") is None
                assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
                assert_rendered_geometry(page)
                browser_page.diagnostics.assert_clean()


def test_selected_review_finding_uses_one_durable_remediation_request(
    tmp_path: Path,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / "review-remediation",
        "review-qa-rejected",
    )
    configure_sleeping_fixture_runtime(fixture.project_root)
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(
            _journey_url(harness.url, fixture.work_item or "", fixture.run_id or ""),
            wait_until="networkidle",
        )
        _open_gate(page, "review-findings")
        with page.expect_response(
            lambda response: urlsplit(response.url).path == "/api/remediation/launch"
        ) as launched:
            page.get_by_role("button", name="Send selected to implement").click()
        assert launched.value.status == 202
        requests = page.evaluate(
            "async () => (await (await fetch("
            "'/api/remediation/requests?run_id=run-browser')).json())"
        )
        assert len(requests["requests"]) == 1
        request = requests["requests"][0]
        assert request["run_id"] == fixture.run_id
        assert request["source_stage"] == "review"
        assert request["source_ids"] == ["RV-1"]
        assert request["target_stage"] == "implement"


def test_stale_qa_has_no_terminal_handoff_and_requires_durable_rerun(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / "review-qa-stale",
        "remediation-stale",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(
            _journey_url(harness.url, fixture.work_item or "", fixture.run_id or ""),
            wait_until="networkidle",
        )
        _open_gate(page, "qa-verdict")
        readback = page.locator('[data-remediation-readback="qa"]')
        assert "Stale stages: Review → QA" in readback.inner_text()
        assert "Terminal handoff stays blocked" in readback.inner_text()
        assert readback.get_by_role("button", name="Rerun stale downstream").count() == 1
        dashboard = page.evaluate(
            "async () => (await (await fetch('/api/dashboard?run_id=run-browser')).json())"
        )
        assert dashboard.get("terminal_handoff") is None
        page.reload(wait_until="networkidle")
        _open_gate(page, "qa-verdict")
        assert page.locator('[data-remediation-readback="qa"]').count() == 1
        browser_page.diagnostics.assert_clean()
