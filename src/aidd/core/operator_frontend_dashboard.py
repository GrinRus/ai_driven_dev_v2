from __future__ import annotations

from pathlib import Path

from aidd.core.operator_frontend_common import validate_operator_stage
from aidd.core.operator_frontend_dashboard_evidence import (
    collect_operator_dashboard_evidence,
)
from aidd.core.operator_frontend_dashboard_reducer import (
    reduce_operator_dashboard_evidence,
)
from aidd.core.operator_frontend_models import OperatorDashboardView
from aidd.core.stages import STAGES


def resolve_operator_dashboard_view(
    *,
    workspace_root: Path,
    work_item: str,
    active_stage: str = STAGES[0],
    run_id: str | None = None,
    project_root: Path | None = None,
) -> OperatorDashboardView:
    validate_operator_stage(active_stage)
    evidence = collect_operator_dashboard_evidence(
        workspace_root=workspace_root,
        work_item=work_item,
        active_stage=active_stage,
        run_id=run_id,
        project_root=project_root,
    )
    return reduce_operator_dashboard_evidence(evidence)


__all__ = ["resolve_operator_dashboard_view"]
