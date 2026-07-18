from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def test_studio_document_canvas_uses_safe_workbench_for_all_modes(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "qa-decision", "qa-decision")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        response = browser_page.page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        assert response is not None and response.ok
        canvas = browser_page.page.locator("#studioDocumentCanvas")
        canvas.locator('[data-document-canvas-mode="preview"]').wait_for(state="visible")
        for mode in ("source", "diff", "preview"):
            canvas.locator(f'[data-artifact-mode="{mode}"]').click()
            canvas.locator(f'[data-document-canvas-mode="{mode}"]').wait_for(state="visible")
        workbench_requests = [
            urlsplit(url).path
            for url, status in browser_page.diagnostics.http_statuses
            if urlsplit(url).path == "/api/stage/workbench" and status == 200
        ]
        assert len(workbench_requests) >= 3
        browser_page.diagnostics.assert_clean()
