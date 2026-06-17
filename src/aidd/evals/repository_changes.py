from __future__ import annotations

import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

LIVE_KNOWN_HARNESS_UNTRACKED_FILES = ("aidd.example.toml",)
LIVE_ALLOWED_AIDD_UNTRACKED_PREFIXES = (
    ".aidd/workitems/",
    ".aidd/reports/",
    ".aidd/config/",
    ".aidd/traces/",
    ".aidd/harness-cache/",
)
LIVE_IGNORED_WORKSPACE_POLLUTION_PREFIXES = (
    ".coverage",
    ".mypy_cache/",
    ".pdm-build/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".tox/",
    ".venv/",
    "build/",
    "coverage/",
    "dist/",
    "node_modules/",
    "venv/",
)
LIVE_IGNORED_WORKSPACE_POLLUTION_DIR_NAMES = frozenset({"__pycache__"})
LIVE_IGNORED_WORKSPACE_POLLUTION_FILE_SUFFIXES = (".pyc", ".pyo")


@dataclass(frozen=True, slots=True)
class RepositoryChanges:
    changed_files: tuple[str, ...]
    tracked_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    diff_summary: str
    command_errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LiveWorkspaceSnapshot:
    tracked_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    status_short: str
    command_errors: tuple[str, ...]
    ignored_files: tuple[str, ...] = tuple()

    def to_payload(self) -> dict[str, object]:
        return {
            "tracked_files": list(self.tracked_files),
            "untracked_files": list(self.untracked_files),
            "ignored_files": list(self.ignored_files),
            "status_short": self.status_short,
            "command_errors": list(self.command_errors),
        }


@dataclass(frozen=True, slots=True)
class LiveWorkspaceFinding:
    kind: str
    severity: str
    path: str
    message: str
    manual_quality_implication: str

    def to_payload(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
            "manual_quality_implication": self.manual_quality_implication,
        }


@dataclass(frozen=True, slots=True)
class LiveWorkspaceClassification:
    tracked_files: tuple[str, ...]
    baseline_untracked_files: tuple[str, ...]
    new_untracked_files: tuple[str, ...]
    baseline_ignored_files: tuple[str, ...]
    new_ignored_files: tuple[str, ...]
    setup_baseline_ignored_churn_files: tuple[str, ...]
    known_harness_files: tuple[str, ...]
    unexpected_non_aidd_untracked_files: tuple[str, ...]
    unexpected_top_level_workitems_files: tuple[str, ...]
    unexpected_aidd_internal_files: tuple[str, ...]
    unexpected_ignored_workspace_files: tuple[str, ...]
    non_gating_findings: tuple[LiveWorkspaceFinding, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "tracked_files": list(self.tracked_files),
            "baseline_untracked_files": list(self.baseline_untracked_files),
            "new_untracked_files": list(self.new_untracked_files),
            "baseline_ignored_files": list(self.baseline_ignored_files),
            "new_ignored_files": list(self.new_ignored_files),
            "setup_baseline_ignored_churn_files": list(
                self.setup_baseline_ignored_churn_files
            ),
            "known_harness_files": list(self.known_harness_files),
            "unexpected_non_aidd_untracked_files": list(
                self.unexpected_non_aidd_untracked_files
            ),
            "unexpected_top_level_workitems_files": list(
                self.unexpected_top_level_workitems_files
            ),
            "unexpected_aidd_internal_files": list(self.unexpected_aidd_internal_files),
            "unexpected_ignored_workspace_files": list(
                self.unexpected_ignored_workspace_files
            ),
        }


def _run_git(*, repo_root: Path, args: tuple[str, ...]) -> tuple[str | None, str | None]:
    command_label = f"git {' '.join(args)}"
    try:
        completed = subprocess.run(
            ("git", *args),
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return None, f"{command_label} timed out after 10s"
    except OSError as exc:
        return None, f"{command_label} failed to execute: {exc}"
    if completed.returncode == 0:
        return completed.stdout, None
    stderr = completed.stderr.strip() or completed.stdout.strip() or "no command output"
    return None, f"{command_label} failed: {stderr}"


def _repo_relative_paths(output: str | None) -> tuple[str, ...]:
    if output is None:
        return tuple()
    return tuple(
        line.strip()
        for line in output.splitlines()
        if line.strip() and not line.strip().startswith(".aidd/")
    )


def _repo_relative_paths_including_aidd(output: str | None) -> tuple[str, ...]:
    if output is None:
        return tuple()
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def _ignored_paths_from_status(output: str | None) -> tuple[str, ...]:
    if output is None:
        return tuple()
    ignored_paths = []
    for line in output.splitlines():
        if line.startswith("!! "):
            ignored_path = line[3:].strip()
            if ignored_path:
                ignored_paths.append(ignored_path)
    return tuple(ignored_paths)


def _dedupe_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(paths))


