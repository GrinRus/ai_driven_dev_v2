from __future__ import annotations

from pathlib import Path

from aidd.core.task_ledger import TaskFinalizationStatus, load_task_ledger
from aidd.core.task_plan import parse_task_plan


def implementation_finalization_blocker(
    *, workspace_root: Path, work_item: str, run_id: str
) -> str | None:
    """Return why downstream stages cannot trust implementation success."""

    tasklist_path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    if not tasklist_path.is_file():
        return f"Published tasklist is missing: {tasklist_path.as_posix()}."
    try:
        plan = parse_task_plan(tasklist_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return str(exc)
    ledger = load_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if ledger is None:
        return "Implementation task ledger is missing."
    if ledger.source_tasklist_sha256 != plan.source_sha256:
        return "Implementation task ledger source hash does not match the published tasklist."
    if not ledger.all_succeeded():
        return "Implementation task ledger does not record success for every task."
    if ledger.finalization.status is not TaskFinalizationStatus.SUCCEEDED:
        return "Implementation aggregate finalization has not succeeded."
    if not ledger.finalization.latest_attempt_path:
        return "Implementation aggregate finalization evidence path is missing."
    finalization_path = workspace_root / ledger.finalization.latest_attempt_path
    if not finalization_path.is_dir():
        return "Implementation aggregate finalization evidence is missing."
    published_report = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "output"
        / "implementation-report.md"
    )
    if not published_report.is_file():
        return "Published aggregate implementation report is missing."
    return None


__all__ = ["implementation_finalization_blocker"]
