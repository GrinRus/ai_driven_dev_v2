from __future__ import annotations

from pathlib import Path
from shutil import copy2

from aidd.core.stage_models import (
    AdapterInvocationBundle,
    StageExecutionState,
    StageOutputDiscovery,
    StageOutputPublication,
    StageStructuralValidationResult,
)
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    resolve_expected_output_documents,
)
from aidd.core.workspace import stage_output_root as workspace_stage_output_root
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.validators.cross_document import validate_cross_document_consistency
from aidd.validators.models import ValidationFinding
from aidd.validators.reports import write_validator_report
from aidd.validators.semantic import validate_semantic_outputs
from aidd.validators.structural import (
    validate_required_document_existence,
    validate_required_sections,
)


def _stage_root_for_expected_output(expected_output_path: Path) -> Path:
    if expected_output_path.parent.name == "output":
        return expected_output_path.parent.parent
    return expected_output_path.parent


def _should_promote_misplaced_stage_output(
    *,
    source_path: Path,
    destination_path: Path,
) -> bool:
    if not source_path.exists():
        return False
    if not destination_path.exists():
        return True
    try:
        destination_text = destination_path.read_text(encoding="utf-8").strip()
    except OSError:
        destination_text = ""
    if destination_text in {
        "# Questions\n\nNo questions yet.",
        "# Answers\n\nNo answers yet.",
        "# Validator report\n\nNo validator output yet.",
        "# Stage result\n\nStage not run yet.",
    }:
        return True
    try:
        return source_path.stat().st_mtime_ns > destination_path.stat().st_mtime_ns
    except OSError:
        return False


def _promote_misplaced_stage_output_documents(
    *,
    expected_markdown_documents: tuple[Path, ...],
) -> None:
    for destination_path in expected_markdown_documents:
        stage_root = _stage_root_for_expected_output(destination_path)
        misplaced_output_path = stage_root / "output" / destination_path.name
        if misplaced_output_path.resolve(strict=False) == destination_path.resolve(strict=False):
            continue
        if not _should_promote_misplaced_stage_output(
            source_path=misplaced_output_path,
            destination_path=destination_path,
        ):
            continue
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(misplaced_output_path, destination_path)


def discover_stage_markdown_outputs(
    *,
    execution_state: StageExecutionState,
    invocation_bundle: AdapterInvocationBundle,
) -> StageOutputDiscovery:
    if execution_state.stage != invocation_bundle.stage:
        raise ValueError(
            "Execution state stage does not match adapter invocation stage: "
            f"{execution_state.stage} != {invocation_bundle.stage}"
        )
    if execution_state.work_item != invocation_bundle.work_item:
        raise ValueError(
            "Execution state work item does not match adapter invocation work item: "
            f"{execution_state.work_item} != {invocation_bundle.work_item}"
        )
    if execution_state.run_id != invocation_bundle.run_id:
        raise ValueError(
            "Execution state run id does not match adapter invocation run id: "
            f"{execution_state.run_id} != {invocation_bundle.run_id}"
        )
    if execution_state.attempt_number != invocation_bundle.attempt_number:
        raise ValueError(
            "Execution state attempt number does not match adapter invocation attempt number: "
            f"{execution_state.attempt_number} != {invocation_bundle.attempt_number}"
        )

    expected_markdown_documents = tuple(
        path
        for path in invocation_bundle.expected_output_documents
        if path.suffix.lower() == ".md"
    )
    _promote_misplaced_stage_output_documents(
        expected_markdown_documents=expected_markdown_documents
    )
    discovered_markdown_documents = tuple(
        path for path in expected_markdown_documents if path.exists()
    )
    missing_markdown_documents = tuple(
        path for path in expected_markdown_documents if not path.exists()
    )
    return StageOutputDiscovery(
        stage=execution_state.stage,
        work_item=execution_state.work_item,
        run_id=execution_state.run_id,
        attempt_number=execution_state.attempt_number,
        expected_markdown_documents=expected_markdown_documents,
        discovered_markdown_documents=discovered_markdown_documents,
        missing_markdown_documents=missing_markdown_documents,
    )


def run_structural_validation_after_output_discovery(
    *,
    workspace_root: Path,
    discovery: StageOutputDiscovery,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> StageStructuralValidationResult:
    structural_findings = validate_required_document_existence(
        stage=discovery.stage,
        work_item=discovery.work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    section_findings = validate_required_sections(
        stage=discovery.stage,
        work_item=discovery.work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    findings: tuple[ValidationFinding, ...]
    findings = (*structural_findings, *section_findings)
    if not findings:
        semantic_findings = validate_semantic_outputs(
            stage=discovery.stage,
            work_item=discovery.work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
        cross_document_findings = validate_cross_document_consistency(
            stage=discovery.stage,
            work_item=discovery.work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
        findings = (*semantic_findings, *cross_document_findings)

    stage_root = workspace_stage_root(
        root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    stage_root.mkdir(parents=True, exist_ok=True)
    validator_report_path = stage_root / "validator-report.md"
    write_validator_report(path=validator_report_path, findings=findings)
    return StageStructuralValidationResult(
        stage=discovery.stage,
        work_item=discovery.work_item,
        run_id=discovery.run_id,
        attempt_number=discovery.attempt_number,
        validator_report_path=validator_report_path,
        findings=findings,
    )


def _deduplicate_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    deduplicated: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        normalized = path.resolve(strict=False)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(path)
    return tuple(deduplicated)


def publish_stage_outputs_after_validation_pass(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> StageOutputPublication:
    stage_documents_root = workspace_stage_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    published_output_root = workspace_stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    published_output_root.mkdir(parents=True, exist_ok=True)

    declared_primary_outputs = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    source_documents = _deduplicate_paths(
        (
            *declared_primary_outputs,
            stage_documents_root / "stage-result.md",
            stage_documents_root / "validator-report.md",
        )
    )

    published_documents: list[Path] = []
    for source_document in source_documents:
        if source_document.suffix.lower() != ".md":
            continue
        if not source_document.exists():
            raise FileNotFoundError(
                "Stage output publishing requires an existing source document: "
                f"{workspace_relative_path(workspace_root, source_document)}"
            )
        destination_document = published_output_root / source_document.name
        copy2(source_document, destination_document)
        published_documents.append(destination_document)

    return StageOutputPublication(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        published_output_root=published_output_root,
        published_documents=tuple(published_documents),
    )


__all__ = [
    "discover_stage_markdown_outputs",
    "publish_stage_outputs_after_validation_pass",
    "run_structural_validation_after_output_discovery",
]
