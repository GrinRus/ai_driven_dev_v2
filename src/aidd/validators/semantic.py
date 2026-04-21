from __future__ import annotations

import re
from pathlib import Path

from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    load_stage_manifest,
    resolve_expected_output_documents,
)
from aidd.validators.document_loader import load_markdown_document
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.structural import MarkdownHeading, extract_markdown_headings

INCOMPLETE_SECTION_CODE = "SEM-INCOMPLETE-SECTION"
UNSUPPORTED_CLAIM_CODE = "SEM-UNSUPPORTED-CLAIM"
PLACEHOLDER_CONTENT_CODE = "SEM-PLACEHOLDER-CONTENT"

_INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
_STAGE_HEADING_REQUIREMENT_PATTERN = re.compile(
    r"required heading coverage in\s+`([^`]+)`\s*\((.+)\)",
    flags=re.IGNORECASE,
)
_PLACEHOLDER_PATTERN = re.compile(r"\b(TBD|TODO|TBA|N/A)\b|\.{3}", flags=re.IGNORECASE)
_UNSUPPORTED_CLAIM_PATTERN = re.compile(
    r"\b(always|never|guarantee(?:d|s)?|proven|certain(?:ly)?)\b",
    flags=re.IGNORECASE,
)


def _extract_section_lines(markdown_text: str, heading: str) -> list[str]:
    target_heading = f"## {heading}".lower()
    in_section = False
    section_lines: list[str] = []

    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped.lower() == target_heading
            continue
        if in_section:
            section_lines.append(raw_line)

    return section_lines


def _extract_required_sections_from_document_contract(contract_text: str) -> tuple[str, ...]:
    sections: list[str] = []
    for line in _extract_section_lines(contract_text, heading="Required sections"):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        sections.extend(token.strip() for token in _INLINE_CODE_PATTERN.findall(stripped))
    return tuple(dict.fromkeys(section for section in sections if section))


def _extract_stage_required_heading_map(stage_contract_text: str) -> dict[str, tuple[str, ...]]:
    requirements: dict[str, tuple[str, ...]] = {}
    for line in _extract_section_lines(stage_contract_text, heading="Validation focus"):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue

        match = _STAGE_HEADING_REQUIREMENT_PATTERN.search(stripped)
        if match is None:
            continue

        document_name = match.group(1).strip()
        sections = tuple(
            token.strip() for token in _INLINE_CODE_PATTERN.findall(match.group(2)) if token.strip()
        )
        if sections:
            requirements[document_name] = sections

    return requirements


def _required_sections_for_document(
    *,
    stage: str,
    document_name: str,
    contracts_root: Path,
) -> tuple[str, ...]:
    sections: list[str] = []
    document_contract_path = contracts_root.parent / "documents" / document_name
    if document_contract_path.exists():
        sections.extend(
            _extract_required_sections_from_document_contract(
                document_contract_path.read_text(encoding="utf-8")
            )
        )

    stage_contract_path = contracts_root / f"{stage}.md"
    if stage_contract_path.exists():
        stage_requirements = _extract_stage_required_heading_map(
            stage_contract_path.read_text(encoding="utf-8")
        )
        sections.extend(stage_requirements.get(document_name, ()))

    return tuple(dict.fromkeys(section for section in sections if section))


def _normalized_heading(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _section_content_for_heading(
    *,
    heading_index: int,
    headings: tuple[MarkdownHeading, ...],
    markdown_lines: list[str],
) -> str:
    # headings come from structural.extract_markdown_headings (MarkdownHeading instances).
    heading = headings[heading_index]
    start_index = heading.line_number
    end_index = len(markdown_lines)

    for next_heading in headings[heading_index + 1 :]:
        if next_heading.level <= heading.level:
            end_index = next_heading.line_number - 1
            break

    return "\n".join(markdown_lines[start_index:end_index]).strip()


def has_non_placeholder_text(text: str) -> bool:
    return _PLACEHOLDER_PATTERN.search(text) is None


def validate_semantic_outputs(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
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

        required_sections = _required_sections_for_document(
            stage=stage,
            document_name=output_path.name,
            contracts_root=contracts_root,
        )
        if not required_sections:
            continue

        loaded_document = load_markdown_document(path=output_path, workspace_root=workspace_root)
        headings = extract_markdown_headings(loaded_document.body)
        markdown_lines = loaded_document.body.splitlines()
        headings_by_title: dict[str, list[tuple[int, MarkdownHeading]]] = {}
        for index, heading in enumerate(headings):
            normalized_title = _normalized_heading(heading.title)
            headings_by_title.setdefault(normalized_title, []).append((index, heading))

        for section in required_sections:
            matches = headings_by_title.get(_normalized_heading(section), [])
            if not matches:
                continue

            heading_index, heading = matches[0]
            section_content = _section_content_for_heading(
                heading_index=heading_index,
                headings=headings,
                markdown_lines=markdown_lines,
            )
            location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=heading.line_number,
            )

            if _PLACEHOLDER_PATTERN.search(section_content):
                findings.append(
                    ValidationFinding(
                        code=PLACEHOLDER_CONTENT_CODE,
                        message=(
                            "Placeholder content remains in required section "
                            f"`{section}`."
                        ),
                        severity="high",
                        location=location,
                    )
                )

            if stage == "idea" and output_path.name == "idea-brief.md":
                normalized_section = _normalized_heading(section)
                compact_content = re.sub(r"\s+", " ", section_content).strip()

                if normalized_section in {"problem statement", "desired outcome"}:
                    if compact_content.lower() in {"none", "- none"} or len(compact_content) < 20:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    f"Required section `{section}` is too brief to establish "
                                    "a reviewable semantic baseline."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

                if normalized_section in {"problem statement", "desired outcome"}:
                    if _UNSUPPORTED_CLAIM_PATTERN.search(compact_content):
                        findings.append(
                            ValidationFinding(
                                code=UNSUPPORTED_CLAIM_CODE,
                                message=(
                                    f"Section `{section}` includes unsupported absolute claims "
                                    "without evidence grounding."
                                ),
                                severity="high",
                                location=location,
                            )
                        )

    return tuple(findings)
