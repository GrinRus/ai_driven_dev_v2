from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidd.core.markdown import extract_bullets, extract_paragraph
from aidd.core.ownership_registry import (
    DEFAULT_OWNERSHIP_MATRIX_PATH,
    DocumentOwnershipRegistry,
    OwnershipClass,
    OwnershipMatrixRow,
    OwnershipRegistryError,
    load_ownership_registry,
)
from aidd.core.resources import (
    default_stage_contracts_root,
    resolve_prompt_pack_path,
    resolve_resource_layout_from_contracts_root,
)
from aidd.core.stage_manifest import StageManifest
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.core.workspace import work_item_root as workspace_work_item_root

DEFAULT_STAGE_CONTRACTS_ROOT = default_stage_contracts_root()


class StageManifestLoadError(ValueError):
    """Raised when a stage manifest cannot be loaded from contracts."""


@dataclass(frozen=True, slots=True)
class StageOutputRegistry:
    """Owner-separated stage document paths.

    ``published`` is the complete declared-output view used for validation and publication.
    The other collections separate document ownership so callers can request only the set
    they are allowed to create or mutate.
    """

    runtime_authored: tuple[Path, ...]
    aidd_generated: tuple[Path, ...]
    interview_control: tuple[Path, ...]
    published: tuple[Path, ...]


def stage_contract_path(stage: str, contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT) -> Path:
    if not is_valid_stage(stage):
        raise StageManifestLoadError(f"Unknown stage: {stage}")
    return contracts_root / f"{stage}.md"


def _extract_declared_stage_id(markdown_text: str) -> str | None:
    match = re.search(r"^# Stage Contract:\s*`([^`]+)`\s*$", markdown_text, re.MULTILINE)
    if match is None:
        return None
    return match.group(1).strip()


def _validate_stage_contract_references(
    *,
    required_inputs: tuple[str, ...],
    optional_inputs: tuple[str, ...],
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
    contracts_root: Path,
) -> None:
    problems: list[str] = []
    layout = resolve_resource_layout_from_contracts_root(contracts_root)
    document_contracts_root = layout.document_contracts_root

    for declaration in (*required_inputs, *optional_inputs, *required_outputs):
        candidate = Path(declaration)
        if len(candidate.parts) != 1 or candidate.suffix.lower() != ".md":
            continue
        referenced_contract = document_contracts_root / candidate.name
        if not referenced_contract.exists():
            problems.append(f"missing document contract reference: {candidate.name}")

    if not prompt_pack_paths:
        problems.append("missing prompt-pack section entries")
    for prompt_reference in prompt_pack_paths:
        prompt_path = resolve_prompt_pack_path(
            prompt_reference=prompt_reference,
            contracts_root=contracts_root,
        )
        if not prompt_path.exists():
            problems.append(f"missing prompt-pack path: {prompt_reference}")

    if problems:
        joined = "; ".join(problems)
        raise StageManifestLoadError(f"Invalid contract references for stage manifest: {joined}")


