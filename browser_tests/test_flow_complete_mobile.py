from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", ((320, 568), (390, 844)))
def test_flow_complete_keeps_terminal_decision_in_first_mobile_viewport(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"terminal-{viewport[0]}", "terminal-handoff")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa",
            wait_until="networkidle",
        )
        flow = page.locator("[data-studio-flow-complete]")
        flow.wait_for(state="visible")
        hero = flow.locator(".flow-complete-hero")
        decision = flow.locator("[data-core-recommended-outcome]")
        assert hero.is_visible()
        assert decision.is_visible()
        decision_box = decision.bounding_box()
        assert decision_box is not None and decision_box["y"] < viewport[1]
        primary = decision.locator("button[data-next-flow-action]")
        primary_box = primary.bounding_box()
        assert primary_box is not None and primary_box["height"] >= 44
        disclosure = flow.locator(".studio-flow-complete-other")
        assert disclosure.locator("summary").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser_page.diagnostics.assert_clean()
