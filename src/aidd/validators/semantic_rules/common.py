from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from aidd.core.markdown import (
    MarkdownHeading,
    MarkdownSectionIndex,
    extract_required_sections_from_document_contract,
    extract_stage_required_heading_map,
    normalize_heading,
)
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT
from aidd.validators.models import SeverityLevel, ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic_rules.blocks import (
    extract_bullet_items as extract_bullet_items,
)
from aidd.validators.semantic_rules.blocks import (
    extract_implementation_verification_blocks as extract_implementation_verification_blocks,
)
from aidd.validators.semantic_rules.blocks import (
    extract_markdown_list_items as extract_markdown_list_items,
)
from aidd.validators.semantic_rules.blocks import (
    extract_markdown_table_rows as extract_markdown_table_rows,
)
from aidd.validators.semantic_rules.blocks import (
    extract_risk_blocks as extract_risk_blocks,
)
from aidd.validators.semantic_rules.blocks import (
    extract_subheading_blocks as extract_subheading_blocks,
)
from aidd.validators.semantic_rules.blocks import (
    extract_top_level_bullet_blocks as extract_top_level_bullet_blocks,
)
from aidd.validators.semantic_rules.blocks import (
    has_bullet_items as has_bullet_items,
)
from aidd.validators.semantic_rules.blocks import (
    is_markdown_table_separator as is_markdown_table_separator,
)
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_ARTIFACT_REFERENCE_PATTERN as IMPLEMENT_ARTIFACT_REFERENCE_PATTERN,
)
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_COMMAND_PATTERN as IMPLEMENT_COMMAND_PATTERN,
)
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_COMPLETION_CLAIM_PATTERN as IMPLEMENT_COMPLETION_CLAIM_PATTERN,
)
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_DEFERRED_VERIFICATION_PATTERN as IMPLEMENT_DEFERRED_VERIFICATION_PATTERN,
)
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_FILE_ENTRY_PATTERN as IMPLEMENT_FILE_ENTRY_PATTERN,
)
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_NOOP_JUSTIFICATION_PATTERN as IMPLEMENT_NOOP_JUSTIFICATION_PATTERN,
)
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_RESULT_PATTERN as IMPLEMENT_RESULT_PATTERN,
)
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN as IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN,
)
from aidd.validators.semantic_rules.evidence import (
    has_implementation_command_evidence as has_implementation_command_evidence,
)
from aidd.validators.semantic_rules.evidence import (
    is_deferred_implementation_verification as is_deferred_implementation_verification,
)
from aidd.validators.semantic_rules.findings import validation_finding
from aidd.validators.semantic_rules.ids import (
    CITATION_ID_PATTERN as CITATION_ID_PATTERN,
)
from aidd.validators.semantic_rules.ids import (
    MILESTONE_ID_PATTERN as MILESTONE_ID_PATTERN,
)
from aidd.validators.semantic_rules.ids import (
    TASKLIST_TASK_ID_PATTERN as TASKLIST_TASK_ID_PATTERN,
)
from aidd.validators.semantic_rules.ids import (
    extract_citation_ids as extract_citation_ids,
)
from aidd.validators.semantic_rules.ids import (
    extract_milestone_ids as extract_milestone_ids,
)
from aidd.validators.semantic_rules.ids import (
    extract_tasklist_task_ids as extract_tasklist_task_ids,
)
from aidd.validators.semantic_rules.placeholders import contains_placeholder_content
from aidd.validators.semantic_rules.risks import (
    QA_EVIDENCE_ID_PATTERN as QA_EVIDENCE_ID_PATTERN,
)
from aidd.validators.semantic_rules.risks import (
    QA_OWNER_PATTERN as QA_OWNER_PATTERN,
)
from aidd.validators.semantic_rules.risks import (
    QA_RISK_SEVERITY_PATTERN as QA_RISK_SEVERITY_PATTERN,
)
from aidd.validators.semantic_rules.risks import (
    RISK_MITIGATION_PATTERN as RISK_MITIGATION_PATTERN,
)
from aidd.validators.semantic_rules.risks import (
    is_empty_risk_entry as is_empty_risk_entry,
)
from aidd.validators.semantic_rules.risks import (
    is_risk_metadata_entry as is_risk_metadata_entry,
)

