from __future__ import annotations

from pathlib import Path
from shutil import copy2, rmtree
from uuid import uuid4

from aidd.core.run_store import write_attempt_artifact_index
from aidd.core.stage_models import (
    AdapterInvocationBundle,
    StageExecutionState,
    StageOutputDiscovery,
    StageOutputPromotion,
    StageOutputPublication,
    StageStructuralValidationResult,
)
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    resolve_expected_output_documents,
    resolve_runtime_output_documents,
)
from aidd.core.workspace import STAGE_RESULT_BOOTSTRAP_TEMPLATE
from aidd.core.workspace import stage_output_root as workspace_stage_output_root
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.validators.cross_document import validate_cross_document_consistency
from aidd.validators.models import ValidationFinding
from aidd.validators.protocol import DOCUMENT_READ_FAILURE_CODES
from aidd.validators.reports import write_validator_report
from aidd.validators.semantic import validate_semantic_outputs
from aidd.validators.structural import (
    validate_required_document_existence,
    validate_required_sections,
)

_CONDITIONAL_INTERVIEW_DOCUMENT_NAMES = frozenset({"questions.md", "answers.md"})


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
        STAGE_RESULT_BOOTSTRAP_TEMPLATE.strip(),
    }:
        return True
    try:
        return source_path.stat().st_mtime_ns > destination_path.stat().st_mtime_ns
    except OSError:
        return False


_MISPLACED_OUTPUT_PROMOTION_WARNING_CODE = "STRUCT-OUTPUT-PROMOTED"
_UNEXPECTED_RUNTIME_DOCUMENTS: dict[str, tuple[str, str | None]] = {
    "stage-result.md": (
        "runtime-stage-result.md",
        STAGE_RESULT_BOOTSTRAP_TEMPLATE.strip(),
    ),
    "validator-report.md": (
        "runtime-validator-report.md",
        "# Validator report\n\nNo validator output yet.",
    ),
    "repair-brief.md": ("runtime-repair-brief.md", None),
}


def _workspace_root_for_document(path: Path) -> Path:
    parts = path.parts
    try:
        workitems_index = parts.index("workitems")
    except ValueError as exc:
        raise ValueError(f"Stage document is not inside a workitems workspace: {path}") from exc
    return Path(*parts[:workitems_index])


def retain_unexpected_runtime_documents(
    *,
    workspace_root: Path,
    execution_state: StageExecutionState,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    attempt_started_at_ns: int | None = None,
) -> tuple[Path, ...]:
    """Retain runtime writes to AIDD-owned records as attempt evidence.

    Canonical stage results, validator reports, and repair briefs are written by AIDD services.
    A runtime may still write a same-named draft, so retain a modified, non-placeholder copy
    under the current attempt before the canonical writer restores ownership.
    """

    stage_root = workspace_stage_root(
        root=workspace_root,
        work_item=execution_state.work_item,
        stage=execution_state.stage,
    )
    attempt_started_at = (
        execution_state.attempt_path.stat().st_mtime_ns
        if attempt_started_at_ns is None else attempt_started_at_ns
    )
    retained: list[Path] = []
    for filename, (evidence_name, placeholder) in _UNEXPECTED_RUNTIME_DOCUMENTS.items():
        canonical_path = stage_root / filename
        if not canonical_path.exists():
            continue
        try:
            text = canonical_path.read_text(encoding="utf-8")
            modified_after_attempt_start = canonical_path.stat().st_mtime_ns > attempt_started_at
        except (OSError, UnicodeDecodeError):
            continue
        if not modified_after_attempt_start or not text.strip():
            continue
        if placeholder is not None and text.strip() == placeholder:
            continue
        evidence_path = execution_state.attempt_path / evidence_name
        try:
            copy2(canonical_path, evidence_path)
        except OSError:
            continue
        retained.append(evidence_path)

    if retained:
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=execution_state.work_item,
            run_id=execution_state.run_id,
            stage=execution_state.stage,
            attempt_number=execution_state.attempt_number,
            contracts_root=contracts_root,
        )
    return tuple(retained)


def _promote_misplaced_stage_output_documents(
    *,
    expected_markdown_documents: tuple[Path, ...],
) -> tuple[StageOutputPromotion, ...]:
    promotions: list[StageOutputPromotion] = []
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
        promotions.append(
            StageOutputPromotion(
                source_path=misplaced_output_path,
                destination_path=destination_path,
            )
        )
    return tuple(promotions)


def _append_misplaced_output_promotion_warnings(
    *,
    workspace_root: Path,
    validator_report_path: Path,
    promotions: tuple[StageOutputPromotion, ...],
) -> None:
    if not promotions:
        return

    warning_lines = ["## Warnings", ""]
    for promotion in promotions:
        source = workspace_relative_path(workspace_root, promotion.source_path)
        destination = workspace_relative_path(workspace_root, promotion.destination_path)
        warning_lines.append(
            f"- `{_MISPLACED_OUTPUT_PROMOTION_WARNING_CODE}` (`low`) in `{source}`: "
            "Promoted misplaced stage output to canonical stage document "
            f"`{destination}`."
        )
    warning_lines.append("")
    report_text = validator_report_path.read_text(encoding="utf-8").rstrip()
    validator_report_path.write_text(
        report_text + "\n\n" + "\n".join(warning_lines),
        encoding="utf-8",
    )


