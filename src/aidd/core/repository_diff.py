from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from aidd.core.operator_reports import ImplementationEvidenceView, resolve_implementation_evidence

_MAX_DIFF_BYTES = 192 * 1024
_MAX_UNTRACKED_PREVIEW_BYTES = 32 * 1024


@dataclass(frozen=True, slots=True)
class RepositoryDiffFile:
    path: str
    status: str
    category: str
    diff: str
    truncated: bool
    mentioned_in_report: bool
    allowed_scope_status: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RepositoryDiffView:
    project_root: Path
    workspace_root: Path
    source_files: tuple[RepositoryDiffFile, ...]
    aidd_artifacts: tuple[RepositoryDiffFile, ...]
    mentioned_but_unchanged: tuple[str, ...]
    warnings: tuple[str, ...]
    implementation: ImplementationEvidenceView


def _resolve_directory(path: Path, *, label: str) -> Path:
    try:
        resolved = path.expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"{label} does not exist: {path.as_posix()}.") from exc
    if not resolved.is_dir():
        raise ValueError(f"{label} must be a directory: {path.as_posix()}.")
    return resolved


def _run_git(project_root: Path, args: tuple[str, ...]) -> str:
    completed = subprocess.run(
        ("git", "-C", project_root.as_posix(), *args),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def _git_available(project_root: Path) -> bool:
    try:
        _run_git(project_root, ("rev-parse", "--show-toplevel"))
    except ValueError:
        return False
    return True


def _bounded_text(text: str, max_bytes: int) -> tuple[str, bool]:
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text, False
    return data[:max_bytes].decode("utf-8", errors="replace"), True


def _status_entries(project_root: Path) -> list[tuple[str, str]]:
    output = _run_git(
        project_root,
        (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--renames",
        ),
    )
    entries: list[tuple[str, str]] = []
    records = output.split("\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4:
            raise ValueError("git status returned an invalid porcelain record.")
        status = record[:2].strip() or "modified"
        raw_path = record[3:]
        if "R" in status or "C" in status:
            index += 1
        entries.append((status, raw_path))
    return entries


def _normalize_status(short_status: str) -> str:
    if short_status == "??":
        return "untracked"
    if "D" in short_status:
        return "deleted"
    if "R" in short_status:
        return "renamed"
    if "A" in short_status:
        return "added"
    if "M" in short_status:
        return "modified"
    return short_status.lower() or "modified"


def _safe_repo_path(project_root: Path, relative_path: str) -> Path:
    if not relative_path.strip():
        raise ValueError("Repository diff path must not be empty.")
    raw = Path(relative_path)
    if raw.is_absolute() or any(part == ".." for part in raw.parts):
        raise ValueError(f"Repository diff path must be project-relative: {relative_path}.")
    resolved = (project_root / raw).resolve(strict=False)
    if not resolved.is_relative_to(project_root):
        raise ValueError(f"Repository diff path must stay inside project root: {relative_path}.")
    return resolved


def _file_diff(
    project_root: Path,
    relative_path: str,
    status: str,
) -> tuple[str, bool, tuple[str, ...]]:
    warnings: list[str] = []
    if status == "untracked":
        path = _safe_repo_path(project_root, relative_path)
        if not path.exists() or not path.is_file():
            return "", False, ("Untracked path is not a regular file.",)
        data = path.read_bytes()[:_MAX_UNTRACKED_PREVIEW_BYTES]
        truncated = path.stat().st_size > _MAX_UNTRACKED_PREVIEW_BYTES
        text = data.decode("utf-8", errors="replace")
        return (
            f"--- /dev/null\n+++ b/{relative_path}\n"
            + "\n".join(f"+{line}" for line in text.splitlines()),
            truncated,
            tuple(warnings),
        )
    try:
        staged = _run_git(
            project_root,
            ("diff", "--cached", "--no-ext-diff", "--", relative_path),
        )
        unstaged = _run_git(project_root, ("diff", "--no-ext-diff", "--", relative_path))
    except ValueError as exc:
        warnings.append(str(exc))
        return "", False, tuple(warnings)
    diff = "\n".join(part for part in (staged.strip(), unstaged.strip()) if part)
    bounded, truncated = _bounded_text(diff, _MAX_DIFF_BYTES)
    return bounded, truncated, tuple(warnings)


def _read_allowed_scope_paths(*, workspace_root: Path, work_item: str) -> tuple[str, ...]:
    scope_path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "context"
        / "allowed-write-scope.md"
    )
    if not scope_path.exists():
        return ()
    text = scope_path.read_text(encoding="utf-8", errors="replace")
    values: list[str] = []
    for line in text.splitlines():
        for chunk in line.split("`")[1::2]:
            path = chunk.strip().strip("/")
            if path:
                values.append(path)
    return tuple(dict.fromkeys(values))


def _allowed_scope_status(path: str, allowed_paths: tuple[str, ...]) -> str:
    if not allowed_paths:
        return "unknown"
    normalized = path.strip("/")
    for allowed in allowed_paths:
        allowed_normalized = allowed.strip("/")
        if normalized == allowed_normalized or normalized.startswith(f"{allowed_normalized}/"):
            return "inside"
    return "outside"


def resolve_repository_diff(
    *,
    project_root: Path,
    workspace_root: Path,
    work_item: str,
) -> RepositoryDiffView:
    resolved_project = _resolve_directory(project_root, label="Project root")
    resolved_workspace = workspace_root.resolve(strict=False)
    if not resolved_workspace.is_relative_to(resolved_project):
        raise ValueError("Workspace root must stay inside the selected project root.")
    implementation = resolve_implementation_evidence(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    warnings: list[str] = []
    if not _git_available(resolved_project):
        return RepositoryDiffView(
            project_root=resolved_project,
            workspace_root=resolved_workspace,
            source_files=(),
            aidd_artifacts=(),
            mentioned_but_unchanged=implementation.touched_files,
            warnings=("Project root is not a git repository; repository diff is unavailable.",),
            implementation=implementation,
        )

    mentioned = set(implementation.touched_files)
    allowed_paths = _read_allowed_scope_paths(workspace_root=workspace_root, work_item=work_item)
    source_files: list[RepositoryDiffFile] = []
    artifacts: list[RepositoryDiffFile] = []
    changed_paths: set[str] = set()
    for short_status, relative_path in _status_entries(resolved_project):
        _safe_repo_path(resolved_project, relative_path)
        status = _normalize_status(short_status)
        diff, truncated, file_warnings = _file_diff(resolved_project, relative_path, status)
        category = (
            "aidd-artifact"
            if relative_path == ".aidd" or relative_path.startswith(".aidd/")
            else "source"
        )
        item = RepositoryDiffFile(
            path=relative_path,
            status=status,
            category=category,
            diff=diff,
            truncated=truncated,
            mentioned_in_report=relative_path in mentioned,
            allowed_scope_status=(
                "aidd-artifact"
                if category == "aidd-artifact"
                else _allowed_scope_status(relative_path, allowed_paths)
            ),
            warnings=file_warnings,
        )
        changed_paths.add(relative_path)
        if category == "aidd-artifact":
            artifacts.append(item)
        else:
            source_files.append(item)

    mentioned_but_unchanged = tuple(
        path for path in implementation.touched_files if path not in changed_paths
    )
    if mentioned_but_unchanged:
        warnings.append("Some implementation-report touched files are not present in git status.")
    return RepositoryDiffView(
        project_root=resolved_project,
        workspace_root=resolved_workspace,
        source_files=tuple(source_files),
        aidd_artifacts=tuple(artifacts),
        mentioned_but_unchanged=mentioned_but_unchanged,
        warnings=tuple(warnings),
        implementation=implementation,
    )


__all__ = [
    "RepositoryDiffFile",
    "RepositoryDiffView",
    "resolve_repository_diff",
]