def load_stage_manifest(
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> StageManifest:
    contract_path = stage_contract_path(stage=stage, contracts_root=contracts_root)
    if not contract_path.exists():
        raise StageManifestLoadError(f"Stage contract file not found: {contract_path}")

    markdown_text = contract_path.read_text(encoding="utf-8")
    declared_stage = _extract_declared_stage_id(markdown_text)
    if declared_stage is None:
        raise StageManifestLoadError(
            f"Missing stage contract heading in file: {contract_path}"
        )
    if declared_stage != stage:
        raise StageManifestLoadError(
            f"Stage contract heading mismatch in {contract_path}: "
            f"expected '{stage}', declared '{declared_stage}'."
        )

    required_inputs = extract_bullets(markdown_text=markdown_text, heading="Required inputs")
    optional_inputs = extract_bullets(
        markdown_text=markdown_text,
        heading="Optional context inputs",
    )
    required_outputs = extract_bullets(markdown_text=markdown_text, heading="Primary output")
    prompt_pack_paths = extract_bullets(markdown_text=markdown_text, heading="Prompt pack")
    purpose = extract_paragraph(markdown_text=markdown_text, heading="Purpose")

    _validate_stage_contract_references(
        required_inputs=required_inputs,
        optional_inputs=optional_inputs,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_pack_paths,
        contracts_root=contracts_root,
    )

    try:
        return StageManifest.from_document_paths(
            stage=stage,
            required_inputs=required_inputs,
            optional_inputs=optional_inputs,
            required_outputs=required_outputs,
            purpose=purpose,
        )
    except ValueError as exc:
        raise StageManifestLoadError(
            f"Invalid stage contract model for stage '{stage}' at {contract_path}."
        ) from exc


def load_all_stage_manifests(
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> dict[str, StageManifest]:
    declared_ids: dict[str, list[str]] = {}
    for contract_path in contracts_root.glob("*.md"):
        if contract_path.name == "AGENTS.md":
            continue

        declared = _extract_declared_stage_id(contract_path.read_text(encoding="utf-8"))
        if not declared:
            continue
        declared_ids.setdefault(declared, []).append(contract_path.name)

    duplicates = {stage_id: files for stage_id, files in declared_ids.items() if len(files) > 1}
    if duplicates:
        duplicate_text = ", ".join(
            f"{stage_id} -> {', '.join(sorted(files))}"
            for stage_id, files in sorted(duplicates.items())
        )
        raise StageManifestLoadError(f"Duplicate stage ids detected: {duplicate_text}")

    return {
        stage: load_stage_manifest(stage=stage, contracts_root=contracts_root)
        for stage in STAGES
    }


def resolve_prompt_pack_paths(
    *,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[str, ...]:
    # Reuse manifest validation so prompt-pack paths remain contract-backed.
    load_stage_manifest(stage=stage, contracts_root=contracts_root)
    contract_path = stage_contract_path(stage=stage, contracts_root=contracts_root)
    return extract_bullets(
        markdown_text=contract_path.read_text(encoding="utf-8"),
        heading="Prompt pack",
    )


def resolve_prompt_pack_file_paths(
    *,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[Path, ...]:
    return tuple(
        resolve_prompt_pack_path(
            prompt_reference=prompt_reference,
            contracts_root=contracts_root,
        )
        for prompt_reference in resolve_prompt_pack_paths(
            stage=stage,
            contracts_root=contracts_root,
        )
    )


def _resolve_declared_document_path(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    declaration: str,
) -> Path:
    relative = Path(declaration)
    if relative.is_absolute():
        raise StageManifestLoadError(f"Document declaration must be relative: {declaration}")

    if relative.parts and relative.parts[0] == "context":
        base = workspace_work_item_root(root=workspace_root, work_item=work_item)
    else:
        base = workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage)

    resolved_workspace = workspace_root.resolve(strict=False)
    candidate = (base / relative).resolve(strict=False)
    if not candidate.is_relative_to(resolved_workspace):
        raise StageManifestLoadError(
            "Document declaration escapes workspace root: "
            f"{declaration} (stage={stage}, work_item={work_item})"
        )
    return candidate


def resolve_required_input_documents(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[Path, ...]:
    manifest = load_stage_manifest(stage=stage, contracts_root=contracts_root)
    return tuple(
        _resolve_declared_document_path(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            declaration=declaration.path,
        )
        for declaration in manifest.required_inputs
    )


def resolve_optional_input_documents(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[Path, ...]:
    manifest = load_stage_manifest(stage=stage, contracts_root=contracts_root)
    return tuple(
        _resolve_declared_document_path(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            declaration=declaration.path,
        )
        for declaration in manifest.optional_inputs
    )


def _resolve_declared_output_documents(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[Path, ...]:
    manifest = load_stage_manifest(stage=stage, contracts_root=contracts_root)
    return tuple(
        _resolve_declared_document_path(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            declaration=declaration.path,
        )
        for declaration in manifest.required_outputs
    )


def _ownership_path_pattern(
    *,
    path: Path,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> str:
    """Normalize one resolved stage path to the matrix's placeholder pattern."""

    try:
        relative = path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False))
    except ValueError as exc:
        raise StageManifestLoadError(
            f"Declared document is outside workspace root: {path}"
        ) from exc

    expected_prefix = ("workitems", work_item, "stages", stage)
    if relative.parts[:4] != expected_prefix or len(relative.parts) == 4:
        raise StageManifestLoadError(
            "Declared stage output must be a stage-local document: "
            f"{relative.as_posix()} (stage={stage}, work_item={work_item})"
        )

    suffix = "/".join(relative.parts[4:])
    suffix = re.sub(r"(^|/)request-[^/]+(?=\.md$)", r"\1request-<n>", suffix)
    return f"workitems/<id>/stages/<stage>/{suffix}"


def _ownership_row_for_path(
    *,
    path: Path,
    workspace_root: Path,
    work_item: str,
    stage: str,
    ownership_registry: DocumentOwnershipRegistry,
) -> OwnershipMatrixRow:
    pattern = _ownership_path_pattern(
        path=path,
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    try:
        row = ownership_registry.row_for(pattern)
    except OwnershipRegistryError as exc:
        raise StageManifestLoadError(
            f"Declared output is absent from the ownership matrix: {pattern}"
        ) from exc
    if not row.applies_to(stage):
        raise StageManifestLoadError(
            f"Ownership matrix row does not apply to stage '{stage}': {pattern}"
        )
    return row


def _resolve_registry_control_documents(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    ownership_registry: DocumentOwnershipRegistry,
) -> tuple[Path, ...]:
    """Resolve static stage-local AIDD control rows, excluding dynamic request records."""

    stage_root = workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage)
    paths: list[Path] = []
    prefix = "workitems/<id>/stages/<stage>/"
    for row in ownership_registry.for_stage(stage):
        if row.ownership_class is not OwnershipClass.AIDD_CONTROL_DOCUMENT:
            continue
        if not row.path_pattern.startswith(prefix):
            continue
        suffix = row.path_pattern.removeprefix(prefix)
        if "<" in suffix or "/" in suffix:
            continue
        paths.append(stage_root / suffix)
    return tuple(paths)


def resolve_stage_output_registry(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    ownership_registry: DocumentOwnershipRegistry | None = None,
) -> StageOutputRegistry:
    """Resolve the four owner-separated output sets for one stage.

    Runtime-authored outputs are substantive stage documents only. Canonical terminal records
    and interview/control documents are deliberately excluded from that set. ``published`` is
    the complete declared-output projection retained for existing validators and publication
    callers.
    """

    declared = _resolve_declared_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    matrix = ownership_registry or load_ownership_registry(DEFAULT_OWNERSHIP_MATRIX_PATH)
    rows = tuple(
        _ownership_row_for_path(
            path=path,
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            ownership_registry=matrix,
        )
        for path in declared
    )
    runtime_authored = tuple(
        path
        for path, row in zip(declared, rows, strict=True)
        if row.ownership_class is OwnershipClass.RUNTIME_CONTENT
    )
    aidd_generated = tuple(
        path
        for path, row in zip(declared, rows, strict=True)
        if row.ownership_class is OwnershipClass.AIDD_WORKFLOW_RECORD
    )
    interview_control = tuple(
        path
        for path, row in zip(declared, rows, strict=True)
        if row.ownership_class
        in {OwnershipClass.INTERVIEW_LEDGER, OwnershipClass.AIDD_CONTROL_DOCUMENT}
    )
    for path in _resolve_registry_control_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        ownership_registry=matrix,
    ):
        if path not in interview_control:
            interview_control += (path,)
    return StageOutputRegistry(
        runtime_authored=runtime_authored,
        aidd_generated=aidd_generated,
        interview_control=interview_control,
        published=declared,
    )


def resolve_runtime_output_documents(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    ownership_registry: DocumentOwnershipRegistry | None = None,
) -> tuple[Path, ...]:
    return resolve_stage_output_registry(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
        ownership_registry=ownership_registry,
    ).runtime_authored


def resolve_aidd_generated_output_documents(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    ownership_registry: DocumentOwnershipRegistry | None = None,
) -> tuple[Path, ...]:
    return resolve_stage_output_registry(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
        ownership_registry=ownership_registry,
    ).aidd_generated


def resolve_expected_output_documents(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    ownership_registry: DocumentOwnershipRegistry | None = None,
) -> tuple[Path, ...]:
    """Resolve the complete current declared-output view for validation and publication."""

    return resolve_stage_output_registry(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
        ownership_registry=ownership_registry,
    ).published
