from __future__ import annotations

from pathlib import Path

from aidd.core.operator_frontend_common import validate_operator_stage
from aidd.core.operator_frontend_models import OperatorArtifactDocumentView
from aidd.core.run_inspection import RunArtifactsSummary, resolve_run_artifacts_summary
from aidd.core.run_lookup import latest_attempt_number, latest_run_id
from aidd.core.run_store import load_attempt_artifact_index
from aidd.core.stage_paths import workspace_relative_path

_DEFAULT_ARTIFACT_PREVIEW_BYTES = 64 * 1024
_DEFAULT_ARTIFACT_SOURCE_BYTES = 128 * 1024
_MAX_ARTIFACT_READ_BYTES = 256 * 1024

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
]
