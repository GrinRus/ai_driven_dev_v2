from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationFinding:
    code: str
    message: str


@dataclass(frozen=True)
class MarkdownDocumentMetadata:
    path: Path
    workspace_relative_path: Path
    size_bytes: int
    modified_time_epoch_s: float


@dataclass(frozen=True)
class LoadedMarkdownDocument:
    body: str
    metadata: MarkdownDocumentMetadata
    frontmatter: dict[str, str] | None = None
