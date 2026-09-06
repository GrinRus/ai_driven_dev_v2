from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.validators.models import LoadedMarkdownDocument, MarkdownDocumentMetadata
from aidd.validators.protocol import (
    DocumentReadFailureKind,
    resolve_document_read_failure,
)

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


class DocumentLoadError(ValueError):
    """Raised when a resolved document cannot be loaded."""


@dataclass(frozen=True, slots=True)
class MarkdownReadFailure:
    """A normalized, repair-oriented failure from a Markdown readability probe."""

    kind: DocumentReadFailureKind
    message: str

    def __post_init__(self) -> None:
        normalized_message = self.message.strip()
        if not normalized_message:
            raise ValueError("Markdown read failure message must not be empty.")
        object.__setattr__(self, "message", normalized_message)

    @property
    def code(self) -> str:
        return resolve_document_read_failure(self.kind).code


@dataclass(frozen=True, slots=True)
class MarkdownReadProbeResult:
    """Typed result of probing one Markdown path for readability."""

    path: Path
    document: LoadedMarkdownDocument | None = None
    failure: MarkdownReadFailure | None = None

    def __post_init__(self) -> None:
        if (self.document is None) == (self.failure is None):
            raise ValueError("Markdown read probe must contain exactly one outcome.")

    @property
    def readable(self) -> bool:
        return self.document is not None


def _parse_optional_frontmatter(raw_body: str) -> dict[str, str] | None:
    lines = raw_body.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise DocumentLoadError("Frontmatter is missing a closing '---' delimiter.")

    frontmatter: dict[str, str] = {}
    for line in lines[1:closing_index]:
        if not line.strip():
            continue
        if ":" not in line:
            raise DocumentLoadError(f"Malformed frontmatter line: {line!r}")

        key, value = line.split(":", maxsplit=1)
        normalized_key = key.strip()
        if not normalized_key:
            raise DocumentLoadError(f"Malformed frontmatter key in line: {line!r}")
        if normalized_key in frontmatter:
            raise DocumentLoadError(f"Duplicate frontmatter key: {normalized_key}")

        frontmatter[normalized_key] = value.strip()

    return frontmatter


def _markdown_read_failure(
    *,
    path: Path,
    kind: DocumentReadFailureKind,
    message: str,
) -> MarkdownReadProbeResult:
    return MarkdownReadProbeResult(
        path=path,
        failure=MarkdownReadFailure(kind=kind, message=message),
    )


def _classify_document_load_error(exc: Exception) -> DocumentReadFailureKind:
    if isinstance(exc, UnicodeDecodeError):
        return DocumentReadFailureKind.INVALID_UTF8
    if isinstance(exc, DocumentPathError):
        return DocumentReadFailureKind.UNREADABLE
    if isinstance(exc, DocumentLoadError):
        normalized = str(exc).casefold()
        if "not a file" in normalized:
            return DocumentReadFailureKind.NON_FILE
        if "frontmatter" in normalized:
            return DocumentReadFailureKind.MALFORMED_FRONTMATTER
    return DocumentReadFailureKind.UNREADABLE


def probe_markdown_document(
    *,
    path: Path,
    workspace_root: Path,
) -> MarkdownReadProbeResult:
    """Return a typed readability outcome without leaking expected read exceptions."""

    try:
        document = load_markdown_document(path=path, workspace_root=workspace_root)
    except (DocumentPathError, DocumentLoadError, OSError, UnicodeDecodeError) as exc:
        return _markdown_read_failure(
            path=path,
            kind=_classify_document_load_error(exc),
            message=str(exc),
        )
    return MarkdownReadProbeResult(path=path, document=document)


def classify_document_type(workspace_relative_path: Path) -> str:
    parts = workspace_relative_path.parts
    if len(parts) < 5:
        return "unknown"
    if parts[0] != "workitems" or parts[2] != "stages":
        return "unknown"

    stage_local_parts = parts[4:]
    if len(stage_local_parts) == 1 and stage_local_parts[0] in _COMMON_DOCUMENTS:
        doc_name = stage_local_parts[0].removesuffix(".md")
        return f"common:{doc_name}"
    if (
        len(stage_local_parts) >= 2
        and stage_local_parts[0] in _STAGE_IO_DIRECTORIES
        and workspace_relative_path.suffix.lower() == ".md"
    ):
        return f"stage-{stage_local_parts[0]}"

    return "unknown"


def load_markdown_document(path: Path, workspace_root: Path) -> LoadedMarkdownDocument:
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = path.resolve(strict=False)

    if not resolved_path.is_relative_to(resolved_workspace):
        raise DocumentPathError(
            f"Document path must stay inside workspace: {path} (workspace={resolved_workspace})"
        )
    if resolved_path.suffix.lower() != ".md":
        raise DocumentPathError(f"Expected a Markdown file (.md), got: {resolved_path.name}")
    if not resolved_path.exists():
        raise DocumentLoadError(f"Markdown file does not exist: {resolved_path}")
    if not resolved_path.is_file():
        raise DocumentLoadError(f"Markdown path is not a file: {resolved_path}")

    body = resolved_path.read_text(encoding="utf-8")
    frontmatter = _parse_optional_frontmatter(body)
    stat = resolved_path.stat()
    workspace_relative_path = resolved_path.relative_to(resolved_workspace)
    metadata = MarkdownDocumentMetadata(
        path=resolved_path,
        workspace_relative_path=workspace_relative_path,
        document_type=classify_document_type(workspace_relative_path),
        size_bytes=stat.st_size,
        modified_time_epoch_s=stat.st_mtime,
    )
    return LoadedMarkdownDocument(body=body, metadata=metadata, frontmatter=frontmatter)
