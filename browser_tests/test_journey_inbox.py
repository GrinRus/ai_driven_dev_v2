from __future__ import annotations

import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import Locator, Page, sync_playwright

from browser_tests.browser_harness import VIEWPORTS, BrowserPage, operator_browser_harness
from browser_tests.journey_support import configure_sleeping_fixture_runtime
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "inbox"

_ITEMS = {
    "needs-decision": ("WI-DECISION", "run-decision", "idea", "answer-questions"),
    "running-now": ("WI-RUN", None, "idea", "open-running-job"),
    "ready-to-continue": ("WI-READY", None, "idea", "choose-runtime"),
    "flow-complete": ("WI-COMPLETE", "run-complete", "qa", "review-complete"),
}


def _assert_rendered_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


def _item_for(section: Locator, work_item: str) -> Locator:
    return section.locator(
        f'[data-operator-route-intent][data-route-work-item="{work_item}"]'
    ).locator("xpath=ancestor::*[@data-inbox-item]")


def _assert_clean_navigation_diagnostics(browser_page: BrowserPage) -> None:
    diagnostics = browser_page.diagnostics
    navigation_aborts = [
        failure
        for failure in diagnostics.failed_requests
        if "/api/" in failure and "net::ERR_ABORTED" in failure
    ]
    assert diagnostics.failed_requests == navigation_aborts
    diagnostics.failed_requests.clear()
    diagnostics.assert_clean()


def _seed_inbox_states(project_root: Path) -> None:
    build_browser_state_fixture(
        project_root,
        "blocking-question",
        work_item="WI-DECISION",
        run_id="run-decision",
    )
    build_browser_state_fixture(project_root, "no-run", work_item="WI-RUN")
    build_browser_state_fixture(project_root, "no-run", work_item="WI-READY")
    build_browser_state_fixture(
        project_root,
        "terminal-handoff",
        work_item="WI-COMPLETE",
        run_id="run-complete",
    )


