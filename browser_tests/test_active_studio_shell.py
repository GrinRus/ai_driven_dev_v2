from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize(
    "fixture_state",
    ("no-run", "running", "blocking-question", "remediation-stale"),
)
def test_active_studio_shell_preserves_context_and_one_primary_action(
    tmp_path: Path,
    fixture_state: str,
) -> None:
    fixture = build_browser_state_fixture(tmp_path / fixture_state, fixture_state)
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        response = browser_page.page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        assert response is not None and response.ok
        assert browser_page.page.locator(".cockpit").get_attribute("data-active-studio") == "true"
        assert (
            browser_page.page.locator("#stageRail").get_attribute("data-studio-stage-navigation")
            == "true"
        )
        assert browser_page.page.locator("[data-studio-context-bar]").count() == (
            0 if fixture_state == "blocking-question" else 1
        )
        assert browser_page.page.locator("[data-primary-action]:visible").count() == 1
        body = browser_page.page.locator("body").inner_text()
        assert fixture.work_item in body
        browser_page.diagnostics.assert_clean()
