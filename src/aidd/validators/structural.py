from __future__ import annotations

from pathlib import Path

from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    resolve_expected_output_documents,
    resolve_required_input_documents,
)
from aidd.validators.models import ValidationFinding

MISSING_REQUIRED_DOCUMENT_CODE = "STRUCT-MISSING-REQUIRED-DOCUMENT"


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
