from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.test_journey_inbox import _seed_inbox_states

VIEWPORTS = ((1280, 900), (1440, 900), (768, 1024), (390, 844))


def _right(box: dict[str, float]) -> float:
    return box["x"] + box["width"]


def _bottom(box: dict[str, float]) -> float:
    return box["y"] + box["height"]


def _assert_project_work_composition(page: Page, viewport: tuple[int, int]) -> None:
    sections = page.locator(".studio-inbox-sections")
    inspector = page.locator('[data-inbox-selected-context="WI-DECISION"]')
    selected = page.locator('[data-inbox-item][data-inbox-select="WI-DECISION"]')
    sections_box = sections.bounding_box()
    inspector_box = inspector.bounding_box()
    selected_box = selected.bounding_box()
    assert sections_box is not None
    assert inspector_box is not None
    assert selected_box is not None

    if viewport[0] > 900:
        # The selected inspector is a real second grid column, never a floating panel over
        # the authoritative server-owned list.
        assert _right(sections_box) <= inspector_box["x"] + 1
        assert _right(selected_box) <= inspector_box["x"] + 1
    else:
        # On tablet/mobile the inspector follows the list and remains in normal flow.
        assert inspector_box["y"] >= _bottom(sections_box) - 1

    assert page.locator("[data-inbox-selected-context] [data-inbox-action]").count() == 1
    assert selected.get_attribute("aria-current") == "true"
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_selected_project_work_uses_target_list_and_inspector_geometry(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    project_root = tmp_path / f"project-work-{viewport[0]}"
    _seed_inbox_states(project_root)

    with sync_playwright() as playwright, operator_browser_harness(
        project_root,
        playwright,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(
            f"{harness.url}?mode=inbox&inbox_work_item=WI-DECISION",
            wait_until="networkidle",
        )
        assert response is not None and response.ok
        page.locator('[data-inbox-selected-context="WI-DECISION"]').wait_for(
            state="visible"
        )
        _assert_project_work_composition(page, viewport)
        browser_page.diagnostics.assert_clean()
