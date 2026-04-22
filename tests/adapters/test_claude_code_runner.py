from __future__ import annotations

import os
from pathlib import Path

import pytest

from aidd.adapters.claude_code.runner import (
    ClaudeCodeCommandContext,
    ClaudeCodeConfigFlag,
    ClaudeCodeLaunchOptions,
    ClaudeCodeSubprocessSpec,
    assemble_command,
    build_execution_environment,
    build_subprocess_spec,
    command_preview,
)


def _context() -> ClaudeCodeCommandContext:
    return ClaudeCodeCommandContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=Path(".aidd/workitems/WI-001"),
        stage_brief_path=Path("stages/plan/stage-brief.md"),
        prompt_pack_paths=(
            Path("prompt-packs/stages/plan/system.md"),
            Path("prompt-packs/stages/plan/task.md"),
        ),
    )


def test_assemble_command_includes_stage_brief_workspace_and_prompt_packs(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd" / "workitems" / "WI-001"
    context = ClaudeCodeCommandContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=Path("stages/plan/stage-brief.md"),
        prompt_pack_paths=(
            Path("prompt-packs/stages/plan/system.md"),
            Path("prompt-packs/stages/plan/task.md"),
        ),
    )

    command = assemble_command(
        configured_command="claude",
        context=context,
        repository_root=repository_root,
    )

    assert command[:1] == ("claude",)
    assert "--workspace-root" in command
    assert "--stage-brief" in command
    assert command.count("--prompt-pack") == 2
    assert command[command.index("--stage") + 1] == "plan"
    assert command[command.index("--work-item") + 1] == "WI-001"
    assert command[command.index("--run-id") + 1] == "run-001"
    assert command[command.index("--workspace-root") + 1] == workspace_root.resolve(
        strict=False
    ).as_posix()
    assert command[command.index("--stage-brief") + 1] == (
        workspace_root / "stages/plan/stage-brief.md"
    ).resolve(strict=False).as_posix()
    prompt_pack_values = tuple(
        command[idx + 1] for idx, token in enumerate(command) if token == "--prompt-pack"
    )
    assert prompt_pack_values == (
        (repository_root / "prompt-packs/stages/plan/system.md").resolve(strict=False).as_posix(),
        (repository_root / "prompt-packs/stages/plan/task.md").resolve(strict=False).as_posix(),
    )


def test_assemble_command_respects_shell_quoted_base_tokens() -> None:
    command = assemble_command(
        configured_command='claude --profile "team alpha"',
        context=_context(),
    )

    assert command[:3] == ("claude", "--profile", "team alpha")


def test_assemble_command_maps_sandbox_permission_and_config_flags() -> None:
    command = assemble_command(
        configured_command="claude",
        context=_context(),
        launch_options=ClaudeCodeLaunchOptions(
            sandbox_mode="workspace-write",
            permission_mode="approval-required",
            config_flags=(
                ClaudeCodeConfigFlag(flag="model", value="sonnet"),
                ClaudeCodeConfigFlag(flag="--verbose"),
            ),
        ),
    )

    assert command[1:11] == (
        "--sandbox",
        "workspace-write",
        "--permission-mode",
        "approval-required",
        "--model",
        "sonnet",
        "--verbose",
        "--stage",
        "plan",
        "--work-item",
    )


def test_assemble_command_maps_bypass_permission_to_dangerous_flag() -> None:
    command = assemble_command(
        configured_command="claude",
        context=_context(),
        launch_options=ClaudeCodeLaunchOptions(permission_mode="bypass"),
    )

    assert "--dangerously-skip-permissions" in command
    assert "--permission-mode" not in command


def test_build_execution_environment_sets_stage_workspace_and_prompt_pack_values(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd" / "workitems" / "WI-001"
    env = build_execution_environment(
        context=ClaudeCodeCommandContext(
            stage="plan",
            work_item="WI-001",
            run_id="run-001",
            workspace_root=workspace_root,
            stage_brief_path=Path("stages/plan/stage-brief.md"),
            prompt_pack_paths=(
                Path("prompt-packs/stages/plan/system.md"),
                Path("prompt-packs/stages/plan/task.md"),
            ),
        ),
        base_env={"PATH": "/usr/bin", "AIDD_STAGE": "stale"},
        repository_root=repository_root,
    )

    assert env["PATH"] == "/usr/bin"
    assert env["AIDD_WORKSPACE_ROOT"] == workspace_root.resolve(strict=False).as_posix()
    assert env["AIDD_STAGE"] == "plan"
    assert env["AIDD_WORK_ITEM"] == "WI-001"
    assert env["AIDD_RUN_ID"] == "run-001"
    assert env["AIDD_STAGE_BRIEF_PATH"] == (
        workspace_root / "stages/plan/stage-brief.md"
    ).resolve(strict=False).as_posix()
    assert env["AIDD_PROMPT_PACK_PATHS"] == (
        (repository_root / "prompt-packs/stages/plan/system.md").resolve(strict=False).as_posix()
        + os.pathsep
        + (repository_root / "prompt-packs/stages/plan/task.md").resolve(strict=False).as_posix()
    )
    assert env["AIDD_RUNTIME_ID"] == "claude-code"


def test_build_subprocess_spec_sets_command_cwd_and_env(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd" / "workitems" / "WI-001"
    context = ClaudeCodeCommandContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=Path("stages/plan/stage-brief.md"),
        prompt_pack_paths=(Path("prompt-packs/stages/plan/system.md"),),
    )
    spec = build_subprocess_spec(
        configured_command="claude",
        context=context,
        launch_options=ClaudeCodeLaunchOptions(sandbox_mode="workspace-write"),
        base_env={"PATH": "/usr/bin"},
        repository_root=repository_root,
    )

    assert isinstance(spec, ClaudeCodeSubprocessSpec)
    assert spec.command[0] == "claude"
    assert spec.command[1:3] == ("--sandbox", "workspace-write")
    assert spec.cwd == workspace_root.resolve(strict=False)
    assert spec.env["PATH"] == "/usr/bin"
    assert spec.env["AIDD_WORKSPACE_ROOT"] == workspace_root.resolve(strict=False).as_posix()


def test_assemble_command_rejects_empty_configured_command() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        assemble_command(configured_command="   ", context=_context())


def test_assemble_command_rejects_invalid_shell_syntax() -> None:
    with pytest.raises(ValueError, match="not valid shell syntax"):
        assemble_command(configured_command='"unterminated', context=_context())


def test_command_preview_renders_shell_escaped_output() -> None:
    preview = command_preview(
        configured_command='claude --profile "team alpha"',
        context=_context(),
    )

    assert preview.startswith("claude --profile 'team alpha'")
    assert "--workspace-root" in preview
    assert "--stage-brief" in preview
    assert "--prompt-pack" in preview


def test_context_rejects_empty_prompt_pack_inputs() -> None:
    with pytest.raises(ValueError, match="at least one prompt-pack"):
        ClaudeCodeCommandContext(
            stage="plan",
            work_item="WI-001",
            run_id="run-001",
            workspace_root=Path(".aidd"),
            stage_brief_path=Path("stages/plan/stage-brief.md"),
            prompt_pack_paths=(),
        )


def test_launch_options_reject_blank_modes() -> None:
    with pytest.raises(ValueError, match="Sandbox mode must not be blank"):
        ClaudeCodeLaunchOptions(sandbox_mode="   ")

    with pytest.raises(ValueError, match="Permission mode must not be blank"):
        ClaudeCodeLaunchOptions(permission_mode="   ")
