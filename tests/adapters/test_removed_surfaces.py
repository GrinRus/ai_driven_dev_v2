from __future__ import annotations

import ast
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _defined_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_superseded_claude_question_resume_surface_is_absent() -> None:
    runner_path = REPOSITORY_ROOT / "src/aidd/adapters/claude_code/runner.py"

    assert _defined_names(runner_path).isdisjoint(
        {
            "ClaudeCodeQuestionDetection",
            "ClaudeCodeQuestionRouting",
            "ClaudeCodeQuestionPersistence",
            "ClaudeCodeResumeDecision",
            "detect_question_or_pause_events",
            "route_questions_with_file_fallback",
            "persist_surfaced_questions",
            "prepare_resume_after_answers",
        }
    )
