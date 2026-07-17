from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import BROWSER_FIXTURE_STATES, build_browser_state_fixture


@pytest.mark.parametrize("state", BROWSER_FIXTURE_STATES)
def test_provider_free_state_opens_through_public_ui(tmp_path: Path, state: str) -> None:
    fixture = build_browser_state_fixture(tmp_path / state, state)
    assert fixture.project_root.resolve().is_relative_to(tmp_path.resolve())
    assert fixture.expected_route_intent in {"setup", "inbox", "studio", "history"}
    assert fixture.context_keys
    assert fixture.primary_surface
    assert fixture.primary_action

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        response = browser_page.page.goto(harness.url, wait_until="networkidle")
        assert response is not None and response.ok
        payload = browser_page.page.evaluate(
            "async (path) => (await fetch(path)).json()",
            fixture.api_path,
        )
        serialized = str(payload).lower().replace("_", "-")
        assert fixture.state_marker in serialized, (state, payload)
        body_text = browser_page.page.locator("body").inner_text()
        assert fixture.primary_action.lower() in body_text.lower(), (state, body_text)
        browser_page.diagnostics.assert_clean()
