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

INLINE_CODE_PATTERN = re.compile(r"(?<!`)`(?!`)(.*?)(?<!`)`(?!`)", flags=re.DOTALL)
STAGE_HEADING_REQUIREMENT_PATTERN = re.compile(
    r"required heading coverage in\s+`([^`]+)`\s*\((.+)\)",
    flags=re.IGNORECASE,
)
PLACEHOLDER_PATTERN = re.compile(r"\b(TBD|TODO|TBA|N/A)\b|\.{3}", flags=re.IGNORECASE)
PLACEHOLDER_EXAMPLE_CONTEXT_PATTERN = re.compile(
    r"\b(placeholder|literal|token|sentinel|example|marker|entr(?:y|ies)|value)s?\b",
    flags=re.IGNORECASE,
)
PLACEHOLDER_NEGATED_EXAMPLE_PATTERN = re.compile(
    r"\b(no|not|none|without|free of)\b",
    flags=re.IGNORECASE,
)
UNSUPPORTED_CLAIM_PATTERN = re.compile(
    r"\b(always|never|guarantee(?:d|s)?|proven|certain(?:ly)?)\b",
    flags=re.IGNORECASE,
)
CITATION_ID_PATTERN = re.compile(r"\[(S\d+)\]")
MILESTONE_ID_PATTERN = re.compile(r"\b(M\d+)\b", flags=re.IGNORECASE)
RISK_MITIGATION_PATTERN = re.compile(
    r"\b(mitigation|mitigate|fallback|retry|reduce|avoid|monitor)\b",
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
QA_RISK_SEVERITY_PATTERN = re.compile(
    r"\bseverity\s*:?\s*(?:`|\*\*)?(critical|high|medium|low)(?:`|\*\*)?\b|"
    r"\(`?(critical|high|medium|low)`?\)|"
    r"\b(critical|high|medium|low)\s+severity\b",
    flags=re.IGNORECASE,
)
REVIEW_SPEC_NO_ISSUE_SEVERITY_PATTERN = re.compile(
    r"\bseverity\s*:\s*`?none`?\b",
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
TASKLIST_TASK_ID_PATTERN = re.compile(
    r"\b([A-Z][A-Z0-9]{0,15}-\d+|T\d+)\b",
)
IMPLEMENT_FILE_ENTRY_PATTERN = re.compile(r"`(?=[^`\n]*(?:/|\.))[^\n`]+`")
IMPLEMENT_COMMAND_PATTERN = re.compile(
    r"(\$ [^\n]+|\.venv/bin/[^\s`]+|\b("
    r"uv run|pytest|ruff|mypy|python -m|npm|pnpm|yarn|go test|cargo test|"
    r"make|git|grep|echo|printf|flake8|black|ty check|sqlite-utils"
    r")\b|`(?:insert|upsert|memory)\b[^`\n]*`)",
    flags=re.IGNORECASE,
)
IMPLEMENT_RESULT_PATTERN = re.compile(
    r"("
    r"->\s*(pass|fail|ok|error|empty|no output|`?\d+`?|exit\s*`?\d+`?)|"
    r"->\s*[^.\n]*(?:\bonly\b|\bshows?\b|\bempty\b|\bno output\b)|"
    r"\b(pass(?:ed)?|fail(?:ed)?|succeeded|error|exit code|exited with status|returned)\b|"
    r"\bexit\s*`?\d+`?|"
    r"`?\bexit[_\s-]?code\b`?\s*(?:==|=|:)?\s*`?\d+`?|"
    r"\b\d+\s+passed\b|"
    r"\bSuccess:|"
    r"\bFound\s+\d+\s+diagnostics\b|"
    r"\bshows?\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|no)\b|"
    r"\bexactly\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+matches\b|"
    r"\b\d+\s+(?:production\s+)?matches\b|"
    r"\b\d+\s+files?\s+changed\b|"
    r"\bzero\s+differences\b|"
    r"\bobserved\s*:|"
    r"\b(?:does|do)\s+not\s+exist\b|"
    r"\bexists\(\)\s+is\s+(?:true|false)\b|"
    r"\btable_names\(\)\s*(?:==|is)\s*\[\]|"
    r"\bno\s+(?:stderr|exception|output|traceback)\b|"
    r"\bprinted\s+`?OK`?\b|"
    r"\bmatches\s+expected\b"
    r")",
    flags=re.IGNORECASE,
)
IMPLEMENT_ARTIFACT_REFERENCE_PATTERN = re.compile(
    r"`[^`]+(?:\.md|\.json|\.log|\.txt)`",
    flags=re.IGNORECASE,
)
IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN = re.compile(
    r"\b(same\s+)?stash/pop\s+procedure\b|"
    r"\bsame\b.{0,80}\b(?:procedure|command|check|run)\b.{0,80}\bas\s+`?(?:T\d+|TL-\d+)`?",
    flags=re.IGNORECASE | re.DOTALL,
)
IMPLEMENT_DEFERRED_VERIFICATION_PATTERN = re.compile(
    r"\b(?:not\s+(?:run|executed)|skipped|deferred|hand[- ]off)\b",
    flags=re.IGNORECASE,
)
IMPLEMENT_COMPLETION_CLAIM_PATTERN = re.compile(
    r"\b(completed|fully|done|implemented|finished)\b",
    flags=re.IGNORECASE,
)
IMPLEMENT_NOOP_JUSTIFICATION_PATTERN = re.compile(
    r"\b(no-op|already (satisfied|implemented)|blocked|external constraint|out of scope)\b",
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
QA_RELEASE_RECOMMENDATION_PATTERN = re.compile(
    r"\b(proceed-with-conditions|hold|proceed)\b",
    flags=re.IGNORECASE,
)
QA_EVIDENCE_ID_PATTERN = re.compile(r"\bEV-\d+\b", flags=re.IGNORECASE)
QA_OWNER_PATTERN = re.compile(r"\bowner\b", flags=re.IGNORECASE)


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


def validation_finding(
    *,
    code: str,
    message: str,
    severity: SeverityLevel = "high",
    location: ValidationIssueLocation | None = None,
) -> ValidationFinding:
    return ValidationFinding(
        code=code,
        message=message,
        severity=severity,
        location=location,
    )


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


def has_non_placeholder_text(text: str) -> bool:
    return not contains_placeholder_content(text)


def contains_placeholder_content(text: str) -> bool:
    placeholder_matches = tuple(PLACEHOLDER_PATTERN.finditer(text))
    if not placeholder_matches:
        return False

    inline_code_matches = tuple(INLINE_CODE_PATTERN.finditer(text))
    placeholder_requires_context = False
    for placeholder_match in placeholder_matches:
        inline_code_match = inline_code_match_for_placeholder(
            placeholder_match=placeholder_match,
            inline_code_matches=inline_code_matches,
        )
        if inline_code_match is None:
            if placeholder_outside_inline_code_is_content(text, placeholder_match):
                return True
            continue

        if inline_placeholder_requires_context(placeholder_match, inline_code_match):
            placeholder_requires_context = True

    if not placeholder_requires_context:
        return False

    return inline_placeholder_context_is_content(text)


def inline_code_match_for_placeholder(
    *,
    placeholder_match: re.Match[str],
    inline_code_matches: tuple[re.Match[str], ...],
) -> re.Match[str] | None:
    return next(
        (
            code_match
            for code_match in inline_code_matches
            if code_match.start() <= placeholder_match.start()
            and placeholder_match.end() <= code_match.end()
        ),
        None,
    )


def placeholder_outside_inline_code_is_content(
    text: str,
    placeholder_match: re.Match[str],
) -> bool:
    if (
        placeholder_match.group(0) == "..."
        and not is_standalone_ellipsis_placeholder(text, placeholder_match)
    ):
        return False
    if is_negated_placeholder_example_line(text, placeholder_match):
        return False
    return True


def inline_placeholder_requires_context(
    placeholder_match: re.Match[str],
    inline_code_match: re.Match[str],
) -> bool:
    inline_code_text = inline_code_match.group(1).strip()
    return placeholder_match.group(0) != "..." or inline_code_text == "..."


def inline_placeholder_context_is_content(text: str) -> bool:
    text_without_inline_code = INLINE_CODE_PATTERN.sub("", text)
    if not text_without_inline_code.strip():
        return True

    return PLACEHOLDER_EXAMPLE_CONTEXT_PATTERN.search(text_without_inline_code) is None


def is_negated_placeholder_example_line(
    text: str,
    placeholder_match: re.Match[str],
) -> bool:
    line_start = text.rfind("\n", 0, placeholder_match.start()) + 1
    line_end = text.find("\n", placeholder_match.end())
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]

    for candidate in (line, placeholder_sentence_context(text, placeholder_match)):
        if PLACEHOLDER_EXAMPLE_CONTEXT_PATTERN.search(candidate) is None:
            continue
        if PLACEHOLDER_NEGATED_EXAMPLE_PATTERN.search(candidate) is None:
            continue

        candidate_without_placeholders = PLACEHOLDER_PATTERN.sub("", candidate)
        if re.search(r"[A-Za-z]{4,}", candidate_without_placeholders):
            return True

    return False


def placeholder_sentence_context(text: str, placeholder_match: re.Match[str]) -> str:
    sentence_start = 0
    for marker in ("\n\n", ". ", ".\n", "! ", "!\n", "? ", "?\n"):
        marker_index = text.rfind(marker, 0, placeholder_match.start())
        if marker_index != -1:
            sentence_start = max(sentence_start, marker_index + len(marker))

    sentence_end = len(text)
    for marker in ("\n\n", ". ", ".\n", "! ", "!\n", "? ", "?\n"):
        marker_index = text.find(marker, placeholder_match.end())
        if marker_index != -1:
            sentence_end = min(sentence_end, marker_index + len(marker.rstrip()))

    return text[sentence_start:sentence_end]


def is_standalone_ellipsis_placeholder(
    text: str,
    placeholder_match: re.Match[str],
) -> bool:
    line_start = text.rfind("\n", 0, placeholder_match.start()) + 1
    line_end = text.find("\n", placeholder_match.end())
    if line_end == -1:
        line_end = len(text)

    line = text[line_start:line_end]
    match_start = placeholder_match.start() - line_start
    match_end = placeholder_match.end() - line_start
    before = line[:match_start].strip(" \t-*_`\"'")
    after = line[match_end:].strip(" \t-*_`\"'")

    if before and after:
        return False

    normalized_line = line.strip()
    if re.fullmatch(r"[-*]?\s*`?\.{3}`?", normalized_line):
        return True

    return bool(
        re.search(
            r"\b(placeholder|fill|details|content|unknown|later|todo|tbd)\b",
            line,
            flags=re.IGNORECASE,
        )
    )


def has_bullet_items(section_content: str) -> bool:
    return any(line.strip().startswith("- ") for line in section_content.splitlines())


def extract_bullet_items(section_content: str) -> tuple[str, ...]:
    return tuple(
        line.strip()[2:].strip()
        for line in section_content.splitlines()
        if line.strip().startswith("- ")
    )


def extract_markdown_list_items(section_content: str) -> tuple[str, ...]:
    items: list[str] = []
    for line in section_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
            continue
        ordered_match = re.match(r"\d+[.)]\s+(.+)", stripped)
        if ordered_match is not None:
            items.append(ordered_match.group(1).strip())
    return tuple(items)


def extract_top_level_bullet_blocks(section_content: str) -> tuple[str, ...]:
    blocks: list[list[str]] = []
    current_block: list[str] | None = None
    in_fenced_code = False

    for line in section_content.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fenced_code = not in_fenced_code
            if current_block is not None:
                current_block.append(stripped)
            continue

        if in_fenced_code:
            if current_block is not None:
                current_block.append(stripped)
            continue

        if line.startswith("- "):
            current_block = [line[2:].strip()]
            blocks.append(current_block)
            continue

        if current_block is not None:
            current_block.append(line.strip())

    return tuple(
        "\n".join(line for line in block if line).strip()
        for block in blocks
        if any(line.strip() for line in block)
    )


def extract_subheading_blocks(section_content: str, *, level: int) -> tuple[str, ...]:
    marker = f"{'#' * level} "
    blocks: list[list[str]] = []
    current_block: list[str] | None = None

    for line in section_content.splitlines():
        if line.startswith(marker):
            current_block = [line.strip()]
            blocks.append(current_block)
            continue

        if current_block is not None:
            current_block.append(line.strip())

    return tuple(
        "\n".join(line for line in block if line).strip()
        for block in blocks
        if any(line.strip() for line in block)
    )


def is_markdown_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) is not None for cell in cells
    )


