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
