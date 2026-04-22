from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from aidd.harness.repo_prep import prepare_scenario_repository, prepare_working_copy
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _build_scenario(
    repo_url: str,
    *,
    default_branch: str | None = None,
    revision: str | None = None,
) -> Scenario:
    return Scenario(
        scenario_id="AIDD-TEST-REPO-PREP",
        task="Prepare repo",
        repo=ScenarioRepoSource(
            url=repo_url,
            default_branch=default_branch,
            revision=revision,
        ),
        setup=ScenarioCommandSteps(commands=("echo setup",)),
        run=ScenarioRunConfig(
            stage_start=None,
            stage_end=None,
            runtime_targets=("generic-cli",),
            patch_budget_files=None,
            timeout_minutes=None,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=("echo verify",)),
        runtime_targets=("generic-cli",),
        raw={"id": "AIDD-TEST-REPO-PREP"},
    )


def _init_source_repo(path: Path) -> tuple[str, str]:
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", path.as_posix()])
    _run(["git", "config", "user.email", "tests@example.com"], cwd=path)
    _run(["git", "config", "user.name", "AIDD Tests"], cwd=path)
    (path / "README.md").write_text("init\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=path)
    _run(["git", "commit", "-m", "init"], cwd=path)
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    head = _run(["git", "rev-parse", "HEAD"], cwd=path)
    return branch, head


def test_prepare_scenario_repository_clones_repository(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    branch, source_head = _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri())

    prepared = prepare_scenario_repository(cache_root=tmp_path / "cache", scenario=scenario)

    assert prepared.action == "cloned"
    assert (prepared.repo_path / ".git").exists()
    assert prepared.resolved_revision
    assert (
        _run(["git", "rev-parse", f"refs/remotes/origin/{branch}"], cwd=prepared.repo_path)
        == source_head
    )


def test_prepare_scenario_repository_fetches_existing_clone(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    branch, _ = _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri())

    first = prepare_scenario_repository(cache_root=tmp_path / "cache", scenario=scenario)
    (source_repo / "README.md").write_text("updated\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=source_repo)
    _run(["git", "commit", "-m", "update"], cwd=source_repo)
    updated_head = _run(["git", "rev-parse", "HEAD"], cwd=source_repo)

    second = prepare_scenario_repository(cache_root=tmp_path / "cache", scenario=scenario)

    assert second.action == "fetched"
    assert second.repo_path == first.repo_path
    assert second.resolved_revision
    assert (
        _run(["git", "rev-parse", f"refs/remotes/origin/{branch}"], cwd=second.repo_path)
        == updated_head
    )


def test_prepare_scenario_repository_pins_explicit_revision(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _, first_head = _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri(), revision=first_head)

    prepared = prepare_scenario_repository(cache_root=tmp_path / "cache", scenario=scenario)

    assert prepared.resolved_revision == first_head
    assert _run(["git", "rev-parse", "HEAD"], cwd=prepared.repo_path) == first_head


def test_prepare_scenario_repository_rejects_invalid_revision(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri(), revision="deadbeef")

    with pytest.raises(
        RuntimeError,
        match="Failed to pin repository to revision 'deadbeef'",
    ):
        prepare_scenario_repository(cache_root=tmp_path / "cache", scenario=scenario)


def test_prepare_scenario_repository_pins_default_branch_when_revision_missing(
    tmp_path: Path,
) -> None:
    source_repo = tmp_path / "source"
    branch, source_head = _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri(), default_branch=branch)

    prepared = prepare_scenario_repository(cache_root=tmp_path / "cache", scenario=scenario)

    assert prepared.resolved_revision == source_head
    assert _run(["git", "rev-parse", "HEAD"], cwd=prepared.repo_path) == source_head
    assert _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=prepared.repo_path) == "HEAD"


