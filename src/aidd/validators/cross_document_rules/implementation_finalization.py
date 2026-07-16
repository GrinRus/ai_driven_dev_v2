from __future__ import annotations

from aidd.core.implementation_eligibility import implementation_finalization_blocker
from aidd.core.run_lookup import latest_run_id
from aidd.validators.cross_document_rules.context import (
    CrossDocumentContext,
    workspace_relative,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation

IMPLEMENTATION_FINALIZATION_CODE = "CROSS-IMPLEMENTATION-FINALIZATION"


def validate_implementation_finalization(
    context: CrossDocumentContext,
) -> tuple[ValidationFinding, ...]:
    if context.stage not in {"review", "qa"} or not context.published_tasklist_path.exists():
        return ()
    run_id = latest_run_id(
        workspace_root=context.workspace_root,
        work_item=context.work_item,
    )
    blocker = (
        "Implementation run is missing."
        if run_id is None
        else implementation_finalization_blocker(
            workspace_root=context.workspace_root,
            work_item=context.work_item,
            run_id=run_id,
        )
    )
    if blocker is None:
        return ()
    return (
        ValidationFinding(
            IMPLEMENTATION_FINALIZATION_CODE,
            blocker,
            "critical",
            ValidationIssueLocation(
                workspace_relative(context.stage_root, context.workspace_root)
            ),
        ),
    )
