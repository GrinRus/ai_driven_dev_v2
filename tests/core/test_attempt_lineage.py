from __future__ import annotations

import pytest

from aidd.core.attempt_lineage import (
    AttemptKind,
    AttemptLineage,
    AttemptScope,
    FinalizationAttemptState,
)
from aidd.core.models.run import RunArtifactIndex
from aidd.core.task_attempt_evidence import TaskAttemptEvidenceReferences


@pytest.mark.parametrize(
    ("scope", "attempt_kind", "attempt_number"),
    [
        (AttemptScope.STAGE, AttemptKind.INITIAL, 1),
        (AttemptScope.STAGE, AttemptKind.REPAIR, 2),
        (AttemptScope.STAGE, AttemptKind.RESUME, 3),
        (AttemptScope.STAGE, AttemptKind.INTERVENTION, 4),
        (AttemptScope.STAGE, AttemptKind.REPAIR_EXTENSION, 5),
        (AttemptScope.TASK, AttemptKind.TASK, 1),
        (AttemptScope.FINALIZATION, AttemptKind.FINALIZATION, 1),
    ],
)
def test_attempt_lineage_round_trip_distinguishes_scope_and_kind(
    scope: AttemptScope,
    attempt_kind: AttemptKind,
    attempt_number: int,
) -> None:
    lineage = AttemptLineage(
        scope=scope,
        attempt_kind=attempt_kind,
        attempt_number=attempt_number,
        parent_attempt_path="reports/runs/WI-1/run-1/stages/plan/attempts/attempt-0001"
        if attempt_number > 1
        else None,
    )

    restored = AttemptLineage.from_dict(lineage.to_dict())

    assert restored == lineage


def test_artifact_index_round_trip_keeps_lineage_explicit() -> None:
    index = RunArtifactIndex.create(
        run_id="run-1",
        work_item_id="WI-1",
        stage="plan",
        attempt_number=2,
        documents={},
        logs={},
        attempt_mode="repair",
        lineage=AttemptLineage(
            scope=AttemptScope.STAGE,
            attempt_kind=AttemptKind.REPAIR,
            attempt_number=2,
        ),
        changed_at_utc="2026-09-06T00:00:00Z",
    )

    restored = RunArtifactIndex.from_dict(index.to_dict())
    assert restored.effective_lineage.attempt_kind is AttemptKind.REPAIR

    retired_payload = index.to_dict()
    retired_payload.pop("lineage")
    with pytest.raises(ValueError, match="current-format lineage"):
        RunArtifactIndex.from_dict(retired_payload)


def test_retired_task_and_finalization_state_are_not_upgraded() -> None:
    finalization = FinalizationAttemptState.from_dict(
        {
            "schema_version": 1,
            "attempt_number": 2,
            "status": "failed",
            "updated_at_utc": "2026-09-06T00:00:00Z",
            "lineage": {
                "schema_version": 1,
                "scope": "finalization",
                "attempt_kind": "finalization",
                "attempt_number": 2,
                "parent_attempt_path": None,
            },
        }
    )

    assert finalization.effective_lineage.attempt_kind is AttemptKind.FINALIZATION
    retired_payload = finalization.to_dict()
    retired_payload.pop("lineage")
    with pytest.raises(ValueError, match="requires.*lineage"):
        FinalizationAttemptState.from_dict(retired_payload)


def test_task_reference_manifest_round_trip_accepts_task_lineage() -> None:
    manifest = TaskAttemptEvidenceReferences.from_dict(
        {
            "schema_version": 1,
            "task_id": "TL-1",
            "task_attempt_number": 1,
            "stage": "implement",
            "stage_attempts": [],
            "lineage": {
                "schema_version": 1,
                "scope": "task",
                "attempt_kind": "task",
                "attempt_number": 1,
                "parent_attempt_path": None,
            },
        }
    )

    assert manifest.effective_lineage.attempt_kind is AttemptKind.TASK
    assert manifest.lineage is not None


def test_task_reference_manifest_rejects_retired_ordinal_only_payload() -> None:
    with pytest.raises(ValueError, match="current-format lineage"):
        TaskAttemptEvidenceReferences.from_dict(
            {
                "schema_version": 1,
                "task_id": "TL-1",
                "task_attempt_number": 2,
                "stage": "implement",
                "stage_attempts": [],
            }
        )


@pytest.mark.parametrize(
    ("scope", "attempt_kind"),
    [
        (AttemptScope.TASK, AttemptKind.REPAIR),
        (AttemptScope.FINALIZATION, AttemptKind.RESUME),
    ],
)
def test_attempt_lineage_rejects_cross_scope_kind(
    scope: AttemptScope,
    attempt_kind: AttemptKind,
) -> None:
    with pytest.raises(ValueError, match="invalid"):
        AttemptLineage(scope=scope, attempt_kind=attempt_kind, attempt_number=1)


def test_attempt_lineage_rejects_parent_path_escape() -> None:
    with pytest.raises(ValueError, match="workspace-relative"):
        AttemptLineage(
            scope=AttemptScope.STAGE,
            attempt_kind=AttemptKind.REPAIR,
            attempt_number=2,
            parent_attempt_path="../attempt-0001",
        )
