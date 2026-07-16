from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aidd.core import run_archive
from aidd.core.run_archive import (
    RunArchiveProtocolError,
    load_run_archive_decisions,
    persist_run_archive_decision,
    run_archive_decisions_root,
)
from aidd.core.run_inspection import resolve_run_metadata_summary
from aidd.core.run_store import create_run_manifest


def _manifest(
    workspace_root: Path, *, work_item: str = "WI-ARCHIVE", run_id: str = "run-1"
) -> Path:
    return create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target="qa",
        config_snapshot={"mode": "test"},
        workflow_stage_start="idea",
        workflow_stage_end="qa",
    )


def test_archive_decisions_are_append_only_and_leave_manifest_immutable(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest = _manifest(workspace_root)
    before = manifest.read_bytes()
    before_hash = hashlib.sha256(before).hexdigest()

    first = persist_run_archive_decision(
        workspace_root=workspace_root,
        work_item="WI-ARCHIVE",
        run_id="run-1",
        reason="First archive decision.",
        source="ui",
        changed_at_utc=datetime(2026, 7, 16, 12, 0, tzinfo=UTC),
    )
    second = persist_run_archive_decision(
        workspace_root=workspace_root,
        work_item="WI-ARCHIVE",
        run_id="run-1",
        reason="Confirmed after review.",
        source="cli",
        changed_at_utc=datetime(2026, 7, 16, 12, 1, tzinfo=UTC),
    )

    decisions = load_run_archive_decisions(
        workspace_root=workspace_root,
        work_item="WI-ARCHIVE",
        run_id="run-1",
    )
    summary = resolve_run_metadata_summary(
        workspace_root=workspace_root,
        work_item="WI-ARCHIVE",
        run_id="run-1",
    )

    assert first["archived"] is True
    assert second["source"] == "cli"
    assert [decision.decision_number for decision in decisions] == [1, 2]
    assert [decision.reason for decision in decisions] == [
        "First archive decision.",
        "Confirmed after review.",
    ]
    assert summary.archive.archived is True
    assert summary.archive.reason == "Confirmed after review."
    assert summary.archive.source == "cli"
    assert manifest.read_bytes() == before
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == before_hash


def test_archive_read_model_supports_legacy_manifest_state(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest = _manifest(workspace_root)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["operator_archive"] = {
        "archived": True,
        "archived_at_utc": "2026-07-16T12:00:00Z",
        "reason": "Legacy archive.",
        "source": "ui",
    }
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    summary = resolve_run_metadata_summary(
        workspace_root=workspace_root,
        work_item="WI-ARCHIVE",
        run_id="run-1",
    )

    assert summary.archive.archived is True
    assert summary.archive.reason == "Legacy archive."


def test_archive_read_model_rejects_malformed_overlay(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _manifest(workspace_root)
    root = run_archive_decisions_root(
        workspace_root=workspace_root,
        work_item="WI-ARCHIVE",
        run_id="run-1",
    )
    decision = root / "decision-0001"
    decision.mkdir(parents=True)
    (decision / "archive-decision.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(RunArchiveProtocolError, match="schema"):
        resolve_run_metadata_summary(
            workspace_root=workspace_root,
            work_item="WI-ARCHIVE",
            run_id="run-1",
        )


def test_archive_write_rejects_symlinked_run_overlay_escape(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _manifest(workspace_root)
    outside = tmp_path / "outside"
    outside.mkdir()
    archive_root = workspace_root / "reports" / "operator-overlays" / "WI-ARCHIVE" / "run-archive"
    archive_root.mkdir(parents=True)
    (archive_root / "run-1").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="resolve directly below"):
        persist_run_archive_decision(
            workspace_root=workspace_root,
            work_item="WI-ARCHIVE",
            run_id="run-1",
        )

    assert tuple(outside.iterdir()) == ()


def test_archive_write_failure_removes_new_partial_overlay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace_root = tmp_path / ".aidd"
    _manifest(workspace_root)

    def _fail_write(path: Path, payload: dict[str, object]) -> None:
        _ = path, payload
        raise OSError("injected archive write failure")

    monkeypatch.setattr(run_archive, "write_json_payload", _fail_write)

    with pytest.raises(OSError, match="injected"):
        persist_run_archive_decision(
            workspace_root=workspace_root,
            work_item="WI-ARCHIVE",
            run_id="run-1",
        )

    assert not (workspace_root / "reports" / "operator-overlays" / "WI-ARCHIVE").exists()
