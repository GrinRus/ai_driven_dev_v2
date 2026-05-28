from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.core.next_flow import (
    FollowUpDraftRequest,
    FollowUpSourceSelection,
    create_follow_up_work_item_draft,
)


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
