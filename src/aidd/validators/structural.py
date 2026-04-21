from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    resolve_expected_output_documents,
    resolve_required_input_documents,
)
from aidd.validators.document_loader import load_markdown_document
from aidd.validators.models import ValidationFinding

MISSING_REQUIRED_DOCUMENT_CODE = "STRUCT-MISSING-REQUIRED-DOCUMENT"
_HEADING_PATTERN = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
_FENCE_PREFIXES = ("```", "~~~")


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
            )
        )

    return tuple(findings)
