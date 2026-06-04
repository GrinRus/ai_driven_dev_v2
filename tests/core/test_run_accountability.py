from __future__ import annotations

import json
from pathlib import Path

from aidd.core.run_accountability import resolve_run_accountability
from aidd.core.run_store import create_run_manifest, persist_stage_status


def test_run_accountability_exposes_prompt_config_and_stage_graph(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-acc",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "ui-workflow", "runtime_command": "codex exec"},
        workflow_stage_start="idea",
        workflow_stage_end="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-acc",
        stage="plan",
        status="succeeded",
    )

    view = resolve_run_accountability(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-acc",
    )

    assert view.run_id == "run-acc"
    assert view.runtime_id == "codex"
    assert view.workflow_stage_start == "idea"
    assert view.workflow_stage_end == "plan"
    assert view.config_snapshot["mode"] == "ui-workflow"
    assert view.prompt_pack_provenance
    assert view.prompt_pack_provenance[0].sha256
    assert view.stage_graph[:3] == ("idea", "research", "plan")
    assert view.stages[0].stage == "plan"
    assert view.stages[0].status == "succeeded"


def test_run_accountability_warns_for_legacy_prompt_provenance(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest_path = create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-legacy",
        runtime_id="generic-cli",
        stage_target="idea",
        config_snapshot={"mode": "legacy"},
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["prompt_pack_provenance"] = []
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    view = resolve_run_accountability(
        workspace_root=workspace_root,
        work_item="WI-ACC",
        run_id="run-legacy",
    )

    assert view.prompt_pack_provenance == ()
    assert any("no prompt-pack provenance" in warning for warning in view.warnings)
