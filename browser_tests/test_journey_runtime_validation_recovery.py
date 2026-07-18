from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "runtime-validation-recovery"

_RUNTIME_CASES = (
    ("runtime-launch-failure", "launch_failure", "Runtime launch failed"),
    ("runtime-authentication-failure", "authentication_failure", "authentication"),
    ("runtime-timeout", "timeout", "Runtime timeout"),
    ("runtime-cancelled", "cancelled", "Runtime interrupted"),
    ("runtime-no-progress", "provider-no-progress", "Provider no progress"),
)


def _assert_rendered_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


def _open_recovery(page: Page) -> None:
    page.evaluate(
        "async () => {"
        "  activateTab('recovery', {historyMode: 'replace'});"
        "  await renderCockpit();"
        "}"
    )
    page.locator("[data-recovery-summary]").wait_for(state="visible")


@pytest.mark.parametrize(("fixture_state", "kind", "title"), _RUNTIME_CASES)
def test_runtime_failures_show_exact_durable_signal_without_mutation(
    tmp_path: Path,
    fixture_state: str,
    kind: str,
    title: str,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / fixture_state,
        fixture_state,
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness:
        for viewport in VIEWPORTS:
            with harness.open_page(viewport) as browser_page:
                page = browser_page.page
                mutation_posts: list[str] = []
                page.on(
                    "request",
                    lambda request, sink=mutation_posts: sink.append(request.url)
                    if request.method == "POST"
                    else None,
                )
                page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
                _open_recovery(page)

                recovery = page.locator(f'[data-runtime-failure-kind="{kind}"]')
                recovery.wait_for(state="visible")
                assert title.lower() in recovery.inner_text().lower()
                assert "runtime-exit.json" in recovery.inner_text()
                assert recovery.get_attribute("data-runtime-stopped") == "true"
                assert (
                    recovery.get_attribute("data-validation-repair-budget-consumed")
                    == "false"
                )
                assert mutation_posts == []

                if viewport == VIEWPORTS[0]:
                    page.reload(wait_until="networkidle")
                    _open_recovery(page)
                    assert page.locator(
                        f'[data-runtime-failure-kind="{kind}"]'
                    ).count() == 1
                _assert_rendered_gate(page, viewport)
                browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize(
    ("fixture_state", "action", "forbidden"),
    (
        ("validation-repair", "Run Repair", "Request Change"),
        ("validation-repair-exhausted", "Request Change", "Run Repair"),
    ),
)
def test_validation_recovery_exposes_one_eligible_primary_action(
    tmp_path: Path,
    fixture_state: str,
    action: str,
    forbidden: str,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / fixture_state,
        fixture_state,
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness:
        for viewport in VIEWPORTS:
            with harness.open_page(viewport) as browser_page:
                page = browser_page.page
                page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
                page.evaluate(
                    "async () => {"
                    "  state.activeStage = 'plan';"
                    "  state.activeStageExplicit = true;"
                    "  await fetchDashboard();"
                    "}"
                )
                _open_recovery(page)

                primary = page.locator("[data-primary-recovery-slot]")
                assert primary.get_by_role("button", name=action).is_enabled()
                assert primary.get_by_role("button", name=forbidden).count() == 0
                assert "validator-report.md" in page.locator("#cockpitContent").inner_text()
                if fixture_state.endswith("exhausted"):
                    assert primary.locator('[data-recovery-stage="plan"]').count() == 1
                _assert_rendered_gate(page, viewport)
                browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize(
    ("fixture_state", "stage"),
    (("runtime-failure", "idea"), ("validation-repair-exhausted", "plan")),
)
def test_runtime_validation_recovery_parity_preserves_durable_read_models(
    tmp_path: Path,
    fixture_state: str,
    stage: str,
) -> None:
    fixture = build_browser_state_fixture(tmp_path / fixture_state, fixture_state)
    snapshots: list[dict[str, object]] = []
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness:
        for selector in ("", "?ui=legacy", "?ui=studio", "?ui=unknown"):
            with harness.open_page((1280, 900)) as browser_page:
                page = browser_page.page
                page.goto(f"{harness.url}{selector}", wait_until="networkidle")
                page.evaluate(
                    "async (stage) => {"
                    "  state.activeStage = stage;"
                    "  state.activeStageExplicit = true;"
                    "  await fetchDashboard();"
                    "}",
                    stage,
                )
                _open_recovery(page)
                snapshots.append(
                    page.evaluate(
                        "() => {"
                        "  const view = activeStageView();"
                        "  const diagnostics = view?.diagnostics || {};"
                        "  const primary = document.querySelector("
                        "    '[data-primary-recovery-slot] button'"
                        "  );"
                        "  return {"
                        "    first_failure: state.dashboard?.first_failure || null,"
                        "    validation: diagnostics.validation || null,"
                        "    raw_log: diagnostics.raw_log || null,"
                        "    request_change: diagnostics.request_change || null,"
                        "    evidence_path: document.querySelector("
                        "      '[data-recovery-summary] [data-evidence-path]'"
                        "    )?.dataset.evidencePath || null,"
                        "    primary_action: primary?.dataset.recoveryAction || null,"
                        "    primary_stage: primary?.dataset.recoveryStage || null"
                        "  };"
                        "}"
                    )
                )
                browser_page.diagnostics.assert_clean()

    assert snapshots[1:] == snapshots[:1] * 3
