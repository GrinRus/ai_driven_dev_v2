from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidd.core.operator_frontend_models import (
    OperatorDashboardView,
    OperatorFirstFailure,
    OperatorNextAction,
)
from aidd.core.operator_frontend_project_home import resolve_operator_project_home_view
from aidd.core.operator_inbox import resolve_operator_inbox_view
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
)
from aidd.core.workspace import seed_work_item_metadata


def _prepare_work_item(
    workspace_root: Path,
    work_item: str,
    *,
    running: bool = False,
) -> None:
    seed_work_item_metadata(root=workspace_root, work_item=work_item)
    if not running:
        return
    run_id = f"run-{work_item.lower()}"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target="idea",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="idea",
    )
    persist_stage_status(workspace_root, work_item, run_id, "idea", "executing")


def test_inbox_projection_has_stable_sections_and_exact_identity(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_work_item(workspace_root, "WI-READY")

    inbox = resolve_operator_inbox_view(
        project_root=tmp_path,
        workspace_root=workspace_root,
    )

    assert [section.key for section in inbox.sections] == [
        "needs-input",
        "running",
        "ready",
        "complete",
    ]
    assert inbox.item_count == 1
    item = inbox.sections[2].items[0]
    assert item.route.intent == "inbox-work-item"
    assert item.route.work_item == "WI-READY"
    assert item.route.run_id is None
    assert item.route.stage == "idea"
    assert item.primary_action.action == "choose-runtime"
    assert inbox.entry_recommendation is not None
    assert inbox.entry_recommendation.action == "continue-existing-intent"
    assert inbox.entry_recommendation.label == "Continue existing Work Item"
    assert inbox.entry_recommendation.work_item == "WI-READY"


def test_project_home_intent_excerpt_is_bounded_and_excludes_markdown_heading(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_work_item(workspace_root, "WI-INTENT")
    request_path = (
        workspace_root / "workitems" / "WI-INTENT" / "context" / "user-request.md"
    )
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        "# Original request\n\nBuild a calmer operator workspace. " + ("Keep it bounded. " * 40),
        encoding="utf-8",
    )

    home = resolve_operator_project_home_view(
        project_root=tmp_path,
        workspace_root=workspace_root,
        selected_work_item="WI-INTENT",
        recent_project_roots=(),
    )
    assert home.selected_work_item_resume is not None
    assert home.selected_work_item_resume.intent.excerpt.startswith(
        "Build a calmer operator workspace."
    )
    assert len(home.selected_work_item_resume.intent.excerpt) <= 220
    assert home.selected_work_item_resume.intent.source_path == (
        "workitems/WI-INTENT/context/user-request.md"
    )

    inbox = resolve_operator_inbox_view(
        project_root=tmp_path,
        workspace_root=workspace_root,
    )
    item = inbox.sections[2].items[0]
    assert item.route.work_item == "WI-INTENT"


def test_inbox_projection_keeps_durable_running_item_visible(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_work_item(workspace_root, "WI-RUNNING", running=True)

    inbox = resolve_operator_inbox_view(
        project_root=tmp_path,
        workspace_root=workspace_root,
    )

    running = next(section for section in inbox.sections if section.key == "running")
    assert [item.route.work_item for item in running.items] == ["WI-RUNNING"]
    assert running.items[0].primary_action.action == "wait-for-stage"
    assert inbox.item_count == 1


def test_inbox_projection_orders_items_without_frontend_priority_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_work_item(workspace_root, "WI-ZETA")
    _prepare_work_item(workspace_root, "WI-ALPHA")

    from aidd.core import operator_inbox

    real_resolve = operator_inbox.resolve_operator_dashboard_view

    def resolve_with_decision(
        *,
        workspace_root: Path,
        work_item: str,
        active_stage: str,
        project_root: Path | None = None,
    ) -> OperatorDashboardView:
        dashboard = real_resolve(
            workspace_root=workspace_root,
            work_item=work_item,
            active_stage=active_stage,
            project_root=project_root,
        )
        return replace(
            dashboard,
            blockers=(),
            first_failure=OperatorFirstFailure(
                kind="operator-decision",
                title="Decision required",
                detail="Choose the retained evidence boundary.",
                stage="plan",
                path=None,
                time_utc=None,
            ),
            next_action=OperatorNextAction(
                action="review-findings",
                label="Review findings",
                detail="Review the retained evidence boundary.",
                stage="plan",
                enabled=True,
            ),
        )

    monkeypatch.setattr(operator_inbox, "resolve_operator_dashboard_view", resolve_with_decision)
    inbox = resolve_operator_inbox_view(
        project_root=tmp_path,
        workspace_root=workspace_root,
    )

    needs_input = inbox.sections[0]
    assert [item.route.work_item for item in needs_input.items] == [
        "WI-ALPHA",
        "WI-ZETA",
    ]
    assert all(item.primary_action.action == "review-findings" for item in needs_input.items)


def test_inbox_projection_classifies_failed_and_stale_terminal_states_as_needs_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_work_item(workspace_root, "WI-FAILED")
    _prepare_work_item(workspace_root, "WI-STALE")

    from aidd.core import operator_inbox

    real_resolve = operator_inbox.resolve_operator_dashboard_view

    def resolve_terminal_states(
        *,
        workspace_root: Path,
        work_item: str,
        active_stage: str,
        project_root: Path | None = None,
    ) -> OperatorDashboardView:
        dashboard = real_resolve(
            workspace_root=workspace_root,
            work_item=work_item,
            active_stage=active_stage,
            project_root=project_root,
        )
        if work_item == "WI-FAILED":
            return replace(
                dashboard,
                terminal_handoff=SimpleNamespace(status="failed"),
                blockers=(),
                first_failure=None,
            )
        return replace(
            dashboard,
            terminal_handoff=None,
            blockers=(),
            first_failure=None,
            next_action=replace(
                dashboard.next_action,
                action="rerun-stale-downstream",
                detail="QA evidence is stale after remediation.",
            ),
        )

    monkeypatch.setattr(operator_inbox, "resolve_operator_dashboard_view", resolve_terminal_states)
    inbox = resolve_operator_inbox_view(
        project_root=tmp_path,
        workspace_root=workspace_root,
    )

    needs_input = next(section for section in inbox.sections if section.key == "needs-input")
    assert [item.route.work_item for item in needs_input.items] == ["WI-FAILED", "WI-STALE"]
    assert all(item.state == "blocking" for item in needs_input.items)


def test_inbox_projection_recommends_needs_input_then_ready_not_running_or_complete(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    for work_item in ("WI-COMPLETE", "WI-RUNNING", "WI-READY", "WI-NEEDS"):
        _prepare_work_item(workspace_root, work_item, running=work_item == "WI-RUNNING")

    from aidd.core import operator_inbox

    real_resolve = operator_inbox.resolve_operator_dashboard_view

    def resolve_grouped_states(
        *,
        workspace_root: Path,
        work_item: str,
        active_stage: str,
        project_root: Path | None = None,
    ) -> OperatorDashboardView:
        dashboard = real_resolve(
            workspace_root=workspace_root,
            work_item=work_item,
            active_stage=active_stage,
            project_root=project_root,
        )
        if work_item == "WI-COMPLETE":
            return replace(
                dashboard,
                terminal_handoff=SimpleNamespace(
                    status="completed",
                    recommendation_rationale="QA is fresh and complete.",
                ),
                blockers=(),
                first_failure=None,
            )
        if work_item == "WI-READY":
            return replace(dashboard, blockers=(), first_failure=None)
        if work_item == "WI-NEEDS":
            return replace(
                dashboard,
                blockers=(),
                first_failure=OperatorFirstFailure(
                    kind="operator-decision",
                    title="Decision required",
                    detail="Choose the retained evidence boundary.",
                    stage="plan",
                    path=None,
                    time_utc=None,
                ),
            )
        return dashboard

    monkeypatch.setattr(operator_inbox, "resolve_operator_dashboard_view", resolve_grouped_states)
    inbox = resolve_operator_inbox_view(
        project_root=tmp_path,
        workspace_root=workspace_root,
    )

    assert inbox.entry_recommendation is not None
    assert inbox.entry_recommendation.work_item == "WI-NEEDS"
    assert inbox.entry_recommendation.action == "continue-existing-intent"
