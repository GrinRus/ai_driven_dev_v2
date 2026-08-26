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

        assert geometry["topbar"]["x"] >= 320
        assert geometry["workspace"]["x"] >= 320
        assert geometry["workspace"]["width"] <= viewport[0] - 320
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


@pytest.mark.parametrize("viewport", ((1280, 900), (1440, 900)))
def test_work_item_detail_uses_split_primary_and_work_item_rails(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"split-rail-{viewport[0]}", "no-run")
    assert fixture.work_item is not None
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")

        primary = page.locator(".topbar .primary-nav")
        secondary = page.locator("#operatorWorkItemsRail")
        primary.wait_for(state="visible")
        secondary.wait_for(state="visible")

        geometry = page.evaluate(
            """() => {
              const box = (selector) => {
                const node = document.querySelector(selector);
                if (!node) return null;
                const rect = node.getBoundingClientRect();
                return {x: rect.x, width: rect.width, right: rect.right};
              };
              return {
                primary: box('.topbar .primary-nav'),
                secondary: box('#operatorWorkItemsRail'),
                workspace: box('.operator-workspace'),
                scrollWidth: document.documentElement.scrollWidth,
              };
            }"""
        )
        assert geometry["primary"]["x"] == 0
        assert 80 <= geometry["primary"]["width"] <= 88
        assert geometry["secondary"]["x"] == geometry["primary"]["width"]
        assert 232 <= geometry["secondary"]["width"] <= 240
        assert geometry["workspace"]["x"] == geometry["secondary"]["right"]
        assert page.locator(
            f'[data-operator-rail-item][data-route-work-item="{fixture.work_item}"]'
        ).count() == 1

        page.locator("#projectInboxButton").click()
        page.locator(".studio-inbox").wait_for(state="visible")
        assert secondary.is_hidden()
        inbox_geometry = page.evaluate(
            """() => {
              const node = document.querySelector('.topbar .primary-nav');
              const workspace = document.querySelector('.operator-workspace');
              return {
                primaryWidth: node.getBoundingClientRect().width,
                workspaceX: workspace.getBoundingClientRect().x,
                workItems: document.querySelectorAll('[data-operator-rail-item]').length,
                scrollWidth: document.documentElement.scrollWidth,
              };
            }"""
        )
        assert 236 <= inbox_geometry["primaryWidth"] <= 248
        assert inbox_geometry["workspaceX"] == inbox_geometry["primaryWidth"]
        assert inbox_geometry["workItems"] == 0
        assert inbox_geometry["scrollWidth"] <= viewport[0]
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (390, 844)))
def test_shared_breadcrumb_uses_project_work_item_and_stage_labels(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"breadcrumb-{viewport[0]}", "no-run")
    assert fixture.work_item is not None
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.locator("#intentChip").get_by_text(
            f"Work Item: {fixture.work_item}", exact=True
        ).wait_for(state="attached")

        breadcrumb = page.locator(".top-context")
        project_label = fixture.project_root.name
        assert page.locator("#projectPath").inner_text() == project_label
        assert page.locator("#topContextProject").inner_text() == project_label
        assert page.locator("#topContextIntent").inner_text() == fixture.work_item
        assert page.locator("#topContextRun").inner_text() == "Idea"
        assert fixture.project_root.as_posix() not in breadcrumb.inner_text()
        assert page.locator("#projectPath").get_attribute("title") == (
            f"Project: {project_label}"
        )
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
        flow.locator(".studio-flow-complete-other").evaluate(
            "element => { element.open = true; }"
        )
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
        assert layout["gridWidth"] >= 280
        assert all(width >= 280 for width in layout["cardWidths"])
        browser_page.diagnostics.assert_clean()
