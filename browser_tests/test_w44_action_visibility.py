from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import operator_browser_harness, wait_for_history_surface
from browser_tests.state_fixtures import build_browser_state_fixture


def _assert_non_launch_surface_has_no_global_launch(page: Page) -> None:
    assert page.locator(".intent-decision-surface:visible").count() == 0
    technical_status = page.locator(
        '#technicalDecisionStatus:visible, '
        '[data-current-decision-stable-id="technicalDecisionStatus"]:visible'
    )
    assert technical_status.count() == 0
    assert page.locator("#globalNextActionButton:visible").count() == 0
    assert page.locator("#nextActionButton:visible").count() == 0
    assert page.locator("[data-contextual-runner-control]").count() == 0
    assert page.locator("#runtimeSettings").is_hidden()


def test_inbox_does_not_require_or_render_a_runner(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "inbox", "no-run")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.locator("#projectInboxButton").click()
        page.locator(".studio-inbox").wait_for(state="visible")
        _assert_non_launch_surface_has_no_global_launch(page)
        browser_page.diagnostics.assert_clean()


def test_history_is_read_only_without_runner_or_global_launch(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "history", "history")
    assert fixture.work_item and fixture.run_id
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        query = urlencode(
            {
                "mode": "history",
                "work_item": fixture.work_item,
                "run_id": fixture.run_id,
                "stage": "implement",
            }
        )
        page.goto(
            f"{harness.url}?{query}",
            wait_until="domcontentloaded",
        )
        wait_for_history_surface(page, work_item=fixture.work_item, run_id=fixture.run_id)
        _assert_non_launch_surface_has_no_global_launch(page)
        browser_page.diagnostics.assert_clean()


def test_generated_documents_do_not_render_a_launch_control(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "documents", "remediation-stale")
    assert fixture.work_item and fixture.run_id
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        query = urlencode(
            {
                "mode": "studio",
                "work_item": fixture.work_item,
                "run_id": fixture.run_id,
                "stage": "qa",
                "work_tab": "documents",
            }
        )
        page.goto(
            f"{harness.url}?{query}",
            wait_until="networkidle",
        )
        page.locator("#intentContent").wait_for(state="visible")
        _assert_non_launch_surface_has_no_global_launch(page)
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((320, 568), (1280, 900)))
def test_flow_complete_keeps_only_the_core_recommended_primary_action(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"terminal-{viewport[0]}", "terminal-handoff")
    assert fixture.work_item and fixture.run_id
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        query = urlencode(
            {
                "mode": "studio",
                "work_item": fixture.work_item,
                "run_id": fixture.run_id,
                "stage": "qa",
            }
        )
        page.goto(
            f"{harness.url}?{query}",
            wait_until="networkidle",
        )
        flow = page.locator("[data-studio-flow-complete]")
        flow.wait_for(state="visible")
        _assert_non_launch_surface_has_no_global_launch(page)
        assert flow.locator("[data-primary-action]:visible").count() == 1
        browser_page.diagnostics.assert_clean()
