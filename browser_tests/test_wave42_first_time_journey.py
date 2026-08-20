from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from aidd.core.interview import AdapterQuestionEvent, QuestionPolicy, persist_questions_document
from aidd.core.run_store import create_next_attempt_directory, persist_stage_status
from browser_tests.browser_evidence import BrowserCleanupStatus, BrowserEvidenceWriter
from browser_tests.browser_harness import operator_browser_harness
from browser_tests.journey_support import configure_sleeping_fixture_runtime
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.wave42_first_time_journey import (
    JOURNEY_STEP_IDS,
    WAVE42_FIRST_TIME_JOURNEY_SCHEMA,
    FirstTimeJourneyEvidence,
    JourneyStepEvidence,
    validate_first_time_journey_evidence,
    write_first_time_journey_evidence,
)


def _mark_question_fixture(project_root: Path, work_item: str, run_id: str) -> None:
    workspace_root = project_root / ".aidd"
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="idea",
    )
    persist_stage_status(workspace_root, work_item, run_id, "idea", "blocked")
    persist_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage="idea",
        adapter_question_events=(
            AdapterQuestionEvent(
                question_id="Q1",
                policy=QuestionPolicy.BLOCKING,
                text="Which acceptance boundary should the run preserve?",
            ),
        ),
    )


def _assert_first_action(page: Page, selector: str) -> None:
    action = page.locator(selector).first
    action.wait_for(state="visible")
    action.scroll_into_view_if_needed()
    box = action.bounding_box()
    assert box is not None
    viewport = page.viewport_size or {"width": 0, "height": 0}
    assert box["x"] >= -1
    assert box["x"] + box["width"] <= viewport["width"] + 1
    assert box["y"] >= -1
    assert box["y"] + box["height"] <= viewport["height"] + 1


def _wait_for_blocked_dashboard(page: Page, url: str, run_id: str) -> None:
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        response = page.request.get(
            f"{url}api/dashboard?run_id={run_id}&stage=idea"
        )
        assert response.status == 200
        dashboard = response.json()["dashboard"]
        stage = next(item for item in dashboard["stages"] if item["stage"] == "idea")
        if stage["status"] == "blocked":
            return
        time.sleep(0.1)
    raise AssertionError("question fixture did not reach a durable blocked state")


