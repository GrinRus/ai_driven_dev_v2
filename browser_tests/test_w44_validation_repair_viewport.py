from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_validation_repair_action_is_contained_without_desktop_overlap(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"validation-repair-{viewport[0]}",
        "validation-repair",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(
            f"{harness.url}?mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=plan&view=recovery",
            wait_until="networkidle",
        )
        assert response is not None and response.ok

        surface = page.locator(".validation-repair-center").first
        inspector = page.locator(".validation-finding-inspector").first
        action = page.locator("[data-run-repair]")
        preview = page.locator(".repair-extension-preview").first
        runner = page.locator("[data-contextual-runner-control]")
        surface.wait_for(state="visible")
        action.wait_for(state="visible")
        assert action.count() == 1
        assert runner.count() <= 1
        assert page.locator("[data-aidd-primary-action]:visible").count() <= 1

        action_box = action.bounding_box()
        surface_box = surface.bounding_box()
        inspector_box = inspector.bounding_box()
        preview_box = preview.bounding_box()
        assert (
            action_box is not None
            and surface_box is not None
            and inspector_box is not None
        )
        assert preview_box is not None
        assert page.evaluate("() => window.scrollX === 0 && window.scrollY === 0")
        assert action_box["x"] >= -1
        assert action_box["x"] + action_box["width"] <= viewport[0] + 1
        assert action_box["y"] >= -1
        if viewport[0] <= 760:
            assert action_box["y"] + action_box["height"] <= viewport[1] + 1
        elif viewport[0] >= 1280:
            assert action_box["y"] + action_box["height"] <= viewport[1] + 1
        else:
            assert action_box["x"] >= inspector_box["x"] - 1
            assert action_box["x"] + action_box["width"] <= (
                inspector_box["x"] + inspector_box["width"] + 1
            )
            assert action_box["y"] >= inspector_box["y"] - 1
            assert (
                action_box["y"] + action_box["height"]
                <= inspector_box["y"] + inspector_box["height"] + 1
            )
        assert preview_box["x"] >= surface_box["x"] - 1
        assert preview_box["x"] + preview_box["width"] <= (
            surface_box["x"] + surface_box["width"] + 1
        )
        assert page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth"
        )
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_validation_repair_prioritizes_finding_consequence_and_runner(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"validation-repair-hierarchy-{viewport[0]}",
        "validation-repair",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(
            f"{harness.url}?mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=plan&view=recovery",
            wait_until="networkidle",
        )
        assert response is not None and response.ok

        surface = page.locator(".validation-repair-center").first
        inspector = page.locator(".validation-finding-inspector").first
        band = inspector
        decision = inspector.locator(".repair-decision-copy").first
        actions = inspector.locator(".repair-actions").first
        consequence = inspector.locator(".repair-decision-consequence").first
        finding = inspector.locator(".validation-finding-facts").first
        runner = inspector.locator(".repair-actions [data-contextual-runner-control]").first
        supporting = inspector.locator(".repair-supporting-preview").first
        primary = inspector.locator("[data-run-repair]").first
        surface.wait_for(state="visible")
        band.wait_for(state="visible")
        decision.wait_for(state="visible")
        actions.wait_for(state="visible")
        consequence.wait_for(state="visible")
        finding.wait_for(state="visible")
        runner.wait_for(state="visible")
        supporting.wait_for(state="visible")
        primary.wait_for(state="visible")

        assert consequence.get_by_text("Repair consequence", exact=True).count() == 1
        assert "new attempt" in consequence.inner_text()
        assert "Request Change" in consequence.inner_text()
        assert "STRUCT-MISSING-REQUIRED-SECTION" in finding.inner_text()
        assert "generic-cli" in runner.inner_text()
        assert page.locator("[data-aidd-primary-action]:visible").count() <= 1

        band_box = band.bounding_box()
        decision_box = decision.bounding_box()
        actions_box = actions.bounding_box()
        finding_box = finding.bounding_box()
        runner_box = runner.bounding_box()
        supporting_box = supporting.bounding_box()
        primary_box = primary.bounding_box()
        assert (
            band_box is not None
            and decision_box is not None
            and actions_box is not None
            and finding_box is not None
            and runner_box is not None
            and supporting_box is not None
            and primary_box is not None
        )
        assert decision_box["x"] >= band_box["x"]
        assert decision_box["x"] + decision_box["width"] <= band_box["x"] + band_box["width"] + 1
        assert finding_box["x"] >= decision_box["x"]
        assert (
            finding_box["x"] + finding_box["width"]
            <= decision_box["x"] + decision_box["width"] + 1
        )
        actions_position = page.evaluate(
            "() => getComputedStyle(document.querySelector('.repair-actions')).position"
        )
        if actions_position == "fixed":
            assert supporting_box["y"] >= decision_box["y"] + decision_box["height"] - 1
        else:
            assert supporting_box["y"] >= max(
                decision_box["y"] + decision_box["height"],
                actions_box["y"] + actions_box["height"],
            ) - 1
        assert primary_box["y"] >= -1
        if viewport[0] <= 760:
            assert primary_box["y"] + primary_box["height"] <= viewport[1] + 1
        elif viewport[0] >= 1280:
            assert primary_box["y"] + primary_box["height"] <= viewport[1] + 1

        if viewport[0] > 760:
            assert actions_position == "static"
            band_grid_columns = page.evaluate(
                "() => getComputedStyle(document.querySelector("
                "'.validation-finding-inspector')).gridTemplateColumns"
            )
            assert len(band_grid_columns.split()) == 1
            assert decision_box["x"] >= band_box["x"]
            assert actions_box["x"] >= band_box["x"]
            assert runner_box["width"] >= 210
            assert actions_box["y"] >= decision_box["y"] + decision_box["height"] - 1
            assert supporting_box["y"] >= actions_box["y"] + actions_box["height"] - 1
        else:
            document_stage = page.locator(".validation-document-stage").first
            inspector_box = inspector.bounding_box()
            document_stage_box = document_stage.bounding_box()
            assert inspector_box is not None and document_stage_box is not None
            assert inspector_box["y"] < document_stage_box["y"]
            assert (
                inspector_box["y"] + inspector_box["height"]
                <= document_stage_box["y"] + 1
            )
            assert decision_box["y"] < viewport[1]
            assert decision_box["y"] < actions_box["y"]
            consequence_box = consequence.bounding_box()
            assert consequence_box is not None
            assert consequence_box["y"] < document_stage_box["y"]

        assert page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth"
        )
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()
