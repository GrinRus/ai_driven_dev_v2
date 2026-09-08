from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.evidence_freshness import EvidenceFreshnessRequest, classify_evidence_freshness
from aidd.core.operator_frontend import project_operator_run_freshness
from aidd.core.operator_frontend_dashboard_evidence import _terminal_recommended_outcome
from aidd.core.run_inspection import (
    RunArchiveSummary,
    RunLineageSummary,
    RunMetadataSummary,
)
from aidd.core.run_store import run_manifest_path


def _metadata(*, workspace_root: Path, work_item: str = "WI-FRESH") -> RunMetadataSummary:
    run_id = "run-fresh"
    manifest_path = run_manifest_path(workspace_root, work_item, run_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("{}\n", encoding="utf-8")
    return RunMetadataSummary(
        run_id=run_id,
        work_item=work_item,
        runtime_id="generic-cli",
        adapter_id="generic-cli",
        stage_target="qa",
        workflow_stage_start="idea",
        workflow_stage_end="qa",
        repository_git_sha="a" * 40,
        resource_revision="pin-a",
        prompt_pack_provenance=(),
        lineage=RunLineageSummary(
            source_run_id=None,
            source_work_item_id=None,
            baseline_id=None,
            baseline_label=None,
            child_work_item_candidates=(),
        ),
        archive=RunArchiveSummary(
            archived=False,
            archived_at_utc=None,
            reason=None,
            source=None,
        ),
        created_at_utc="2026-09-08T00:00:00Z",
        updated_at_utc="2026-09-08T00:00:00Z",
        stages=(),
    )


@pytest.mark.parametrize(
    ("candidate_sha", "target_pin", "versions", "expected"),
    (
        ("a" * 40, "pin-a", (1,), "current"),
        ("b" * 40, "pin-a", (1,), "stale"),
        ("a" * 40, "pin-a", (2,), "incompatible"),
        (None, "pin-a", (1,), "unavailable"),
    ),
)
def test_operator_run_projection_matches_shared_freshness_states(
    tmp_path: Path,
    candidate_sha: str | None,
    target_pin: str,
    versions: tuple[int, ...],
    expected: str,
) -> None:
    result = project_operator_run_freshness(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-FRESH",
        metadata=_metadata(workspace_root=tmp_path / ".aidd"),
        candidate_sha=candidate_sha,
        candidate_target_pin=target_pin,
        supported_evidence_schema_versions=versions,
    )

    reference = classify_evidence_freshness(
        EvidenceFreshnessRequest(
            candidate_sha=candidate_sha,
            evidence_sha="a" * 40,
            evidence_schema_version=1,
            target_pin=target_pin,
            evidence_target_pin="pin-a",
            locator="reports/runs/WI-FRESH/run-fresh/run-manifest.json",
            supported_schema_versions=versions,
        )
    )
    assert result.status.value == expected
    assert result.status is reference.status
    assert result.reason == reference.reason
    assert result.locator == "reports/runs/WI-FRESH/run-fresh/run-manifest.json"


def test_non_current_terminal_evidence_cannot_recommend_flow_completion(
    tmp_path: Path,
) -> None:
    freshness = project_operator_run_freshness(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-FRESH",
        metadata=_metadata(workspace_root=tmp_path / ".aidd"),
        candidate_sha="b" * 40,
        candidate_target_pin="pin-a",
    )

    recommendation, rationale = _terminal_recommended_outcome(
        handoff_status="completed",
        final_qa_status="ready",
        freshness=freshness,
    )

    assert freshness.status.value == "stale"
    assert recommendation is None
    assert rationale is not None
    assert "stale" in rationale
