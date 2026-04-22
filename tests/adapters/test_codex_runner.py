from __future__ import annotations

import os
from pathlib import Path

import pytest

from aidd.adapters.codex.runner import (
    CodexCommandContext,
    assemble_command,
    build_execution_environment,
    build_subprocess_spec,
    command_preview,
)


def _context(tmp_path: Path) -> CodexCommandContext:
    workspace_root = tmp_path / ".aidd"
    return CodexCommandContext(
        stage="plan",
        work_item="WI-123",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=Path("workitems/WI-123/stages/plan/stage-brief.md"),
        prompt_pack_paths=(
            Path("prompt-packs/stages/plan/run.md"),
            Path("prompt-packs/stages/plan/repair.md"),
        ),
    )


def test_assemble_command_includes_stage_workspace_brief_and_prompt_packs(tmp_path: Path) -> None:
    context = _context(tmp_path)
    command = assemble_command(
        configured_command="codex",
        context=context,
        repository_root=tmp_path,
    )

    expected_workspace = context.workspace_root.resolve(strict=False).as_posix()
    expected_stage_brief = (
        context.workspace_root / context.stage_brief_path
    ).resolve(strict=False).as_posix()
    expected_prompt_1 = (tmp_path / context.prompt_pack_paths[0]).resolve(strict=False).as_posix()
    expected_prompt_2 = (tmp_path / context.prompt_pack_paths[1]).resolve(strict=False).as_posix()

    assert command == (
        "codex",
        "--stage",
        "plan",
        "--work-item",
        "WI-123",
        "--run-id",
        "run-001",
        "--workspace-root",
        expected_workspace,
        "--stage-brief",
        expected_stage_brief,
        "--prompt-pack",
        expected_prompt_1,
        "--prompt-pack",
        expected_prompt_2,
    )


def test_assemble_command_respects_shell_quoted_base_tokens(tmp_path: Path) -> None:
    context = _context(tmp_path)
    command = assemble_command(
        configured_command="codex exec",
        context=context,
        repository_root=tmp_path,
    )

    assert command[:2] == ("codex", "exec")


def test_command_preview_renders_shell_quoted_command(tmp_path: Path) -> None:
    context = _context(tmp_path)
    preview = command_preview(
        configured_command="codex",
        context=context,
        repository_root=tmp_path,
    )

    assert preview.startswith("codex ")
    assert "--stage plan" in preview
    assert "--work-item WI-123" in preview


def test_build_execution_environment_sets_runtime_metadata(tmp_path: Path) -> None:
    context = _context(tmp_path)
    env = build_execution_environment(
        context=context,
        base_env={"BASE_FLAG": "1"},
        repository_root=tmp_path,
    )

    assert env["BASE_FLAG"] == "1"
    assert env["AIDD_RUNTIME_ID"] == "codex"
    assert env["AIDD_STAGE"] == "plan"
    assert env["AIDD_WORK_ITEM"] == "WI-123"
    assert env["AIDD_RUN_ID"] == "run-001"
    assert env["AIDD_WORKSPACE_ROOT"] == context.workspace_root.resolve(strict=False).as_posix()
    assert env["AIDD_STAGE_BRIEF_PATH"] == (
        context.workspace_root / context.stage_brief_path
    ).resolve(strict=False).as_posix()
    assert env["AIDD_PROMPT_PACK_PATHS"] == os.pathsep.join(
        (tmp_path / path).resolve(strict=False).as_posix() for path in context.prompt_pack_paths
    )


def test_build_subprocess_spec_uses_workspace_as_cwd(tmp_path: Path) -> None:
    context = _context(tmp_path)
    spec = build_subprocess_spec(
        configured_command="codex",
        context=context,
        base_env={"BASE_FLAG": "1"},
        repository_root=tmp_path,
    )

    assert spec.cwd == context.workspace_root.resolve(strict=False)
    assert spec.command[0] == "codex"
    assert spec.env["BASE_FLAG"] == "1"
    assert spec.env["AIDD_RUNTIME_ID"] == "codex"


def test_assemble_command_rejects_empty_configured_command(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        assemble_command(configured_command="   ", context=_context(tmp_path))


def test_assemble_command_rejects_invalid_shell_syntax(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not valid shell syntax"):
        assemble_command(configured_command='"unterminated', context=_context(tmp_path))
