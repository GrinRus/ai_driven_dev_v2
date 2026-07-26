from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aidd.application.stage_reconciliation import (
    TerminalStageReconciliationRequest,
    reconcile_terminal_stage,
)
from aidd.core.run_store import (
    create_run_manifest,
    load_stage_metadata,
    persist_stage_status,
    run_manifest_path,
    run_stage_metadata_path,
)

WORK_ITEM = "WI-RECONCILE"
RUN_ID = "run-reconcile"
STAGE = "idea"
CHANGED_AT = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def _prepare_stage(workspace_root: Path, *, status: str = "executing") -> Path:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=WORK_ITEM,
        run_id=RUN_ID,
        runtime_id="generic-cli",
        stage_target=STAGE,
        config_snapshot={"runtime_command": "runtime"},
    )
    return persist_stage_status(
        workspace_root=workspace_root,
        work_item=WORK_ITEM,
        run_id=RUN_ID,
        stage=STAGE,
        status=status,
        changed_at_utc=datetime(2026, 7, 26, 11, 0, tzinfo=UTC),
    )


def _request(workspace_root: Path, *, expected_state: str = "executing"):
    return TerminalStageReconciliationRequest(
        workspace_root=workspace_root,
        work_item=WORK_ITEM,
        run_id=RUN_ID,
        stage=STAGE,
        expected_state=expected_state,
        reason="stage-command-timeout",
    )


def test_reconcile_terminal_stage_is_idempotent_and_byte_stable(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    metadata_path = _prepare_stage(workspace_root)
    manifest_path = run_manifest_path(workspace_root, WORK_ITEM, RUN_ID)

    first = reconcile_terminal_stage(_request(workspace_root), changed_at_utc=CHANGED_AT)
    metadata = load_stage_metadata(workspace_root, WORK_ITEM, RUN_ID, STAGE)

    assert first.disposition == "reconciled"
    assert first.reconciled is True
    assert metadata is not None
    assert metadata.status == "failed"
    assert [entry.status for entry in metadata.status_history] == ["executing", "failed"]
    stable_bytes = (
        metadata_path.read_bytes(),
        manifest_path.read_bytes(),
        first.evidence_path.read_bytes(),
    )

    second = reconcile_terminal_stage(_request(workspace_root), changed_at_utc=CHANGED_AT)

    assert second.to_payload() == first.to_payload()
    assert (
        metadata_path.read_bytes(),
        manifest_path.read_bytes(),
        first.evidence_path.read_bytes(),
    ) == stable_bytes


@pytest.mark.parametrize("status", ("succeeded", "failed"))
def test_reconcile_terminal_stage_does_not_rewrite_terminal_stage(
    tmp_path: Path,
    status: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    metadata_path = _prepare_stage(workspace_root, status=status)
    before = metadata_path.read_bytes()

    result = reconcile_terminal_stage(_request(workspace_root), changed_at_utc=CHANGED_AT)

    assert result.disposition == "already-terminal"
    assert result.reconciled is False
    assert metadata_path.read_bytes() == before


def test_reconcile_terminal_stage_does_not_rewrite_expected_state_mismatch(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    metadata_path = _prepare_stage(workspace_root, status="preparing")
    before = metadata_path.read_bytes()

    result = reconcile_terminal_stage(_request(workspace_root), changed_at_utc=CHANGED_AT)

    assert result.disposition == "expected-state-mismatch"
    assert result.reconciled is False
    assert metadata_path.read_bytes() == before


def test_reconcile_terminal_stage_does_not_rewrite_identity_mismatch(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    metadata_path = _prepare_stage(workspace_root)
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["run_id"] = "wrong-run"
    metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    before = metadata_path.read_bytes()

    result = reconcile_terminal_stage(_request(workspace_root), changed_at_utc=CHANGED_AT)

    assert result.disposition == "metadata-identity-mismatch"
    assert result.reconciled is False
    assert metadata_path.read_bytes() == before


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("work_item", "../WI"),
        ("run_id", "/tmp/run"),
        ("stage", "not-a-stage"),
        ("expected_state", "failed"),
        ("reason", "not canonical"),
    ),
)
def test_reconciliation_request_rejects_noncanonical_identity(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    values = {
        "workspace_root": tmp_path / ".aidd",
        "work_item": WORK_ITEM,
        "run_id": RUN_ID,
        "stage": STAGE,
        "expected_state": "executing",
        "reason": "stage-command-timeout",
    }
    values[field] = value

    with pytest.raises(ValueError):
        TerminalStageReconciliationRequest(**values)


def test_reconcile_terminal_stage_reports_missing_metadata_without_creating_it(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    result = reconcile_terminal_stage(_request(workspace_root), changed_at_utc=CHANGED_AT)

    assert result.disposition == "metadata-missing"
    assert result.reconciled is False
    assert not run_stage_metadata_path(workspace_root, WORK_ITEM, RUN_ID, STAGE).exists()
