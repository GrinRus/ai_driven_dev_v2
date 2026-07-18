from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from aidd.core.run_store import run_manifest_path
from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_history_journey_preserves_retained_runs(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"history-{viewport[0]}", "history")
    assert fixture.work_item is not None
    assert fixture.run_id is not None
    current_manifest = run_manifest_path(
        fixture.workspace_root,
        fixture.work_item,
        fixture.run_id,
    )
    source_manifest = run_manifest_path(
        fixture.workspace_root,
        fixture.work_item,
        "run-source",
    )
    before = (_sha256(current_manifest), _sha256(source_manifest))

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=history&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement",
            wait_until="networkidle",
        )
        page.locator("[data-studio-history]").wait_for(state="visible")
        assert page.locator("[data-history-frame]").count() >= 3
        assert page.locator("[data-studio-run-comparison]").is_visible()
        assert page.locator("[data-history-lineage-parent='run-source']").is_visible()
        archive = page.locator("[data-studio-history-archive]")
        assert archive.get_attribute("data-archive-state") == "archived"
        assert "Retained after History acceptance" in archive.inner_text()

        page.get_by_role("button", name="Inspect parent run").click()
        page.wait_for_url("**run_id=run-source**")
        assert "run-source" in page.url
        page.go_back(wait_until="networkidle")
        page.locator("[data-history-lineage-current='run-browser']").wait_for(state="visible")
        page.reload(wait_until="networkidle")
        assert page.locator("[data-history-lineage-parent='run-source']").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        navigation_aborts = [
            failure
            for failure in browser_page.diagnostics.failed_requests
            if "/api/dashboard" in failure and "net::ERR_ABORTED" in failure
        ]
        assert browser_page.diagnostics.failed_requests == navigation_aborts
        browser_page.diagnostics.failed_requests.clear()
        browser_page.diagnostics.assert_clean()
        assert (_sha256(current_manifest), _sha256(source_manifest)) == before
