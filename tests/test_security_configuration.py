from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aidd.core.contracts import repo_root_from


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _read_yaml(relative_path: str) -> dict[str, Any]:
    path = _repo_root() / relative_path
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_dependabot_tracks_project_and_release_dependencies() -> None:
    config = _read_yaml(".github/dependabot.yml")
    updates = config["updates"]
    assert isinstance(updates, list)

    ecosystems = {
        update["package-ecosystem"]
        for update in updates
        if isinstance(update, dict) and "package-ecosystem" in update
    }

    assert "uv" in ecosystems
    assert "github-actions" in ecosystems
    assert "pip" in ecosystems

    pip_updates = [
        update
        for update in updates
        if isinstance(update, dict) and update.get("package-ecosystem") == "pip"
    ]
    assert len(pip_updates) == 1
    assert pip_updates[0]["directory"] == "/.github"
    assert pip_updates[0]["groups"]["release-tools"]["patterns"] == ["pipx"]


def test_uv_lockfile_is_committable_for_dependabot_updates() -> None:
    repo_root = _repo_root()

    assert (repo_root / "uv.lock").is_file()
    ignored_patterns = (repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "uv.lock" not in {pattern.strip() for pattern in ignored_patterns}


def test_security_workflow_has_static_analysis_and_scorecard_jobs() -> None:
    workflow = _read_yaml(".github/workflows/security.yml")
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)

    assert "dependency-review" in jobs
    assert "codeql" in jobs
    assert "scorecard" in jobs

    serialized = yaml.safe_dump(workflow, sort_keys=False)
    assert "dependency-review-action@" in serialized
    assert "github/codeql-action/init@" in serialized
    assert "github/codeql-action/analyze@" in serialized
    assert "ossf/scorecard-action@" in serialized


def test_ci_and_release_workflows_use_locked_uv_sync() -> None:
    workflow_paths = sorted((_repo_root() / ".github" / "workflows").glob("*.yml"))
    assert workflow_paths

    for workflow_path in workflow_paths:
        workflow_text = workflow_path.read_text(encoding="utf-8")
        assert "uv sync --extra dev" not in workflow_text, workflow_path.as_posix()
        if "uv sync" in workflow_text:
            assert "uv sync --locked --extra dev" in workflow_text, workflow_path.as_posix()


def test_ci_and_release_workflows_pin_the_uv_executable() -> None:
    for workflow_name in ("ci.yml", "release.yml"):
        workflow = _read_yaml(f".github/workflows/{workflow_name}")
        setup_uv_steps = [
            step
            for job in workflow["jobs"].values()
            for step in job.get("steps", ())
            if isinstance(step, dict)
            and str(step.get("uses", "")).startswith("astral-sh/setup-uv@")
        ]

        assert setup_uv_steps, workflow_name
        for step in setup_uv_steps:
            assert step["with"]["version"] == "0.12.8", workflow_name


def test_makefile_install_uses_locked_uv_sync() -> None:
    makefile_text = (_repo_root() / "Makefile").read_text(encoding="utf-8")
    assert "uv sync --locked --extra dev" in makefile_text
    assert "uv sync --extra dev" not in makefile_text


def test_github_actions_workflows_do_not_run_live_e2e() -> None:
    workflow_paths = sorted((_repo_root() / ".github" / "workflows").glob("*.yml"))
    assert workflow_paths

    forbidden_markers = (
        "harness/scenarios/live/",
        "live_e2e_black_box",
        "AIDD_EVAL_",
        "OPENAI_API_KEY",
    )

    for workflow_path in workflow_paths:
        workflow_text = workflow_path.read_text(encoding="utf-8")
        for marker in forbidden_markers:
            assert marker not in workflow_text, f"{workflow_path.as_posix()} contains {marker}"
