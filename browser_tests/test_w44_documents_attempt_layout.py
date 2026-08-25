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
                return {
                  x: rect.x,
                  y: rect.y,
                  width: rect.width,
                  height: rect.height,
                  bottom: rect.bottom,
                };
              };
              return {
                tree: box('.stage-document-workbench > #workbenchTree'),
                viewer: box('.stage-document-workbench > #artifactViewer'),
                reader: box('#artifactViewer .reader-document-column'),
                inspector: box('#artifactViewer .workbench-sidebar'),
                brief: box('#artifactViewer .reader-brief-compact'),
                body: box('#artifactViewer .reader-body-content'),
                headingMap: box('#artifactViewer [data-reader-heading-map]'),
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
        assert geometry["brief"]["y"] + geometry["brief"]["height"] <= geometry["body"]["y"]
        assert geometry["body"]["y"] < viewport[1]
        assert geometry["headingMap"]["y"] < viewport[1]
        assert page.locator("#artifactViewer [data-reader-freshness]").count() == 1
        assert page.locator("#artifactViewer [data-reader-heading-map]").get_by_text(
            "Heading map", exact=True
        ).count() == 1
        assert page.locator("#artifactViewer [data-artifact-mode='write']").count() == 0
        assert geometry["scrollWidth"] <= viewport[0]
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (1440, 900), (390, 844)))
def test_markdown_workspace_uses_target_context_inspector_and_compact_reader(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"documents-target-{viewport[0]}",
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
        viewer = page.locator("#artifactViewer")
        viewer.locator('[data-document-canvas-mode="preview"]').wait_for(state="visible")

        context = viewer.locator("[data-document-context-inspector]")
        context.wait_for(state="visible")
        assert context.locator("[data-document-context-contract]").is_visible()
        assert context.locator("[data-document-context-provenance]").is_visible()
        assert context.locator("[data-document-context-source]").is_visible()
        assert context.locator("[data-document-context-actions]").is_visible()
        assert context.locator('[data-aidd-primary-action]:visible').count() == 1
        assert (
            context.locator('[data-document-context-action="request-change"]').inner_text()
            == "Request change"
        )
        assert context.locator('[data-document-context-action="return-to-task"]').is_visible()
        assert viewer.locator(".document-context-readonly").is_visible()
        assert viewer.locator("[data-reader-heading-map]").is_visible()
        assert viewer.locator("[data-reader-freshness]").count() == 1
        assert viewer.locator(".reader-brief-compact-main:visible").count() == 0
        assert page.locator("body.markdown-workspace-mode").count() == 1
        assert (
            page.locator(".stage-document-workbench .artifact-category-note:visible").count()
            == 0
        )

        if viewport[0] > 1120:
            body_box = viewer.locator(".reader-body-content").bounding_box()
            brief_box = viewer.locator(".reader-brief-compact").bounding_box()
            assert body_box is not None and body_box["y"] < viewport[1]
            assert brief_box is not None and brief_box["height"] <= 40

        assert page.evaluate("document.documentElement.scrollWidth") <= viewport[0]
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
                return {
                  x: rect.x,
                  y: rect.y,
                  width: rect.width,
                  height: rect.height,
                  bottom: rect.bottom,
                };
              };
              return {
                list: box('[data-task-workspace]'),
                detail: box('[data-task-detail]'),
                tray: box('[data-task-attempt-tray]'),
                live: box('[data-task-live-output]'),
                livePosition: getComputedStyle(
                    document.querySelector('[data-task-live-output]')
                ).position,
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
        assert geometry["tray"]["x"] >= geometry["detail"]["x"]
        assert geometry["tray"]["width"] <= geometry["detail"]["width"]
        assert (
            page.locator(
                '[data-task-attempt-tray][data-active-task-attempt="true"]'
            ).count()
            == 1
        )
        assert page.locator("[data-task-live-output]").count() == 1
        assert page.locator("[data-task-attempt-tray] [data-task-attempt-output]").count() == 0
        assert geometry["livePosition"] == "fixed"
        assert geometry["live"]["y"] >= 0
        assert geometry["live"]["bottom"] <= viewport[1]
        assert geometry["live"]["y"] < viewport[1]
        assert geometry["list"]["bottom"] <= geometry["live"]["y"] + 1
        assert geometry["detail"]["bottom"] <= geometry["live"]["y"] + 1
        assert geometry["live"]["width"] >= geometry["list"]["width"]
        assert page.locator('[data-task-action="resume"]').count() == 1
        assert page.locator("[data-task-action-bar] [data-contextual-runner-control]").count() == 1
        assert geometry["scrollWidth"] <= viewport[0]
        browser_page.diagnostics.assert_clean()
