from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aidd.harness.repo_prep import prepare_scenario_repository
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
