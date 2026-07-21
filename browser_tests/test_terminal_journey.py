from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from aidd.core.run_store import run_manifest_path
from browser_tests.browser_harness import (
    VIEWPORTS,
    operator_browser_harness,
    wait_for_work_item_surface,
)
from browser_tests.state_fixtures import build_browser_state_fixture


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _return_to_handoff(page) -> None:
    close = page.locator("[data-close-next-flow-wizard]")
    if close.count():
        close.click()
    else:
        page.locator("[data-next-flow-back-to-definition]").click()
    page.locator("[data-studio-flow-complete]").wait_for(state="visible")


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_terminal_outcomes_keep_completed_source_run_immutable(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"terminal-{viewport[0]}", "terminal-handoff")
    assert fixture.work_item is not None
    assert fixture.run_id is not None
    manifest = run_manifest_path(fixture.workspace_root, fixture.work_item, fixture.run_id)
    source_hash = _sha256(manifest)

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa",
            wait_until="domcontentloaded",
        )
        wait_for_work_item_surface(page, fixture.work_item)
        flow = page.locator("[data-studio-flow-complete]")
        flow.wait_for(state="visible")
        assert flow.locator("[data-core-recommended-outcome]").count() == 1
        flow.locator(".studio-flow-complete-other").evaluate("element => { element.open = true; }")

        flow.locator('[data-next-flow-action="start-follow-up-flow"]').click()
        follow_up = page.locator('[data-studio-next-flow-action="start-follow-up-flow"]')
        follow_up.wait_for(state="visible")
        follow_up.locator("[data-next-flow-continue]").click()
        title = follow_up.locator('[data-follow-up-field="title"]')
        title.wait_for(state="visible")
        title.fill("Follow up on terminal evidence")
        assert page.evaluate(
            "readOperatorDraft(nextFlowBrowserDraftIdentity('start-follow-up-flow')) !== null"
        )
        follow_up.locator("[data-next-flow-back-to-sources]").click()
        _return_to_handoff(page)

        flow = page.locator("[data-studio-flow-complete]")
        flow.locator(".studio-flow-complete-other").evaluate("element => { element.open = true; }")
        flow.locator('[data-next-flow-action="clone-flow"]').click()
        clone = page.locator('[data-studio-next-flow-action="clone-flow"]')
        clone.wait_for(state="visible")
        page.wait_for_function("Boolean(state.nextFlowWizard.createdDraft)")
        clone_work_item = page.evaluate("state.nextFlowWizard.createdDraft.work_item")
        assert clone_work_item and clone_work_item != fixture.work_item
        _return_to_handoff(page)

        flow = page.locator("[data-studio-flow-complete]")
        flow.locator(".studio-flow-complete-other").evaluate("element => { element.open = true; }")
        flow.locator('[data-next-flow-action="run-eval-batch"]').click()
        eval_handoff = page.locator('[data-studio-next-flow-action="run-eval-batch"]')
        eval_handoff.wait_for(state="visible")
        assert "aidd eval execute <scenario-path> --root .aidd" in eval_handoff.inner_text()
        _return_to_handoff(page)

        flow = page.locator("[data-studio-flow-complete]")
        flow.locator(".studio-flow-complete-other").evaluate("element => { element.open = true; }")
        flow.locator('[data-next-flow-action="archive-run"]').click()
        page.locator("[data-archive-confirm]").click()
        page.locator("[data-studio-flow-complete]").wait_for(state="visible")
        response = page.request.get(
            f"{harness.url}api/dashboard?stage=qa&run_id={fixture.run_id}"
        )
        assert response.ok
        assert response.json()["dashboard"]["run"]["archive"]["archived"] is True
        assert _sha256(manifest) == source_hash
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser_page.diagnostics.assert_clean()


def test_stale_qa_does_not_render_flow_complete(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "terminal-stale", "remediation-stale")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa",
            wait_until="domcontentloaded",
        )
        wait_for_work_item_surface(page, fixture.work_item)
        assert page.locator("[data-studio-flow-complete]").count() == 0
        assert "stale" in page.locator("body").inner_text().lower()
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize(
    ("fixture_state", "status", "recommended"),
    (
        ("terminal-handoff", "completed", "create-new-work-item"),
        ("terminal-handoff-warning", "completed-with-warning", "start-follow-up-flow"),
        ("terminal-handoff-failed", "failed", "start-follow-up-flow"),
        ("terminal-handoff-blocked", "blocked", "start-follow-up-flow"),
    ),
)
def test_fresh_terminal_status_uses_exact_core_recommendation(
    tmp_path: Path,
    fixture_state: str,
    status: str,
    recommended: str,
) -> None:
    fixture = build_browser_state_fixture(tmp_path / fixture_state, fixture_state)
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa",
            wait_until="domcontentloaded",
        )
        wait_for_work_item_surface(page, fixture.work_item)
        flow = page.locator("[data-studio-flow-complete]")
        flow.wait_for(state="visible")
        assert flow.get_attribute("data-terminal-status") == status
        assert flow.locator("[data-core-recommended-outcome]").get_attribute(
            "data-core-recommended-outcome"
        ) == recommended
        browser_page.diagnostics.assert_clean()
