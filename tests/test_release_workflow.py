from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aidd.core.contracts import repo_root_from


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _release_workflow() -> dict[str, Any]:
    release_workflow_path = _repo_root() / ".github" / "workflows" / "release.yml"
    release_workflow = yaml.safe_load(release_workflow_path.read_text(encoding="utf-8"))
    assert isinstance(release_workflow, dict)
    return release_workflow


def _release_workflow_jobs() -> dict[str, Any]:
    release_workflow = _release_workflow()
    return release_workflow["jobs"]


def _normalize_needs(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _job_run_blocks(job: dict[str, Any]) -> str:
    return "\n".join(
        step["run"]
        for step in job.get("steps", [])
        if isinstance(step, dict) and isinstance(step.get("run"), str)
    )


def test_release_workflow_uses_published_release_event_not_tag_push() -> None:
    workflow = _release_workflow()
    triggers = workflow["on"]

    assert "push" not in triggers
    assert triggers["release"]["types"] == ["published"]
    assert "workflow_dispatch" in triggers


def test_release_workflow_has_pypi_install_verification_job() -> None:
    jobs = _release_workflow_jobs()
    assert "verify-pypi-install" in jobs

    verify_job = jobs["verify-pypi-install"]
    assert "publish-pypi" in _normalize_needs(verify_job.get("needs"))

    run_blocks = _job_run_blocks(verify_job)
    assert "ATTEMPTS=10" in run_blocks
    assert "BACKOFF_SECONDS=30" in run_blocks
    assert "python -m pipx install --force" in run_blocks
    assert "aidd --version" in run_blocks
    assert "aidd doctor" in run_blocks


def test_release_workflow_runs_deterministic_quality_before_publish() -> None:
    jobs = _release_workflow_jobs()
    assert "quality" in jobs

    quality_job = jobs["quality"]
    assert quality_job["strategy"]["matrix"]["python-version"] == ["3.12", "3.13", "3.14"]

    quality_run_blocks = _job_run_blocks(quality_job)
    assert "uv sync --locked --extra dev" in quality_run_blocks
    assert "uv run --extra dev ruff check ." in quality_run_blocks
    assert "uv run --extra dev python -m mypy src scripts" in quality_run_blocks
    assert "uv run --extra dev pytest -q" in quality_run_blocks

    build_job = jobs["build"]
    assert "quality" in _normalize_needs(build_job.get("needs"))
    assert "build" in _normalize_needs(jobs["publish-pypi"].get("needs"))


def test_release_workflow_validates_release_branch_and_tag_before_build() -> None:
    jobs = _release_workflow_jobs()
    build_job = jobs["build"]

    run_blocks = _job_run_blocks(build_job)
    assert "Validate release branch and PyPI tag" in yaml.safe_dump(build_job)
    assert "github.event_name == 'release'" in yaml.safe_dump(build_job)
    assert "github.event.release.tag_name" in yaml.safe_dump(build_job)
    assert 'EXPECTED_RELEASE_BRANCH="release/${RELEASE_TAG}"' in run_blocks
    assert "refs/heads/${EXPECTED_RELEASE_BRANCH}" in run_blocks
    assert "refs/remotes/origin/${EXPECTED_RELEASE_BRANCH}" in run_blocks
    assert "refs/tags/${RELEASE_TAG}" in run_blocks
    assert "${RELEASE_TAG}^{commit}" in run_blocks
    assert "project.version" in run_blocks
    assert "does not point at '${EXPECTED_RELEASE_BRANCH}'" in run_blocks


def test_release_workflow_publishes_only_for_github_release_event() -> None:
    jobs = _release_workflow_jobs()

    for job_id in (
        "publish-pypi",
        "verify-pypi-install",
        "verify-uv-tool-install",
    ):
        assert jobs[job_id]["if"] == "github.event_name == 'release'"


def test_release_workflow_has_uv_tool_install_verification_job() -> None:
    jobs = _release_workflow_jobs()
    assert "verify-uv-tool-install" in jobs

    verify_job = jobs["verify-uv-tool-install"]
    assert "verify-pypi-install" in _normalize_needs(verify_job.get("needs"))

    run_blocks = _job_run_blocks(verify_job)
    assert "ATTEMPTS=10" in run_blocks
    assert "BACKOFF_SECONDS=30" in run_blocks
    assert "uv tool install --force" in run_blocks
    assert "uv tool run --from" in run_blocks
    assert "aidd --version" in run_blocks
    assert "aidd doctor" in run_blocks


def test_release_workflow_does_not_publish_container_images_for_alpha() -> None:
    jobs = _release_workflow_jobs()
    assert "publish-container" not in jobs
    assert "verify-ghcr-install" not in jobs

    serialized = yaml.safe_dump({"jobs": jobs}, sort_keys=False)
    assert "docker/login-action" not in serialized
    assert "docker/metadata-action" not in serialized
    assert "docker/build-push-action" not in serialized
    assert "docker pull" not in serialized
    assert "docker run" not in serialized
    assert "ghcr.io" not in serialized


def test_release_workflow_does_not_run_live_e2e() -> None:
    jobs = _release_workflow_jobs()
    assert "verify-published-live-e2e" not in jobs

    serialized = yaml.safe_dump({"jobs": jobs}, sort_keys=False)
    assert "harness/scenarios/live/" not in serialized
    assert "live_e2e_black_box" not in serialized
    assert "AIDD_EVAL_PUBLISHED_PACKAGE_SPEC" not in serialized
    assert "aidd eval run" not in serialized
    assert "AIDD_EVAL_CLAUDE_CODE_COMMAND" not in serialized
    assert "AIDD_EVAL_CODEX_COMMAND" not in serialized
    assert "AIDD_EVAL_OPENCODE_COMMAND" not in serialized