def test_wave42_first_time_operator_journey_records_bounded_rehearsal(
    tmp_path: Path,
) -> None:
    """Exercise the five-step route in one browser session without claiming human evidence."""

    project_root = tmp_path / "first-time-journey"
    project_root.mkdir()
    work_item = "WI-FIRST-TIME"
    configure_sleeping_fixture_runtime(project_root, sleep_seconds=300)
    evidence_writer = BrowserEvidenceWriter(tmp_path / "browser-evidence")
    steps: list[JourneyStepEvidence] = []
    journey_started = time.monotonic()

    with sync_playwright() as playwright, operator_browser_harness(
        project_root,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")

        step_started = time.monotonic()
        page.locator("#onboardingProjectRoot").fill(project_root.as_posix())
        page.locator("#onboardingProjectForm").evaluate("form => form.requestSubmit()")
        page.locator('[data-onboarding-runtime="generic-cli"]').wait_for(state="visible")
        steps.append(
            JourneyStepEvidence(
                step_id="create",
                action="Validate the local project and expose Work Item creation.",
                outcome="project validated; create form visible",
                elapsed_ms=round((time.monotonic() - step_started) * 1000),
            )
        )

        step_started = time.monotonic()
        page.locator('[data-onboarding-runtime="generic-cli"]').click(force=True)
        page.locator("#onboardingWorkItem").fill(work_item)
        page.locator("#onboardingRequest").fill(
            "Preserve the governed acceptance boundary and durable evidence."
        )
        page.locator("#onboardingCreateForm").evaluate("form => form.requestSubmit()")
        page.locator(".active-studio").wait_for(state="visible")
        assert page.evaluate("eval('state.selectedRuntime')") == "generic-cli"
        steps.append(
            JourneyStepEvidence(
                step_id="choose-runner",
                action="Choose the eligible generic-cli Runner and create the Work Item.",
                outcome="generic-cli selected; Work Item created",
                elapsed_ms=round((time.monotonic() - step_started) * 1000),
            )
        )

        step_started = time.monotonic()
        page.locator("#runtimeSettings").evaluate("node => { node.open = true; }")
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
        launch_button = page.locator("#globalNextActionButton")
        _assert_first_action(page, "#globalNextActionButton")
        with page.expect_response(
            lambda response: response.url.endswith("/api/workflow/run")
        ) as launch:
            launch_button.click()
        assert launch.value.status == 200
        launch_payload = launch.value.json()
        page.wait_for_function(
            "['running', 'waiting-for-operator'].includes(eval('state.activeJobStatus?.status'))",
            timeout=5_000,
        )
        run_id = str(launch_payload.get("run_id") or "")
        assert run_id, launch_payload
        job_id = page.evaluate("eval('state.activeJobId')")
        if job_id:
            cancelled = page.request.post(f"{harness.url}api/jobs/{job_id}/cancel")
            assert cancelled.status == 200
        _mark_question_fixture(project_root, work_item, run_id)
        _wait_for_blocked_dashboard(page, harness.url, run_id)
        steps.append(
            JourneyStepEvidence(
                step_id="launch",
                action="Launch the workflow with the selected Runner.",
                outcome="launch accepted; durable question recovery fixture prepared",
                elapsed_ms=round((time.monotonic() - step_started) * 1000),
            )
        )

        step_started = time.monotonic()
        page.goto(
            f"{harness.url}?ui=studio&mode=studio&work_item={work_item}"
            f"&run_id={run_id}&stage=idea&view=recovery",
            wait_until="networkidle",
        )
        page.locator('[data-recovery-action="answer-questions"]').click()
        page.locator('[data-human-decision-surface="question"]').wait_for(
            state="visible"
        )
        answer = page.locator('[data-question-text="Q1"]')
        answer.fill("Preserve the public CLI and durable evidence boundary.")
        page.locator('[data-question-resolution="Q1"]').select_option("resolved")
        assert not page.locator('[data-answer-resume="Q1"]').is_disabled()
        steps.append(
            JourneyStepEvidence(
                step_id="answer-question",
                action="Read the blocking question and record a resolved answer.",
                outcome="Q1 resolved; Save answer & resume enabled",
                elapsed_ms=round((time.monotonic() - step_started) * 1000),
            )
        )

        step_started = time.monotonic()
        with page.expect_response(
            lambda response: response.url.endswith("/api/stage/run")
        ) as resumed:
            page.locator('[data-answer-resume="Q1"]').click()
        assert resumed.value.status == 200
        page.wait_for_function(
            "['running', 'waiting-for-operator'].includes(eval('state.activeJobStatus?.status'))",
            timeout=5_000,
        )
        assert page.evaluate(
            "eval('state.dashboard.active_stage_view.questions.unresolved_blocking_question_ids')"
        ) == []
        steps.append(
            JourneyStepEvidence(
                step_id="resume-session",
                action="Resume the blocked stage after durable answer readback.",
                outcome="stage resume accepted; no unresolved blocking questions",
                elapsed_ms=round((time.monotonic() - step_started) * 1000),
            )
        )

        assert tuple(step.step_id for step in steps) == JOURNEY_STEP_IDS
        assert_accessible_render(page, target_size=32)
        assert_rendered_geometry(page)
        assert page.locator("[data-aidd-primary-action]:visible").count() <= 1
        assert page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth"
        )
        evidence_writer.capture(
            fixture="first-time-journey",
            page=page,
            diagnostics=browser_page.diagnostics,
        )
        browser_page.diagnostics.assert_clean()

    evidence_writer.commit(
        cleanup=BrowserCleanupStatus(
            page_closed=True,
            context_closed=True,
            browser_closed=True,
            server_stopped=True,
            workspace_removed=True,
        )
    )
    evidence = FirstTimeJourneyEvidence(
        schema=WAVE42_FIRST_TIME_JOURNEY_SCHEMA,
        session_id="S-W42-REHEARSAL-1",
        observation_mode="scripted-provider-free-rehearsal",
        environment_status="provider-free",
        completion="completed",
        elapsed_ms=round((time.monotonic() - journey_started) * 1000),
        wrong_actions=0,
        first_wrong_action=None,
        assistance="none",
        confidence=None,
        first_decisive_confusion=None,
        resulting_tasks=(),
        default_routing_decision=(
            "Keep the current renderer until Wave 42 exit evidence is complete; "
            "route the next action through the core-owned Runner and question recovery."
        ),
        durable_outcome="answers.md persisted and the blocked stage accepted a resume request",
        steps=tuple(steps),
    )
    validate_first_time_journey_evidence(evidence)
    report_path = tmp_path / "first-time-journey" / "first-time-operator-evidence.json"
    write_first_time_journey_evidence(report_path, evidence)
    payload = report_path.read_text(encoding="utf-8")
    assert '"schema": "wave42-first-time-operator-journey-v1"' in payload
    assert '"wrong_actions": 0' in payload
    assert payload.count('"step_id":') == len(JOURNEY_STEP_IDS)


def test_wave42_first_time_journey_contract_rejects_incomplete_steps() -> None:
    evidence = FirstTimeJourneyEvidence(
        schema=WAVE42_FIRST_TIME_JOURNEY_SCHEMA,
        session_id="S-invalid",
        observation_mode="scripted-provider-free-rehearsal",
        environment_status="provider-free",
        completion="completed",
        elapsed_ms=1,
        wrong_actions=0,
        first_wrong_action=None,
        assistance="none",
        confidence=None,
        first_decisive_confusion=None,
        resulting_tasks=(),
        default_routing_decision="keep current renderer",
        durable_outcome="none",
        steps=(),
    )
    try:
        validate_first_time_journey_evidence(evidence)
    except AssertionError:
        return
    raise AssertionError("incomplete first-time journey evidence must fail closed")
