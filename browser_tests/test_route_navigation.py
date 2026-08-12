from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def test_back_forward_and_reload_restore_studio_detail(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "running", "running")
    query = urlencode(
        {
            "mode": "studio",
            "view": "artifacts",
            "work_item": fixture.work_item,
            "run_id": fixture.run_id,
            "stage": "implement",
            "artifact": "implementation-report.md",
        }
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        response = page.goto(f"{harness.url}?{query}", wait_until="networkidle")
        assert response is not None and response.ok
        page.evaluate("activateTab('logs', {historyMode: 'push'})")
        page.evaluate("activateTab('artifacts', {historyMode: 'push'})")
        assert "view=artifacts" in page.url

        page.go_back(wait_until="networkidle")
        page.evaluate("window.aiddRouteRestore")
        page.wait_for_function(
            "state.activeTab === 'evidence' && state.evidenceDetail === 'logs'"
        )
        assert "view=logs" in page.url

        page.go_forward(wait_until="networkidle")
        page.evaluate("window.aiddRouteRestore")
        page.wait_for_function(
            "state.activeTab === 'evidence' && state.evidenceDetail === 'artifacts'"
        )
        assert "artifact=implementation-report.md" in page.url

        page.reload(wait_until="networkidle")
        restored = page.evaluate(
            "({stage: state.activeStage, run: state.activeRunId, "
            "artifact: state.activeArtifactKey})"
        )
        assert restored == {
            "stage": "implement",
            "run": fixture.run_id,
            "artifact": "implementation-report.md",
        }
        assert browser_page.diagnostics.failed_requests == []
        assert browser_page.diagnostics.cancelled_requests
        assert all(
            "/api/runtime-readiness: net::ERR_ABORTED" in request
            for request in browser_page.diagnostics.cancelled_requests
        )
        browser_page.diagnostics.assert_clean()


def test_work_item_tabs_and_stage_strip_restore_without_duplicate_landmarks(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "running", "running")
    query = urlencode(
        {
            "mode": "studio",
            "work_item": fixture.work_item,
            "run_id": fixture.run_id,
            "stage": "implement",
            "work_tab": "tasks",
        }
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        response = page.goto(f"{harness.url}?{query}", wait_until="networkidle")
        assert response is not None and response.ok
        page.wait_for_function("state.workItemTab === 'tasks'")
        tabs = page.locator("[data-work-item-tab]")
        assert [text.strip() for text in tabs.all_text_contents()] == [
            "Overview", "Tasks", "Documents", "Runs"
        ]
        assert page.locator("[data-work-item-tab][aria-selected='true']").count() == 1
        assert page.locator("[data-work-item-tab='tasks'][aria-selected='true']").count() == 1
        stages = page.locator("#intentPhaseStepper [data-canonical-stage]")
        assert stages.count() == 8
        assert stages.evaluate_all("nodes => nodes.map(node => node.dataset.canonicalStage)") == [
            "idea", "research", "plan", "review-spec", "tasklist", "implement", "review", "qa"
        ]
        assert page.locator("nav[aria-label='Work Item sections']").count() == 1
        assert page.locator("nav[aria-label='Work Item delivery phases']").count() == 1

        page.locator("[data-work-item-tab='tasks']").focus()
        page.keyboard.press("ArrowRight")
        page.wait_for_function("state.workItemTab === 'documents'")
        assert page.locator("[data-work-item-tab='documents'][aria-selected='true']").count() == 1

        page.locator("[data-work-item-tab='runs']").click()
        page.wait_for_function("state.workItemTab === 'runs' && state.workDetail === 'runs'")
        page.reload(wait_until="networkidle")
        page.wait_for_function("state.workItemTab === 'runs' && state.workDetail === 'runs'")
        assert "work_tab=runs" in page.url
        browser_page.diagnostics.assert_clean()
