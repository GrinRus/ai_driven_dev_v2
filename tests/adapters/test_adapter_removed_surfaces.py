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
        "_read_text_for_prompt" not in _defined_names(runner_path) for runner_path in runner_paths
    )


def test_unused_core_and_adapter_facades_stay_removed() -> None:
    removed_paths = (
        REPOSITORY_ROOT / "src/aidd/adapters/runtime_artifacts.py",
        REPOSITORY_ROOT / "src/aidd/adapters/runtime_registry.py",
        REPOSITORY_ROOT / "src/aidd/cli/run_lookup.py",
    )
    assert all(not path.exists() for path in removed_paths)

    removed_symbols = {
        REPOSITORY_ROOT / "src/aidd/core/adapter_interview.py": {
            "AdapterQuestionMetadataPersistence",
            "persist_adapter_question_metadata",
        },
        REPOSITORY_ROOT / "src/aidd/core/stage_models.py": {"StageResumeResult"},
        REPOSITORY_ROOT / "src/aidd/core/stage_validation.py": {
            "prepare_stage_resume_after_answers",
        },
        REPOSITORY_ROOT / "src/aidd/core/stage_runner.py": {
            "prepare_stage_resume_after_answers",
            "_route_stage_questions_to_interview_with_validation",
        },
        REPOSITORY_ROOT / "src/aidd/core/run_inspection.py": {
            "ResolvedCliRunTarget",
            "resolve_cli_run_target",
        },
        REPOSITORY_ROOT / "src/aidd/core/run_lookup.py": {
            "ResumeGuardError",
            "CorruptedRunError",
            "ClosedRunError",
            "guard_run_resume",
            "guard_latest_run_resume",
            "latest_attempt_path_for_work_item",
            "attempt_artifact_index_path",
            "resolve_latest_attempt_artifact_paths",
        },
    }
    for path, names in removed_symbols.items():
        assert _defined_names(path).isdisjoint(names)
