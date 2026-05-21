from __future__ import annotations

import subprocess
from pathlib import Path
from subprocess import TimeoutExpired

import pytest

from aidd.evals.repository_changes import collect_repository_changes


def _run(args: tuple[str, ...], *, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _init_git_repo(repo_root: Path) -> None:
    _run(("git", "init"), cwd=repo_root)
    _run(("git", "config", "user.email", "tests@example.com"), cwd=repo_root)
    _run(("git", "config", "user.name", "AIDD Tests"), cwd=repo_root)
    (repo_root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    _run(("git", "add", "tracked.txt"), cwd=repo_root)
    _run(("git", "commit", "-m", "baseline"), cwd=repo_root)


def test_collect_repository_changes_includes_tracked_and_untracked_files(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "tracked.txt").write_text("changed\n", encoding="utf-8")
    (tmp_path / "new.txt").write_text("new\n", encoding="utf-8")
    (tmp_path / ".aidd").mkdir()
    (tmp_path / ".aidd" / "generated.md").write_text("ignore\n", encoding="utf-8")

    changes = collect_repository_changes(tmp_path)

    assert changes.changed_files == ("tracked.txt", "new.txt")
    assert changes.tracked_files == ("tracked.txt",)
    assert changes.untracked_files == ("new.txt",)
    assert "tracked.txt" in changes.diff_summary
    assert "new.txt" in changes.diff_summary
    assert ".aidd/generated.md" not in changes.changed_files
    assert changes.command_errors == tuple()


def test_collect_repository_changes_records_git_execution_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)

    def raise_os_error(*_args: object, **_kwargs: object) -> None:
        raise OSError("git unavailable")

    monkeypatch.setattr(subprocess, "run", raise_os_error)

    changes = collect_repository_changes(tmp_path)

    assert changes.changed_files == tuple()
    assert changes.tracked_files == tuple()
    assert changes.untracked_files == tuple()
    assert len(changes.command_errors) == 3
    assert all("failed to execute" in error for error in changes.command_errors)
    assert "Git change collection errors:" in changes.diff_summary


def test_collect_repository_changes_records_git_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)

    def raise_timeout(command: object, **_kwargs: object) -> None:
        raise TimeoutExpired(command, timeout=10)

    monkeypatch.setattr(subprocess, "run", raise_timeout)

    changes = collect_repository_changes(tmp_path)

    assert changes.changed_files == tuple()
    assert len(changes.command_errors) == 3
    assert all("timed out after 10s" in error for error in changes.command_errors)