def extract_markdown_table_rows(section_content: str) -> tuple[str, ...]:
    rows: list[str] = []
    headers: list[str] | None = None
    for line in section_content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            headers = None
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if is_markdown_table_separator(cells):
            continue
        if headers is None:
            headers = cells
            continue
        labeled_cells: list[str] = []
        for index, cell in enumerate(cells):
            if not cell:
                continue
            header = (
                headers[index]
                if index < len(headers) and headers[index]
                else f"Column {index + 1}"
            )
            labeled_cells.append(f"{header}: {cell}")
        if labeled_cells:
            rows.append(" | ".join(labeled_cells))
    return tuple(rows)


def extract_risk_blocks(section_content: str) -> tuple[str, ...]:
    subsection_blocks = extract_subheading_blocks(section_content, level=3)
    if subsection_blocks:
        return subsection_blocks
    bullet_blocks = extract_top_level_bullet_blocks(section_content)
    if bullet_blocks:
        return bullet_blocks
    return extract_markdown_table_rows(section_content)


def extract_implementation_verification_blocks(section_content: str) -> tuple[str, ...]:
    subsection_blocks = extract_subheading_blocks(section_content, level=3)
    if subsection_blocks:
        return subsection_blocks
    return extract_top_level_bullet_blocks(section_content)


