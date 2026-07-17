from __future__ import annotations

import json
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_evidence import (
    BrowserCleanupStatus,
    BrowserEvidenceWriter,
)
from browser_tests.browser_harness import BrowserDiagnostics


def test_browser_evidence_is_bounded_atomic_and_viewport_complete(tmp_path: Path) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.set_content(
                """
                <style>
                  body { margin: 0; background: #fff; color: #111; }
                  button { min-width: 44px; min-height: 44px; }
                </style>
                <header id="context" data-aidd-sticky-header style="height:64px">
                  Work item
                </header>
                <button id="primary" data-aidd-primary-action>Run workflow</button>
                """
            )
            diagnostics = BrowserDiagnostics(
                console_errors=["first", "second", "third"],
                http_statuses=[("http://127.0.0.1/", 200)],
            )
            writer = BrowserEvidenceWriter(tmp_path / "evidence", diagnostic_limit=2)
            record = writer.capture(
                fixture="setup",
                page=page,
                diagnostics=diagnostics,
            )
            report_path = writer.commit(
                cleanup=BrowserCleanupStatus(
                    page_closed=True,
                    context_closed=True,
                    browser_closed=True,
                    server_stopped=True,
                    workspace_removed=True,
                )
            )
        finally:
            browser.close()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["cleanup"] == {
        "browser_closed": True,
        "context_closed": True,
        "page_closed": True,
        "server_stopped": True,
        "workspace_removed": True,
    }
    assert len(payload["viewports"]) == 1
    viewport = payload["viewports"][0]
    assert viewport["fixture"] == "setup"
    assert (viewport["viewport_width"], viewport["viewport_height"]) == (390, 844)
    assert viewport["screenshot_path"] == "screenshots/setup-390x844.png"
    assert (report_path.parent / viewport["screenshot_path"]).is_file()
    assert viewport["console_errors"] == ["first", "second"]
    assert viewport["dropped_diagnostics"] == 1
    assert viewport["accessibility_results"] == []
    assert viewport["geometry_results"] == []
    assert viewport["dom_measurements"]["sticky_headers"][0]["selector"] == "#context"
    assert viewport["dom_measurements"]["primary_actions"][0]["selector"] == "#primary"
    assert not report_path.with_suffix(".json.tmp").exists()
    assert record.screenshot_path == viewport["screenshot_path"]


def test_browser_evidence_rejects_unbounded_fixture_path(tmp_path: Path) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.set_content("<p>Fixture</p>")
            writer = BrowserEvidenceWriter(tmp_path / "evidence")
            with pytest.raises(ValueError, match="unsafe browser fixture name"):
                writer.capture(
                    fixture="../escape",
                    page=page,
                    diagnostics=BrowserDiagnostics(),
                )
        finally:
            browser.close()
