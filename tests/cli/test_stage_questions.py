from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def _write_questions(root: Path, *, stage: str, work_item: str, body: str) -> None:
    questions_path = root / "workitems" / work_item / "stages" / stage / "questions.md"
    questions_path.parent.mkdir(parents=True, exist_ok=True)
    questions_path.write_text(body, encoding="utf-8")


def _write_answers(root: Path, *, stage: str, work_item: str, body: str) -> None:
    answers_path = root / "workitems" / work_item / "stages" / stage / "answers.md"
    answers_path.parent.mkdir(parents=True, exist_ok=True)
    answers_path.write_text(body, encoding="utf-8")


def test_stage_questions_reports_unresolved_blocking_questions(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    _write_questions(
        root,
        stage="plan",
        work_item="WI-001",
        body=(
            "# Questions\n\n"
            "## Questions\n\n"
            "- Q1 [blocking] Confirm release owner approval before rollout.\n"
        ),
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "questions",
            "plan",
            "--work-item",
            "WI-001",
            "--root",
            str(root),
        ],
    )

    assert result.exit_code == 0
    assert "pending-blocking" in result.stdout
    assert "Blocking questions are unresolved." in result.stdout
    assert "answers.md" in result.stdout


def test_stage_questions_reports_resolved_blocking_questions(tmp_path: Path) -> None:
    root = tmp_path / ".aidd"
    _write_questions(
        root,
        stage="plan",
        work_item="WI-001",
        body=(
            "# Questions\n\n"
            "## Questions\n\n"
            "- Q1 [blocking] Confirm release owner approval before rollout.\n"
        ),
    )
    _write_answers(
        root,
        stage="plan",
        work_item="WI-001",
        body=(
            "# Answers\n\n"
            "## Answers\n\n"
            "- Q1 [resolved] Release owner approval is recorded.\n"
        ),
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "questions",
            "plan",
            "--work-item",
            "WI-001",
            "--root",
            str(root),
        ],
    )

    assert result.exit_code == 0
    assert "resolved" in result.stdout
    assert "No unresolved blocking questions." in result.stdout
