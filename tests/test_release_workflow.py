from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aidd.core.contracts import repo_root_from


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _release_workflow_jobs() -> dict[str, Any]:
    release_workflow_path = _repo_root() / ".github" / "workflows" / "release.yml"
    release_workflow = yaml.safe_load(release_workflow_path.read_text(encoding="utf-8"))
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


def test_release_workflow_has_published_live_e2e_job() -> None:
    jobs = _release_workflow_jobs()
    assert "verify-published-live-e2e" in jobs

    verify_job = jobs["verify-published-live-e2e"]
    assert "verify-uv-tool-install" in _normalize_needs(verify_job.get("needs"))

    run_blocks = _job_run_blocks(verify_job)
    assert "uv sync --extra dev" in run_blocks
    assert "AIDD_EVAL_PUBLISHED_PACKAGE_SPEC" in run_blocks
    assert "sqlite-utils-detect-types-header-only.yaml" in run_blocks
    assert "--runtime generic-cli" in run_blocks
    env_text = "\n".join(
        str(step.get("env", {}))
        for step in verify_job.get("steps", [])
        if isinstance(step, dict)
    )
    assert "release_live_proof_runtime.py" in env_text


def test_release_workflow_has_ghcr_verification_job() -> None:
    jobs = _release_workflow_jobs()
    assert "verify-ghcr-install" in jobs

    verify_job = jobs["verify-ghcr-install"]
    normalized_needs = _normalize_needs(verify_job.get("needs"))
    assert "publish-container" in normalized_needs
    assert "verify-uv-tool-install" in normalized_needs
    assert "verify-published-live-e2e" in normalized_needs

    run_blocks = _job_run_blocks(verify_job)
    assert "ATTEMPTS=10" in run_blocks
    assert "BACKOFF_SECONDS=30" in run_blocks
    assert "docker pull" in run_blocks
    assert "docker run --rm" in run_blocks
    assert "--version" in run_blocks
    assert "doctor" in run_blocks
