from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


@pytest.mark.parametrize(
    "query",
    (
        "",
        "?ui=legacy",
        "?ui=studio",
        "?ui=unknown",
    ),
)
def test_retired_presentation_selector_always_resolves_studio(
    tmp_path: Path,
    query: str,
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        response = browser_page.page.goto(f"{harness.url}{query}", wait_until="networkidle")
        assert response is not None and response.ok
        browser_page.page.locator("#onboardingProjectForm").wait_for(state="visible")
        root = browser_page.page.locator("html")
        assert root.get_attribute("data-presentation-requested") == "studio"
        assert root.get_attribute("data-presentation-effective") == "studio"
        requested_paths = {
            urlsplit(response_url).path
            for response_url, _ in browser_page.diagnostics.http_statuses
        }
        assert "/api/onboarding/state" in requested_paths
        assert not any(path.startswith("/api/studio") for path in requested_paths)
        browser_page.diagnostics.assert_clean()
