from __future__ import annotations

from pathlib import Path

from aidd.core.onboarding import OnboardingWorkItemSummary
from aidd.core.operator_frontend_dashboard import resolve_operator_dashboard_view
from aidd.core.operator_frontend_models import (
    OperatorProjectHomeView,
    OperatorProjectSetRootSummary,
    OperatorRunSummary,
    OperatorWorkItemSummary,
)
from aidd.core.project_set import PROJECT_SET_CONTEXT_FILENAME
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stages import STAGES
from aidd.core.workspace import (
    WORKITEM_CONTEXT_USER_REQUEST_FILENAME,
    WORKITEM_METADATA_FILENAME,
    work_item_context_root,
    workspace_workitems_root,
)

_RUNTIME_FAILURE_KINDS = frozenset(
    {
        "cancelled",
        "failed",
        "non_zero_exit",
        "non-zero-exit",
        "provider_error",
        "provider-no-progress",
        "runtime-error",
        "runtime-exit-metadata-invalid",
        "runtime-failure",
        "stage-failed",
        "timeout",
    }
)


def _discover_work_items(workspace_root: Path) -> tuple[OnboardingWorkItemSummary, ...]:
    workitems_root = workspace_workitems_root(workspace_root)
    if not workitems_root.is_dir():
        return ()
    items: list[OnboardingWorkItemSummary] = []
    for path in sorted(workitems_root.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_dir():
            continue
        if not (path / WORKITEM_METADATA_FILENAME).exists():
            continue
        context_root = work_item_context_root(root=workspace_root, work_item=path.name)
        items.append(
            OnboardingWorkItemSummary(
                work_item=path.name,
                has_request_context=(
                    context_root / WORKITEM_CONTEXT_USER_REQUEST_FILENAME
                ).exists(),
            )
        )
    return tuple(items)


def _project_set_roots(
    *,
    workspace_root: Path,
    work_item: str,
) -> tuple[OperatorProjectSetRootSummary, ...]:
    path = (
        work_item_context_root(root=workspace_root, work_item=work_item)
        / PROJECT_SET_CONTEXT_FILENAME
    )
    if not path.exists():
        return ()
    rows: list[OperatorProjectSetRootSummary] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return ()
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("| `") or "` | `" not in stripped:
            continue
        parts = [part.strip().strip("` ") for part in stripped.strip("|").split("|")]
        if len(parts) < 3 or parts[0] == "Project id":
            continue
        rows.append(
            OperatorProjectSetRootSummary(
                root_id=parts[0],
                root=(workspace_root.parent / parts[1]).resolve(strict=False).as_posix(),
                relative_root=parts[1],
                role=None if parts[2] == "unspecified" else parts[2],
            )
        )
    return tuple(rows)


def _active_stage_from_run(run: OperatorRunSummary) -> str:
    if run.stage_target in STAGES:
        return run.stage_target
    return STAGES[0]


def _work_item_summary(
    *,
    project_root: Path,
    workspace_root: Path,
    item: OnboardingWorkItemSummary,
) -> OperatorWorkItemSummary:
    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item=item.work_item,
        active_stage=STAGES[0],
        project_root=project_root,
    )
    if (
        dashboard.first_failure is not None
        and dashboard.first_failure.kind in _RUNTIME_FAILURE_KINDS
        and dashboard.first_failure.stage in STAGES
    ):
        dashboard = resolve_operator_dashboard_view(
            workspace_root=workspace_root,
            work_item=item.work_item,
            active_stage=dashboard.first_failure.stage,
            project_root=project_root,
        )
    stages = dashboard.stages
    completed = sum(1 for stage in stages if stage.status == "succeeded")
    terminal_state = (
        "completed"
        if dashboard.terminal_handoff is not None
        else "blocked"
        if dashboard.blockers
        else "running"
        if any(stage.status in {"preparing", "executing", "validating"} for stage in stages)
        else "ready"
    )
    active = (
        "qa"
        if terminal_state == "completed" and any(stage.stage == "qa" for stage in stages)
        else next(
            (
                stage.stage
                for stage in stages
                if stage.status in {"preparing", "executing", "validating"}
            ),
            dashboard.next_action.stage or next(
                (stage.stage for stage in stages if stage.status != "succeeded"),
                _active_stage_from_run(dashboard.run),
            ),
        )
    )
    return OperatorWorkItemSummary(
        work_item=item.work_item,
        has_request_context=item.has_request_context,
        latest_run=dashboard.run,
        active_stage=active,
        stage_progress_label=f"{completed}/{len(STAGES)}",
        stage_progress_count=completed,
        stage_total_count=len(STAGES),
        blocker_count=len(dashboard.blockers),
        terminal_state=terminal_state,
        project_set_roots=_project_set_roots(
            workspace_root=workspace_root,
            work_item=item.work_item,
        ),
    )


def resolve_operator_project_home_view(
    *,
    project_root: Path,
    workspace_root: Path,
    selected_work_item: str | None = None,
    recent_project_roots: tuple[Path, ...] = (),
) -> OperatorProjectHomeView:
    resolved_project_root = project_root.resolve(strict=False)
    resolved_workspace_root = workspace_root.resolve(strict=False)
    if not resolved_workspace_root.is_relative_to(resolved_project_root):
        raise ValueError("AIDD workspace root must stay inside the selected project root.")

    summaries = tuple(
        _work_item_summary(
            project_root=resolved_project_root,
            workspace_root=resolved_workspace_root,
            item=item,
        )
        for item in _discover_work_items(resolved_workspace_root)
    )
    selected = (selected_work_item or "").strip() or None
    selected_summary = None
    if selected is not None:
        selected_summary = next(
            (summary for summary in summaries if summary.work_item == selected),
            None,
        )
        if selected_summary is None:
            raise ValueError(f"Work item '{selected}' does not exist in selected project.")

    return OperatorProjectHomeView(
        project_root=resolved_project_root,
        workspace_root=resolved_workspace_root,
        workspace_exists=resolved_workspace_root.exists(),
        work_items=summaries,
        recent_project_roots=tuple(
            workspace_relative_path(resolved_project_root, path.resolve(strict=False))
            if path.resolve(strict=False).is_relative_to(resolved_project_root)
            else path.resolve(strict=False).as_posix()
            for path in recent_project_roots
            if path.exists()
        ),
        selected_work_item=selected,
        selected_work_item_resume=selected_summary,
    )


__all__ = ["resolve_operator_project_home_view"]
