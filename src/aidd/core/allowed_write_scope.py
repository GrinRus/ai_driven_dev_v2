from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from aidd.core.workspace import work_item_context_root

ALLOWED_WRITE_SCOPE_FILENAME = "allowed-write-scope.md"
_LIST_ENTRY_PATTERN = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
_BACKTICKED_VALUE_PATTERN = re.compile(r"`([^`]+)`")
_DRIVE_PATH_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_SAFE_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class AllowedWriteScopeError(ValueError):
    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("Invalid allowed write scope: " + "; ".join(issues))


@dataclass(frozen=True, slots=True)
class AllowedWriteScope:
    prefixes: tuple[str, ...]
    source_path: Path

    def allows(self, repository_relative_path: str | Path) -> bool:
        candidate = _normalize_path(
            repository_relative_path.as_posix()
            if isinstance(repository_relative_path, Path)
            else repository_relative_path,
            label="repository path",
        )
        return any(
            candidate == prefix or candidate.startswith(f"{prefix}/")
            for prefix in self.prefixes
        )


def _normalize_path(value: str, *, label: str) -> str:
    raw = value.strip()
    while raw.startswith("./"):
        raw = raw[2:]
    raw = raw.rstrip("/")
    parts = raw.split("/")
    invalid = (
        not raw
        or raw in {".", ".."}
        or raw.startswith(("/", "\\"))
        or _DRIVE_PATH_PATTERN.match(raw) is not None
        or "\\" in raw
        or any(part in {"", ".", ".."} for part in parts)
        or any(marker in raw for marker in ("*", "?", "[", "]"))
        or any(_SAFE_SEGMENT_PATTERN.fullmatch(part) is None for part in parts)
        or PurePosixPath(raw).is_absolute()
    )
    if invalid:
        raise AllowedWriteScopeError(
            (f"{label} `{value}` is not a safe repository-relative path.",)
        )
    return raw


def parse_allowed_write_scope(markdown: str, *, source_path: Path) -> AllowedWriteScope:
    prefixes: list[str] = []
    issues: list[str] = []
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        entry = _LIST_ENTRY_PATTERN.match(line)
        if entry is None:
            continue
        for value in _BACKTICKED_VALUE_PATTERN.findall(entry.group(1)):
            try:
                prefixes.append(_normalize_path(value, label=f"line {line_number} path"))
            except AllowedWriteScopeError as exc:
                issues.extend(exc.issues)
    prefixes = list(dict.fromkeys(prefixes))
    if not prefixes:
        issues.append("the document must contain at least one backticked path in a list entry.")
    if issues:
        raise AllowedWriteScopeError(tuple(issues))
    return AllowedWriteScope(prefixes=tuple(prefixes), source_path=source_path)


def resolve_allowed_write_scope(
    workspace_root: Path,
    work_item: str,
) -> AllowedWriteScope | None:
    source_path = work_item_context_root(
        root=workspace_root,
        work_item=work_item,
    ) / ALLOWED_WRITE_SCOPE_FILENAME
    if not source_path.exists():
        return None
    return parse_allowed_write_scope(
        source_path.read_text(encoding="utf-8", errors="replace"),
        source_path=source_path,
    )


__all__ = [
    "ALLOWED_WRITE_SCOPE_FILENAME",
    "AllowedWriteScope",
    "AllowedWriteScopeError",
    "parse_allowed_write_scope",
    "resolve_allowed_write_scope",
]
