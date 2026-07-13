from __future__ import annotations

from pathlib import Path

from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    load_stage_manifest,
    resolve_expected_output_documents,
)
from aidd.validators.document_loader import load_markdown_document
from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_EXECUTION_SUMMARY_CODE,
    INCOMPLETE_SECTION_CODE,
    MISSING_DIFF_EVIDENCE_CODE,
    MISSING_EVIDENCE_LINK_CODE,
    MISSING_EVIDENCE_REF_CODE,
    PLACEHOLDER_CONTENT_CODE,
    RISK_UNDERREPORT_CODE,
    UNSUPPORTED_CLAIM_CODE,
    UNSUPPORTED_VERDICT_CODE,
    UNVERIFIABLE_CHECK_CLAIM_CODE,
    SemanticDocumentContext,
    SemanticRule,
    required_sections_for_document,
    validate_placeholder_sections,
)
from aidd.validators.semantic_rules.idea import RULES as IDEA_RULES
from aidd.validators.semantic_rules.implement import RULES as IMPLEMENT_RULES
from aidd.validators.semantic_rules.placeholders import has_non_placeholder_text
from aidd.validators.semantic_rules.plan import RULES as PLAN_RULES
from aidd.validators.semantic_rules.qa import RULES as QA_RULES
from aidd.validators.semantic_rules.research import RULES as RESEARCH_RULES
from aidd.validators.semantic_rules.review import RULES as REVIEW_RULES
from aidd.validators.semantic_rules.review_spec import RULES as REVIEW_SPEC_RULES
from aidd.validators.semantic_rules.stage_result import validate_stage_result
from aidd.validators.semantic_rules.tasklist import RULES as TASKLIST_RULES

_RULE_GROUPS = (
    IDEA_RULES,
    RESEARCH_RULES,
    PLAN_RULES,
    REVIEW_SPEC_RULES,
    TASKLIST_RULES,
    IMPLEMENT_RULES,
    REVIEW_RULES,
    QA_RULES,
)

SEMANTIC_RULES: dict[tuple[str, str], SemanticRule] = {
    (rule.stage, rule.document_name): rule for rules in _RULE_GROUPS for rule in rules
}


def semantic_rule_for(*, stage: str, document_name: str) -> SemanticRule | None:
    return SEMANTIC_RULES.get((stage, document_name))


def validate_semantic_outputs(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    validate_stage_result_document: bool = False,
) -> tuple[ValidationFinding, ...]:
    load_stage_manifest(stage=stage, contracts_root=contracts_root)
    expected_outputs = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    findings: list[ValidationFinding] = []
    for output_path in expected_outputs:
        if not output_path.exists():
            continue

        required_sections = required_sections_for_document(
            stage=stage,
            document_name=output_path.name,
            contracts_root=contracts_root,
        )
        if not required_sections:
            continue

        loaded_document = load_markdown_document(path=output_path, workspace_root=workspace_root)
        context = SemanticDocumentContext.from_markdown(
            stage=stage,
            output_path=output_path,
            workspace_root=workspace_root,
            required_sections=required_sections,
            markdown_text=loaded_document.body,
        )
        if output_path.name == "stage-result.md":
            if validate_stage_result_document:
                findings.extend(validate_stage_result(context))
            else:
                findings.extend(validate_placeholder_sections(context))
            continue
        rule = semantic_rule_for(stage=stage, document_name=output_path.name)
        if rule is None:
            findings.extend(validate_placeholder_sections(context))
            continue
        findings.extend(rule.validate(context))

    return tuple(findings)


__all__ = [
    "INCOMPLETE_EXECUTION_SUMMARY_CODE",
    "INCOMPLETE_SECTION_CODE",
    "MISSING_DIFF_EVIDENCE_CODE",
    "MISSING_EVIDENCE_LINK_CODE",
    "MISSING_EVIDENCE_REF_CODE",
    "PLACEHOLDER_CONTENT_CODE",
    "RISK_UNDERREPORT_CODE",
    "SEMANTIC_RULES",
    "UNSUPPORTED_CLAIM_CODE",
    "UNSUPPORTED_VERDICT_CODE",
    "UNVERIFIABLE_CHECK_CLAIM_CODE",
    "has_non_placeholder_text",
    "semantic_rule_for",
    "validate_semantic_outputs",
]
