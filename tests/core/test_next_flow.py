from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.core.next_flow import (
    CloneFlowDraftRequest,
    FollowUpDraftRequest,
    FollowUpSourceSelection,
    NextFlowLaunchPreflightRequest,
    create_clone_flow_draft,
    create_follow_up_work_item_draft,
    validate_next_flow_launch_preflight,
)
from aidd.core.run_store import create_run_manifest, run_manifest_path
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT


def test_create_follow_up_work_item_draft_writes_durable_context_with_references(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    source_artifact = (
        workspace_root
        / "workitems"
        / "WI-SOURCE"
        / "stages"
        / "qa"
        / "qa-report.md"
    )
    source_artifact.parent.mkdir(parents=True, exist_ok=True)
    source_artifact.write_text(
        "# QA Report\n\n## Finding\n\nRaw source body that must not be copied.\n",
        encoding="utf-8",
    )

    result = create_follow_up_work_item_draft(
        FollowUpDraftRequest(
            workspace_root=workspace_root,
            source_work_item="WI-SOURCE",
            source_run_id="run-source",
            new_work_item="WI-FOLLOW-UP",
            title="Fix risky mobile QA gap",
            selections=(
                FollowUpSourceSelection(
                    kind="qa-finding",
                    title="QAF-1 Mobile viewport evidence is missing",
                    source_path="workitems/WI-SOURCE/stages/qa/qa-report.md",
                    stage="qa",
                    note="Add mobile viewport proof before launch.",
                ),
            ),
        )
    )

    request_text = result.request_path.read_text(encoding="utf-8")
    assert result.work_item == "WI-FOLLOW-UP"
    assert result.source_artifact_paths == (
        "workitems/WI-SOURCE/stages/qa/qa-report.md",
    )
    assert "QAF-1 Mobile viewport evidence is missing" in request_text
    assert "Add mobile viewport proof before launch." in request_text
    assert "`workitems/WI-SOURCE/stages/qa/qa-report.md`" in request_text
    assert "Raw source body that must not be copied." not in request_text
    assert result.context_seed.user_request_path.exists()
    assert result.context_seed.intake_path.exists()

    metadata = json.loads(
        (
            workspace_root / "workitems" / "WI-FOLLOW-UP" / "work-item.json"
        ).read_text(encoding="utf-8")
    )
    assert metadata["lineage"] == {
        "source_run_id": "run-source",
        "source_work_item_id": "WI-SOURCE",
    }


def test_create_follow_up_work_item_draft_rejects_missing_source_artifacts(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        create_follow_up_work_item_draft(
            FollowUpDraftRequest(
                workspace_root=tmp_path / ".aidd",
                source_work_item="WI-SOURCE",
                source_run_id="run-source",
                new_work_item="WI-FOLLOW-UP",
                title="Fix risky mobile QA gap",
                selections=(
                    FollowUpSourceSelection(
                        kind="failed-evidence",
                        title="Missing artifact",
                        source_path="workitems/WI-SOURCE/stages/qa/missing.md",
                    ),
                ),
            )
        )


def test_create_follow_up_work_item_draft_rejects_absolute_source_paths(
    tmp_path: Path,
) -> None:
    source_artifact = tmp_path / ".aidd" / "workitems" / "WI-SOURCE" / "qa-report.md"
    source_artifact.parent.mkdir(parents=True, exist_ok=True)
    source_artifact.write_text("# QA\n", encoding="utf-8")

    with pytest.raises(ValueError, match="workspace-relative"):
        create_follow_up_work_item_draft(
            FollowUpDraftRequest(
                workspace_root=tmp_path / ".aidd",
                source_work_item="WI-SOURCE",
                source_run_id="run-source",
                new_work_item="WI-FOLLOW-UP",
                title="Fix risky mobile QA gap",
                selections=(
                    FollowUpSourceSelection(
                        kind="manual-request",
                        title="Manual request",
                        source_path=source_artifact.as_posix(),
                    ),
                ),
            )
        )


def test_create_follow_up_work_item_draft_accepts_manual_request_without_source_path(
    tmp_path: Path,
) -> None:
    result = create_follow_up_work_item_draft(
        FollowUpDraftRequest(
            workspace_root=tmp_path / ".aidd",
            source_work_item="WI-SOURCE",
            source_run_id="run-source",
            new_work_item="WI-FOLLOW-UP",
            title="Capture operator follow-up note",
            selections=(
                FollowUpSourceSelection(
                    kind="manual-request",
                    title="Operator requested a smaller follow-up",
                    source_path=None,
                    note="Split the risky rollout into a separate task.",
                ),
            ),
        )
    )

    request_text = result.request_path.read_text(encoding="utf-8")
    assert result.source_artifact_paths == ()
    assert "- Source artifact: manual operator request only" in request_text
    assert "Split the risky rollout into a separate task." in request_text


def test_create_clone_flow_draft_writes_editable_configuration_from_source_run(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-SOURCE",
        run_id="run-source",
        runtime_id="codex",
        adapter_id="codex-adapter",
        stage_target="qa",
        workflow_stage_start="idea",
        workflow_stage_end="qa",
        config_snapshot={"mode": "test"},
    )
    manifest_path = run_manifest_path(workspace_root, "WI-SOURCE", "run-source")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "repository_git_sha": "a" * 40,
            "resource_root": "/repo/contracts-source",
            "resource_revision": "resource-rev-1",
            "prompt_pack_provenance": [
                {
                    "path": "prompt-packs/stages/qa/run.md",
                    "sha256": "b" * 64,
                }
            ],
            "lineage": {
                "baseline_id": "baseline-run",
                "baseline_label": "main before handoff",
            },
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    result = create_clone_flow_draft(
        CloneFlowDraftRequest(
            workspace_root=workspace_root,
            source_work_item="WI-SOURCE",
            source_run_id="run-source",
            new_work_item="WI-CLONE",
            title="Retry the completed flow with a different implementation strategy",
        )
    )

    draft_text = result.draft_path.read_text(encoding="utf-8")
    assert result.work_item == "WI-CLONE"
    assert result.config.runtime_id == "codex"
    assert result.config.adapter_id == "codex-adapter"
    assert result.config.stage_target == "qa"
    assert result.config.workflow_stage_start == "idea"
    assert result.config.workflow_stage_end == "qa"
    assert result.config.resource_root == "/repo/contracts-source"
    assert result.config.repository_git_sha == "a" * 40
    assert result.config.resource_revision == "resource-rev-1"
    assert result.config.baseline_id == "baseline-run"
    assert result.config.baseline_label == "main before handoff"
    assert result.config.prompt_pack_provenance[0].path == "prompt-packs/stages/qa/run.md"
    assert "## Editable configuration" in draft_text
    assert "- Runtime id: `codex`" in draft_text
    assert "- Resource/contracts root: `/repo/contracts-source`" in draft_text
    assert "- `prompt-packs/stages/qa/run.md` sha256" in draft_text
    assert result.context_seed.user_request_path.exists()
    assert not (workspace_root / "reports" / "runs" / "WI-CLONE").exists()

    metadata = json.loads(
        (workspace_root / "workitems" / "WI-CLONE" / "work-item.json").read_text(
            encoding="utf-8"
        )
    )
    assert metadata["lineage"] == {
        "baseline_id": "baseline-run",
        "baseline_label": "main before handoff",
        "source_run_id": "run-source",
        "source_work_item_id": "WI-SOURCE",
    }


def test_create_clone_flow_draft_rejects_missing_source_run(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="No runs found|missing"):
        create_clone_flow_draft(
            CloneFlowDraftRequest(
                workspace_root=tmp_path / ".aidd",
                source_work_item="WI-SOURCE",
                source_run_id="run-source",
                new_work_item="WI-CLONE",
                title="Clone missing run",
            )
        )


def test_validate_next_flow_launch_preflight_passes_for_explicit_available_inputs(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-SOURCE",
        run_id="run-source",
        runtime_id="codex",
        stage_target="qa",
        config_snapshot={"mode": "preflight-test"},
    )

    result = validate_next_flow_launch_preflight(
        NextFlowLaunchPreflightRequest(
            workspace_root=workspace_root,
            source_work_item="WI-SOURCE",
            source_run_id="run-source",
            runtime_id="codex",
            contracts_root=DEFAULT_STAGE_CONTRACTS_ROOT,
            baseline_id="run-source",
        )
    )

    assert result.status == "pass"
    assert result.can_launch is True
    assert result.blocking_codes == ()
    assert result.warning_codes == ()
    assert result.resolved_baseline_id == "run-source"
    assert result.error_payload == {}
    assert {check.code for check in result.checks} >= {
        "workspace-writable",
        "runtime-supported",
        "contracts-available",
        "source-run-exists",
        "baseline-available",
    }


def test_validate_next_flow_launch_preflight_warns_when_baseline_falls_back_to_source(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-SOURCE",
        run_id="run-source",
        runtime_id="codex",
        stage_target="qa",
        config_snapshot={"mode": "preflight-test"},
    )

    result = validate_next_flow_launch_preflight(
        NextFlowLaunchPreflightRequest(
            workspace_root=workspace_root,
            source_work_item="WI-SOURCE",
            source_run_id="run-source",
            runtime_id="codex",
            contracts_root=DEFAULT_STAGE_CONTRACTS_ROOT,
        )
    )

    assert result.status == "warning"
    assert result.can_launch is True
    assert result.blocking_codes == ()
    assert result.warning_codes == ("baseline-fallback-source-run",)
    assert result.resolved_baseline_id == "run-source"
    assert result.error_payload == {}


def test_validate_next_flow_launch_preflight_blocks_missing_baseline(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-SOURCE",
        run_id="run-source",
        runtime_id="codex",
        stage_target="qa",
        config_snapshot={"mode": "preflight-test"},
    )

    result = validate_next_flow_launch_preflight(
        NextFlowLaunchPreflightRequest(
            workspace_root=workspace_root,
            source_work_item="WI-SOURCE",
            source_run_id="run-source",
            runtime_id="codex",
            contracts_root=DEFAULT_STAGE_CONTRACTS_ROOT,
            baseline_id="missing-baseline",
        )
    )

    assert result.status == "blocked"
    assert result.can_launch is False
    assert result.blocking_codes == ("baseline-missing",)
    assert result.warning_codes == ()
    assert result.resolved_baseline_id == "missing-baseline"
    assert result.error_payload["error"] == "next-flow launch preflight blocked"
    assert result.error_payload["blocking_codes"] == ["baseline-missing"]


def test_validate_next_flow_launch_preflight_blocks_unsafe_missing_launch_inputs(
    tmp_path: Path,
) -> None:
    result = validate_next_flow_launch_preflight(
        NextFlowLaunchPreflightRequest(
            workspace_root=tmp_path / ".aidd",
            source_work_item="WI-SOURCE",
            source_run_id="run-source",
            runtime_id="unknown-runtime",
            contracts_root=tmp_path / "missing" / "contracts" / "stages",
        )
    )

    assert result.status == "blocked"
    assert result.can_launch is False
    assert set(result.blocking_codes) == {
        "workspace-missing",
        "unsupported-runtime",
        "contracts-missing",
        "source-run-missing",
    }
    assert result.resolved_baseline_id is None
    assert result.error_payload["status"] == "blocked"
    assert set(result.error_payload["blocking_codes"]) == set(result.blocking_codes)
