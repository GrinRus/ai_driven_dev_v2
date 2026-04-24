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


def test_load_live_scenario_rejects_missing_feature_source(tmp_path: Path) -> None:
    live_root = tmp_path / "harness" / "scenarios" / "live"
    live_root.mkdir(parents=True)
    manifest = _write_manifest(
        live_root / "scenario.yaml",
        """
id: AIDD-LIVE-TEST-001
task: Exercise live manifest validation
repo:
  url: https://github.com/example/repo
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
quality:
  commands:
    - echo quality
  rubric_profile: live-full
  require_review_status: approved
  allowed_qa_verdicts:
    - ready
    - ready-with-risks
  code_review_required: true
stage_scope:
  start: idea
  end: qa
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="missing required key: feature_source"):
        load_scenario(manifest)


def test_load_live_scenario_rejects_non_full_flow_stage_scope(tmp_path: Path) -> None:
    live_root = tmp_path / "harness" / "scenarios" / "live"
    live_root.mkdir(parents=True)
    manifest = _write_manifest(
        live_root / "scenario.yaml",
        """
id: AIDD-LIVE-TEST-002
task: Exercise live manifest validation
repo:
  url: https://github.com/example/repo
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
feature_source:
  mode: curated-issue-pool
  selection_policy: first-listed
  issues:
    - id: 1
      title: Example issue
      url: https://github.com/example/repo/issues/1
      summary: Example summary
quality:
  commands:
    - echo quality
  rubric_profile: live-full
  require_review_status: approved
  allowed_qa_verdicts:
    - ready
    - ready-with-risks
  code_review_required: true
stage_scope:
  start: plan
  end: qa
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="explicit full-flow stage scope"):
        load_scenario(manifest)


def test_load_live_scenario_rejects_invalid_quality_block(tmp_path: Path) -> None:
    live_root = tmp_path / "harness" / "scenarios" / "live"
    live_root.mkdir(parents=True)
    manifest = _write_manifest(
        live_root / "scenario.yaml",
        """
id: AIDD-LIVE-TEST-003
task: Exercise live manifest validation
repo:
  url: https://github.com/example/repo
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
feature_source:
  mode: curated-issue-pool
  selection_policy: first-listed
  issues:
    - id: 1
      title: Example issue
      url: https://github.com/example/repo/issues/1
      summary: Example summary
quality:
  commands:
    - echo quality
  rubric_profile: live-full
  require_review_status: rejected
  allowed_qa_verdicts:
    - ready
  code_review_required: true
stage_scope:
  start: idea
  end: qa
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="quality.require_review_status"):
        load_scenario(manifest)