INCOMPLETE_SECTION_CODE = "SEM-INCOMPLETE-SECTION"
UNSUPPORTED_CLAIM_CODE = "SEM-UNSUPPORTED-CLAIM"
PLACEHOLDER_CONTENT_CODE = "SEM-PLACEHOLDER-CONTENT"
MISSING_EVIDENCE_LINK_CODE = "SEM-MISSING-EVIDENCE-LINK"
MISSING_DIFF_EVIDENCE_CODE = "SEM-MISSING-DIFF-EVIDENCE"
UNVERIFIABLE_CHECK_CLAIM_CODE = "SEM-UNVERIFIABLE-CHECK-CLAIM"
INCOMPLETE_EXECUTION_SUMMARY_CODE = "SEM-INCOMPLETE-EXECUTION-SUMMARY"
UNSUPPORTED_VERDICT_CODE = "SEM-UNSUPPORTED-VERDICT"
MISSING_EVIDENCE_REF_CODE = "SEM-MISSING-EVIDENCE-REF"
RISK_UNDERREPORT_CODE = "SEM-RISK-UNDERREPORT"

STAGE_HEADING_REQUIREMENT_PATTERN = re.compile(
    r"required heading coverage in\s+`([^`]+)`\s*\((.+)\)",
    flags=re.IGNORECASE,
)
UNSUPPORTED_CLAIM_PATTERN = re.compile(
    r"\b(always|never|guarantee(?:d|s)?|proven|certain(?:ly)?)\b",
    flags=re.IGNORECASE,
)
NEGATED_GUARANTEE_CAVEAT_PATTERN = re.compile(
    r"\b(?:(?:no|not|without)\b|(?:disclaim(?:s|ed|ing)?|disclaimer\s+of)\b)"
    r"[^\n.]{0,80}\bguarantee(?:d|s)?\b",
    flags=re.IGNORECASE,
)
REVIEW_SPEC_READINESS_PATTERN = re.compile(
    r"\b(ready-with-conditions|not-ready|ready)\b",
    flags=re.IGNORECASE,
)
REVIEW_SPEC_DECISION_PATTERN = re.compile(
    r"\b(approved-with-conditions|rejected|approved)\b",
    flags=re.IGNORECASE,
)
EXPLICIT_SEVERITY_LABEL_PATTERN = re.compile(
    r"^\s*[-*]?\s*(?:\*\*)?Severity(?:\*\*)?\s*:?(?:\*\*)?\s*:?\s*`?"
    r"(critical|high|medium|low|info|none)`?\b",
    flags=re.IGNORECASE | re.MULTILINE,
)
INLINE_FINDING_SEVERITY_PATTERN = re.compile(
    r"(?:"
    r"`?(?:RV|REV|I|OBS)-?\d+`?\s+`?(critical|high|medium|low|info|none)`?\b|"
    r"\[`?(critical|high|medium|low|info|none)`?\]|"
    r"\(`?(critical|high|medium|low|info|none)`?(?:[,)]|$)|"
    r"\s-\s`?(critical|high|medium|low|info|none)`?\s-"
    r")",
    flags=re.IGNORECASE,
)
REVIEW_SPEC_NO_ISSUE_SEVERITY_PATTERN = re.compile(
    r"\bseverity\s*:\s*`?none`?\b",
    flags=re.IGNORECASE,
)
REVIEW_SPEC_INLINE_SEVERITY_LABEL_PATTERN = re.compile(
    r"\bseverity\s*:\s*`?(critical|high|medium|low|info|none)`?\b",
    flags=re.IGNORECASE,
)
REVIEW_SPEC_NO_ISSUES_PATTERN = re.compile(
    r"\b(no material (?:issues?|defects?) identified|no issues? identified|none)\b",
    flags=re.IGNORECASE,
)
REVIEW_SPEC_SEVERITY_PATTERN = QA_RISK_SEVERITY_PATTERN
REVIEW_SPEC_RATIONALE_PATTERN = re.compile(
    r"\b(rationale|because)\b",
    flags=re.IGNORECASE,
)
REVIEW_FINDING_ID_PATTERN = re.compile(r"\b(?:RV|REV)-\d+\b", flags=re.IGNORECASE)
REVIEW_DISPOSITION_PATTERN = re.compile(
    r"\b(must-fix|follow-up|accepted-risk|invalid)\b",
    flags=re.IGNORECASE,
)
REVIEW_DISPOSITION_LABEL_PATTERN = re.compile(
    r"^\s*[-*]?\s*(?:\*\*)?Disposition\s*:?(?:\*\*)?\s*:?\s*`?"
    r"(must-fix|follow-up|accepted-risk|invalid)`?\b",
    flags=re.IGNORECASE | re.MULTILINE,
)
REVIEW_ACCEPTANCE_CRITERIA_PATTERN = re.compile(r"\bAC-\d+\b", flags=re.IGNORECASE)
QA_VERDICT_PATTERN = re.compile(
    r"\b(ready-with-risks|not-ready|ready)\b",
    flags=re.IGNORECASE,
)
QA_VERDICT_LABEL_PATTERN = re.compile(
    r"^\s*[-*]?\s*(?:\*\*)?(?:QA verdict|Quality verdict)\s*:?(?:\*\*)?\s*:?\s*`?"
    r"(ready-with-risks|not-ready|ready)`?\b",
    flags=re.IGNORECASE | re.MULTILINE,
)
QA_RELEASE_RECOMMENDATION_PATTERN = re.compile(
    r"\b(proceed-with-conditions|hold|proceed)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class SemanticSection:
    name: str
    content: str
    location: ValidationIssueLocation


@dataclass(frozen=True, slots=True)
class SemanticRule:
    stage: str
    document_name: str
    validate: Callable[[SemanticDocumentContext], tuple[ValidationFinding, ...]]


@dataclass(frozen=True, slots=True)
class SemanticDocumentContext:
    stage: str
    output_path: Path
    workspace_root: Path
    required_sections: tuple[str, ...]
    section_index: MarkdownSectionIndex

    @classmethod
    def from_markdown(
        cls,
        *,
        stage: str,
        output_path: Path,
        workspace_root: Path,
        required_sections: tuple[str, ...],
        markdown_text: str,
    ) -> SemanticDocumentContext:
        return cls(
            stage=stage,
            output_path=output_path,
            workspace_root=workspace_root,
            required_sections=required_sections,
            section_index=MarkdownSectionIndex.from_markdown(markdown_text),
        )

    @property
    def document_name(self) -> str:
        return self.output_path.name

    @property
    def headings(self) -> tuple[MarkdownHeading, ...]:
        return self.section_index.headings

    @property
    def markdown_lines(self) -> list[str]:
        return list(self.section_index.markdown_lines)

    @property
    def headings_by_title(self) -> dict[str, list[tuple[int, MarkdownHeading]]]:
        return {
            heading: list(matches)
            for heading, matches in self.section_index.headings_by_title.items()
        }

    @property
    def workspace_relative_path(self) -> str:
        return workspace_relative(self.output_path, self.workspace_root)

    def location(self, *, line_number: int = 1) -> ValidationIssueLocation:
        return ValidationIssueLocation(
            workspace_relative_path=self.workspace_relative_path,
            line_number=line_number,
        )

    def finding(
        self,
        *,
        code: str,
        message: str,
        severity: SeverityLevel = "high",
        location: ValidationIssueLocation | None = None,
    ) -> ValidationFinding:
        return validation_finding(
            code=code,
            message=message,
            severity=severity,
            location=location,
        )

    def first_heading_match(
        self,
        *,
        candidates: tuple[str, ...],
    ) -> tuple[int, MarkdownHeading] | None:
        for candidate in candidates:
            matches = self.headings_by_title.get(normalized_heading(candidate), [])
            if matches:
                return matches[0]
        return None

    def section_content_for_heading(self, *, heading_index: int) -> str:
        return section_content_for_heading(
            heading_index=heading_index,
            headings=self.headings,
            markdown_lines=self.markdown_lines,
        )

    def section_by_candidates(self, *, candidates: tuple[str, ...]) -> SemanticSection:
        match = self.first_heading_match(candidates=candidates)
        if match is None:
            return SemanticSection(
                name=candidates[0],
                content="",
                location=self.location(),
            )

        heading_index, heading = match
        return SemanticSection(
            name=heading.title,
            content=self.section_content_for_heading(heading_index=heading_index),
            location=self.location(line_number=heading.line_number),
        )

    def iter_required_sections(self) -> Iterator[SemanticSection]:
        for section in self.required_sections:
            matches = self.headings_by_title.get(normalized_heading(section), [])
            if not matches:
                continue

            heading_index, heading = matches[0]
            yield SemanticSection(
                name=section,
                content=self.section_content_for_heading(heading_index=heading_index),
                location=self.location(line_number=heading.line_number),
            )


def required_sections_for_document(
    *,
    stage: str,
    document_name: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[str, ...]:
    sections: list[str] = []
    document_contract_path = contracts_root.parent / "documents" / document_name
    if document_contract_path.exists():
        sections.extend(
            extract_required_sections_from_document_contract(
                document_contract_path.read_text(encoding="utf-8")
            )
        )

    stage_contract_path = contracts_root / f"{stage}.md"
    if stage_contract_path.exists():
        stage_requirements = extract_stage_required_heading_map(
            stage_contract_path.read_text(encoding="utf-8")
        )
        sections.extend(stage_requirements.get(document_name, ()))

    return tuple(dict.fromkeys(section for section in sections if section))


def normalized_heading(title: str) -> str:
    return normalize_heading(title)


def workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def section_content_for_heading(
    *,
    heading_index: int,
    headings: tuple[MarkdownHeading, ...],
    markdown_lines: list[str],
) -> str:
    heading = headings[heading_index]
    start_index = heading.line_number
    end_index = len(markdown_lines)

    for next_heading in headings[heading_index + 1 :]:
        if next_heading.level <= heading.level:
            end_index = next_heading.line_number - 1
            break

    return "\n".join(markdown_lines[start_index:end_index]).strip()


def validate_placeholder_sections(
    context: SemanticDocumentContext,
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    for section in context.iter_required_sections():
        if contains_placeholder_content(section.content):
            findings.append(
                context.finding(
                    code=PLACEHOLDER_CONTENT_CODE,
                    message=(
                        "Placeholder content remains in required section "
                        f"`{section.name}`."
                    ),
                    severity="high",
                    location=section.location,
                )
            )
    return tuple(findings)


def extract_review_finding_blocks(section_content: str) -> tuple[str, ...]:
    subsection_blocks = extract_subheading_blocks(section_content, level=3)
    if subsection_blocks:
        return subsection_blocks
    return extract_top_level_bullet_blocks(section_content)


def extract_review_spec_issue_blocks(section_content: str) -> tuple[str, ...]:
    subsection_blocks = extract_subheading_blocks(section_content, level=3)
    if subsection_blocks:
        return subsection_blocks
    return extract_top_level_bullet_blocks(section_content)


def extract_review_spec_readiness_state(text: str) -> str | None:
    match = REVIEW_SPEC_READINESS_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def extract_review_spec_decision(text: str) -> str | None:
    match = REVIEW_SPEC_DECISION_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def extract_review_disposition(finding_block: str) -> str | None:
    label_match = REVIEW_DISPOSITION_LABEL_PATTERN.search(finding_block)
    if label_match is not None:
        return label_match.group(1).lower()

    for line in finding_block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if REVIEW_FINDING_ID_PATTERN.search(stripped) is None:
            continue
        inline_match = REVIEW_DISPOSITION_PATTERN.search(stripped)
        if inline_match is not None:
            return inline_match.group(1).lower()
        return None
    return None


def review_spec_issue_has_explicit_severity(issue_block: str) -> bool:
    if has_explicit_severity(issue_block):
        return True
    inline_severity_match = REVIEW_SPEC_INLINE_SEVERITY_LABEL_PATTERN.search(issue_block)
    if (
        inline_severity_match is not None
        and inline_severity_match.group(1).lower() != "none"
    ):
        return True
    if REVIEW_SPEC_NO_ISSUE_SEVERITY_PATTERN.search(issue_block) is None:
        return False
    return REVIEW_SPEC_NO_ISSUES_PATTERN.search(issue_block) is not None


def has_explicit_severity(finding_or_issue_block: str) -> bool:
    if EXPLICIT_SEVERITY_LABEL_PATTERN.search(finding_or_issue_block) is not None:
        return True

    first_line = next(
        (line.strip() for line in finding_or_issue_block.splitlines() if line.strip()),
        "",
    )
    return INLINE_FINDING_SEVERITY_PATTERN.search(first_line) is not None


def extract_qa_verdict(text: str, *, prefer_labeled: bool = False) -> str | None:
    if prefer_labeled:
        labeled_match = QA_VERDICT_LABEL_PATTERN.search(text)
        if labeled_match is not None:
            return labeled_match.group(1).lower()
    match = QA_VERDICT_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def extract_qa_release_recommendation(text: str) -> str | None:
    match = QA_RELEASE_RECOMMENDATION_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()
