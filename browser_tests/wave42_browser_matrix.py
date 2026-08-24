"""Declarative browser acceptance matrix for the Wave 42 operator surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

from browser_tests.browser_harness import VIEWPORTS

WAVE42_BROWSER_MATRIX_SCHEMA = "wave42-responsive-browser-matrix-v1"


@dataclass(frozen=True, slots=True)
class Wave42BrowserJourney:
    journey_id: str
    fixture_state: str
    route: str
    surface_selector: str
    first_action_selector: str
    coverage_sources: tuple[str, ...]
    requires_initial_viewport: bool = False


WAVE42_BROWSER_JOURNEYS: tuple[Wave42BrowserJourney, ...] = (
    Wave42BrowserJourney(
        journey_id="create-runner-launch",
        fixture_state="no-run",
        route="studio",
        surface_selector=".active-studio",
        first_action_selector="#globalNextActionButton",
        coverage_sources=("browser_tests/test_journey_guided_setup.py",),
        requires_initial_viewport=True,
    ),
    Wave42BrowserJourney(
        journey_id="task-run",
        fixture_state="implementation-finalized",
        route="tasks",
        surface_selector="[data-task-workspace]",
        first_action_selector="[data-task-select]",
        coverage_sources=("browser_tests/test_journey_implementation.py",),
    ),
    Wave42BrowserJourney(
        journey_id="question-recovery",
        fixture_state="blocking-question",
        route="question-recovery",
        surface_selector=".recovery-workbench",
        first_action_selector="[data-recovery-summary] [data-primary-action]",
        coverage_sources=("browser_tests/test_journey_question_recovery.py",),
        requires_initial_viewport=True,
    ),
    Wave42BrowserJourney(
        journey_id="validation-repair",
        fixture_state="validation-repair",
        route="validation-repair",
        surface_selector=".recovery-workbench",
        first_action_selector="[data-recovery-summary] [data-primary-action]",
        coverage_sources=("browser_tests/test_journey_runtime_validation_recovery.py",),
        requires_initial_viewport=True,
    ),
    Wave42BrowserJourney(
        journey_id="markdown-change",
        fixture_state="remediation-stale",
        route="markdown-change",
        surface_selector="#studioDocumentCanvas",
        first_action_selector="#studioDocumentCanvas [data-artifact-mode]",
        coverage_sources=("browser_tests/test_journey_document_evidence.py",),
    ),
    Wave42BrowserJourney(
        journey_id="review-remediation",
        fixture_state="remediation-stale",
        route="review-remediation",
        surface_selector="[data-recovery-summary]",
        first_action_selector='[data-recovery-summary] [data-primary-action]',
        coverage_sources=("browser_tests/test_journey_review_qa.py",),
        requires_initial_viewport=True,
    ),
    Wave42BrowserJourney(
        journey_id="history",
        fixture_state="history",
        route="history",
        surface_selector="[data-studio-history]",
        first_action_selector="[data-history-run]",
        coverage_sources=("browser_tests/test_history_journey.py",),
    ),
    Wave42BrowserJourney(
        journey_id="completion",
        fixture_state="terminal-handoff",
        route="completion",
        surface_selector="[data-studio-flow-complete]",
        first_action_selector="[data-next-flow-action]",
        coverage_sources=("browser_tests/test_terminal_journey.py",),
        requires_initial_viewport=True,
    ),
)


def wave42_route_query(
    journey: Wave42BrowserJourney,
    *,
    work_item: str,
    run_id: str | None,
) -> str:
    """Return the canonical query used by the provider-free matrix."""

    common = {"mode": "studio", "work_item": work_item}
    if run_id:
        common["run_id"] = run_id
    if journey.route == "studio":
        common.update({"view": "overview"})
    elif journey.route == "tasks":
        common.update({"stage": "implement", "work_tab": "tasks"})
    elif journey.route == "question-recovery":
        common.update({"stage": "idea", "view": "recovery"})
    elif journey.route == "validation-repair":
        common.update({"stage": "plan", "view": "recovery"})
    elif journey.route == "markdown-change":
        common.update({"stage": "qa", "view": "overview"})
    elif journey.route == "review-remediation":
        common.update({"stage": "qa", "view": "recovery"})
    elif journey.route == "completion":
        common.update({"stage": "qa"})
    elif journey.route == "history":
        common = {
            "mode": "history",
            "work_item": work_item,
            "run_id": run_id,
            "stage": "implement",
        }
    else:
        raise ValueError(f"Unknown Wave 42 journey route: {journey.route}")
    return "?" + urlencode(common)


def validate_wave42_browser_matrix() -> None:
    """Fail closed when the acceptance registry becomes ambiguous."""

    ids = [journey.journey_id for journey in WAVE42_BROWSER_JOURNEYS]
    assert len(ids) == len(set(ids)), "Wave 42 journey ids must be unique"
    assert len(WAVE42_BROWSER_JOURNEYS) == 8
    assert VIEWPORTS == (
        (320, 568),
        (390, 844),
        (768, 1024),
        (1280, 900),
        (1440, 900),
    )
    for journey in WAVE42_BROWSER_JOURNEYS:
        assert journey.journey_id == journey.journey_id.strip()
        assert journey.fixture_state
        assert journey.surface_selector
        assert journey.first_action_selector
        assert journey.coverage_sources
        for source in journey.coverage_sources:
            assert (Path(__file__).resolve().parents[1] / source).is_file()
        query = wave42_route_query(
            journey,
            work_item="WI-BROWSER",
            run_id="run-browser",
        )
        assert "random" not in query.lower()
        assert "credential" not in query.lower()
        assert "provider" not in query.lower()
