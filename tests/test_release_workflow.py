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


def test_release_workflow_has_pypi_install_verification_job() -> None:
    jobs = _release_workflow_jobs()
    assert "verify-pypi-install" in jobs

    verify_job = jobs["verify-pypi-install"]
    assert "publish-pypi" in _normalize_needs(verify_job.get("needs"))

    run_blocks = "\n".join(
        step["run"]
        for step in verify_job.get("steps", [])
        if isinstance(step, dict) and isinstance(step.get("run"), str)
    )
    assert "ATTEMPTS=10" in run_blocks
    assert "BACKOFF_SECONDS=30" in run_blocks
    assert "python -m pipx install --force" in run_blocks
    assert "aidd --version" in run_blocks
    assert "aidd doctor" in run_blocks
