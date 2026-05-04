from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.interview import AnswerResolution
from aidd.core.operator_frontend import (
    persist_operator_answer,
    resolve_operator_artifacts_view,
    resolve_operator_questions_view,
    resolve_operator_run_log_view,
    resolve_operator_run_view,
    resolve_operator_stage_view,
)
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_runtime_log_path,
)


def _prepare_run(workspace_root: Path) -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="blocked",
    )
    run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ).write_text("runtime-line\n", encoding="utf-8")


def _write_questions(workspace_root: Path) -> None:
    questions_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "questions.md"
    questions_path.parent.mkdir(parents=True, exist_ok=True)
    questions_path.write_text(
        "\n".join(
            (
                "# Questions",
                "",
                "## Questions",
                "",
                "- `Q1` `[blocking]` Confirm the target release.",
                "- `Q2` `[non-blocking]` Confirm reviewer preference.",
                "",
            )
        ),
        encoding="utf-8",
    )


def test_operator_read_models_expose_run_stage_logs_artifacts_and_questions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)

    run_view = resolve_operator_run_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
    )
    stage_view = resolve_operator_stage_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )
    log_view = resolve_operator_run_log_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
        attempt_number=1,
    )
    artifacts_view = resolve_operator_artifacts_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
        attempt_number=1,
    )

    assert run_view.metadata.runtime_id == "codex"
    assert stage_view.result.final_state == "blocked"
    assert stage_view.questions.unresolved_blocking_question_ids == ("Q1",)
    assert log_view.runtime_log_path.read_text(encoding="utf-8") == "runtime-line\n"
    assert artifacts_view.documents["stage_result"] == (
        "workitems/WI-UI/stages/plan/stage-result.md"
    )


def test_persist_operator_answer_writes_standard_answers_document(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_questions(workspace_root)

    questions_view = persist_operator_answer(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        question_id="Q1",
        text="The target release is 0.2.0.",
    )

    assert questions_view.has_unresolved_blocking_questions is False
    assert questions_view.questions[0].status == "resolved"
    assert questions_view.answers_path.read_text(encoding="utf-8") == (
        "# Answers\n\n"
        "## Answers\n\n"
        "- `Q1` `[resolved]` The target release is 0.2.0.\n"
    )


def test_persist_operator_answer_preserves_partial_semantics(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_questions(workspace_root)

    questions_view = persist_operator_answer(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        question_id="Q1",
        text="Release is not final yet.",
        resolution=AnswerResolution.PARTIAL,
    )

    assert questions_view.has_unresolved_blocking_questions is True
    assert questions_view.questions[0].status == "pending-blocking"


def test_persist_operator_answer_rejects_unknown_question_id(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_questions(workspace_root)

    with pytest.raises(ValueError, match="does not exist"):
        persist_operator_answer(
            workspace_root=workspace_root,
            work_item="WI-UI",
            stage="plan",
            question_id="Q404",
            text="Unknown answer.",
        )


def test_resolve_operator_questions_rejects_unknown_stage(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown stage"):
        resolve_operator_questions_view(
            workspace_root=tmp_path / ".aidd",
            work_item="WI-UI",
            stage="unknown",
        )
