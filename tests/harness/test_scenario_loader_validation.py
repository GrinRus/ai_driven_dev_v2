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
scenario_class: deterministic-stage
feature_size: small
automation_lane: ci
canonical_runtime: generic-cli
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
scenario_class: deterministic-stage
feature_size: small
automation_lane: ci
canonical_runtime: generic-cli
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
scenario_class: deterministic-stage
feature_size: small
automation_lane: ci
canonical_runtime: generic-cli
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
scenario_class: deterministic-stage
feature_size: small
automation_lane: ci
canonical_runtime: generic-cli
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
scenario_class: live-full-flow
feature_size: small
automation_lane: manual
canonical_runtime: generic-cli
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
scenario_class: live-full-flow
feature_size: small
automation_lane: manual
canonical_runtime: generic-cli
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
scenario_class: live-full-flow
feature_size: small
automation_lane: manual
canonical_runtime: generic-cli
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


def test_load_scenario_rejects_live_manifest_marked_for_ci(tmp_path: Path) -> None:
    live_root = tmp_path / "harness" / "scenarios" / "live"
    live_root.mkdir(parents=True)
    manifest = _write_manifest(
        live_root / "scenario.yaml",
        """
id: AIDD-LIVE-TEST-004
scenario_class: live-full-flow
feature_size: small
automation_lane: ci
canonical_runtime: generic-cli
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
  start: idea
  end: qa
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="automation_lane: manual"):
        load_scenario(manifest)


def test_load_scenario_rejects_large_ci_scenario(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "scenario.yaml",
        """
id: AIDD-DET-TEST-001
scenario_class: deterministic-workflow
feature_size: large
automation_lane: ci
canonical_runtime: generic-cli
task: Example task
repo:
  url: https://github.com/example/repo
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
feature_source:
  mode: fixture-seed
  selection_policy: fixture-owned
  fixture_path: harness/fixtures/minimal-python
  seed_id: det-large
  summary: Example deterministic seed
stage_scope:
  start: idea
  end: qa
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="feature_size: large"):
        load_scenario(manifest)


def test_load_scenario_rejects_deterministic_manifest_without_fixture_seed(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "scenario.yaml",
        """
id: AIDD-DET-TEST-002
scenario_class: deterministic-workflow
feature_size: medium
automation_lane: ci
canonical_runtime: generic-cli
task: Example task
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
stage_scope:
  start: plan
  end: tasklist
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="feature_source.mode: fixture-seed"):
        load_scenario(manifest)


def test_load_scenario_rejects_live_manifest_without_curated_issue_pool(tmp_path: Path) -> None:
    live_root = tmp_path / "harness" / "scenarios" / "live"
    live_root.mkdir(parents=True)
    manifest = _write_manifest(
        live_root / "scenario.yaml",
        """
id: AIDD-LIVE-TEST-005
scenario_class: live-full-flow
feature_size: small
automation_lane: manual
canonical_runtime: generic-cli
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
  mode: fixture-seed
  selection_policy: fixture-owned
  fixture_path: harness/fixtures/minimal-python
  seed_id: wrong-live-seed
  summary: Wrong seed type
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

    with pytest.raises(ScenarioManifestError, match="curated-issue-pool"):
        load_scenario(manifest)


def test_load_scenario_rejects_noncanonical_runtime_outside_runtime_targets(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "scenario.yaml",
        """
id: AIDD-DET-TEST-003
scenario_class: deterministic-stage
feature_size: small
automation_lane: ci
canonical_runtime: codex
task: Example task
repo:
  url: https://github.com/example/repo
setup:
  commands:
    - echo setup
verify:
  commands:
    - echo verify
feature_source:
  mode: fixture-seed
  selection_policy: fixture-owned
  fixture_path: harness/fixtures/minimal-python
  seed_id: det-stage
  summary: Example deterministic seed
stage_scope:
  start: plan
  end: plan
runtime_targets:
  - generic-cli
""".strip()
        + "\n",
    )

    with pytest.raises(ScenarioManifestError, match="canonical_runtime"):
        load_scenario(manifest)