def collect_repository_changes(repo_root: Path) -> RepositoryChanges:
    tracked_output, tracked_error = _run_git(
        repo_root=repo_root,
        args=("diff", "--name-only", "HEAD", "--", "."),
    )
    untracked_output, untracked_error = _run_git(
        repo_root=repo_root,
        args=("ls-files", "--others", "--exclude-standard", "--", "."),
    )
    stat_output, stat_error = _run_git(
        repo_root=repo_root,
        args=("diff", "--stat", "HEAD", "--", "."),
    )

    tracked_files = _repo_relative_paths(tracked_output)
    untracked_files = _repo_relative_paths(untracked_output)
    summary_parts: list[str] = []
    if stat_output is not None and stat_output.strip():
        summary_parts.append(stat_output.strip())
    if untracked_files:
        summary_parts.append(
            "Untracked files:\n" + "\n".join(f"  {path}" for path in untracked_files)
        )

    command_errors = tuple(
        error for error in (tracked_error, untracked_error, stat_error) if error is not None
    )
    if command_errors:
        summary_parts.append(
            "Git change collection errors:\n"
            + "\n".join(f"- {error}" for error in command_errors)
        )

    return RepositoryChanges(
        changed_files=_dedupe_paths((*tracked_files, *untracked_files)),
        tracked_files=tracked_files,
        untracked_files=untracked_files,
        diff_summary="\n\n".join(summary_parts),
        command_errors=command_errors,
    )


def collect_live_workspace_snapshot(repo_root: Path) -> LiveWorkspaceSnapshot:
    tracked_output, tracked_error = _run_git(
        repo_root=repo_root,
        args=("diff", "--name-only", "HEAD", "--", "."),
    )
    untracked_output, untracked_error = _run_git(
        repo_root=repo_root,
        args=("ls-files", "--others", "--exclude-standard", "--", "."),
    )
    status_output, status_error = _run_git(
        repo_root=repo_root,
        args=("status", "--short", "--untracked-files=all"),
    )
    ignored_status_output, ignored_status_error = _run_git(
        repo_root=repo_root,
        args=("status", "--ignored", "--short", "--untracked-files=all"),
    )

    command_errors = tuple(
        error
        for error in (
            tracked_error,
            untracked_error,
            status_error,
            ignored_status_error,
        )
        if error is not None
    )
    return LiveWorkspaceSnapshot(
        tracked_files=_dedupe_paths(_repo_relative_paths_including_aidd(tracked_output)),
        untracked_files=_dedupe_paths(_repo_relative_paths_including_aidd(untracked_output)),
        status_short="" if status_output is None else status_output.rstrip(),
        command_errors=command_errors,
        ignored_files=_dedupe_paths(_ignored_paths_from_status(ignored_status_output)),
    )


def live_workspace_snapshot_from_payload(
    payload: Mapping[str, object],
) -> LiveWorkspaceSnapshot:
    status_short = payload.get("status_short")
    return LiveWorkspaceSnapshot(
        tracked_files=_string_tuple(payload.get("tracked_files")),
        untracked_files=_string_tuple(payload.get("untracked_files")),
        status_short=status_short if isinstance(status_short, str) else "",
        command_errors=_string_tuple(payload.get("command_errors")),
        ignored_files=_string_tuple(payload.get("ignored_files")),
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return tuple()
    return tuple(item for item in value if isinstance(item, str) and item)


def _is_top_level_workitems_path(path: str) -> bool:
    return path == "workitems" or path.startswith("workitems/")


def _is_allowed_aidd_untracked_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in LIVE_ALLOWED_AIDD_UNTRACKED_PREFIXES)


def _is_ignored_workspace_pollution_path(path: str) -> bool:
    if any(
        path == prefix.rstrip("/") or path.startswith(prefix)
        for prefix in LIVE_IGNORED_WORKSPACE_POLLUTION_PREFIXES
    ):
        return True
    parts = Path(path).parts
    if any(part in LIVE_IGNORED_WORKSPACE_POLLUTION_DIR_NAMES for part in parts):
        return True
    return path.endswith(LIVE_IGNORED_WORKSPACE_POLLUTION_FILE_SUFFIXES)


def _ignored_workspace_root(path: str) -> str:
    if "/" not in path:
        return path
    return path.split("/", 1)[0] + "/"


def _is_under_ignored_workspace_root(path: str, roots: set[str]) -> bool:
    for root in roots:
        if root.endswith("/"):
            if path.startswith(root):
                return True
            continue
        if path == root:
            return True
    return False


