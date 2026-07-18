from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import RUN_ID, WORK_ITEM, build_browser_state_fixture


@pytest.mark.parametrize(
    ("fixture_state", "section", "stage"),
    (
        ("blocking-question", "needs-decision", "idea"),
        ("no-run", "ready-to-continue", "idea"),
        ("terminal-handoff", "flow-complete", "qa"),
    ),
)
def test_studio_inbox_routes_each_durable_section_to_exact_context(
    tmp_path: Path,
    fixture_state: str,
    section: str,
    stage: str,
) -> None:
    fixture = build_browser_state_fixture(tmp_path / fixture_state, fixture_state)
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        response = browser_page.page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        assert response is not None and response.ok
        browser_page.page.locator('[data-tab-shortcut="project-home"]').click()
        inbox_section = browser_page.page.locator(f'[data-inbox-section="{section}"]')
        inbox_section.locator("[data-inbox-item]").wait_for(state="visible")
        inbox_section.locator("[data-operator-route-intent]").first.click(force=True)
        browser_page.page.wait_for_load_state("networkidle")

        query = parse_qs(urlsplit(browser_page.page.url).query)
        assert query["mode"] == ["studio"]
        assert query["work_item"] == [WORK_ITEM]
        assert query["stage"] == [stage]
        if fixture_state == "no-run":
            assert "run_id" not in query
        else:
            assert query["run_id"] == [RUN_ID]
        browser_page.diagnostics.assert_clean()
