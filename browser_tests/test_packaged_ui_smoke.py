from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


def test_packaged_operator_ui_launches_in_chromium(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path, playwright
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        response = page.goto(harness.url, wait_until="networkidle")
        assert response is not None and response.ok
        assert page.title() == "AIDD Operator Console"
        page.locator("#onboardingProjectForm").wait_for(state="visible")
        asset = page.request.get(f"{harness.url}operator.css")
        assert asset.ok
        assert '@import url("/operator-layout.css")' in asset.text()
        browser_page.diagnostics.assert_clean()