def test_prepare_working_copy_clones_from_prepared_repository(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri())
    prepared_repository = prepare_scenario_repository(
        cache_root=tmp_path / "cache",
        scenario=scenario,
    )

    prepared_working_copy = prepare_working_copy(
        cache_root=tmp_path / "cache",
        scenario=scenario,
        prepared_repository=prepared_repository,
    )

    assert prepared_working_copy.action == "cloned"
    assert (prepared_working_copy.working_copy_path / ".git").exists()
    assert prepared_working_copy.resolved_revision == prepared_repository.resolved_revision
    assert (
        _run(["git", "rev-parse", "HEAD"], cwd=prepared_working_copy.working_copy_path)
        == prepared_repository.resolved_revision
    )


def test_prepare_working_copy_resets_dirty_state_between_invocations(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri())
    prepared_repository = prepare_scenario_repository(
        cache_root=tmp_path / "cache",
        scenario=scenario,
    )

    first = prepare_working_copy(
        cache_root=tmp_path / "cache",
        scenario=scenario,
        prepared_repository=prepared_repository,
    )
    readme_path = first.working_copy_path / "README.md"
    readme_path.write_text("dirty\n", encoding="utf-8")
    (first.working_copy_path / "TEMP.txt").write_text("temp\n", encoding="utf-8")
    assert _run(["git", "status", "--porcelain"], cwd=first.working_copy_path)

    second = prepare_working_copy(
        cache_root=tmp_path / "cache",
        scenario=scenario,
        prepared_repository=prepared_repository,
    )

    assert second.action == "reused"
    assert second.working_copy_path == first.working_copy_path
    assert second.resolved_revision == prepared_repository.resolved_revision
    assert readme_path.read_text(encoding="utf-8") == "init\n"
    assert not (second.working_copy_path / "TEMP.txt").exists()
    assert _run(["git", "status", "--porcelain"], cwd=second.working_copy_path) == ""


def test_prepare_scenario_repository_replaces_stale_non_git_cache_path(
    tmp_path: Path,
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri())

    first = prepare_scenario_repository(cache_root=tmp_path / "cache", scenario=scenario)
    shutil.rmtree(first.repo_path / ".git")
    (first.repo_path / "STALE.txt").write_text("stale\n", encoding="utf-8")

    second = prepare_scenario_repository(cache_root=tmp_path / "cache", scenario=scenario)

    assert second.action == "cloned"
    assert second.repo_path == first.repo_path
    assert (second.repo_path / ".git").exists()
    assert not (second.repo_path / "STALE.txt").exists()


def test_prepare_working_copy_removes_transient_git_lock_file(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri())
    prepared_repository = prepare_scenario_repository(
        cache_root=tmp_path / "cache",
        scenario=scenario,
    )
    prepared_working_copy = prepare_working_copy(
        cache_root=tmp_path / "cache",
        scenario=scenario,
        prepared_repository=prepared_repository,
    )

    lock_path = prepared_working_copy.working_copy_path / ".git" / "index.lock"
    lock_path.write_text("locked\n", encoding="utf-8")

    refreshed_working_copy = prepare_working_copy(
        cache_root=tmp_path / "cache",
        scenario=scenario,
        prepared_repository=prepared_repository,
    )

    assert refreshed_working_copy.action == "reused"
    assert refreshed_working_copy.working_copy_path == prepared_working_copy.working_copy_path
    assert not lock_path.exists()


def test_prepare_working_copy_replaces_stale_non_git_path(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario = _build_scenario(source_repo.as_uri())
    prepared_repository = prepare_scenario_repository(
        cache_root=tmp_path / "cache",
        scenario=scenario,
    )
    first_working_copy = prepare_working_copy(
        cache_root=tmp_path / "cache",
        scenario=scenario,
        prepared_repository=prepared_repository,
    )

    shutil.rmtree(first_working_copy.working_copy_path / ".git")
    stale_file = first_working_copy.working_copy_path / "STALE.txt"
    stale_file.write_text("stale\n", encoding="utf-8")

    refreshed_working_copy = prepare_working_copy(
        cache_root=tmp_path / "cache",
        scenario=scenario,
        prepared_repository=prepared_repository,
    )

    assert refreshed_working_copy.action == "cloned"
    assert refreshed_working_copy.working_copy_path == first_working_copy.working_copy_path
    assert (refreshed_working_copy.working_copy_path / ".git").exists()
    assert not stale_file.exists()
