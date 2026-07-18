from __future__ import annotations

import hashlib
from pathlib import Path

from playwright.sync_api import sync_playwright

from aidd.core.run_store import run_manifest_path
from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_studio_default_and_legacy_rollback_share_durable_outcomes(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "rollback-window", "terminal-handoff")
    assert fixture.work_item is not None
    assert fixture.run_id is not None
    manifest = run_manifest_path(fixture.workspace_root, fixture.work_item, fixture.run_id)
    before = _sha256(manifest)

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as studio_page, harness.open_page(
        (1280, 900)
    ) as legacy_page:
        query = (
            f"work_item={fixture.work_item}&run_id={fixture.run_id}&stage=qa"
        )
        studio_page.page.goto(f"{harness.url}?{query}", wait_until="networkidle")
        legacy_page.page.goto(f"{harness.url}?ui=legacy&{query}", wait_until="networkidle")

        assert studio_page.page.locator("html").get_attribute(
            "data-presentation-requested"
        ) == "studio"
        assert legacy_page.page.locator("html").get_attribute(
            "data-presentation-requested"
        ) == "legacy"
        studio_page.page.locator("[data-studio-flow-complete]").wait_for(state="visible")
        legacy_page.page.locator(".flow-complete-state").wait_for(state="visible")

        dashboard_path = f"api/dashboard?stage=qa&run_id={fixture.run_id}"
        timeline_path = f"api/run/timeline?run_id={fixture.run_id}"
        for path in (dashboard_path, timeline_path):
            studio_response = studio_page.page.request.get(f"{harness.url}{path}")
            legacy_response = legacy_page.page.request.get(f"{harness.url}{path}")
            assert studio_response.ok and legacy_response.ok
            assert studio_response.json() == legacy_response.json()

        studio_actions = set(
            studio_page.page.locator("[data-next-flow-action]").evaluate_all(
                "elements => elements.map(element => element.dataset.nextFlowAction)"
            )
        )
        legacy_actions = set(
            legacy_page.page.locator("[data-next-flow-action]").evaluate_all(
                "elements => elements.map(element => element.dataset.nextFlowAction)"
            )
        )
        assert studio_actions == legacy_actions
        assert studio_actions == {
            "archive-run",
            "clone-flow",
            "create-new-work-item",
            "run-eval-batch",
            "start-follow-up-flow",
        }
        assert _sha256(manifest) == before
        studio_page.diagnostics.assert_clean()
        legacy_page.diagnostics.assert_clean()
