from __future__ import annotations

import sys
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from aidd.core.workspace import WorkspaceBootstrapService
from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry

JOURNEY_ID = "guided-setup"
_CREATE_WIDTHS = {320, 768, 1440}


def _configure_fixture_runtime(project_root: Path) -> None:
    fixture_runtime = (
        Path(__file__).parents[1]
        / "harness/fixtures/minimal-python/aidd_fixture_runtime.py"
    ).resolve()
    wrapper = project_root / "guided_runtime.py"
    wrapper.write_text(
        "import runpy\n"
        "import time\n"
        "try:\n"
        f"    runpy.run_path({fixture_runtime.as_posix()!r}, run_name='__main__')\n"
        "except SystemExit as error:\n"
        "    if error.code not in (None, 0):\n"
        "        raise\n"
        "time.sleep(20)\n",
        encoding="utf-8",
    )
    project_root.joinpath("aidd.example.toml").write_text(
        "[workspace]\n"
        'root = ".aidd"\n\n'
        "[runtime.generic_cli]\n"
        f'command = "{sys.executable} {wrapper.as_posix()}"\n'
        'mode = "adapter-flags"\n'
        'permission_policy = "full-access"\n\n'
        "[logging]\n"
        'mode = "both"\n\n'
        "[repair]\n"
        "max_attempts = 2\n",
        encoding="utf-8",
    )


def _seed_resume_work_item(project_root: Path, work_item: str) -> None:
    workspace = WorkspaceBootstrapService(root=project_root / ".aidd")
    workspace.bootstrap_work_item(work_item)
    workspace.seed_request_context(
        work_item=work_item,
        request_text="Resume the provider-free Guided Setup journey.",
        project_root=project_root,
    )


def _assert_rendered_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_guided_setup_create_or_resume_launches_into_inbox(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    branch = "create" if viewport[0] in _CREATE_WIDTHS else "resume"
    work_item = f"WI-GUIDED-{branch.upper()}"
    project_root = tmp_path / f"guided-{viewport[0]}"
    project_root.mkdir(parents=True)
    _configure_fixture_runtime(project_root)
    if branch == "resume":
        _seed_resume_work_item(project_root, work_item)

    with sync_playwright() as playwright, operator_browser_harness(
        project_root,
        playwright,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.locator("#onboardingProjectRoot").fill(project_root.as_posix())
        page.locator("#onboardingProjectForm").evaluate("form => form.requestSubmit()")
        page.locator('[data-onboarding-runtime="generic-cli"]').wait_for(state="visible")
        _assert_rendered_gate(page, viewport)

        if branch == "create":
            page.locator('[data-onboarding-runtime="generic-cli"]').click(force=True)
            page.locator("#onboardingWorkItem").fill(work_item)
            page.locator("#onboardingRequest").fill(
                "Exercise the provider-free Guided Setup browser journey."
            )
            page.locator("#onboardingCreateForm").evaluate("form => form.requestSubmit()")
        else:
            page.locator(f'[data-onboarding-resume="{work_item}"]').click(force=True)

        page.locator(".active-studio").wait_for(state="visible")
        if branch == "resume":
            page.locator("#runtimeSelect").select_option("generic-cli")
            page.wait_for_timeout(200)
        assert browser_page.diagnostics.page_errors == []
        assert page.evaluate("eval('state.selectedRuntime')") == "generic-cli"
        page.wait_for_function("eval('selectedRuntimeView()') !== null", timeout=15_000)
        runtime_view = page.evaluate("eval('selectedRuntimeView()')")
        assert runtime_view is not None
        assert runtime_view["provider_available"], runtime_view
        assert runtime_view["execution_command_available"], runtime_view
        page.wait_for_function(
            "!document.querySelector('#globalNextActionButton')?.disabled",
            timeout=5_000,
        )
        _assert_rendered_gate(page, viewport)

        launch_button = page.locator("#globalNextActionButton")
        assert not launch_button.is_disabled(), launch_button.evaluate(
            "node => ({text: node.textContent, title: node.title, html: node.outerHTML})"
        )
        with page.expect_response(
            lambda response: response.url.endswith("/api/workflow/run")
        ) as launch:
            launch_button.click()
        assert launch.value.status == 200
        page.wait_for_function(
            "['running', 'waiting-for-operator'].includes(eval('state.activeJobStatus?.status'))",
            timeout=5_000,
        )

        page.locator('[data-tab-shortcut="project-home"]').first.evaluate(
            "node => node.click()"
        )
        running = page.locator('[data-inbox-section="running-now"] [data-inbox-item]')
        running.wait_for(state="visible")
        assert running.get_attribute("data-state") == "running"
        _assert_rendered_gate(page, viewport)
        browser_page.diagnostics.assert_clean()
