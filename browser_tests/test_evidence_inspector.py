from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def test_studio_evidence_inspector_is_value_conditional(tmp_path: Path) -> None:
    no_run = build_browser_state_fixture(tmp_path / "no-run", "no-run")
    with sync_playwright() as playwright, operator_browser_harness(
        no_run.project_root,
        playwright,
        work_item=no_run.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        browser_page.page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        assert browser_page.page.locator("#studioEvidenceInspector:visible").count() == 0
        browser_page.diagnostics.assert_clean()

    qa = build_browser_state_fixture(tmp_path / "qa-decision", "qa-decision")
    with sync_playwright() as playwright, operator_browser_harness(
        qa.project_root,
        playwright,
        work_item=qa.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        browser_page.page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        inspector = browser_page.page.locator("#studioEvidenceInspector:visible")
        inspector.wait_for(state="visible")
        assert inspector.locator("[data-inspector-section]").count() > 0
        browser_page.diagnostics.assert_clean()
