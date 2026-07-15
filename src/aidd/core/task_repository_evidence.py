from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from aidd.core.allowed_write_scope import (
    AllowedWriteScopeError,
    resolve_allowed_write_scope,
)
from aidd.core.stage_models import StageExecutionState, StageOutputDiscovery
from aidd.core.task_attempt_lifecycle import TaskExecutionContext
from aidd.validators.models import ValidationFinding, ValidationIssueLocation


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    task_id: str
    status: tuple[str, ...]
    files: tuple[tuple[str, str], ...]

    def file_map(self) -> dict[str, str]:
        return dict(self.files)

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "task_id": self.task_id,
            "status": list(self.status),
            "files": self.file_map(),
        }

    @classmethod
    def from_payload(cls, payload: object) -> RepositorySnapshot:
        if not isinstance(payload, dict):
            raise ValueError("Repository snapshot must be a JSON object.")
        task_id = payload.get("task_id")
        status = payload.get("status")
        files = payload.get("files")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("Repository snapshot task_id must be a non-empty string.")
        if not isinstance(status, list) or not all(isinstance(item, str) for item in status):
            raise ValueError("Repository snapshot status must be a string list.")
        if not isinstance(files, dict) or not all(
            isinstance(path, str) and isinstance(digest, str) for path, digest in files.items()
        ):
            raise ValueError("Repository snapshot files must map paths to digests.")
        return cls(
            task_id=task_id,
            status=tuple(status),
            files=tuple(sorted(files.items())),
        )


