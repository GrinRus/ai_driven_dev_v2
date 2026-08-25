from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import (
    operator_browser_harness,
    wait_for_history_surface,
    wait_for_work_item_surface,
)
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", ((1280, 900), (390, 844)))
def test_create_work_item_uses_target_editor_and_preview(
    tmp_path: Path, viewport: tuple[int, int]
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path, playwright
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        surface = page.locator("[data-create-work-item-surface]")
        surface.wait_for(state="visible")
        assert surface.locator("[data-request-editor]").is_visible()
        assert surface.locator("[data-request-preview-panel]").is_visible()
        assert "operator-request.md" in surface.inner_text()
        assert "Runner is selected when you launch work." in surface.inner_text()
        assert surface.locator("[data-contextual-runner-control]").count() == 0
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (768, 1024), (390, 844)))
def test_create_work_item_target_shell_has_one_action_and_live_markdown_modes(
    tmp_path: Path, viewport: tuple[int, int]
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path / f"create-contract-{viewport[0]}", playwright
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        surface = page.locator("[data-create-work-item-surface]")
        surface.wait_for(state="visible")

        assert surface.locator("[data-target-create-submit]").count() == 1
        assert surface.locator("#onboardingCreateForm button[type=submit]").count() == 0
        assert surface.locator("[data-create-editor-mode='preview']").is_enabled()
        # Project/Runner setup remains expanded until the required context is
        # available; once selected, the renderer collapses it to keep the
        # primary create action prominent.
        assert surface.locator(".target-create-supporting").count() == 1
        assert page.evaluate(
            "getComputedStyle(document.querySelector("
            "'[data-create-work-item-surface]')).gridTemplateColumns.split(' ').length"
        ) == 1

        page.locator("#onboardingRequest").fill(
            "Improve checkout reliability.\n\n- Prevent duplicate orders."
        )
        page.locator("#onboardingContext").fill(
            "Existing webhook retries are difficult to observe.\n\n"
            "## Constraints\n\nKeep the public API stable."
        )
        preview = surface.locator("[data-request-preview-markdown]")
        assert "Improve checkout reliability" in preview.inner_text()
        assert "Existing webhook retries" in preview.inner_text()
        assert "Keep the public API stable" in preview.inner_text()

        surface.locator("[data-create-editor-mode='preview']").click()
        assert surface.locator("#onboardingRequest").is_hidden()
        assert surface.locator("[data-create-editor-preview]").is_visible()
        assert (
            surface.locator("[data-create-editor-mode='preview']").get_attribute("aria-selected")
            == "true"
        )
        surface.locator("[data-create-editor-mode='write']").click()
        assert surface.locator("#onboardingRequest").is_visible()
        assert (
            surface.locator("[data-create-editor-mode='write']").get_attribute("aria-selected")
            == "true"
        )

        primary = page.locator("[data-target-create-submit]:visible")
        primary_box = primary.bounding_box()
        assert primary_box is not None
        assert primary_box["y"] >= 0
        assert primary_box["y"] + primary_box["height"] <= viewport[1]
        assert page.locator("[data-aidd-primary-action]:visible").count() == 1
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (768, 1024), (390, 844)))
def test_implementation_review_uses_repository_truth_and_review_gate_shell(
    tmp_path: Path, viewport: tuple[int, int]
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"implementation-review-{viewport[0]}",
        "implementation-finalized",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root, playwright, work_item=fixture.work_item
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement",
            wait_until="domcontentloaded",
        )
        wait_for_work_item_surface(page, fixture.work_item or "")
        page.evaluate(
            "async () => {"
            " state.activeTab='work'; state.workDetail='implement-review';"
            " await renderImplementReview(); }"
        )
        target = page.locator("[data-target-implementation-review]")
        target.wait_for(state="visible")
        assert page.locator(
            "[data-current-decision-stable-id='intentDecisionSurface']"
        ).is_hidden()
        assert target.locator("[data-document-canvas='implementation-evidence']").is_visible()
        assert target.locator("[data-target-review-gate]").is_visible()
        assert target.locator("[data-review-scope-coverage]").is_visible()
        assert target.locator("[data-review-verification]").is_visible()
        assert target.locator("[data-aidd-primary-action]:visible").count() == 1
        assert page.evaluate("document.documentElement.scrollWidth") <= viewport[0]
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (768, 1024), (390, 844)))
def test_review_remediation_uses_finding_evidence_and_request_hierarchy(
    tmp_path: Path, viewport: tuple[int, int]
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"review-remediation-target-{viewport[0]}",
        "review-qa-rejected",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root, playwright, work_item=fixture.work_item
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa",
            wait_until="domcontentloaded",
        )
        wait_for_work_item_surface(page, fixture.work_item or "")
        page.evaluate(
            "async () => {"
            " state.activeTab='work'; state.workDetail='review-findings';"
            " await renderReviewFindings(); }"
        )
        target = page.locator("[data-target-remediation-surface='review']")
        target.wait_for(state="visible")
        assert target.locator("[data-review-findings]").is_visible()
        assert target.locator("[data-review-finding]").count() == 1
        assert target.locator("[data-remediation-source-evidence]").count() == 1
        assert target.locator("[data-remediation-write-preview]").is_visible()
        assert target.locator("[data-remediation-launch='review']").count() == 1
        assert target.locator("[data-aidd-primary-action]:visible").count() == 1
        assert page.evaluate("document.documentElement.scrollWidth") <= viewport[0]
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()


