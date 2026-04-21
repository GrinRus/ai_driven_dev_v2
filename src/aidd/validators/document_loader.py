from __future__ import annotations

from pathlib import Path

_COMMON_DOCUMENTS = frozenset(
    {
        "answers.md",
        "questions.md",
        "repair-brief.md",
        "stage-brief.md",
        "stage-result.md",
        "validator-report.md",
    }
)
_STAGE_IO_DIRECTORIES = frozenset({"input", "output"})


class DocumentPathError(ValueError):
    """Raised when a document path cannot be resolved safely."""


def _resolve_workspace_relative_path(workspace_root: Path, relative_path: Path) -> Path:
    if relative_path.is_absolute():
        raise DocumentPathError(
            f"Path must be workspace-relative, got absolute path: {relative_path}"
        )

    workspace_root_resolved = workspace_root.resolve(strict=False)
    candidate = (workspace_root / relative_path).resolve(strict=False)
    if not candidate.is_relative_to(workspace_root_resolved):
        raise DocumentPathError(
            f"Path escapes workspace root: {relative_path} (workspace={workspace_root_resolved})"
        )

    return candidate


def _validate_document_name(document_name: str) -> None:
    if not document_name:
        raise DocumentPathError("Document name must not be empty.")

    candidate = Path(document_name)
    if candidate.name != document_name:
        raise DocumentPathError(
            f"Document name must be a simple filename without path separators: {document_name}"
        )


def resolve_stage_root(workspace_root: Path, work_item: str, stage: str) -> Path:
    if not work_item:
        raise DocumentPathError("Work item id must not be empty.")
    if not stage:
        raise DocumentPathError("Stage id must not be empty.")

    relative_path = Path("workitems") / work_item / "stages" / stage
    return _resolve_workspace_relative_path(workspace_root, relative_path)


def resolve_common_document_path(
    workspace_root: Path,
    work_item: str,
    stage: str,
    document_name: str,
) -> Path:
    _validate_document_name(document_name)
    if document_name not in _COMMON_DOCUMENTS:
        allowed = ", ".join(sorted(_COMMON_DOCUMENTS))
        raise DocumentPathError(
            f"Unknown common document '{document_name}'. Expected one of: {allowed}"
        )

    stage_root = resolve_stage_root(workspace_root=workspace_root, work_item=work_item, stage=stage)
    return _resolve_workspace_relative_path(
        workspace_root=workspace_root,
        relative_path=stage_root.relative_to(workspace_root.resolve(strict=False)) / document_name,
    )


def resolve_stage_document_path(
    workspace_root: Path,
    work_item: str,
    stage: str,
    io_direction: str,
    document_name: str,
) -> Path:
    _validate_document_name(document_name)
    if io_direction not in _STAGE_IO_DIRECTORIES:
        allowed = ", ".join(sorted(_STAGE_IO_DIRECTORIES))
        raise DocumentPathError(
            f"Unknown stage document direction '{io_direction}'. Expected one of: {allowed}"
        )

    stage_root = resolve_stage_root(workspace_root=workspace_root, work_item=work_item, stage=stage)
    return _resolve_workspace_relative_path(
        workspace_root=workspace_root,
        relative_path=stage_root.relative_to(workspace_root.resolve(strict=False))
        / io_direction
        / document_name,
    )
