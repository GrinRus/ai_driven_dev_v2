from __future__ import annotations

from pathlib import Path

from aidd.harness.scenarios import load_scenario


def test_load_scenario_applies_runtime_workspace_and_scenario_parameters(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd" / "workspace"
    manifest = tmp_path / "scenario.yaml"
    manifest.write_text(
        """
id: AIDD-TMP-001
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
