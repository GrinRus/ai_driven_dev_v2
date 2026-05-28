from __future__ import annotations

from pathlib import Path

from aidd.core.markdown import (
    extract_markdown_headings,
    extract_required_sections_from_document_contract,
    extract_stage_required_heading_map,
    normalize_heading,
)
from aidd.core.operator_frontend_common import validate_operator_stage
from aidd.core.operator_frontend_models import (
    OperatorArtifactDocumentView,
    OperatorStageDocumentDiffInput,
    OperatorStageDocumentReference,
    OperatorStageDocumentRequirement,
    OperatorStageDocumentValidationResult,
    OperatorStageDocumentVersion,
    OperatorStageDocumentWorkbench,
    OperatorStageWorkbenchDocument,
)
from aidd.core.resources import resolve_resource_layout_from_contracts_root
from aidd.core.run_inspection import (
    RunArtifactsSummary,
    resolve_run_artifacts_summary,
    resolve_stage_result_summary,
)
from aidd.core.run_lookup import latest_attempt_number, latest_run_id
from aidd.core.run_store import load_attempt_artifact_index, load_stage_metadata
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    StageManifestLoadError,
    load_stage_manifest,
    resolve_expected_output_documents,
    stage_contract_path,
)

_DEFAULT_ARTIFACT_PREVIEW_BYTES = 64 * 1024
_DEFAULT_ARTIFACT_SOURCE_BYTES = 128 * 1024
_MAX_ARTIFACT_READ_BYTES = 256 * 1024
_SYSTEM_DOCUMENT_KEYS = {
    "answers",
    "input_bundle",
    "operator_request",
    "questions",
    "repair_brief",
    "repair_context",
    "stage_brief",
    "validator_report",
}


def resolve_operator_artifacts_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunArtifactsSummary:
    validate_operator_stage(stage)
    return resolve_run_artifacts_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        attempt_number=attempt_number,
    )


