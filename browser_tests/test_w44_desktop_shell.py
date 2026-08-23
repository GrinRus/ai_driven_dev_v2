from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", ((1280, 900), (1440, 900)))
def test_desktop_shell_keeps_rail_tabs_stage_strip_and_decision_column_in_view(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"desktop-{viewport[0]}", "no-run")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")

        page.locator(".operator-workspace").wait_for(state="visible")
        action = page.locator("#globalNextActionButton")
        action.wait_for(state="visible")

        geometry = page.evaluate(
            """() => {
              const box = (selector) => {
                const node = document.querySelector(selector);
                if (!node) return null;
                const rect = node.getBoundingClientRect();
                return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
              };
              const style = (selector) => {
                const node = document.querySelector(selector);
                if (!node) return null;
                const computed = getComputedStyle(node);
                return {
                  gridArea: computed.gridArea,
                  position: computed.position,
                  marginLeft: computed.marginLeft,
                };
              };
              return {
                topbar: box('.topbar'),
                rail: box('.topbar .primary-nav'),
                railStyle: style('.topbar .primary-nav'),
                workspace: box('.operator-workspace'),
                context: style('.intent-context-region'),
                tabs: style('.work-item-tabs'),
                phases: style('.intent-phase-region'),
                decision: style('.intent-decision-surface'),
                content: style('.intent-document-surface'),
                scrollWidth: document.documentElement.scrollWidth,
              };
            }"""
        )

        assert geometry["topbar"]["x"] >= 232
        assert geometry["workspace"]["x"] >= 232
        assert geometry["workspace"]["width"] <= viewport[0] - 232
        assert geometry["rail"]["x"] == 14
        assert geometry["railStyle"]["position"] == "fixed"
        assert geometry["context"]["gridArea"] == "context"
        assert geometry["tabs"]["gridArea"] == "tabs"
        assert geometry["phases"]["gridArea"] == "phases"
        assert geometry["decision"]["gridArea"] == "decision"
        assert geometry["content"]["gridArea"] == "content"

        action_bounds = action.bounding_box()
        assert action_bounds is not None
        assert action_bounds["x"] >= geometry["workspace"]["x"]
        assert action_bounds["x"] + action_bounds["width"] <= viewport[0]
        assert action_bounds["y"] + action_bounds["height"] <= viewport[1]
        assert geometry["scrollWidth"] <= viewport[0]
        browser_page.diagnostics.assert_clean()
