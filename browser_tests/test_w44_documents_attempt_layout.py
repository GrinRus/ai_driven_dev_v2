from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", ((1280, 900), (1440, 900)))
def test_documents_keep_navigator_reader_and_context_visible(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"documents-{viewport[0]}",
        "remediation-stale",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa&work_tab=documents&artifact=qa_report",
            wait_until="networkidle",
        )
        tree = page.locator(".stage-document-workbench > #workbenchTree")
        viewer = page.locator(".stage-document-workbench > #artifactViewer")
        tree.wait_for(state="visible")
        viewer.locator('[data-document-canvas-mode="preview"]').wait_for(
            state="visible"
        )
        page.locator("[data-studio-context-bar]").wait_for(state="visible")
        page.locator("[data-intent-phase-stepper]").wait_for(state="visible")

        geometry = page.evaluate(
            """() => {
              const box = (selector) => {
                const node = document.querySelector(selector);
                if (!node) return null;
                const rect = node.getBoundingClientRect();
                return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
              };
              return {
                tree: box('.stage-document-workbench > #workbenchTree'),
                viewer: box('.stage-document-workbench > #artifactViewer'),
                reader: box('#artifactViewer .reader-document-column'),
                inspector: box('#artifactViewer .workbench-sidebar'),
                columns: getComputedStyle(
                  document.querySelector('.stage-document-workbench')
                ).gridTemplateColumns,
                scrollWidth: document.documentElement.scrollWidth,
              };
            }"""
        )

        assert len(geometry["columns"].split()) == 2
        assert geometry["tree"]["width"] >= 180
        assert abs(geometry["tree"]["y"] - geometry["viewer"]["y"]) < 2
        assert geometry["reader"]["width"] > geometry["inspector"]["width"]
        assert geometry["inspector"]["x"] > geometry["reader"]["x"]
        assert geometry["scrollWidth"] <= viewport[0]
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (1440, 900)))
def test_task_attempt_detail_and_live_tray_share_desktop_workbench(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"task-attempt-{viewport[0]}",
        "implementation-task-failed",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement&work_tab=tasks",
            wait_until="networkidle",
        )
        page.evaluate(
            "async () => {"
            "  state.activeTab = 'work';"
            "  state.workDetail = 'tasks';"
            "  state.workItemTab = 'tasks';"
            "  await renderCockpit();"
            "}"
        )
        page.locator("[data-task-workspace]").wait_for(state="visible")
        page.locator('[data-task-select="TL-2"]').click()
        detail = page.locator("[data-task-detail]")
        tray = page.locator("[data-task-attempt-tray]")
        detail.locator("h3").wait_for(state="visible")
        tray.wait_for(state="visible")

        geometry = page.evaluate(
            """() => {
              const box = (selector) => {
                const node = document.querySelector(selector);
                if (!node) return null;
                const rect = node.getBoundingClientRect();
                return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
              };
              return {
                list: box('[data-task-workspace]'),
                detail: box('[data-task-detail]'),
                tray: box('[data-task-attempt-tray]'),
                columns: getComputedStyle(
                  document.querySelector(
                    '.active-studio[data-studio-surface="task-workspace"]'
                  )
                ).gridTemplateColumns,
                scrollWidth: document.documentElement.scrollWidth,
              };
            }"""
        )

        assert len(geometry["columns"].split()) == 2
        assert abs(geometry["list"]["y"] - geometry["detail"]["y"]) < 2
        assert geometry["detail"]["x"] > geometry["list"]["x"]
        assert (
            page.locator(
                '[data-task-attempt-tray][data-active-task-attempt="true"]'
            ).count()
            == 1
        )
        assert geometry["tray"]["y"] < geometry["list"]["y"]
        assert geometry["tray"]["width"] >= geometry["list"]["width"]
        assert page.locator('[data-task-action="resume"]').count() == 1
        assert page.locator("[data-task-action-bar] [data-contextual-runner-control]").count() == 1
        assert geometry["scrollWidth"] <= viewport[0]
        browser_page.diagnostics.assert_clean()
