from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from aidd.core.models.run import RepairExtensionGrant
from aidd.core.run_inspection import resolve_run_metadata_summary
from aidd.core.run_lookup import latest_run_id
from aidd.core.run_store import (
    create_run_manifest,
    load_run_manifest,
    persist_repair_extension_grant,
    persist_repair_history_entry,
    persist_stage_status,
)

_REMOVE = object()


def _tree(root: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        *(('schema_version', value) for value in (_REMOVE, None, True, 1.0, "1", 0, 999)),
        ("run_id", "other-run"),
        ("work_item_id", "other-work-item"),
        ("runtime_id", None),
        ("adapter_id", _REMOVE),
        ("adapter_id", ""),
        ("stage_target", _REMOVE),
        ("workflow_bounds", _REMOVE),
        ("workflow_bounds", {}),
        ("workflow_bounds", {"start": None}),
        ("workflow_bounds", {"start": 1, "end": None}),
        ("config_snapshot", _REMOVE),
        ("config_snapshot", []),
        ("repository_git_sha", _REMOVE),
        ("repository_git_sha", 1),
        ("resource_source", _REMOVE),
        ("resource_revision", _REMOVE),
        ("resource_root", _REMOVE),
        ("prompt_pack_provenance", _REMOVE),
        ("prompt_pack_provenance", {}),
        ("prompt_pack_provenance", [None]),
        ("prompt_pack_provenance", [{"path": "prompt.md"}]),
        ("created_at_utc", _REMOVE),
        ("updated_at_utc", _REMOVE),
        ("lineage", None),
    ],
)
@pytest.mark.parametrize("operation", ("reuse", "status", "repair-history", "repair-grant"))
def test_invalid_manifest_stops_mutation_without_rewriting_state(
    tmp_path: Path, field: str, value: object, operation: str,
) -> None:
    workspace = tmp_path / ".aidd"
    manifest = create_run_manifest(workspace, "WI-1", "run-1", "generic-cli", "plan", {})
    persist_stage_status(workspace, "WI-1", "run-1", "plan", "executing")
    payload = json.loads(manifest.read_text())
    if value is _REMOVE:
        payload.pop(field)
    else:
        payload[field] = value
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    before = _tree(workspace)

    with pytest.raises(ValueError, match=field):
        if operation == "reuse":
            create_run_manifest(workspace, "WI-1", "run-1", "generic-cli", "plan", {})
        elif operation == "status":
            persist_stage_status(workspace, "WI-1", "run-1", "review", "executing")
        elif operation == "repair-history":
            persist_repair_history_entry(
                workspace, "WI-1", "run-1", "plan",
                attempt_number=1, trigger="repair", outcome="failed",
            )
        else:
            persist_repair_extension_grant(
                workspace, "WI-1", "run-1", "plan",
                grant=RepairExtensionGrant(
                    work_item_id="WI-1", run_id="run-1", stage="plan",
                    validator_report_path="workitems/WI-1/stages/plan/validator-report.md",
                    validator_report_sha256="a" * 64,
                    repair_brief_path="workitems/WI-1/stages/plan/repair-brief.md",
                    repair_brief_sha256="b" * 64, configuration_identity="config-1",
                    author="operator", authorized_at_utc="2026-09-06T00:00:00Z",
                    reason="One bounded correction.",
                ),
            )

    assert _tree(workspace) == before
    assert latest_run_id(workspace, "WI-1") is None
    with pytest.raises(ValueError, match=field):
        resolve_run_metadata_summary(workspace, "WI-1", run_id="run-1")
    assert _tree(workspace) == before


def test_current_manifest_round_trip_preserves_nullable_provenance_and_default_adapter(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / ".aidd"
    resource_root = tmp_path / "custom-resources"
    resource_root.mkdir()
    shutil.copytree(Path(__file__).parents[2] / "prompt-packs", resource_root / "prompt-packs")
    manifest = create_run_manifest(
        workspace, "WI-1", "run-1", "generic-cli", "plan", {}, repository_root=resource_root,
    )
    payload = load_run_manifest(workspace, "WI-1", "run-1")
    assert payload is not None
    assert payload["repository_git_sha"] is None
    assert payload["resource_revision"] is None
    assert payload["workflow_bounds"] == {"start": None, "end": None}
    assert payload["adapter_id"] == "generic-cli"
    assert payload["config_snapshot"] == {}
    before = manifest.read_bytes()
    assert create_run_manifest(workspace, "WI-1", "run-1", "generic-cli", "plan", {}) == manifest
    assert manifest.read_bytes() == before
    summary = resolve_run_metadata_summary(workspace, "WI-1", run_id="run-1")
    assert summary.repository_git_sha is None
    assert summary.resource_revision is None
    assert summary.workflow_stage_start is None
    assert summary.workflow_stage_end is None
    assert summary.adapter_id == "generic-cli"
