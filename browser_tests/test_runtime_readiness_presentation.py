from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def test_studio_runtime_readiness_is_dimensioned_and_scope_truthful(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "no-run", "no-run")
    scope_path = (
        fixture.project_root
        / ".aidd/workitems"
        / fixture.work_item
        / "context/allowed-write-scope.md"
    )
    scope_path.write_text("# Allowed write scope\n\n- `src`\n- `tests`\n", encoding="utf-8")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        browser_page.page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        browser_page.page.locator("#runtimeSelect").select_option("generic-cli")
        browser_page.page.wait_for_timeout(100)
        assert browser_page.diagnostics.page_errors == []
        panel = browser_page.page.locator("[data-studio-runtime-readiness]")
        selected = browser_page.page.evaluate("() => eval('state.selectedRuntime')")
        assert selected == "generic-cli"
        runtime_ids = browser_page.page.evaluate(
            "() => eval('state.readiness.runtimes.map((item) => item.runtime_id)')"
        )
        selected_view = browser_page.page.evaluate(
            "() => eval('selectedRuntimeView()?.runtime_id || null')"
        )
        assert selected_view == "generic-cli"
        dimensions = panel.locator("[data-runtime-readiness-dimensions]")
        assert dimensions.count() == 1, (runtime_ids, panel.inner_text())
        text = panel.inner_text()
        for label in (
            "Binary",
            "Execution command",
            "Authentication evidence",
            "Adapter capabilities",
            "Latest launch",
            "Protected write scope",
            "src, tests",
        ):
            assert label in text
        assert "No upstream write" not in text
        assert " ready" not in text.lower()
        browser_page.diagnostics.assert_clean()
