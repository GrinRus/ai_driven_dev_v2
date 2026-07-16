from __future__ import annotations

from pathlib import Path

from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT, load_stage_manifest
from aidd.validators.cross_document_rules.context import CrossDocumentContext
from aidd.validators.cross_document_rules.implementation_finalization import (
    IMPLEMENTATION_FINALIZATION_CODE,
    validate_implementation_finalization,
)
from aidd.validators.cross_document_rules.interview import (
    ANSWER_WITHOUT_QUESTION_CODE,
    BLOCKING_UNANSWERED_CODE,
    DUPLICATE_ANSWER_ID_CODE,
    DUPLICATE_QUESTION_ID_CODE,
    MALFORMED_INTERVIEW_DOCUMENT_CODE,
    validate_interview,
)
from aidd.validators.cross_document_rules.qa_upstream import (
    QA_REVIEW_RISK_CODE,
    QA_UPSTREAM_EVIDENCE_CODE,
    QA_UPSTREAM_VERDICT_CODE,
    validate_qa_upstream,
)
from aidd.validators.cross_document_rules.review_implementation import (
    REVIEW_IMPLEMENT_EVIDENCE_CODE,
    REVIEW_IMPLEMENT_FINDING_CODE,
    REVIEW_IMPLEMENT_PATH_CODE,
    validate_review_implementation,
)
from aidd.validators.cross_document_rules.stage_result import (
    PROJECT_SET_EVIDENCE_MISSING_CODE,
    REPAIR_BRIEF_NOT_REFERENCED_CODE,
    REPAIR_BUDGET_EXHAUSTED_CODE,
    REPAIR_MENTION_WITHOUT_BRIEF_CODE,
    validate_stage_result_links,
)
from aidd.validators.cross_document_rules.tasklist_plan import (
    TASKLIST_PLAN_DEPENDENCY_CODE,
    TASKLIST_PLAN_MILESTONE_CODE,
    TASKLIST_PLAN_VERIFICATION_CODE,
    validate_tasklist_plan,
)
from aidd.validators.models import ValidationFinding


def validate_cross_document_consistency(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[ValidationFinding, ...]:
    load_stage_manifest(stage=stage, contracts_root=contracts_root)
    context = CrossDocumentContext.load(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
    )
    return (
        *validate_interview(context),
        *validate_stage_result_links(context),
        *validate_tasklist_plan(context),
        *validate_review_implementation(context),
        *validate_qa_upstream(context),
        *validate_implementation_finalization(context),
    )


__all__ = [
    "ANSWER_WITHOUT_QUESTION_CODE",
    "BLOCKING_UNANSWERED_CODE",
    "DUPLICATE_ANSWER_ID_CODE",
    "DUPLICATE_QUESTION_ID_CODE",
    "IMPLEMENTATION_FINALIZATION_CODE",
    "MALFORMED_INTERVIEW_DOCUMENT_CODE",
    "PROJECT_SET_EVIDENCE_MISSING_CODE",
    "QA_REVIEW_RISK_CODE",
    "QA_UPSTREAM_EVIDENCE_CODE",
    "QA_UPSTREAM_VERDICT_CODE",
    "REPAIR_BRIEF_NOT_REFERENCED_CODE",
    "REPAIR_BUDGET_EXHAUSTED_CODE",
    "REPAIR_MENTION_WITHOUT_BRIEF_CODE",
    "REVIEW_IMPLEMENT_EVIDENCE_CODE",
    "REVIEW_IMPLEMENT_FINDING_CODE",
    "REVIEW_IMPLEMENT_PATH_CODE",
    "TASKLIST_PLAN_DEPENDENCY_CODE",
    "TASKLIST_PLAN_MILESTONE_CODE",
    "TASKLIST_PLAN_VERIFICATION_CODE",
    "validate_cross_document_consistency",
]
