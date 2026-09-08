from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

import pytest

from aidd.core.models.run import RepairExtensionGrant, RepairHistoryEntry, StageRunMetadata
from aidd.core.task_ledger import TaskLedger, TaskLedgerEntry
from aidd.core.task_repository_evidence import RepositorySnapshot


def _grant() -> RepairExtensionGrant:
    return RepairExtensionGrant(
        work_item_id="WI-1",
        run_id="run-1",
        stage="plan",
        validator_report_path="workitems/WI-1/stages/plan/validator-report.md",
        validator_report_sha256="a" * 64,
        repair_brief_path="workitems/WI-1/stages/plan/repair-brief.md",
        repair_brief_sha256="b" * 64,
        configuration_identity="config-1",
        author="operator",
        authorized_at_utc="2026-09-06T00:00:00Z",
        reason="One correction",
    )


def _metadata() -> StageRunMetadata:
    return StageRunMetadata.create(
        run_id="run-1",
        work_item_id="WI-1",
        stage="plan",
        status="pending",
        changed_at_utc="2026-09-06T00:00:00Z",
    )


def _ledger() -> TaskLedger:
    return TaskLedger(
        source_tasklist_sha256="c" * 64,
        tasks=(TaskLedgerEntry(id="TL-1", title="Implement", dependencies=(), acceptance_ids=()),),
        created_at_utc="2026-09-06T00:00:00Z",
        updated_at_utc="2026-09-06T00:00:00Z",
    )


@pytest.fixture(params=("metadata", "grant", "ledger", "snapshot"))
def current_record(request: pytest.FixtureRequest) -> tuple[dict[str, Any], Callable[..., Any]]:
    if request.param == "metadata":
        return _metadata().to_dict(), StageRunMetadata.from_dict
    if request.param == "grant":
        return _grant().to_dict(), RepairExtensionGrant.from_dict
    if request.param == "ledger":
        return _ledger().to_dict(), TaskLedger.from_dict
    return RepositorySnapshot(task_id="TL-1", status=(), files=()).to_payload(), (
        RepositorySnapshot.from_payload
    )


@pytest.mark.parametrize("version", (None, False, True, "1", "2", 1.0, 2.0, 0, 99))
def test_current_records_reject_missing_or_noncurrent_schema(
    current_record: tuple[dict[str, Any], Callable[..., Any]],
    version: object,
) -> None:
    payload, reader = current_record
    payload["schema_version"] = version
    with pytest.raises(ValueError, match="schema_version"):
        reader(payload)
    payload.pop("schema_version")
    with pytest.raises(ValueError, match="schema_version"):
        reader(payload)


def test_current_records_require_every_recorded_field(
    current_record: tuple[dict[str, Any], Callable[..., Any]],
) -> None:
    payload, reader = current_record
    for key in payload.keys() - {"schema_version"}:
        incomplete = deepcopy(payload)
        incomplete.pop(key)
        with pytest.raises(ValueError, match=key):
            reader(incomplete)
    # Wrong JSON roots must fail at the reader boundary, not as incidental attribute errors.
    for invalid in (None, [], "state"):
        with pytest.raises(ValueError, match="object"):
            reader(invalid)


def test_current_initial_and_populated_records_round_trip() -> None:
    metadata = _metadata()
    assert StageRunMetadata.from_dict(metadata.to_dict()) == metadata
    ledger = _ledger()
    assert TaskLedger.from_dict(ledger.to_dict()) == ledger
    assert ledger.tasks[0].updated_at_utc is None
    assert ledger.finalization.latest_attempt_path is None
    repaired = metadata.with_repair_history_entry(
        entry=RepairHistoryEntry(
            attempt_number=1,
            trigger=" Repair ",
            outcome=" failed ",
            recorded_at_utc="2026-09-06T00:01:00Z",
        ),
        changed_at_utc="2026-09-06T00:01:00Z",
    ).with_repair_extension_grant(grant=_grant(), changed_at_utc="2026-09-06T00:02:00Z")
    assert StageRunMetadata.from_dict(repaired.to_dict()) == repaired
    assert RepairExtensionGrant.from_dict(_grant().to_dict()) == _grant()
    snapshot = RepositorySnapshot(
        task_id="TL-1",
        status=(" M file.md",),
        files=(("directory", "non-file"), ("file.md", "a" * 64), ("removed", "missing")),
    )
    assert RepositorySnapshot.from_payload(snapshot.to_payload()) == snapshot


