from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aidd.adapters.runtime_evidence import (
    RuntimeAdapterOutcome,
    RuntimeEvidenceCommitRequest,
    RuntimeStopReason,
    commit_runtime_evidence,
)
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    write_attempt_artifact_index,
)
from aidd.core.runtime_launch_history import resolve_runtime_launch_history
from aidd.core.workspace import seed_work_item_metadata


def _attempt(
    workspace_root: Path,
    *,
    run_id: str,
    runtime_id: str,
    outcome: RuntimeAdapterOutcome,
    timestamp: datetime | None,
) -> Path:
    seed_work_item_metadata(root=workspace_root, work_item="WI-HISTORY")
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
        run_id=run_id,
        runtime_id=runtime_id,
        stage_target="idea",
        config_snapshot={},
    )
    attempt = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
        run_id=run_id,
        stage="idea",
    )
    commit_runtime_evidence(
        RuntimeEvidenceCommitRequest(
            attempt_path=attempt,
            adapter_outcome=outcome,
            exit_classification=outcome.value,
            exit_code=0 if outcome is RuntimeAdapterOutcome.SUCCESS else 1,
            stdout_text="",
            stderr_text="",
            runtime_log_text="runtime\n",
            stop_reason=(
                None
                if outcome is RuntimeAdapterOutcome.SUCCESS
                else RuntimeStopReason(outcome.value)
            ),
        )
    )
    if timestamp is not None:
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item="WI-HISTORY",
            run_id=run_id,
            stage="idea",
            attempt_number=1,
            changed_at_utc=timestamp,
        )
    return attempt


def test_runtime_launch_history_selects_latest_per_runtime(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _attempt(
        workspace_root,
        run_id="run-generic-old",
        runtime_id="generic-cli",
        outcome=RuntimeAdapterOutcome.SUCCESS,
        timestamp=datetime(2026, 7, 1, tzinfo=UTC),
    )
    _attempt(
        workspace_root,
        run_id="run-generic-new",
        runtime_id="generic-cli",
        outcome=RuntimeAdapterOutcome.RUNTIME_FAILURE,
        timestamp=datetime(2026, 7, 2, tzinfo=UTC),
    )
    _attempt(
        workspace_root,
        run_id="run-codex",
        runtime_id="codex",
        outcome=RuntimeAdapterOutcome.BLOCKED,
        timestamp=datetime(2026, 7, 3, tzinfo=UTC),
    )

    history = resolve_runtime_launch_history(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
    )

    assert history["generic-cli"].outcome == "runtime_failure"
    assert history["generic-cli"].recorded_at_utc == "2026-07-02T00:00:00Z"
    assert history["generic-cli"].run_id == "run-generic-new"
    assert history["codex"].outcome == "blocked"
    assert history["codex"].warning is None


def test_runtime_launch_history_marks_legacy_and_malformed_evidence(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    legacy = _attempt(
        workspace_root,
        run_id="run-legacy",
        runtime_id="generic-cli",
        outcome=RuntimeAdapterOutcome.CANCELLATION,
        timestamp=None,
    )
    exit_path = legacy / "runtime-exit.json"
    exit_path.write_text(
        '{"schema_version": 1, "exit_classification": "cancelled"}\n',
        encoding="utf-8",
    )
    legacy.joinpath("artifact-index.json").unlink()

    history = resolve_runtime_launch_history(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
    )

    assert history["generic-cli"].outcome == "cancellation"
    assert history["generic-cli"].recorded_at_utc is None
    assert "legacy runtime evidence" in (history["generic-cli"].warning or "")

    exit_path.write_text("{broken", encoding="utf-8")
    malformed = resolve_runtime_launch_history(
        workspace_root=workspace_root,
        work_item="WI-HISTORY",
    )["generic-cli"]
    assert malformed.outcome == "unknown"
    assert "malformed" in (malformed.warning or "")


def test_runtime_launch_history_is_empty_without_runs(tmp_path: Path) -> None:
    assert resolve_runtime_launch_history(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-HISTORY",
    ) == {}