def classify_live_workspace_changes(
    *,
    baseline_snapshot: LiveWorkspaceSnapshot,
    final_snapshot: LiveWorkspaceSnapshot,
) -> LiveWorkspaceClassification:
    baseline_untracked = set(baseline_snapshot.untracked_files)
    baseline_ignored = set(baseline_snapshot.ignored_files)
    known_harness_files = tuple(
        path
        for path in final_snapshot.untracked_files
        if path in LIVE_KNOWN_HARNESS_UNTRACKED_FILES
    )
    known_harness_file_set = set(known_harness_files)
    new_untracked_files = tuple(
        path
        for path in final_snapshot.untracked_files
        if path not in baseline_untracked and path not in known_harness_file_set
    )
    unexpected_non_aidd_untracked_files = tuple(
        path for path in new_untracked_files if not path.startswith(".aidd/")
    )
    unexpected_top_level_workitems_files = tuple(
        path for path in unexpected_non_aidd_untracked_files if _is_top_level_workitems_path(path)
    )
    unexpected_aidd_internal_files = tuple(
        path
        for path in new_untracked_files
        if path.startswith(".aidd/") and not _is_allowed_aidd_untracked_path(path)
    )
    new_ignored_files = tuple(
        path for path in final_snapshot.ignored_files if path not in baseline_ignored
    )
    baseline_ignored_workspace_roots = {
        _ignored_workspace_root(path)
        for path in baseline_snapshot.ignored_files
        if _is_ignored_workspace_pollution_path(path)
    }
    setup_baseline_ignored_churn_files = tuple(
        path
        for path in new_ignored_files
        if _is_ignored_workspace_pollution_path(path)
        and _is_under_ignored_workspace_root(path, baseline_ignored_workspace_roots)
    )
    setup_baseline_ignored_churn_set = set(setup_baseline_ignored_churn_files)
    unexpected_ignored_workspace_files = tuple(
        path
        for path in new_ignored_files
        if _is_ignored_workspace_pollution_path(path)
        and path not in setup_baseline_ignored_churn_set
    )

    findings: list[LiveWorkspaceFinding] = []
    for error in (*baseline_snapshot.command_errors, *final_snapshot.command_errors):
        findings.append(
            LiveWorkspaceFinding(
                kind="target-workspace-git-evidence-error",
                severity="warning",
                path="",
                message=error,
                manual_quality_implication=(
                    "Manual quality review must treat target workspace evidence as incomplete."
                ),
            )
        )
    for path in unexpected_top_level_workitems_files:
        findings.append(
            LiveWorkspaceFinding(
                kind="unexpected-top-level-workitems-artifact",
                severity="high",
                path=path,
                message=(
                    "A stage/control artifact was written under top-level `workitems/` "
                    "instead of the canonical `.aidd/workitems/` workspace."
                ),
                manual_quality_implication=(
                    "Treat this as severe deliverable pollution; a clean manual "
                    "deliverable decision should normally be `not-counted` unless the "
                    "artifact is removed before final quality review."
                ),
            )
        )
    top_level_workitems = set(unexpected_top_level_workitems_files)
    for path in unexpected_non_aidd_untracked_files:
        if path in top_level_workitems:
            continue
        findings.append(
            LiveWorkspaceFinding(
                kind="unexpected-non-aidd-untracked-file",
                severity="warning",
                path=path,
                message=(
                    "A new untracked file outside `.aidd/` appeared after the setup baseline."
                ),
                manual_quality_implication=(
                    "Manual code review must inspect whether this file is intended "
                    "deliverable scope, setup residue, or product pollution."
                ),
            )
        )
    for path in unexpected_aidd_internal_files:
        findings.append(
            LiveWorkspaceFinding(
                kind="unexpected-aidd-internal-scratch-file",
                severity="medium",
                path=path,
                message=(
                    "A new `.aidd/` file was written outside the expected workspace, "
                    "report, config, traces, or harness-cache areas."
                ),
                manual_quality_implication=(
                    "Manual artifact review should treat this as artifact hygiene debt "
                    "and inspect whether stage prompts left temporary scratch evidence behind."
                ),
            )
        )
    for path in unexpected_ignored_workspace_files:
        findings.append(
            LiveWorkspaceFinding(
                kind="unexpected-ignored-workspace-artifact",
                severity="warning",
                path=path,
                message=(
                    "A new ignored workspace artifact appeared after the setup "
                    "baseline."
                ),
                manual_quality_implication=(
                    "Manual quality review should inspect whether verification or "
                    "debugging left local environment, cache, coverage, or build "
                    "artifacts in the target repository."
                ),
            )
        )

    return LiveWorkspaceClassification(
        tracked_files=final_snapshot.tracked_files,
        baseline_untracked_files=baseline_snapshot.untracked_files,
        new_untracked_files=new_untracked_files,
        baseline_ignored_files=baseline_snapshot.ignored_files,
        new_ignored_files=new_ignored_files,
        setup_baseline_ignored_churn_files=setup_baseline_ignored_churn_files,
        known_harness_files=known_harness_files,
        unexpected_non_aidd_untracked_files=unexpected_non_aidd_untracked_files,
        unexpected_top_level_workitems_files=unexpected_top_level_workitems_files,
        unexpected_aidd_internal_files=unexpected_aidd_internal_files,
        unexpected_ignored_workspace_files=unexpected_ignored_workspace_files,
        non_gating_findings=tuple(findings),
    )


__all__ = [
    "LiveWorkspaceClassification",
    "LiveWorkspaceFinding",
    "LiveWorkspaceSnapshot",
    "RepositoryChanges",
    "classify_live_workspace_changes",
    "collect_live_workspace_snapshot",
    "collect_repository_changes",
    "live_workspace_snapshot_from_payload",
]
