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


def test_native_prompt_module_is_the_only_prompt_read_owner() -> None:
    native_prompt_path = REPOSITORY_ROOT / "src/aidd/adapters/native_prompt.py"
    runner_paths = (
        REPOSITORY_ROOT / "src/aidd/adapters/claude_code/runner.py",
        REPOSITORY_ROOT / "src/aidd/adapters/codex/runner.py",
        REPOSITORY_ROOT / "src/aidd/adapters/opencode/runner.py",
    )

    assert "_read_text_for_prompt" in _defined_names(native_prompt_path)
    assert all(
        "_read_text_for_prompt" not in _defined_names(runner_path)
        for runner_path in runner_paths
    )
