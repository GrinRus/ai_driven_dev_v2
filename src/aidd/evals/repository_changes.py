from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RepositoryChanges:
    changed_files: tuple[str, ...]
    tracked_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    diff_summary: str
    command_errors: tuple[str, ...]


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


__all__ = ["RepositoryChanges", "collect_repository_changes"]
