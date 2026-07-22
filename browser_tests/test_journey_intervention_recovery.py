from __future__ import annotations

import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.journey_support import configure_sleeping_fixture_runtime
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "intervention-recovery"


def _assert_rendered_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


@pytest.mark.parametrize("selector", ("studio", "legacy"))
@pytest.mark.parametrize("blocked", (False, True))
def test_intervention_parity_preserves_allowed_and_blocked_service_paths(
    tmp_path: Path,
    selector: str,
    blocked: bool,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"intervention-parity-{selector}-{blocked}",
        "qa-decision" if blocked else "blocking-question",
    )
    if not blocked:
        configure_sleeping_fixture_runtime(fixture.project_root, sleep_seconds=20)
    stage = "plan" if blocked else "idea"
    request_root = (
        fixture.workspace_root
        / "workitems"
        / fixture.work_item
        / "stages"
        / stage
        / "operator-requests"
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui={selector}", wait_until="networkidle")
        if blocked:
            page.evaluate(
                "state.activeStage = 'plan'; state.activeStageExplicit = true; fetchDashboard()"
            )
        else:
            page.locator("#runtimeSelect").select_option("generic-cli")
            page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
        page.evaluate("setOperatorMode('request'); renderCockpitContent()")
        eligible = page.locator(
            f'[data-intervention-eligible="{"false" if blocked else "true"}"]'
        ).first
        eligible.wait_for(state="visible")

        if blocked:
            assert page.locator("#submitInterventionButton").is_disabled()
            page.evaluate("submitIntervention()")
            page.wait_for_timeout(100)
            assert not request_root.exists()
        else:
            page.locator("#operatorRequestText").fill(
                "Use the same durable intervention service path."
            )
            page.locator("#submitInterventionButton").click()
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and not list(request_root.glob("request-*.md")):
                time.sleep(0.05)
            requests = list(request_root.glob("request-*.md"))
            assert len(requests) == 1
            assert "same durable intervention service path" in requests[0].read_text(
                encoding="utf-8"
            )
            job_id = page.evaluate("eval('state.activeJobId')")
            if job_id:
                assert page.request.post(
                    f"{harness.url}api/jobs/{job_id}/cancel"
                ).status == 200
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_allowed_intervention_restores_draft_and_creates_one_request(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"intervention-allowed-{viewport[0]}",
        "blocking-question",
    )
    configure_sleeping_fixture_runtime(fixture.project_root, sleep_seconds=30)
    request_root = (
        fixture.workspace_root
        / "workitems"
        / fixture.work_item
        / "stages"
        / "idea"
        / "operator-requests"
    )

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
        page.evaluate("setOperatorMode('request'); renderCockpitContent()")
        surface = page.locator('[data-human-decision-surface="intervention"]')
        surface.wait_for(state="visible")
        assert surface.get_attribute("data-intervention-stage") == "idea"
        assert surface.get_attribute("data-intervention-run") == fixture.run_id
        _assert_rendered_gate(page, viewport)

        request = page.locator("#operatorRequestText")
        request.fill("Update only the current stage evidence and preserve public contracts.")
        page.reload(wait_until="networkidle")
        page.evaluate("setOperatorMode('request'); renderCockpitContent()")
        request = page.locator("#operatorRequestText")
        request.wait_for(state="visible")
        assert request.input_value().startswith("Update only the current stage")

        page.evaluate(
            "navigateOperatorRouteIntent('historical-run', {"
            f"workItem: '{fixture.work_item}', runId: '{fixture.run_id}', stage: 'idea'"
            "})"
        )
        page.wait_for_function(
            "new URLSearchParams(location.search).get('mode') === 'history'",
            timeout=10_000,
        )
        page.go_back(wait_until="domcontentloaded")
        page.evaluate(
            "async () => { if (window.aiddRouteRestore) await window.aiddRouteRestore; }"
        )
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
        page.evaluate("setOperatorMode('request'); renderCockpitContent()")
        request = page.locator("#operatorRequestText")
        assert request.input_value().startswith("Update only the current stage")

        launch_posts: list[str] = []
        page.on(
            "request",
            lambda item: launch_posts.append(item.url)
            if item.method == "POST" and item.url.endswith("/api/stage/interact")
            else None,
        )
        submit = page.locator("#submitInterventionButton")
        with page.expect_response(
            lambda response: response.request.method == "POST"
            and response.url.endswith("/api/stage/interact")
        ) as response_info:
            submit.hover()
            page.mouse.down()
            page.evaluate("renderReadinessSurfaces()")
            assert submit.evaluate("element => element.isConnected") is True
            page.mouse.up()
        assert response_info.value.ok
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not list(request_root.glob("request-*.md")):
            time.sleep(0.05)
        requests = list(request_root.glob("request-*.md"))
        assert len(launch_posts) == 1
        assert len(requests) == 1
        assert "Update only the current stage evidence" in requests[0].read_text(
            encoding="utf-8"
        )
        page.wait_for_function(
            "readOperatorDraft(interventionDraftIdentity()) === null",
            timeout=5_000,
        )

        job_id = page.evaluate("eval('state.activeJobId')")
        if job_id:
            cancel = page.request.post(f"{harness.url}api/jobs/{job_id}/cancel")
            assert cancel.status == 200
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_downstream_success_blocks_intervention_without_creating_request(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"intervention-blocked-{viewport[0]}",
        "qa-decision",
    )
    request_root = (
        fixture.workspace_root
        / "workitems"
        / fixture.work_item
        / "stages"
        / "plan"
        / "operator-requests"
    )

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.evaluate(
            "state.activeStage = 'plan'; state.activeStageExplicit = true; fetchDashboard()"
        )
        page.evaluate("setOperatorMode('request'); renderCockpitContent()")
        blocked = page.locator('[data-intervention-eligible="false"]').first
        blocked.wait_for(state="visible")
        surface = page.locator('[data-human-decision-surface="intervention"]')
        assert surface.get_attribute("data-intervention-stage") == "plan"
        assert surface.get_attribute("data-intervention-run") == fixture.run_id
        assert page.locator("#submitInterventionButton").is_disabled()
        assert "requires remediation routing" in surface.inner_text()
        _assert_rendered_gate(page, viewport)

        page.evaluate("submitIntervention()")
        page.wait_for_timeout(100)
        assert not request_root.exists()
        assert page.evaluate("eval('state.activeStage')") == "plan"
        assert page.evaluate("eval('state.activeRunId')") == fixture.run_id
        browser_page.diagnostics.assert_clean()
