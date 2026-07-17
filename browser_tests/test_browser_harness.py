from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness


def test_harness_opens_every_contract_viewport_and_cleans_up(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    with sync_playwright() as playwright, operator_browser_harness(
        project_root, playwright
    ) as harness:
        process = harness.server_process
        for viewport in VIEWPORTS:
            with harness.open_page(viewport) as browser_page:
                response = browser_page.page.goto(harness.url, wait_until="networkidle")
                assert response is not None and response.ok
                browser_page.page.locator("#onboardingProjectForm").wait_for(state="visible")
                assert browser_page.page.viewport_size == {
                    "width": viewport[0],
                    "height": viewport[1],
                }
                browser_page.diagnostics.assert_clean()

    assert process.poll() is not None
    assert not (project_root / ".aidd").exists()
