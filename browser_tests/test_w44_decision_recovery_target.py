from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

_DECISION_VIEWPORTS = ((320, 568), (390, 844), (768, 1024), (1280, 900), (1440, 900))


def _route(base: str, fixture, stage: str) -> str:
    return (
        f"{base}?mode=studio&work_item={fixture.work_item}"
        f"&run_id={fixture.run_id}&stage={stage}&view=recovery"
    )


def _render_approval_surface(page) -> None:
    page.evaluate(
        """() => {
          const request = {
            id: "REQ-T33",
            kind: "shell",
            runtime_id: "generic-cli",
            stage: "idea",
            cwd: "/workspace",
            paths: ["src"],
            risk: "medium",
            suggestions: ["allow_once", "allow_for_session", "deny", "cancel"],
            payload: {command: "python -m pytest -q"}
          };
          document.getElementById("intentContent").innerHTML = renderApprovalsSurface({
            view: null,
            diagnostics: null,
            requests: [request],
            decisions: [],
            pendingIds: new Set([request.id])
          });
        }"""
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
        context = surface.locator("[data-decision-question-context]")
        context.wait_for(state="visible")
        assert context.get_by_text("Why it matters", exact=True).count() == 1
        assert context.locator("[data-decision-evidence]").count() == 1
        assert surface.locator("[data-question-resolution-option]").count() == 3
        assert surface.locator("[data-decision-impact]").count() == 1
        partial = surface.locator('[data-question-resolution-option="partial"]')
        partial.click()
        assert page.locator('[data-question-resolution="Q1"]').input_value() == "partial"
        assert partial.get_attribute("aria-checked") == "true"
        if viewport[0] <= 760:
            assert not page.locator(".intent-context-region").is_visible()
            assert not page.locator(".work-item-tabs").is_visible()
            assert page.locator(".decision-workbench-header").count() == 1
            assert not page.locator(".decision-workbench-header").is_visible()
            work_item_context = page.locator("#topContextIntent")
            work_item_context.wait_for(state="visible")
            assert work_item_context.inner_text() == fixture.work_item
            context_box = work_item_context.bounding_box()
            inbox_box = page.locator("#projectInboxButton").bounding_box()
            assert context_box is not None and context_box["width"] > 0
            assert inbox_box is not None and inbox_box["width"] >= 44
            assert page.evaluate(
                """() => getComputedStyle(
                  document.querySelector('#projectInboxButton'), '::before'
                ).content"""
            ) == '"←"'
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
            if fixture_name == "validation-repair":
                page.locator("[data-validation-finding-inspector]").wait_for(state="visible")
                page.locator("[data-validation-document-workbench]").wait_for(state="visible")
                page.locator("#studioDocumentCanvas").wait_for(state="visible")
                assert (
                    page.locator('[data-validation-finding-inspector] [data-run-repair]').count()
                    == 1
                )
                assert (
                    page.locator('[data-validation-finding-inspector] [data-stop-run]').count()
                    == 0
                )
            assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
            assert_rendered_geometry(page)
            assert page.evaluate(
                "() => document.documentElement.scrollWidth <= window.innerWidth"
            )
            browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", _DECISION_VIEWPORTS)
def test_question_workbench_keeps_target_hierarchy_at_supported_viewports(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"question-hierarchy-{viewport[0]}",
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

        context = surface.locator("[data-decision-question-context]")
        impact = surface.locator("[data-decision-impact]")
        primary = surface.locator('[data-primary-action]:visible')
        options = surface.locator(".decision-resolution-options")
        destination = surface.locator("[data-answer-destination-panel]")
        context_box = context.bounding_box()
        impact_box = impact.bounding_box()
        primary_box = primary.bounding_box()
        options_box = options.bounding_box()
        assert context_box is not None and context_box["y"] < viewport[1]
        assert primary.count() == 1 and primary_box is not None
        assert primary_box["x"] >= -1
        assert primary_box["x"] + primary_box["width"] <= viewport[0] + 1
        assert primary_box["y"] >= -1
        assert primary_box["y"] + primary_box["height"] <= viewport[1] + 1
        assert options.count() == 1 and options_box is not None
        assert options_box["x"] + options_box["width"] <= viewport[0] + 1
        assert destination.count() == 1
        assert context.locator("[data-decision-evidence]").get_attribute("open") == ""
        option_boxes = [
            option.bounding_box()
            for option in surface.locator("[data-question-resolution-option]").all()
        ]
        assert all(box is not None and box["height"] >= 44 for box in option_boxes)
        if viewport[0] <= 760:
            assert len({round(box["y"]) for box in option_boxes if box is not None}) == 1
        if viewport[0] >= 960:
            main_box = surface.locator(".decision-question-main").bounding_box()
            assert main_box is not None and impact_box is not None
            assert impact_box["x"] >= main_box["x"] + main_box["width"] - 1
            assert impact_box["y"] < viewport[1]
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", _DECISION_VIEWPORTS)
def test_approval_workbench_exposes_one_primary_action_at_supported_viewports(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"approval-hierarchy-{viewport[0]}",
        "blocking-question",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        assert response is not None and response.ok
        _render_approval_surface(page)
        surface = page.locator('[data-human-decision-surface="approval"]')
        surface.wait_for(state="visible")
        primary = surface.locator('[data-primary-action]:visible')
        allow_once = surface.locator('[data-operator-action="allow_once"]:visible')
        allow_session = surface.locator('[data-operator-action="allow_for_session"]:visible')
        primary_box = primary.bounding_box()
        assert primary.count() == 1 and primary_box is not None
        assert allow_once.count() == 1
        assert allow_once.get_attribute("data-primary-action") == ""
        assert "secondary" not in (allow_once.get_attribute("class") or "")
        assert "secondary" in (allow_session.get_attribute("class") or "")
        assert primary_box["x"] >= -1
        assert primary_box["x"] + primary_box["width"] <= viewport[0] + 1
        assert primary_box["y"] >= -1
        assert primary_box["y"] + primary_box["height"] <= viewport[1] + 1
        assert surface.locator(".decision-workbench-header").is_visible()
        assert "Allow once" in surface.locator(".decision-workbench-header").inner_text()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()
