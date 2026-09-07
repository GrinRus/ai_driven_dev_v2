from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import (
    VIEWPORTS,
    operator_browser_harness,
    wait_for_work_item_surface,
)
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "implement"


def _open_implementation(page: Page) -> None:
    page.evaluate(
        "async () => {"
        "  activateTab('work', {historyMode: 'replace'});"
        "  await fetchDashboard();"
        "  state.activeStage = 'implement';"
        "  state.activeStageExplicit = true;"
        "  state.activeTab = 'work';"
        "  state.workDetail = 'implement-review';"
        "  await renderCockpit();"
        "}"
    )
    gate = page.locator('[data-studio-quality-gate="implement"]')
    if gate.count() != 1:
        raise AssertionError(page.locator("#intentContent").inner_text())
    gate.wait_for(state="visible")


def _assert_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


def test_implementation_recovery_preserves_success_and_repository_evidence(
    tmp_path: Path,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / "implementation-task-failed",
        "implementation-task-failed",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness:
        for viewport in VIEWPORTS:
            with harness.open_page(viewport) as browser_page:
                page = browser_page.page
                page.goto(
                    f"{harness.url}?mode=studio&work_item={fixture.work_item}"
                    f"&run_id={fixture.run_id}&stage=implement",
                    wait_until="domcontentloaded",
                )
                wait_for_work_item_surface(page, fixture.work_item)
                page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
                _open_implementation(page)

                completed = page.locator('[data-task-id="TL-1"]')
                failed = page.locator('[data-task-id="TL-2"]')
                assert completed.get_attribute("data-task-status") == "succeeded"
                assert completed.get_by_role("button", name="Resume").count() == 0
                assert failed.get_attribute("data-task-status") == "failed"
                assert failed.get_by_role("button", name="Resume").is_enabled()
                assert page.locator("[data-implementation-review-blocker]").count() == 1

                repository = page.locator(
                    '[data-document-canvas="implementation-evidence"]'
                )
                assert "Added · untracked" in repository.inner_text()
                assert "Removed · deleted" in repository.inner_text()
                assert "Changed · modified" in repository.inner_text()
                assert "Allowed scope: inside" in repository.inner_text()
                assert "core-owned .aidd/ evidence" in repository.inner_text()
                assert repository.get_by_role("button", name="Proceed to review").is_disabled()
                _assert_gate(page, viewport)
                browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((1280, 900), (390, 844)))
@pytest.mark.parametrize(
    ("permission_policy", "expected_title", "expected_detail"),
    (
        (
            "full-access",
            "Detected after execution",
            "does not prevent runtime operations",
        ),
        (
            "brokered",
            "Preventive containment",
            "progression remains blocked",
        ),
    ),
)
def test_implementation_review_project_set_copy_matches_run_permission_mode(
    tmp_path: Path,
    viewport: tuple[int, int],
    permission_policy: str,
    expected_title: str,
    expected_detail: str,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"project-set-copy-{permission_policy}-{viewport[0]}",
        "implementation-finalized",
        permission_policy=permission_policy,
    )
    project_set_root = fixture.project_root / "src" / "contained"
    project_set_root.mkdir(parents=True)
    project_set_context = (
        fixture.workspace_root
        / "workitems"
        / (fixture.work_item or "")
        / "context"
        / "project-set.md"
    )
    project_set_context.write_text(
        "# Project set\n\n"
        "## Projects\n\n"
        "| Project id | Root | Role |\n"
        "| --- | --- | --- |\n"
        "| `contained` | `src/contained` | `primary` |\n",
        encoding="utf-8",
    )

    with (
        sync_playwright() as playwright,
        operator_browser_harness(
            fixture.project_root,
            playwright,
            work_item=fixture.work_item,
        ) as harness,
        harness.open_page(viewport) as browser_page,
    ):
        page = browser_page.page
        page.goto(
            f"{harness.url}?mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement",
            wait_until="domcontentloaded",
        )
        wait_for_work_item_surface(page, fixture.work_item or "")
        page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
        _open_implementation(page)

        notice = page.locator("[data-project-set-boundary-notice]")
        notice.wait_for(state="visible")
        assert notice.get_attribute("data-project-set-boundary-mode") == permission_policy
        assert notice.get_attribute("data-project-set-boundary-state") == "outside"
        assert expected_title in notice.inner_text()
        assert expected_detail in notice.inner_text()
        _assert_gate(page, viewport)
        browser_page.diagnostics.assert_clean()


def test_finalization_retry_is_the_only_review_eligibility_boundary(tmp_path: Path) -> None:
    for state_name, finalization_status, review_eligible in (
        ("implementation-finalization-failed", "failed", False),
        ("implementation-finalized", "succeeded", True),
    ):
        fixture = build_browser_state_fixture(tmp_path / state_name, state_name)
        with sync_playwright() as playwright, operator_browser_harness(
            fixture.project_root,
            playwright,
            work_item=fixture.work_item,
        ) as harness, harness.open_page((1280, 900)) as browser_page:
            page = browser_page.page
            page.goto(
                f"{harness.url}?mode=studio&work_item={fixture.work_item}"
                f"&run_id={fixture.run_id}&stage=implement",
                wait_until="domcontentloaded",
            )
            wait_for_work_item_surface(page, fixture.work_item)
            page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
            _open_implementation(page)

            gate = page.locator('[data-studio-quality-gate="implement"]')
            assert gate.get_attribute("data-review-eligible") == str(review_eligible).lower()
            assert (
                gate.locator("[data-aggregate-finalization]").get_attribute(
                    "data-aggregate-finalization"
                )
                == finalization_status
            )
            if review_eligible:
                assert gate.locator("[data-implementation-review-blocker]").count() == 0
                assert page.get_by_role("button", name="Proceed to review").is_enabled()
            else:
                assert gate.get_by_role("button", name="Resume finalization").is_enabled()
                assert gate.locator("[data-implementation-review-blocker]").count() == 1
            assert browser_page.diagnostics.console_errors == [], (
                browser_page.diagnostics.console_errors,
                [
                    item
                    for item in browser_page.diagnostics.http_statuses
                    if item[1] >= 400
                ],
            )
            browser_page.diagnostics.assert_clean()
