from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SeverityLevel = Literal["critical", "high", "medium", "low"]


@dataclass(frozen=True, slots=True)
class ValidationIssueLocation:
    workspace_relative_path: str
    line_number: int | None = None

    def __post_init__(self) -> None:
        normalized_path = self.workspace_relative_path.strip()
        if not normalized_path:
            raise ValueError("Validation issue location must include a workspace-relative path.")
        if Path(normalized_path).is_absolute():
            raise ValueError("Validation issue location path must be workspace-relative.")
        object.__setattr__(self, "workspace_relative_path", normalized_path)

        if self.line_number is not None and self.line_number <= 0:
            raise ValueError("Validation issue location line number must be positive.")


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    code: str
    message: str
    severity: SeverityLevel = "high"
    location: ValidationIssueLocation | None = None

    def __post_init__(self) -> None:
        normalized_code = self.code.strip().upper()
        if not normalized_code:
            raise ValueError("Validation finding code must not be empty.")
        if "-" not in normalized_code:
            raise ValueError("Validation finding code must use stable subsystem-prefixed format.")
        object.__setattr__(self, "code", normalized_code)

        normalized_message = self.message.strip()
        if not normalized_message:
            raise ValueError("Validation finding message must not be empty.")
        object.__setattr__(self, "message", normalized_message)


@dataclass(frozen=True)
class MarkdownDocumentMetadata:
    path: Path
    workspace_relative_path: Path
    document_type: str
    size_bytes: int
    modified_time_epoch_s: float


@dataclass(frozen=True)
class LoadedMarkdownDocument:
    body: str
    metadata: MarkdownDocumentMetadata
    frontmatter: dict[str, str] | None = None