@pytest.mark.parametrize(
    "query",
    ("", "?ui=legacy", "?ui=studio", "?ui=unknown"),
)
def test_inbox_ignores_retired_presentation_selector(
    tmp_path: Path,
    query: str,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / (query.removeprefix("?ui=") or "missing"), "no-run"
    )

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}{query}", wait_until="networkidle")
        assert page.evaluate(
            "window.aiddPresentation.surfaces.inbox.presentation"
        ) == "studio"
        page.locator('[data-tab-shortcut="project-home"]').first.click()
        page.locator(".studio-inbox").wait_for(state="visible")
        assert page.locator(".project-home-screen").count() == 0
        assert page.locator("[data-inbox-dismiss]").count() == 0
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_inbox_prioritizes_and_routes_durable_and_running_work(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    project_root = tmp_path / f"inbox-{viewport[0]}"
    _seed_inbox_states(project_root)
    configure_sleeping_fixture_runtime(project_root, sleep_seconds=60)

    with sync_playwright() as playwright, operator_browser_harness(
        project_root,
        playwright,
        work_item="WI-RUN",
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        assert response is not None and response.ok

        page.locator('[data-tab-shortcut="project-home"]').first.click()
        sections = page.locator("[data-inbox-section]")
        sections.first.wait_for(state="visible")
        assert sections.evaluate_all(
            "items => items.map(item => item.dataset.inboxSection)"
        ) == ["needs-decision", "ready-to-continue", "flow-complete"]
        page.wait_for_function("window.scrollY === 0", timeout=5_000)

        first_action = page.locator(
            '[data-inbox-section="needs-decision"] [data-inbox-action]'
        )
        bounds = first_action.bounding_box()
        assert bounds is not None
        assert bounds["y"] >= 0
        assert bounds["y"] + bounds["height"] <= viewport[1]
        first_action.focus()
        assert first_action.evaluate("node => document.activeElement === node")
        _assert_rendered_gate(page, viewport)

        page.reload(wait_until="networkidle")
        page.locator('[data-inbox-section="needs-decision"]').wait_for(state="visible")
        assert parse_qs(urlsplit(page.url).query).get("mode") == ["inbox"]

        first_action = page.locator(
            '[data-inbox-section="needs-decision"] [data-inbox-action]'
        )
        first_action.wait_for(state="visible")
        first_action.focus()
        with page.expect_response(
            lambda item: urlsplit(item.url).path == "/api/onboarding/work-item"
        ) as context_switch:
            page.keyboard.press("Enter")
        assert context_switch.value.status == 200, context_switch.value.text()
        page.wait_for_function(
            "new URLSearchParams(location.search).get('work_item') === 'WI-DECISION'",
            timeout=15_000,
        )
        page.wait_for_function(
            "eval('state.dashboard?.work_item') === 'WI-DECISION'",
            timeout=15_000,
        )
        page.locator("#cockpitContent").get_by_text(
            "Which acceptance boundary", exact=False
        ).first.wait_for(state="visible", timeout=15_000)
        query = parse_qs(urlsplit(page.url).query)
        assert query["mode"] == ["studio"]
        assert query["work_item"] == ["WI-DECISION"]
        assert query["run_id"] == ["run-decision"]
        assert query["stage"] == ["idea"]

        page.reload(wait_until="networkidle")
        page.locator("#cockpitContent").get_by_text(
            "Which acceptance boundary", exact=False
        ).first.wait_for(state="visible", timeout=15_000)
        inbox_readback = page.request.get(f"{harness.url}api/inbox")
        assert inbox_readback.status == 200
        sections_payload = inbox_readback.json()["inbox"]["durable"]["sections"]
        blocking_items = next(
            item["items"] for item in sections_payload if item["key"] == "needs-decision"
        )
        decision_item = next(
            item for item in blocking_items if item["route"]["work_item"] == "WI-DECISION"
        )
        assert decision_item["primary_action"]["action"] == "answer-questions"
        assert page.locator("[data-inbox-dismiss]").count() == 0

        switch_response = page.request.post(
            f"{harness.url}api/onboarding/work-item",
            data={
                "action": "resume",
                "project_root": project_root.as_posix(),
                "work_item": "WI-RUN",
            },
        )
        assert switch_response.status == 200
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        launch_response = page.request.post(
            f"{harness.url}api/workflow/run",
            data={"runtime": "generic-cli", "log_follow": True},
        )
        assert launch_response.status == 200
        job_id = launch_response.json()["job_id"]
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            job_response = page.request.get(f"{harness.url}api/jobs/{job_id}")
            assert job_response.status == 200
            if job_response.json()["status"] == "running":
                break
            time.sleep(0.05)
        else:
            pytest.fail("provider-free Inbox overlay job did not enter running state")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            running_readback = page.request.get(f"{harness.url}api/inbox")
            assert running_readback.status == 200
            if running_readback.json()["inbox"]["running_now"]:
                break
            time.sleep(0.05)
        else:
            pytest.fail("running job did not appear in the Inbox read model")
        page.locator('[data-tab-shortcut="project-home"]').first.click()
        sections = page.locator("[data-inbox-section]")
        page.locator('[data-inbox-section="running-now"]').wait_for(
            state="visible", timeout=15_000
        )
        assert sections.evaluate_all(
            "items => items.map(item => item.dataset.inboxSection)"
        ) == list(_ITEMS)

        for section_key, (work_item, run_id, stage, action) in _ITEMS.items():
            section = page.locator(f'[data-inbox-section="{section_key}"]')
            item = _item_for(section, work_item)
            item.wait_for(state="visible")
            buttons = item.locator("[data-inbox-action]")
            assert buttons.count() == 1
            button = buttons.first
            assert button.get_attribute("data-inbox-action") == action
            assert button.get_attribute("data-route-work-item") == work_item
            assert button.get_attribute("data-route-stage") == stage
            if run_id is not None:
                assert button.get_attribute("data-route-run-id") == run_id
            elif section_key != "running-now":
                assert button.get_attribute("data-route-run-id") is None

        _assert_rendered_gate(page, viewport)

        _assert_clean_navigation_diagnostics(browser_page)