@pytest.mark.parametrize(
    "field,value",
    (
        ("status_history", []),
        ("status_history", [None]),
        ("status_history", [{"status": "pending"}]),
        ("status_history", [{"status": None, "changed_at_utc": "now"}]),
        ("repair_history", ["repair"]),
        ("repair_history", None),
        ("repair_extension_grant", {}),
        ("repair_extension_grant", False),
        ("run_id", None),
        ("created_at_utc", 1),
    ),
)
def test_stage_metadata_does_not_invent_or_coerce_history(field: str, value: object) -> None:
    payload = _metadata().to_dict()
    payload[field] = value
    with pytest.raises(ValueError):
        StageRunMetadata.from_dict(payload)


@pytest.mark.parametrize(
    "field,value",
    (
        ("attempt_number", "1"),
        ("attempt_number", True),
        ("trigger", None),
        ("outcome", False),
        ("recorded_at_utc", None),
        ("validator_report_path", 4),
    ),
)
def test_repair_history_requires_recorded_types_and_nullable_path_keys(
    field: str,
    value: object,
) -> None:
    entry = RepairHistoryEntry(
        attempt_number=1,
        trigger="repair",
        outcome="failed",
        recorded_at_utc="now",
    ).to_dict()
    entry[field] = value
    with pytest.raises(ValueError, match=field):
        RepairHistoryEntry.from_dict(entry)
    for path_field in ("validator_report_path", "repair_brief_path"):
        missing = RepairHistoryEntry(
            attempt_number=1,
            trigger="repair",
            outcome="failed",
            recorded_at_utc="now",
        ).to_dict()
        missing.pop(path_field)
        with pytest.raises(ValueError, match=path_field):
            RepairHistoryEntry.from_dict(missing)


@pytest.mark.parametrize(
    "field,value",
    (
        ("tasks", [None]),
        ("tasks", {}),
        ("finalization", None),
        ("finalization", {}),
        ("created_at_utc", None),
        ("source_tasklist_sha256", 1),
    ),
)
def test_ledger_rejects_incomplete_entries_instead_of_skipping_or_defaulting(
    field: str,
    value: object,
) -> None:
    payload = _ledger().to_dict()
    payload[field] = value
    with pytest.raises(ValueError):
        TaskLedger.from_dict(payload)


@pytest.mark.parametrize("entry_name", ("task", "finalization"))
def test_ledger_nested_fields_are_required_and_counters_are_integers(entry_name: str) -> None:
    payload = _ledger().to_dict()
    entry = payload["tasks"][0] if entry_name == "task" else payload["finalization"]
    for key in tuple(entry):
        malformed = deepcopy(payload)
        target = malformed["tasks"][0] if entry_name == "task" else malformed["finalization"]
        target.pop(key)
        with pytest.raises(ValueError, match=key):
            TaskLedger.from_dict(malformed)
    for invalid_count in (None, True, "1", 1.5, -1):
        entry["attempt_count"] = invalid_count
        with pytest.raises(ValueError, match="attempt_count"):
            TaskLedger.from_dict(payload)


@pytest.mark.parametrize(
    "field,value",
    (
        ("task_id", None),
        ("status", [None]),
        ("files", {"path": None}),
    ),
)
def test_repository_snapshot_does_not_coerce_recorded_evidence(field: str, value: object) -> None:
    payload = RepositorySnapshot(task_id="TL-1", status=(), files=()).to_payload()
    payload[field] = value
    with pytest.raises(ValueError):
        RepositorySnapshot.from_payload(payload)
