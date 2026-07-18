from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aidd.core.operator_frontend_models import (
    OperatorDashboardView,
    OperatorFirstFailure,
    OperatorNextAction,
)
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
        "needs-decision",
        "ready-to-continue",
        "flow-complete",
    ]
    assert inbox.item_count == 1
    item = inbox.sections[1].items[0]
    assert item.route.intent == "inbox-work-item"
    assert item.route.work_item == "WI-READY"
    assert item.route.run_id is None
    assert item.route.stage == "idea"
    assert item.primary_action.action == "choose-runtime"


def test_inbox_projection_omits_durable_running_item_until_job_overlay(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_work_item(workspace_root, "WI-RUNNING", running=True)

    inbox = resolve_operator_inbox_view(
        project_root=tmp_path,
        workspace_root=workspace_root,
    )

    assert inbox.item_count == 0


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

    needs_decision = inbox.sections[0]
    assert [item.route.work_item for item in needs_decision.items] == [
        "WI-ALPHA",
        "WI-ZETA",
    ]
    assert all(item.primary_action.action == "review-findings" for item in needs_decision.items)