def _git_status(project_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        (
            "git",
            "-C",
            project_root.as_posix(),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ()
    return tuple(line for line in completed.stdout.splitlines() if line.strip())


def _hash_repository_file(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        return digest.hexdigest()
    if not path.exists():
        return "missing"
    if not path.is_file():
        return "non-file"
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_file_snapshot(project_root: Path) -> dict[str, str]:
    completed = subprocess.run(
        (
            "git",
            "-C",
            project_root.as_posix(),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ),
        check=False,
        capture_output=True,
    )
    snapshot: dict[str, str] = {}
    if completed.returncode != 0:
        for candidate in project_root.rglob("*"):
            relative = candidate.relative_to(project_root)
            if not relative.parts or relative.parts[0] in {".aidd", ".git"}:
                continue
            if candidate.is_file() or candidate.is_symlink():
                snapshot[relative.as_posix()] = _hash_repository_file(candidate)
        return snapshot
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative_path = raw_path.decode("utf-8", errors="surrogateescape")
        if relative_path == ".aidd" or relative_path.startswith(".aidd/"):
            continue
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Repository snapshot path escapes project root: {relative_path}.")
        snapshot[relative_path] = _hash_repository_file(project_root / relative_path)
    return snapshot


def capture_repository_snapshot(*, project_root: Path, task_id: str) -> RepositorySnapshot:
    return RepositorySnapshot(
        task_id=task_id,
        status=_git_status(project_root),
        files=tuple(sorted(repository_file_snapshot(project_root).items())),
    )


def repository_snapshot_payload(*, project_root: Path, task_id: str) -> dict[str, object]:
    return capture_repository_snapshot(
        project_root=project_root,
        task_id=task_id,
    ).to_payload()


def load_repository_snapshot(path: Path) -> RepositorySnapshot:
    return RepositorySnapshot.from_payload(json.loads(path.read_text(encoding="utf-8")))


def write_repository_snapshot(path: Path, snapshot: RepositorySnapshot) -> None:
    path.write_text(
        json.dumps(snapshot.to_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _section(markdown: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        markdown,
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group("body").strip() if match is not None else ""


def _reported_touched_paths(report: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in _section(report, "Touched files").splitlines():
        if not line.strip().startswith("-") or line.strip().casefold() == "- none":
            continue
        match = re.search(r"`([^`]+)`", line)
        if match is not None:
            paths.append(match.group(1).strip().strip("/"))
    return tuple(dict.fromkeys(paths))


def task_diff_evidence(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    project_root: Path,
    report: str | None,
) -> tuple[dict[str, object], tuple[str, ...]]:
    baseline_files = load_repository_snapshot(
        context.task_attempt_path / "repository-baseline.json"
    ).file_map()
    final_files = capture_repository_snapshot(
        project_root=project_root,
        task_id=context.task.id,
    ).file_map()
    observed = tuple(
        sorted(
            path
            for path in set(baseline_files) | set(final_files)
            if baseline_files.get(path) != final_files.get(path)
        )
    )
    reported = _reported_touched_paths(report or "")
    issues: list[str] = []
    missing_from_report = sorted(set(observed) - set(reported))
    unsupported_report_paths = sorted(set(reported) - set(observed))
    if missing_from_report:
        issues.append(
            "Observed task-local paths missing from implementation report: "
            + ", ".join(missing_from_report)
            + "."
        )
    if unsupported_report_paths:
        issues.append(
            "Implementation report paths absent from the task-local diff: "
            + ", ".join(unsupported_report_paths)
            + "."
        )
    allowed_scope = None
    try:
        allowed_scope = resolve_allowed_write_scope(workspace_root, work_item)
    except AllowedWriteScopeError as exc:
        issues.extend(f"Allowed write scope: {issue}" for issue in exc.issues)
    allowed_scope_paths = list(allowed_scope.prefixes) if allowed_scope is not None else []

    def _globally_allowed(path: str) -> bool:
        if allowed_scope is None:
            return True
        try:
            return allowed_scope.allows(path)
        except AllowedWriteScopeError:
            return False

    task_scope_paths = list(context.task.scope_paths)
    task_scope_outside_global = sorted(
        path
        for path in task_scope_paths
        if allowed_scope is not None and not _globally_allowed(path)
    )
    if task_scope_outside_global:
        issues.append(
            "Task-local scope is outside the global allowed write scope: "
            + ", ".join(task_scope_outside_global)
            + "."
        )
    out_of_scope = sorted(
        path
        for path in observed
        if not any(
            path == allowed or path.startswith(f"{allowed}/") for allowed in task_scope_paths
        )
        or (allowed_scope is not None and not _globally_allowed(path))
    )
    if out_of_scope:
        issues.append(
            "Observed task-local paths outside allowed write scope: "
            + ", ".join(out_of_scope)
            + "."
        )
    return (
        {
            "schema_version": 1,
            "task_id": context.task.id,
            "observed_touched_paths": list(observed),
            "reported_touched_paths": list(reported),
            "task_scope_paths": task_scope_paths,
            "allowed_scope_paths": allowed_scope_paths,
            "issues": issues,
        },
        tuple(issues),
    )


def task_validation_findings(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    project_root: Path,
    execution_state: StageExecutionState,
    discovery: StageOutputDiscovery,
) -> tuple[ValidationFinding, ...]:
    del discovery
    report_path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else None
    payload, issues = task_diff_evidence(
        context=context,
        workspace_root=workspace_root,
        work_item=work_item,
        project_root=project_root,
        report=report,
    )
    (execution_state.attempt_path / "task-diff.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    location = ValidationIssueLocation(
        workspace_relative_path=report_path.relative_to(workspace_root).as_posix()
    )
    return tuple(
        ValidationFinding(
            code=(
                "SEM-TASK-SCOPE-MISMATCH"
                if "scope" in issue.casefold()
                else "SEM-TASK-DIFF-MISMATCH"
            ),
            message=issue,
            severity="high",
            location=location,
        )
        for issue in issues
    )


__all__ = [
    "RepositorySnapshot",
    "capture_repository_snapshot",
    "load_repository_snapshot",
    "repository_file_snapshot",
    "repository_snapshot_payload",
    "task_diff_evidence",
    "task_validation_findings",
    "write_repository_snapshot",
]
