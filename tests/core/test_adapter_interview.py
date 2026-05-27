from __future__ import annotations

import json
from pathlib import Path

from aidd.core.adapter_interview import persist_adapter_question_metadata
from aidd.core.run_store import persist_stage_status


def test_persist_adapter_question_metadata_updates_existing_stage_metadata(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status="executing",
    )
    questions_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "questions.md"
    questions_path.parent.mkdir(parents=True, exist_ok=True)
    questions_path.write_text("# Questions\n", encoding="utf-8")

    persistence = persist_adapter_question_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        metadata_key="claude_question_artifact",
        questions_path=questions_path,
        unresolved_blocking_question_ids=("Q1",),
    )

    assert persistence.metadata_updated is True
    payload = json.loads(persistence.stage_metadata_path.read_text(encoding="utf-8"))
    assert payload["claude_question_artifact"] == {
        "questions_path": "workitems/WI-001/stages/plan/questions.md",
        "unresolved_blocking_question_ids": ["Q1"],
    }


def test_persist_adapter_question_metadata_skips_missing_stage_metadata(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    persistence = persist_adapter_question_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        metadata_key="claude_question_artifact",
        questions_path=workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "plan"
        / "questions.md",
        unresolved_blocking_question_ids=("Q1",),
    )

    assert persistence.metadata_updated is False
    assert not persistence.stage_metadata_path.exists()
