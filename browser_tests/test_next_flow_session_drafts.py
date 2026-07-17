from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def test_follow_up_definition_survives_back_and_reload(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "follow-up", "terminal-handoff")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(harness.url, wait_until="networkidle")
        page.locator('[data-next-flow-action="start-follow-up-flow"]').first.click()
        page.locator("[data-next-flow-continue]").click()
        title = page.locator('[data-follow-up-field="title"]')
        title.wait_for(state="visible")
        title.fill("Follow up on the retained QA evidence")

        page.locator("[data-next-flow-back-to-sources]").click()
        page.locator("[data-next-flow-continue]").click()
        title.wait_for(state="visible")
        assert title.input_value() == "Follow up on the retained QA evidence"

        page.reload(wait_until="networkidle")
        page.locator('[data-next-flow-action="start-follow-up-flow"]').first.click()
        page.locator("[data-next-flow-continue]").click()
        restored = page.locator('[data-follow-up-field="title"]')
        restored.wait_for(state="visible")
        assert restored.input_value() == "Follow up on the retained QA evidence"
        assert page.evaluate(
            "readOperatorDraft(nextFlowBrowserDraftIdentity('start-follow-up-flow')) !== null"
        )
        browser_page.diagnostics.assert_clean()
