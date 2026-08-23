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
                  background: computed.backgroundColor,
                  color: computed.color,
                  gridArea: computed.gridArea,
                  position: computed.position,
                  marginLeft: computed.marginLeft,
                };
              };
              return {
                topbar: box('.topbar'),
                rail: box('.topbar .primary-nav'),
                railStyle: style('.topbar .primary-nav'),
                railButtonStyle: style('.topbar .primary-nav button'),
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
        assert geometry["rail"]["x"] == 0
        assert geometry["railStyle"]["position"] == "fixed"
        assert geometry["railStyle"]["background"] == "rgb(7, 24, 46)"
        assert geometry["railButtonStyle"]["color"] == "rgb(219, 230, 247)"
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


def test_desktop_flow_complete_reclaims_empty_decision_column(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "terminal", "terminal-handoff")
    assert fixture.work_item is not None
    assert fixture.run_id is not None
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa",
            wait_until="domcontentloaded",
        )
        flow = page.locator("[data-studio-flow-complete]")
        flow.wait_for(state="visible")
        flow.locator(".studio-flow-complete-other summary").click()
        page.wait_for_function("state.terminalOtherActionsOpen === true")

        layout = page.evaluate(
            """() => {
              const workspace = document.querySelector('.operator-workspace');
              const grid = document.querySelector('.next-flow-actions-grid');
              const cards = [...document.querySelectorAll('.next-flow-action-card')];
              const workspaceStyle = getComputedStyle(workspace);
              return {
                columns: workspaceStyle.gridTemplateColumns,
                cardWidths: cards.map(card => card.getBoundingClientRect().width),
                gridWidth: grid.getBoundingClientRect().width,
              };
            }"""
        )

        assert len(layout["columns"].split()) == 1
        assert layout["gridWidth"] >= 4 * 100
        assert all(width >= 100 for width in layout["cardWidths"])
        browser_page.diagnostics.assert_clean()
