from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_evidence import (
    BrowserCleanupStatus,
    BrowserEvidenceWriter,
)
from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture
from browser_tests.wave42_browser_matrix import (
    WAVE42_BROWSER_JOURNEYS,
    WAVE42_BROWSER_MATRIX_SCHEMA,
    Wave42BrowserJourney,
    validate_wave42_browser_matrix,
    wave42_route_query,
)


def _assert_first_action(
    page: Page,
    selector: str,
    *,
    require_initial_viewport: bool,
) -> None:
    action = page.locator(selector).first
    action.wait_for(state="visible")
    if require_initial_viewport:
        scroll = page.evaluate("() => ({x: window.scrollX, y: window.scrollY})")
        assert scroll == {"x": 0, "y": 0}, (
            "first-action assertion must measure the initial viewport"
        )
    else:
        action.scroll_into_view_if_needed()
    box = action.bounding_box()
    assert box is not None
    viewport = page.viewport_size or {"width": 0, "height": 0}
    assert box["x"] >= -1
    assert box["x"] + box["width"] <= viewport["width"] + 1
    assert box["y"] >= -1
    assert box["y"] + box["height"] <= viewport["height"] + 1


def test_wave42_browser_matrix_registry_is_complete() -> None:
    validate_wave42_browser_matrix()
    assert WAVE42_BROWSER_MATRIX_SCHEMA == "wave42-responsive-browser-matrix-v1"
    journeys = {journey.journey_id: journey for journey in WAVE42_BROWSER_JOURNEYS}
    assert journeys["question-recovery"].surface_selector == (
        '[data-human-decision-surface="question"]'
    )
    assert journeys["validation-repair"].surface_selector == ".validation-repair-center"
    assert journeys["review-remediation"].surface_selector == (
        '[data-studio-quality-gate="review"]'
    )
    for journey_id in ("question-recovery", "validation-repair", "review-remediation"):
        assert ".recovery-workbench" not in journeys[journey_id].surface_selector


@pytest.mark.parametrize("journey", WAVE42_BROWSER_JOURNEYS, ids=lambda item: item.journey_id)
def test_wave42_journey_matrix_is_provider_free_and_rendered_across_viewports(
    tmp_path: Path,
    journey: Wave42BrowserJourney,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / journey.journey_id,
        journey.fixture_state,
    )
    assert fixture.work_item is not None
    evidence = BrowserEvidenceWriter(tmp_path / "evidence")

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness:
        for viewport in VIEWPORTS:
            with harness.open_page(viewport) as browser_page:
                page = browser_page.page
                query = wave42_route_query(
                    journey,
                    work_item=fixture.work_item,
                    run_id=fixture.run_id,
                )
                response = page.goto(
                    f"{harness.url}{query}",
                    wait_until="networkidle",
                )
                assert response is not None and response.ok
                surface = page.locator(journey.surface_selector).first
                surface.wait_for(state="visible")
                _assert_first_action(
                    page,
                    journey.first_action_selector,
                    require_initial_viewport=journey.requires_initial_viewport,
                )
                assert_accessible_render(
                    page,
                    target_size=44 if viewport[0] <= 760 else 32,
                )
                assert page.locator("[data-aidd-primary-action]:visible").count() <= 1
                assert_rendered_geometry(page)
                assert page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"
                )
                evidence.capture(
                    fixture=journey.journey_id,
                    page=page,
                    diagnostics=browser_page.diagnostics,
                )
                browser_page.diagnostics.assert_clean()

    report = evidence.commit(
        cleanup=BrowserCleanupStatus(
            page_closed=True,
            context_closed=True,
            browser_closed=True,
            server_stopped=True,
            workspace_removed=True,
        )
    )
    assert report.exists()
    payload = report.read_text(encoding="utf-8")
    assert payload.count('"viewport_width"') == len(VIEWPORTS)