def discover_stage_markdown_outputs(
    *,
    execution_state: StageExecutionState,
    invocation_bundle: AdapterInvocationBundle,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
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
        path for path in invocation_bundle.expected_output_documents if path.suffix.lower() == ".md"
    )
    workspace_root = (
        _workspace_root_for_document(expected_markdown_documents[0])
        if expected_markdown_documents
        else Path(".")
    )
    runtime_output_documents = resolve_runtime_output_documents(
        stage=execution_state.stage,
        work_item=execution_state.work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    unexpected_targets = tuple(
        path for path in expected_markdown_documents if path.resolve(strict=False) not in {
            candidate.resolve(strict=False) for candidate in runtime_output_documents
        }
    )
    if unexpected_targets:
        targets = ", ".join(path.name for path in unexpected_targets)
        raise ValueError(
            "Adapter invocation includes AIDD-owned or non-runtime output documents: "
            f"{targets}"
        )
    unexpected_runtime_documents = retain_unexpected_runtime_documents(
        workspace_root=workspace_root,
        execution_state=execution_state,
        contracts_root=contracts_root,
    )
    promoted_misplaced_documents = _promote_misplaced_stage_output_documents(
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
        promoted_misplaced_documents=promoted_misplaced_documents,
        unexpected_runtime_documents=unexpected_runtime_documents,
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
        output_documents=discovery.expected_markdown_documents,
    )
    section_findings = validate_required_sections(
        stage=discovery.stage,
        work_item=discovery.work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
        output_documents=discovery.expected_markdown_documents,
    )
    findings: tuple[ValidationFinding, ...]
    findings = (*structural_findings, *section_findings)
    has_document_read_failure = any(
        finding.code in DOCUMENT_READ_FAILURE_CODES for finding in findings
    )
    if (not findings or discovery.discovered_markdown_documents) and not has_document_read_failure:
        semantic_findings = validate_semantic_outputs(
            stage=discovery.stage,
            work_item=discovery.work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
            output_documents=discovery.expected_markdown_documents,
        )
        cross_document_findings = validate_cross_document_consistency(
            stage=discovery.stage,
            work_item=discovery.work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
        findings = (*findings, *semantic_findings, *cross_document_findings)

    stage_root = workspace_stage_root(
        root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    stage_root.mkdir(parents=True, exist_ok=True)
    validator_report_path = stage_root / "validator-report.md"
    write_validator_report(path=validator_report_path, findings=findings)
    _append_misplaced_output_promotion_warnings(
        workspace_root=workspace_root,
        validator_report_path=validator_report_path,
        promotions=discovery.promoted_misplaced_documents,
    )
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
    published_output_root.parent.mkdir(parents=True, exist_ok=True)

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

    publication_token = uuid4().hex
    staging_root = published_output_root.with_name(
        f".{published_output_root.name}.staging-{publication_token}"
    )
    backup_root = published_output_root.with_name(
        f".{published_output_root.name}.backup-{publication_token}"
    )
    staging_root.mkdir(parents=False, exist_ok=False)
    expected_names: list[str] = []
    try:
        for source_document in source_documents:
            if source_document.suffix.lower() != ".md":
                continue
            if not source_document.exists():
                if source_document.name in _CONDITIONAL_INTERVIEW_DOCUMENT_NAMES:
                    continue
                raise FileNotFoundError(
                    "Stage output publishing requires an existing source document: "
                    f"{workspace_relative_path(workspace_root, source_document)}"
                )
            copy2(source_document, staging_root / source_document.name)
            expected_names.append(source_document.name)

        staged_names = sorted(path.name for path in staging_root.iterdir() if path.is_file())
        if staged_names != sorted(expected_names):
            raise RuntimeError(
                "Staged stage-output verification failed: expected "
                f"{sorted(expected_names)}, found {staged_names}."
            )

        had_existing_publication = published_output_root.exists()
        if had_existing_publication:
            published_output_root.replace(backup_root)
        try:
            staging_root.replace(published_output_root)
        except BaseException:
            if had_existing_publication and backup_root.exists():
                backup_root.replace(published_output_root)
            raise
        if backup_root.exists():
            rmtree(backup_root)
    finally:
        if staging_root.exists():
            rmtree(staging_root)
        if backup_root.exists() and not published_output_root.exists():
            backup_root.replace(published_output_root)

    published_documents = [published_output_root / name for name in expected_names]

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
    "retain_unexpected_runtime_documents",
    "run_structural_validation_after_output_discovery",
]