def resolve_operator_artifact_document_content(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    key: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
    mode: str = "preview",
    limit_bytes: int | None = None,
) -> OperatorArtifactDocumentView:
    validate_operator_stage(stage)
    normalized_key = key.strip()
    if not normalized_key:
        raise ValueError("Artifact document key is required.")
    normalized_mode = mode.strip().lower() or "preview"
    if normalized_mode not in {"preview", "source"}:
        raise ValueError("mode must be 'preview' or 'source'.")
    if limit_bytes is not None and limit_bytes <= 0:
        raise ValueError("limit_bytes must be greater than zero.")

    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")
    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )
    artifact_index = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_index is None:
        raise ValueError(
            f"Artifact index is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    relative_document_path = artifact_index.documents.get(normalized_key)
    if relative_document_path is None:
        supported = ", ".join(sorted(artifact_index.documents)) or "none"
        raise ValueError(
            f"Artifact document key '{normalized_key}' is not available. "
            f"Available document keys: {supported}."
        )
    return _bounded_operator_artifact_document(
        workspace_root=workspace_root,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        key=normalized_key,
        relative_document_path=relative_document_path,
        mode=normalized_mode,
        limit_bytes=limit_bytes,
    )


def resolve_operator_stage_document_workbench(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    key: str | None = None,
    run_id: str | None = None,
    attempt_number: int | None = None,
    preview_limit_bytes: int | None = None,
    source_limit_bytes: int | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> OperatorStageDocumentWorkbench:
    validate_operator_stage(stage)
    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")
    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )
    artifact_index = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_index is None:
        raise ValueError(
            f"Artifact index is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    selected_key = (key or _preferred_workbench_document_key(artifact_index.documents)).strip()
    if not selected_key:
        raise ValueError("Workbench document key is required.")
    relative_document_path = artifact_index.documents.get(selected_key)
    if relative_document_path is None:
        supported = ", ".join(sorted(artifact_index.documents)) or "none"
        raise ValueError(
            f"Artifact document key '{selected_key}' is not available. "
            f"Available document keys: {supported}."
        )

    preview, preview_error = _try_bounded_workbench_document(
        workspace_root=workspace_root,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        key=selected_key,
        relative_document_path=relative_document_path,
        mode="preview",
        limit_bytes=preview_limit_bytes,
    )
    source, source_error = _try_bounded_workbench_document(
        workspace_root=workspace_root,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        key=selected_key,
        relative_document_path=relative_document_path,
        mode="source",
        limit_bytes=source_limit_bytes,
    )
    document = _workbench_document(
        workspace_root=workspace_root,
        key=selected_key,
        relative_document_path=relative_document_path,
        preview=preview,
        source=source,
        error=preview_error or source_error,
    )

    return OperatorStageDocumentWorkbench(
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        selected_key=selected_key,
        document=document,
        requirements=_document_requirements(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            selected_document=document,
            contracts_root=contracts_root,
        ),
        validation_results=_validation_results(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=selected_run_id,
        ),
        references=_document_references(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=selected_run_id,
            artifact_documents=artifact_index.documents,
            artifact_logs=artifact_index.logs,
        ),
        diff_inputs=_diff_inputs(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=selected_run_id,
            attempt_number=selected_attempt,
            selected_key=selected_key,
            artifact_documents=artifact_index.documents,
        ),
        versions=_document_versions(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=selected_run_id,
            attempt_number=selected_attempt,
            selected_key=selected_key,
        ),
    )


def _bounded_operator_artifact_document(
    *,
    workspace_root: Path,
    run_id: str,
    stage: str,
    attempt_number: int,
    key: str,
    relative_document_path: str,
    mode: str,
    limit_bytes: int | None,
) -> OperatorArtifactDocumentView:
    relative = Path(relative_document_path)
    document_path = _safe_relative_path(workspace_root, relative_document_path)
    if document_path is None:
        if relative.is_absolute():
            raise ValueError(f"Artifact path must be workspace-relative: {relative_document_path}")
        raise ValueError(f"Artifact path escapes workspace root: {relative_document_path}")
    if not document_path.exists():
        raise ValueError(f"Artifact document file does not exist: {document_path.as_posix()}.")

    byte_size = document_path.stat().st_size
    default_bytes = (
        _DEFAULT_ARTIFACT_SOURCE_BYTES if mode == "source" else _DEFAULT_ARTIFACT_PREVIEW_BYTES
    )
    requested_bytes = min(limit_bytes or default_bytes, _MAX_ARTIFACT_READ_BYTES)
    start_byte = 0
    end_byte = min(byte_size, requested_bytes)
    with document_path.open("rb") as file_obj:
        raw_text = file_obj.read(end_byte - start_byte)
    text = _decode_bounded_utf8(raw_text, path=document_path, truncated_tail=end_byte < byte_size)

    return OperatorArtifactDocumentView(
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        key=key,
        path=workspace_relative_path(workspace_root, document_path),
        text=text,
        byte_size=byte_size,
        content_type=_operator_artifact_content_type(document_path),
        mode=mode,
        start_byte=start_byte,
        end_byte=end_byte,
        requested_bytes=requested_bytes,
        max_bytes=_MAX_ARTIFACT_READ_BYTES,
        truncated=start_byte > 0 or end_byte < byte_size,
        truncated_head=start_byte > 0,
        truncated_tail=end_byte < byte_size,
    )


def _preferred_workbench_document_key(documents: dict[str, str]) -> str:
    for key in documents:
        if key not in _SYSTEM_DOCUMENT_KEYS:
            return key
    return next(iter(documents), "")


def _try_bounded_workbench_document(
    *,
    workspace_root: Path,
    run_id: str,
    stage: str,
    attempt_number: int,
    key: str,
    relative_document_path: str,
    mode: str,
    limit_bytes: int | None,
) -> tuple[OperatorArtifactDocumentView | None, str | None]:
    try:
        return (
            _bounded_operator_artifact_document(
                workspace_root=workspace_root,
                run_id=run_id,
                stage=stage,
                attempt_number=attempt_number,
                key=key,
                relative_document_path=relative_document_path,
                mode=mode,
                limit_bytes=limit_bytes,
            ),
            None,
        )
    except ValueError as exc:
        return None, str(exc)


def _workbench_document(
    *,
    workspace_root: Path,
    key: str,
    relative_document_path: str,
    preview: OperatorArtifactDocumentView | None,
    source: OperatorArtifactDocumentView | None,
    error: str | None,
) -> OperatorStageWorkbenchDocument:
    if preview is not None or source is not None:
        content = preview or source
        assert content is not None
        return OperatorStageWorkbenchDocument(
            key=key,
            path=content.path,
            status="present",
            message=None,
            content_type=content.content_type,
            byte_size=content.byte_size,
            preview=preview,
            source=source,
        )
    document_path = _safe_relative_path(workspace_root, relative_document_path)
    if error is not None and "does not exist" in error:
        status = "missing"
    elif error is not None and "not UTF-8 text" in error:
        status = "invalid"
    else:
        status = "invalid"
    return OperatorStageWorkbenchDocument(
        key=key,
        path=(
            workspace_relative_path(workspace_root, document_path)
            if document_path is not None
            else relative_document_path
        ),
        status=status,
        message=error,
        content_type=_operator_artifact_content_type(Path(relative_document_path)),
        byte_size=(
            document_path.stat().st_size
            if document_path is not None and document_path.exists()
            else None
        ),
        preview=None,
        source=None,
    )


def _document_requirements(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    selected_document: OperatorStageWorkbenchDocument,
    contracts_root: Path,
) -> tuple[OperatorStageDocumentRequirement, ...]:
    requirements: list[OperatorStageDocumentRequirement] = []
    try:
        load_stage_manifest(stage=stage, contracts_root=contracts_root)
        expected_outputs = resolve_expected_output_documents(
            stage=stage,
            work_item=work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
    except StageManifestLoadError as exc:
        return (
            OperatorStageDocumentRequirement(
                kind="stage-contract",
                label=stage,
                path=None,
                status="invalid",
                source=str(exc),
            ),
        )

    for expected_output in expected_outputs:
        requirements.append(
            OperatorStageDocumentRequirement(
                kind="required-output",
                label=expected_output.name,
                path=workspace_relative_path(workspace_root, expected_output),
                status="satisfied" if expected_output.exists() else "missing",
                source="stage-contract",
            )
        )

    requirements.extend(
        _section_requirements(
            stage=stage,
            selected_document=selected_document,
            contracts_root=contracts_root,
        )
    )
    return tuple(requirements)


def _section_requirements(
    *,
    stage: str,
    selected_document: OperatorStageWorkbenchDocument,
    contracts_root: Path,
) -> tuple[OperatorStageDocumentRequirement, ...]:
    document_name = Path(selected_document.path).name
    sections: list[tuple[str, str]] = []
    document_contract_path = (
        resolve_resource_layout_from_contracts_root(contracts_root).document_contracts_root
        / document_name
    )
    if document_contract_path.exists():
        for section in extract_required_sections_from_document_contract(
            document_contract_path.read_text(encoding="utf-8")
        ):
            sections.append((section, "document-contract"))
    stage_contract = stage_contract_path(stage, contracts_root)
    if stage_contract.exists():
        stage_requirements = extract_stage_required_heading_map(
            stage_contract.read_text(encoding="utf-8")
        )
        for section in stage_requirements.get(document_name, ()):
            sections.append((section, "stage-contract"))

    if not sections:
        return ()

    headings = (
        {
            normalize_heading(heading.title)
            for heading in extract_markdown_headings(selected_document.source.text)
        }
        if selected_document.source is not None
        else set()
    )
    truncated = bool(selected_document.source and selected_document.source.truncated)
    requirements: list[OperatorStageDocumentRequirement] = []
    for section, source in dict.fromkeys(sections):
        normalized = normalize_heading(section)
        status = (
            "satisfied"
            if normalized in headings
            else "unknown"
            if selected_document.status != "present" or truncated
            else "missing"
        )
        requirements.append(
            OperatorStageDocumentRequirement(
                kind="required-section",
                label=section,
                path=selected_document.path,
                status=status,
                source=source,
            )
        )
    return tuple(requirements)


def _validation_results(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
) -> tuple[OperatorStageDocumentValidationResult, ...]:
    try:
        result = resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError as exc:
        return (
            OperatorStageDocumentValidationResult(
                label="stage-result",
                status="missing",
                path=None,
                detail=str(exc),
            ),
        )
    status = "pass" if result.validator_fail_count == 0 else "fail"
    return (
        OperatorStageDocumentValidationResult(
            label="validator-report",
            status=status,
            path=result.validator_report_path,
            detail=(
                f"{result.validator_pass_count} passing, "
                f"{result.validator_fail_count} failing validator result(s)"
            ),
        ),
        OperatorStageDocumentValidationResult(
            label="stage-result",
            status=result.final_state,
            path=f"workitems/{work_item}/stages/{stage}/stage-result.md",
            detail=(
                f"Stage finished as {result.final_state} "
                f"after {result.attempt_count} attempt(s)."
            ),
        ),
    )


def _document_references(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    artifact_documents: dict[str, str],
    artifact_logs: dict[str, str],
) -> tuple[OperatorStageDocumentReference, ...]:
    refs: list[OperatorStageDocumentReference] = [
        OperatorStageDocumentReference(label=key, kind="document", path=path, stage=stage)
        for key, path in sorted(artifact_documents.items())
    ]
    refs.extend(
        OperatorStageDocumentReference(label=key, kind="log", path=path, stage=stage)
        for key, path in sorted(artifact_logs.items())
    )
    try:
        result = resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError:
        return tuple(refs)
    refs.extend(
        OperatorStageDocumentReference(
            label=Path(path).name,
            kind="repair",
            path=path,
            stage=stage,
        )
        for path in result.repair_output_paths
    )
    return tuple(refs)


def _diff_inputs(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    attempt_number: int,
    selected_key: str,
    artifact_documents: dict[str, str],
) -> tuple[OperatorStageDocumentDiffInput, ...]:
    inputs = [
        OperatorStageDocumentDiffInput(
            label=f"Current {key}",
            kind="current-document",
            key=key,
            path=path,
            attempt_number=attempt_number,
        )
        for key, path in sorted(artifact_documents.items())
        if key != selected_key
    ]
    for previous_attempt in range(attempt_number - 1, 0, -1):
        previous_index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=previous_attempt,
        )
        if previous_index is None:
            continue
        previous_path = previous_index.documents.get(selected_key)
        if previous_path is None:
            continue
        inputs.append(
            OperatorStageDocumentDiffInput(
                label=f"Attempt {previous_attempt} {selected_key}",
                kind="previous-version",
                key=selected_key,
                path=previous_path,
                attempt_number=previous_attempt,
            )
        )
        break
    return tuple(inputs)


def _document_versions(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    attempt_number: int,
    selected_key: str,
) -> tuple[OperatorStageDocumentVersion, ...]:
    stage_metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    trigger_by_attempt = (
        {
            entry.attempt_number: entry.trigger
            for entry in stage_metadata.repair_history
        }
        if stage_metadata is not None
        else {}
    )
    versions: list[OperatorStageDocumentVersion] = []
    for candidate_attempt in range(1, attempt_number + 1):
        artifact_index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=candidate_attempt,
        )
        if artifact_index is None:
            continue
        path = artifact_index.documents.get(selected_key)
        if path is None:
            continue
        source = trigger_by_attempt.get(candidate_attempt)
        if source is None:
            source = "model-authored" if selected_key not in _SYSTEM_DOCUMENT_KEYS else "system"
        versions.append(
            OperatorStageDocumentVersion(
                label=f"Attempt {candidate_attempt}",
                key=selected_key,
                path=path,
                run_id=run_id,
                attempt_number=candidate_attempt,
                updated_at_utc=artifact_index.updated_at_utc,
                source=source,
            )
        )
    return tuple(versions)


def _operator_artifact_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "text/markdown"
    if suffix in {".txt", ".log", ".json", ".jsonl", ".yaml", ".yml", ".toml"}:
        return "text/plain"
    return "application/octet-stream"


def _decode_bounded_utf8(raw_text: bytes, *, path: Path, truncated_tail: bool) -> str:
    try:
        return raw_text.decode("utf-8")
    except UnicodeDecodeError as exc:
        if truncated_tail and exc.reason == "unexpected end of data":
            return raw_text[: exc.start].decode("utf-8")
        raise ValueError(f"Artifact document is not UTF-8 text: {path.as_posix()}.") from exc


def _safe_relative_path(workspace_root: Path, relative_path: str) -> Path | None:
    relative = Path(relative_path)
    if relative.is_absolute():
        return None
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = (workspace_root / relative).resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_workspace):
        return None
    return resolved_path


def _artifact_size(*, workspace_root: Path, relative_path: str) -> int | None:
    path = _safe_relative_path(workspace_root, relative_path)
    if path is None or not path.exists():
        return None
    return path.stat().st_size


__all__ = [
    "_artifact_size",
    "_bounded_operator_artifact_document",
    "_safe_relative_path",
    "resolve_operator_artifact_document_content",
    "resolve_operator_artifacts_view",
    "resolve_operator_stage_document_workbench",
]
