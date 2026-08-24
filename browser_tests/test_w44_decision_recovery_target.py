from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture


def _route(base: str, fixture, stage: str) -> str:
    return (
        f"{base}?mode=studio&work_item={fixture.work_item}"
        f"&run_id={fixture.run_id}&stage={stage}&view=recovery"
    )


@pytest.mark.parametrize("viewport", ((1280, 900), (390, 844)))
def test_question_recovery_renders_the_decision_before_shared_chrome(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"question-{viewport[0]}",
        "blocking-question",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(
            _route(harness.url, fixture, "idea"),
            wait_until="networkidle",
        )
        assert response is not None and response.ok
        surface = page.locator('[data-human-decision-surface="question"]')
        surface.wait_for(state="visible")
        card = page.locator('[data-question-id="Q1"]')
        card.wait_for(state="visible")
        assert "Which acceptance boundary should the run preserve?" in card.inner_text()
        assert page.locator('[data-question-text="Q1"]').count() == 1
        assert page.locator('[data-question-evidence="Q1"]').count() == 1
        assert page.locator('[data-question-consequence="Q1"]').count() == 1
        assert page.locator('[data-answer-destination="Q1"]').count() == 1
        assert page.locator('[data-answer-resume="Q1"]').count() == 1
        assert surface.locator('[data-primary-action]').count() == 1
        if viewport[0] <= 760:
            assert not page.locator(".intent-context-region").is_visible()
            assert not page.locator(".work-item-tabs").is_visible()
            assert page.locator(".decision-workbench-header").count() == 1
            assert not page.locator(".decision-workbench-header").is_visible()
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        assert page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth"
        )
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (390, 844)))
def test_validation_and_review_recovery_routes_land_on_authoritative_surfaces(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    cases = (
        (
            "validation-repair",
            "plan",
            ".validation-repair-center",
            "Required verification section is missing",
        ),
        ("review-qa-rejected", "review", '[data-studio-quality-gate="review"]', "RV-1"),
    )
    for fixture_name, stage, selector, marker in cases:
        fixture = build_browser_state_fixture(
            tmp_path / f"{fixture_name}-{viewport[0]}",
            fixture_name,
        )
        with sync_playwright() as playwright, operator_browser_harness(
            fixture.project_root,
            playwright,
            work_item=fixture.work_item,
        ) as harness, harness.open_page(viewport) as browser_page:
            page = browser_page.page
            response = page.goto(
                _route(harness.url, fixture, stage),
                wait_until="networkidle",
            )
            assert response is not None and response.ok
            surface = page.locator(selector)
            surface.wait_for(state="visible")
            assert marker in surface.inner_text()
            assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
            assert_rendered_geometry(page)
            assert page.evaluate(
                "() => document.documentElement.scrollWidth <= window.innerWidth"
            )
            browser_page.diagnostics.assert_clean()
