from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def test_studio_observes_durable_external_run_without_fake_progress(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "running", "running")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        browser_page.page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        observation = browser_page.page.locator('[data-studio-observation="durable-external"]')
        observation.wait_for(state="visible")
        assert "outside this browser session" in observation.inner_text()
        assert "Open persisted logs" in observation.inner_text()
        assert "%" not in observation.inner_text()
        observation.locator('[data-tab-shortcut="logs"]').click()
        browser_page.page.locator("#cockpitContent").wait_for(state="visible")
        assert "runtime.log" in browser_page.page.locator("#cockpitContent").inner_text().lower()
        browser_page.diagnostics.assert_clean()
