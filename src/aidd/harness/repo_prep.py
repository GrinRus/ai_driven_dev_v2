from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from aidd.harness.scenarios import Scenario


class RepoPreparationError(RuntimeError):
    """Raised when repository preparation fails."""


@dataclass(frozen=True, slots=True)
class PreparedRepository:
    repo_path: Path
    action: str


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


def prepare_workspace(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_scenario_repository(*, cache_root: Path, scenario: Scenario) -> PreparedRepository:
    repo_cache_root = cache_root / "repos"
    repo_cache_root.mkdir(parents=True, exist_ok=True)

    repo_path = repo_cache_root / _repo_slug(scenario.repo.url)
    if repo_path.exists():
        if not (repo_path / ".git").exists():
            raise RepoPreparationError(
                f"Repository cache path exists but is not a git repository: {repo_path.as_posix()}"
            )
        _run_git(["fetch", "--prune", "origin"], cwd=repo_path)
        return PreparedRepository(repo_path=repo_path, action="fetched")

    _run_git(["clone", "--origin", "origin", scenario.repo.url, repo_path.as_posix()])
    return PreparedRepository(repo_path=repo_path, action="cloned")
