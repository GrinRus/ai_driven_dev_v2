from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.scenarios import ScenarioManifestError, load_scenario


def _write_manifest(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_load_scenario_rejects_missing_required_keys(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "scenario.yaml",
        """
id: AIDD-TEST-001
repo:
  url: https://github.com/example/repo
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="missing required key: task"):
        load_scenario(manifest)


def test_load_scenario_rejects_invalid_runtime_targets(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "scenario.yaml",
        """
id: AIDD-TEST-001
task: Example task
repo:
  url: https://github.com/example/repo
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
runtime_targets: generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="key 'runtime_targets'"):
        load_scenario(manifest)


def test_load_scenario_rejects_invalid_setup_commands(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "scenario.yaml",
        """
id: AIDD-TEST-001
task: Example task
repo:
  url: https://github.com/example/repo
setup:
  commands:
    - ""
verify:
  commands:
    - echo verify
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="key 'setup\\.commands'"):
        load_scenario(manifest)


def test_load_scenario_rejects_missing_repo_url(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "scenario.yaml",
        """
id: AIDD-TEST-001
task: Example task
repo:
  default_branch: main
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="missing required key: url"):
        load_scenario(manifest)


def test_load_live_scenario_requires_pinned_repo_revision(tmp_path: Path) -> None:
    live_root = tmp_path / "harness" / "scenarios" / "live"
    live_root.mkdir(parents=True, exist_ok=True)
    manifest = _write_manifest(
        live_root / "scenario.yaml",
        """
id: AIDD-LIVE-TEST-001
task: Example live task
repo:
  url: https://github.com/example/repo
  default_branch: main
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="must pin 'repo\\.revision'"):
        load_scenario(manifest)


def test_load_scenario_rejects_non_sha_repo_revision(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "scenario.yaml",
        """
id: AIDD-TEST-002
task: Example task
repo:
  url: https://github.com/example/repo
  revision: not-a-sha
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="40-character git commit sha"):
        load_scenario(manifest)
