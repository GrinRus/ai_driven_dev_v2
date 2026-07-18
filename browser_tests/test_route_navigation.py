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
        browser_page.diagnostics.assert_clean()
