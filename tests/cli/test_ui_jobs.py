from __future__ import annotations

import ast
from pathlib import Path

from aidd.cli import ui, ui_jobs


def test_ui_reexports_job_lifecycle_from_focused_module() -> None:
    assert ui.UiRunJobStore is ui_jobs.UiRunJobStore
    assert ui.UiJobSummary is ui_jobs.UiJobSummary
    assert ui.UiRunningNowItem is ui_jobs.UiRunningNowItem
    assert ui.compose_operator_inbox_with_jobs is ui_jobs.compose_operator_inbox_with_jobs

    source = Path(ui.__file__).read_text(encoding="utf-8")
    module = ast.parse(source)
    defined_names = {
        node.name
        for node in module.body
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
    }
    assert "UiRunJobStore" not in defined_names
    assert "_UiRunJob" not in defined_names


def test_two_project_job_lifecycle_isolation(tmp_path: Path) -> None:
    store = ui_jobs.UiRunJobStore()
    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"
    workspace_a = project_a / ".aidd"
    workspace_b = project_b / ".aidd"

    job_a = store.create(
        kind="stage",
        stage="plan",
        work_item="WI-A",
        run_id="run-a",
        project_root=project_a,
        workspace_root=workspace_a,
    )
    job_b = store.create(
        kind="stage",
        stage="idea",
        work_item="WI-B",
        run_id="run-b",
        project_root=project_b,
        workspace_root=workspace_b,
    )

    store.complete(job_a, result={"ok": True}, exit_code=0, message="done")
    view_a = store.view(job_a)
    view_b = store.view(job_b)

    assert view_a["status"] == "completed"
    assert view_a["project_root"] == project_a.as_posix()
    assert view_b["status"] == "running"
    assert view_b["project_root"] == project_b.as_posix()
    assert (
        store.active_job_for_context(
            project_root=project_a,
            workspace_root=workspace_a,
        )
        is None
    )
    assert (
        store.active_job_for_context(
            project_root=project_b,
            workspace_root=workspace_b,
        )["job_id"]
        == job_b
    )