def is_deferred_implementation_verification(verification_item: str) -> bool:
    return IMPLEMENT_DEFERRED_VERIFICATION_PATTERN.search(verification_item) is not None


def has_implementation_command_evidence(verification_item: str) -> bool:
    return (
        IMPLEMENT_COMMAND_PATTERN.search(verification_item) is not None
        or IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN.search(verification_item) is not None
    )


def is_empty_risk_entry(risk_block: str) -> bool:
    normalized = re.sub(r"[`*_]", "", risk_block).strip().lower()
    normalized = normalized.strip(" .:-")
    return normalized in {
        "none",
        "none recorded",
        "no known issues",
        "no residual risks",
        "no residual risk remains",
    }


def is_risk_metadata_entry(risk_block: str) -> bool:
    first_line = next(
        (line.strip() for line in risk_block.splitlines() if line.strip()),
        "",
    )
    return bool(
        re.match(
            r"^(severity|mitigation|owner|ownership|disposition|description|evidence)\s*:",
            first_line,
            flags=re.IGNORECASE,
        )
    )


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


def extract_citation_ids(text: str) -> set[str]:
    return {match.group(1) for match in CITATION_ID_PATTERN.finditer(text)}


def extract_milestone_ids(text: str) -> set[str]:
    return {match.group(1).upper() for match in MILESTONE_ID_PATTERN.finditer(text)}


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


def extract_qa_verdict(text: str) -> str | None:
    match = QA_VERDICT_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def extract_qa_release_recommendation(text: str) -> str | None:
    match = QA_RELEASE_RECOMMENDATION_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def extract_tasklist_task_ids(text: str) -> set[str]:
    task_ids = {match.group(1).upper() for match in TASKLIST_TASK_ID_PATTERN.finditer(text)}
    tl_ids = {task_id for task_id in task_ids if task_id.startswith("TL-")}
    if tl_ids:
        return tl_ids
    compact_t_ids = {task_id for task_id in task_ids if re.fullmatch(r"T\d+", task_id)}
    if compact_t_ids:
        return compact_t_ids
    return task_ids
