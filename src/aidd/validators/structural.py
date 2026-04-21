from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    load_stage_manifest,
    resolve_expected_output_documents,
    resolve_required_input_documents,
)
from aidd.validators.document_loader import load_markdown_document
from aidd.validators.models import ValidationFinding, ValidationIssueLocation

MISSING_REQUIRED_DOCUMENT_CODE = "STRUCT-MISSING-REQUIRED-DOCUMENT"
MISSING_REQUIRED_SECTION_CODE = "STRUCT-MISSING-REQUIRED-SECTION"
DUPLICATE_REQUIRED_SECTION_CODE = "STRUCT-DUPLICATE-REQUIRED-SECTION"
EMPTY_REQUIRED_SECTION_CODE = "STRUCT-EMPTY-REQUIRED-SECTION"
_HEADING_PATTERN = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
_FENCE_PREFIXES = ("```", "~~~")
_INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
_STAGE_HEADING_REQUIREMENT_PATTERN = re.compile(
    r"required heading coverage in\s+`([^`]+)`\s*\((.+)\)",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class MarkdownHeading:
    level: int
    title: str
    line_number: int


def _iter_required_documents(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path,
) -> tuple[Path, ...]:
    required_inputs = resolve_required_input_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    required_outputs = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    deduplicated: list[Path] = []
    seen: set[Path] = set()
    for path in (*required_inputs, *required_outputs):
        normalized = path.resolve(strict=False)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(normalized)
    return tuple(deduplicated)


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


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


def _normalized_heading(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def _required_sections_for_document(
    *,
    stage: str,
    document_name: str,
    contracts_root: Path,
) -> tuple[str, ...]:
    sections: list[str] = []
    document_contract_path = contracts_root.parent / "documents" / document_name
    if document_contract_path.exists():
        document_contract_text = document_contract_path.read_text(encoding="utf-8")
        sections.extend(_extract_required_sections_from_document_contract(document_contract_text))

    stage_contract_path = contracts_root / f"{stage}.md"
    if stage_contract_path.exists():
        stage_contract_text = stage_contract_path.read_text(encoding="utf-8")
        stage_requirements = _extract_stage_required_heading_map(stage_contract_text)
        sections.extend(stage_requirements.get(document_name, ()))

    return tuple(dict.fromkeys(section for section in sections if section))


def extract_markdown_headings(markdown_text: str) -> tuple[MarkdownHeading, ...]:
    headings: list[MarkdownHeading] = []
    in_fence = False
    active_fence_prefix: str | None = None

    for line_number, raw_line in enumerate(markdown_text.splitlines(), start=1):
        stripped = raw_line.lstrip()

        fence_prefix = next(
            (prefix for prefix in _FENCE_PREFIXES if stripped.startswith(prefix)),
            None,
        )
        if fence_prefix is not None:
            if not in_fence:
                in_fence = True
                active_fence_prefix = fence_prefix
            elif active_fence_prefix is not None and stripped.startswith(active_fence_prefix):
                in_fence = False
                active_fence_prefix = None
            continue

        if in_fence:
            continue

        leading_spaces = len(raw_line) - len(raw_line.lstrip(" "))
        if leading_spaces > 3:
            continue

        match = _HEADING_PATTERN.match(raw_line.lstrip(" "))
        if match is None:
            continue

        level = len(match.group(1))
        title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
        if not title:
            continue

        headings.append(MarkdownHeading(level=level, title=title, line_number=line_number))

    return tuple(headings)


def extract_document_headings(*, path: Path, workspace_root: Path) -> tuple[MarkdownHeading, ...]:
    loaded_document = load_markdown_document(path=path, workspace_root=workspace_root)
    return extract_markdown_headings(loaded_document.body)


def _section_has_meaningful_content(
    *,
    heading_index: int,
    headings: tuple[MarkdownHeading, ...],
    markdown_lines: list[str],
) -> bool:
    heading = headings[heading_index]
    start_index = heading.line_number
    end_index = len(markdown_lines)

    for next_heading in headings[heading_index + 1 :]:
        if next_heading.level <= heading.level:
            end_index = next_heading.line_number - 1
            break

    section_lines = markdown_lines[start_index:end_index]
    return any(line.strip() for line in section_lines)


def validate_required_document_existence(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    for path in _iter_required_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    ):
        if path.exists():
            continue
        findings.append(
            ValidationFinding(
                code=MISSING_REQUIRED_DOCUMENT_CODE,
                message=f"Missing required document: {_workspace_relative(path, workspace_root)}",
                severity="critical",
                location=ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(path, workspace_root)
                ),
            )
        )

    return tuple(findings)


def validate_required_sections(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[ValidationFinding, ...]:
    # Make dependency explicit for this validation slice.
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
            normalized_section = _normalized_heading(section)
            matches = headings_by_title.get(normalized_section, [])
            if not matches:
                findings.append(
                    ValidationFinding(
                        code=MISSING_REQUIRED_SECTION_CODE,
                        message=(
                            "Missing required section "
                            f"`{section}` in {_workspace_relative(output_path, workspace_root)}"
                        ),
                        severity="high",
                        location=ValidationIssueLocation(
                            workspace_relative_path=_workspace_relative(output_path, workspace_root)
                        ),
                    )
                )
                continue

            if len(matches) > 1:
                duplicate_heading = matches[1][1]
                findings.append(
                    ValidationFinding(
                        code=DUPLICATE_REQUIRED_SECTION_CODE,
                        message=(
                            "Duplicate required section "
                            f"`{section}` in {_workspace_relative(output_path, workspace_root)}"
                        ),
                        severity="high",
                        location=ValidationIssueLocation(
                            workspace_relative_path=_workspace_relative(
                                output_path,
                                workspace_root,
                            ),
                            line_number=duplicate_heading.line_number,
                        ),
                    )
                )

            primary_index, primary_heading = matches[0]
            if _section_has_meaningful_content(
                heading_index=primary_index,
                headings=headings,
                markdown_lines=markdown_lines,
            ):
                continue

            findings.append(
                ValidationFinding(
                    code=EMPTY_REQUIRED_SECTION_CODE,
                    message=(
                        "Required section "
                        f"`{section}` is empty in "
                        f"{_workspace_relative(output_path, workspace_root)}"
                    ),
                    severity="high",
                    location=ValidationIssueLocation(
                        workspace_relative_path=_workspace_relative(output_path, workspace_root),
                        line_number=primary_heading.line_number,
                    ),
                )
            )

    return tuple(findings)
