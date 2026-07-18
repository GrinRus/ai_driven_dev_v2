from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture

_MOBILE_VIEWPORTS = ((320, 568), (390, 844))


def _open_surface(page: Page, surface: str) -> tuple[str, str]:
    if surface == "question":
        return ('[data-human-decision-surface="question"]', '[data-primary-action]')
    if surface == "intervention":
        page.evaluate("renderRequestChange()")
        return (
            '[data-human-decision-surface="intervention"]',
            "#submitInterventionButton",
        )
    page.evaluate(
        """() => {
          const request = {
            id: "REQ-MOBILE", kind: "shell", runtime_id: "generic-cli", stage: "idea",
            cwd: "/workspace", paths: ["src"], risk: "medium",
            suggestions: ["allow_once", "allow_for_session", "deny", "cancel"],
            payload: {command: "python -m pytest -q"}
          };
          document.getElementById("cockpitContent").innerHTML = renderApprovalsSurface({
            view: null,
            diagnostics: null,
            requests: [request],
            decisions: [],
            pendingIds: new Set([request.id])
          });
        }"""
    )
    return (
        '[data-human-decision-surface="approval"]',
        '[data-operator-action="allow_once"]',
    )


@pytest.mark.parametrize("viewport", _MOBILE_VIEWPORTS)
@pytest.mark.parametrize("surface", ("question", "intervention", "approval"))
def test_human_decision_surface_is_mobile_first_without_overflow(
    tmp_path: Path,
    viewport: tuple[int, int],
    surface: str,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"{surface}-{viewport[0]}",
        "blocking-question",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        root_selector, primary_selector = _open_surface(page, surface)
        root = page.locator(root_selector)
        root.wait_for(state="visible")
        primary = root.locator(primary_selector).first
        primary.wait_for(state="visible")

        primary_bounds = primary.bounding_box()
        assert primary_bounds is not None
        assert primary_bounds["height"] >= 44
        assert primary_bounds["y"] + primary_bounds["height"] <= viewport[1]
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )

        undersized = root.locator("button:visible, input:visible, select:visible").evaluate_all(
            "nodes => nodes.filter(node => node.getBoundingClientRect().height < 44)"
            ".map(node => `${node.tagName}:${node.id || node.textContent.trim()}`)"
        )
        assert undersized == []
        browser_page.diagnostics.assert_clean()
