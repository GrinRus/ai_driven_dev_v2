from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.scenarios import ScenarioManifestError, load_scenario


def test_load_scenario_applies_runtime_workspace_and_scenario_parameters(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd" / "workspace"
    manifest = tmp_path / "scenario.yaml"
    manifest.write_text(
        """
id: AIDD-TMP-001
scenario_class: deterministic-stage
feature_size: small
automation_lane: ci
canonical_runtime: ${runtime_id}
parameters:
  repo_name: typer
task: Run ${runtime_id} in ${workspace_root} for ${scenario.repo_name}
repo:
  url: https://github.com/fastapi/${scenario.repo_name}
  default_branch: master
setup:
  commands:
    - echo runtime=${runtime_id}
    - echo root=${workspace_root}
verify:
  commands:
    - echo repo=${scenario.repo_name}
feature_source:
  mode: fixture-seed
  selection_policy: fixture-owned
  fixture_path: harness/fixtures/minimal-python
  seed_id: substitution-fixture-seed
  summary: Use a deterministic fixture seed for substitution coverage.
stage_scope:
  start: plan
  end: plan
runtime_targets:
  - ${runtime_id}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    scenario = load_scenario(
        manifest,
        runtime_id="generic-cli",
        workspace_root=workspace_root,
    )

    assert scenario.task == (
        f"Run generic-cli in {workspace_root.resolve(strict=False).as_posix()} for typer"
    )
    assert scenario.repo.url == "https://github.com/fastapi/typer"
    assert scenario.setup.commands == (
        "echo runtime=generic-cli",
        f"echo root={workspace_root.resolve(strict=False).as_posix()}",
    )
    assert scenario.verify.commands == ("echo repo=typer",)
    assert scenario.runtime_targets == ("generic-cli",)


def test_load_scenario_rejects_unresolved_runtime_placeholder(tmp_path: Path) -> None:
    manifest = tmp_path / "scenario.yaml"
    manifest.write_text(
        """
id: AIDD-TMP-002
scenario_class: deterministic-stage
feature_size: small
automation_lane: ci
canonical_runtime: ${runtime_id}
task: Run ${runtime_id}
repo:
  url: https://github.com/fastapi/typer
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
  seed_id: unresolved-runtime-seed
  summary: Use a deterministic fixture seed for unresolved placeholder coverage.
stage_scope:
  start: plan
  end: plan
runtime_targets:
  - ${runtime_id}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ScenarioManifestError, match="unresolved placeholder\\(s\\): runtime_id"):
        load_scenario(manifest)
