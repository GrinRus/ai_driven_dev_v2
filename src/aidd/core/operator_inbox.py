from __future__ import annotations

from pathlib import Path

from aidd.core.operator_frontend_dashboard import resolve_operator_dashboard_view
from aidd.core.operator_frontend_models import (
    OperatorDashboardView,
    OperatorInboxEntryRecommendation,
    OperatorInboxItem,
    OperatorInboxRoute,
    OperatorInboxSection,
    OperatorInboxView,
    OperatorWorkItemSummary,
)
from aidd.core.operator_frontend_project_home import resolve_operator_project_home_view
from aidd.core.stages import STAGES

_SECTION_ORDER = ("needs-decision", "ready-to-continue", "flow-complete")
_SECTION_LABELS = {
    "needs-decision": "Needs your decision",
    "ready-to-continue": "Ready to continue",
    "flow-complete": "Flow complete",
}
_DECISION_ACTIONS = frozenset(
    {
        "answer-questions",
        "inspect-validation",
        "qa-verdict",
        "review-findings",
        "review-intervention",
        "rerun-stale-downstream",
    }
)


def _section_for(dashboard: OperatorDashboardView) -> str | None:
    handoff = dashboard.terminal_handoff
    if handoff is not None:
        if handoff.status in {"completed", "completed-with-warning", "failed"}:
            return "flow-complete"
        return "needs-decision"
    if dashboard.blockers or dashboard.first_failure is not None:
        return "needs-decision"
    if dashboard.next_action.action in _DECISION_ACTIONS:
        return "needs-decision"
    if dashboard.next_action.action == "wait-for-stage":
        return None
    return "ready-to-continue"


def _item_state(section: str) -> str:
    return {
        "needs-decision": "blocking",
        "ready-to-continue": "ready",
        "flow-complete": "terminal",
    }[section]


def _summary_for(dashboard: OperatorDashboardView, section: str) -> str:
    if section == "needs-decision" and dashboard.first_failure is not None:
        return dashboard.first_failure.detail
    if section == "needs-decision" and dashboard.blockers:
        return dashboard.blockers[0].detail
    if section == "flow-complete" and dashboard.terminal_handoff is not None:
        rationale = dashboard.terminal_handoff.recommendation_rationale
        return rationale or dashboard.next_action.detail
    return dashboard.next_action.detail


def _inbox_item(
    *,
    summary: OperatorWorkItemSummary,
    dashboard: OperatorDashboardView,
    section: str,
) -> OperatorInboxItem:
    run_id = dashboard.run.run_id
    stage = dashboard.next_action.stage or summary.active_stage
    return OperatorInboxItem(
        item_id=f"{summary.work_item}:{run_id or 'no-run'}:{section}",
        state=_item_state(section),
        status_label=_SECTION_LABELS[section],
        title=summary.work_item,
        summary=_summary_for(dashboard, section),
        route=OperatorInboxRoute(
            intent="inbox-work-item",
            work_item=summary.work_item,
            run_id=run_id,
            stage=stage,
        ),
        primary_action=dashboard.next_action,
    )


def _item_sort_key(item: OperatorInboxItem) -> tuple[int, str, str]:
    stage_index = STAGES.index(item.route.stage) if item.route.stage in STAGES else len(STAGES)
    return stage_index, item.route.work_item.casefold(), item.item_id


def _entry_recommendation(
    sections: tuple[OperatorInboxSection, ...],
) -> OperatorInboxEntryRecommendation:
    for section_key in ("needs-decision", "ready-to-continue"):
        section = next((item for item in sections if item.key == section_key), None)
        candidate = section.items[0] if section and section.items else None
        if candidate is not None:
            return OperatorInboxEntryRecommendation(
                action="continue-existing-intent",
                label="Continue existing Work Item",
                detail=candidate.summary,
                work_item=candidate.route.work_item,
                route=candidate.route,
            )
    has_completed = any(
        section.key == "flow-complete" and section.items for section in sections
    )
    return OperatorInboxEntryRecommendation(
        action="create-new-intent",
        label="Create new Work Item",
        detail=(
            "Current Work Items are complete. Start a separate Work Item for new work."
            if has_completed
            else "No active Work Item is waiting. Capture the outcome you want to deliver."
        ),
    )


def resolve_operator_inbox_view(
    *,
    project_root: Path,
    workspace_root: Path,
) -> OperatorInboxView:
    home = resolve_operator_project_home_view(
        project_root=project_root,
        workspace_root=workspace_root,
    )
    grouped: dict[str, list[OperatorInboxItem]] = {
        key: [] for key in _SECTION_ORDER
    }
    for summary in home.work_items:
        dashboard = resolve_operator_dashboard_view(
            workspace_root=workspace_root,
            work_item=summary.work_item,
            active_stage=summary.active_stage,
            project_root=project_root,
        )
        section = _section_for(dashboard)
        if section is None:
            continue
        grouped[section].append(
            _inbox_item(summary=summary, dashboard=dashboard, section=section)
        )
    sections = tuple(
        OperatorInboxSection(
            key=key,
            label=_SECTION_LABELS[key],
            items=tuple(sorted(grouped[key], key=_item_sort_key)),
        )
        for key in _SECTION_ORDER
    )
    return OperatorInboxView(
        project_root=home.project_root,
        workspace_root=home.workspace_root,
        sections=sections,
        entry_recommendation=_entry_recommendation(sections),
    )


__all__ = ["resolve_operator_inbox_view"]
