from __future__ import annotations

import fcntl
import re
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from aidd.harness.scenarios import Scenario


class RepoPreparationError(RuntimeError):
    """Raised when repository preparation fails."""


@dataclass(frozen=True, slots=True)
class PreparedRepository:
    repo_path: Path
    action: str
    resolved_revision: str


@dataclass(frozen=True, slots=True)
class PreparedWorkingCopy:
    working_copy_path: Path
    action: str
    resolved_revision: str


def _repo_slug(repo_url: str) -> str:
    normalized = repo_url.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[: -len(".git")]
    cleaned = re.sub(r"^[a-zA-Z]+://", "", normalized)
    cleaned = cleaned.replace(":", "/")
    parts = [part for part in cleaned.split("/") if part]
    if len(parts) >= 2:
        return f"{parts[-2]}__{parts[-1]}"
    if parts:
        return parts[-1]
    raise RepoPreparationError(f"Cannot derive repository slug from URL: {repo_url}")


def _run_git(args: list[str], *, cwd: Path | None = None) -> None:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return
    stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown git error"
    raise RepoPreparationError(stderr)


def _git_stdout(args: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown git error"
        raise RepoPreparationError(stderr)
    return completed.stdout.strip()


def _remove_tree(path: Path) -> None:
    try:
        shutil.rmtree(path)
    except OSError as exc:
        raise RepoPreparationError(
            f"Failed to remove stale path '{path.as_posix()}': {exc}"
        ) from exc


def _cleanup_transient_git_files(repo_path: Path) -> None:
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        return
    for lock_name in ("index.lock", "HEAD.lock", "packed-refs.lock", "shallow.lock"):
        lock_path = git_dir / lock_name
        if lock_path.exists():
            try:
                lock_path.unlink()
            except OSError as exc:
                raise RepoPreparationError(
                    f"Failed to remove transient git lock '{lock_path.as_posix()}': {exc}"
                ) from exc


@contextmanager
def _acquire_cache_lock(*, lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            except OSError as exc:
                raise RepoPreparationError(
                    f"Failed to acquire harness cache lock '{lock_path.as_posix()}': {exc}"
                ) from exc
            try:
                yield
            finally:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                except OSError:
                    # Lock release on close is best-effort; close still guarantees unlock semantics.
                    pass
    except OSError as exc:
        raise RepoPreparationError(
            f"Failed to open harness cache lock '{lock_path.as_posix()}': {exc}"
        ) from exc


def _pin_repository_revision(*, repo_path: Path, scenario: Scenario) -> None:
    target_revision = scenario.repo.revision
    if target_revision:
        try:
            _run_git(["checkout", "--detach", "--force", target_revision], cwd=repo_path)
        except RepoPreparationError as exc:
            raise RepoPreparationError(
                f"Failed to pin repository to revision '{target_revision}': {exc}"
            ) from exc
        return

    target_branch = scenario.repo.default_branch
    if target_branch:
        try:
            _run_git(
                ["checkout", "--detach", "--force", f"origin/{target_branch}"],
                cwd=repo_path,
            )
        except RepoPreparationError as exc:
            raise RepoPreparationError(
                f"Failed to pin repository to branch '{target_branch}': {exc}"
            ) from exc


def prepare_workspace(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_scenario_repository(*, cache_root: Path, scenario: Scenario) -> PreparedRepository:
    repo_cache_root = cache_root / "repos"
    repo_cache_root.mkdir(parents=True, exist_ok=True)

    slug = _repo_slug(scenario.repo.url)
    repo_path = repo_cache_root / slug
    repo_lock_path = cache_root / ".locks" / f"repo-{slug}.lock"

    with _acquire_cache_lock(lock_path=repo_lock_path):
        if repo_path.exists():
            if not (repo_path / ".git").exists():
                _remove_tree(repo_path)
            else:
                _cleanup_transient_git_files(repo_path)
                _run_git(["fetch", "--prune", "origin"], cwd=repo_path)
                _pin_repository_revision(repo_path=repo_path, scenario=scenario)
                return PreparedRepository(
                    repo_path=repo_path,
                    action="fetched",
                    resolved_revision=_git_stdout(["rev-parse", "HEAD"], cwd=repo_path),
                )

        _run_git(["clone", "--origin", "origin", scenario.repo.url, repo_path.as_posix()])
        _pin_repository_revision(repo_path=repo_path, scenario=scenario)
        return PreparedRepository(
            repo_path=repo_path,
            action="cloned",
            resolved_revision=_git_stdout(["rev-parse", "HEAD"], cwd=repo_path),
        )


def prepare_working_copy(
    *,
    cache_root: Path,
    scenario: Scenario,
    prepared_repository: PreparedRepository,
) -> PreparedWorkingCopy:
    working_copy_root = cache_root / "workdirs"
    working_copy_root.mkdir(parents=True, exist_ok=True)
    slug = _repo_slug(scenario.repo.url)
    working_copy_path = working_copy_root / slug
    workdir_lock_path = cache_root / ".locks" / f"workdir-{slug}.lock"

    with _acquire_cache_lock(lock_path=workdir_lock_path):
        action = "reused"
        if working_copy_path.exists():
            if not (working_copy_path / ".git").exists():
                _remove_tree(working_copy_path)
                action = "cloned"
        else:
            action = "cloned"
        if action == "cloned":
            _run_git(
                [
                    "clone",
                    "--origin",
                    "origin",
                    prepared_repository.repo_path.as_posix(),
                    working_copy_path.as_posix(),
                ]
            )

        _cleanup_transient_git_files(working_copy_path)
        _run_git(
            ["checkout", "--detach", "--force", prepared_repository.resolved_revision],
            cwd=working_copy_path,
        )
        _run_git(["reset", "--hard", prepared_repository.resolved_revision], cwd=working_copy_path)
        _run_git(["clean", "-fdx"], cwd=working_copy_path)

        return PreparedWorkingCopy(
            working_copy_path=working_copy_path,
            action=action,
            resolved_revision=_git_stdout(["rev-parse", "HEAD"], cwd=working_copy_path),
        )