def test_history_uses_target_attempt_inspector_without_changing_lineage(
    tmp_path: Path,
) -> None:
    fixture = build_browser_state_fixture(tmp_path / "history", "history")
    assert fixture.work_item and fixture.run_id
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root, playwright, work_item=fixture.work_item
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?mode=history&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement",
            wait_until="domcontentloaded",
        )
        wait_for_history_surface(page, work_item=fixture.work_item, run_id=fixture.run_id)
        target = page.locator("[data-target-history-surface]")
        target.wait_for(state="visible")
        assert target.locator("[data-history-selected-inspector]").is_visible()
        assert target.locator("[data-copy-history-run]").count() == 1
        assert target.locator("[data-history-lineage-parent='run-source']").is_visible()
        assert target.locator("[data-studio-run-comparison]").is_visible()
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (390, 844)))
def test_history_target_views_keep_selected_attempt_and_read_only_actions(
    tmp_path: Path, viewport: tuple[int, int]
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"history-views-{viewport[0]}", "history")
    assert fixture.work_item and fixture.run_id
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root, playwright, work_item=fixture.work_item
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?mode=history&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement",
            wait_until="domcontentloaded",
        )
        wait_for_history_surface(page, work_item=fixture.work_item, run_id=fixture.run_id)
        target = page.locator("[data-target-history-surface]")
        assert target.locator(".history-attempt-tabs").is_visible()
        assert (
            target.locator("[data-history-view='timeline']").get_attribute("aria-selected")
            == "true"
        )
        assert target.locator("[data-history-open-attempt]").count() == 1
        assert target.locator("[data-history-compare]").count() == 1

        target.locator("[data-history-view='raw-log']").click()
        target.locator("[data-history-raw-log]").wait_for(state="visible")
        target.locator("[data-history-view='artifacts']").click()
        target.locator("[data-history-artifacts]").wait_for(state="visible")
        target.locator("[data-history-view='timeline']").click()
        target.locator("[data-history-timeline]").wait_for(state="visible")

        target.locator("[data-history-open-attempt]").click()
        assert target.locator("[data-history-selection]").is_visible()
        target.locator("[data-history-compare]").click()
        assert target.locator("[data-studio-run-comparison]").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth") <= viewport[0]
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (768, 1024), (390, 844)))
def test_flow_complete_uses_handoff_evidence_and_completion_inspector(
    tmp_path: Path, viewport: tuple[int, int]
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"terminal-{viewport[0]}", "terminal-handoff")
    assert fixture.work_item and fixture.run_id
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root, playwright, work_item=fixture.work_item
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa",
            wait_until="domcontentloaded",
        )
        wait_for_work_item_surface(page, fixture.work_item)
        flow = page.locator("[data-target-flow-complete]")
        flow.wait_for(state="visible")
        handoff = flow.locator("[data-flow-complete-handoff-table]")
        evidence = flow.locator("[data-flow-complete-evidence-table]")
        inspector = flow.locator("[data-flow-complete-completion-inspector]")
        assert handoff.is_visible()
        assert evidence.is_visible()
        assert inspector.is_visible()
        assert flow.locator("[data-core-recommended-outcome]").count() == 1
        assert inspector.locator("[data-primary-action]").count() == 1
        assert flow.locator("[data-primary-action]:visible").count() == 1
        assert inspector.locator(".target-completion-action-list").is_visible()
        if viewport == (768, 1024):
            primary = inspector.locator("[data-primary-action]")
            primary.focus()
            assert page.evaluate(
                "() => document.activeElement === document.querySelector("
                "'[data-next-flow-action][data-primary-action]')"
            )
        if viewport[0] > 900:
            assert handoff.bounding_box()["x"] < inspector.bounding_box()["x"]
        assert page.locator("#runtimeSettings").is_hidden()
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()
