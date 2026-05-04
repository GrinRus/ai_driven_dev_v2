from __future__ import annotations

from pathlib import Path

from aidd.core.markdown import (
    MarkdownHeading,
    MarkdownSectionIndex,
    extract_markdown_headings,
    extract_required_sections_from_document_contract,
    extract_stage_required_heading_map,
)
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
        sections.extend(extract_required_sections_from_document_contract(document_contract_text))

    stage_contract_path = contracts_root / f"{stage}.md"
    if stage_contract_path.exists():
        stage_contract_text = stage_contract_path.read_text(encoding="utf-8")
        stage_requirements = extract_stage_required_heading_map(stage_contract_text)
        sections.extend(stage_requirements.get(document_name, ()))

    return tuple(dict.fromkeys(section for section in sections if section))


def extract_document_headings(*, path: Path, workspace_root: Path) -> tuple[MarkdownHeading, ...]:
    loaded_document = load_markdown_document(path=path, workspace_root=workspace_root)
    return extract_markdown_headings(loaded_document.body)


def _section_has_meaningful_content(
    *,
    heading_index: int,
    headings: tuple[MarkdownHeading, ...],
    markdown_lines: list[str],
) -> bool:
    section_index = MarkdownSectionIndex(
        headings=headings,
        markdown_lines=tuple(markdown_lines),
        headings_by_title={},
    )
    return section_index.section_has_meaningful_content(heading_index)


def _effective_required_section_matches(
    *,
    section: str,
    matches: tuple[tuple[int, MarkdownHeading], ...],
) -> tuple[tuple[int, MarkdownHeading], ...]:
    if len(matches) <= 1:
        return matches
    first_heading = matches[0][1]
    if first_heading.level == 1 and first_heading.title.strip().casefold() == section.casefold():
        return matches[1:]
    return matches


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
        section_index = MarkdownSectionIndex.from_markdown(loaded_document.body)
        headings = section_index.headings
        markdown_lines = list(section_index.markdown_lines)

        for section in required_sections:
            matches = section_index.matches(section)
            matches = _effective_required_section_matches(section=section, matches=matches)
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
