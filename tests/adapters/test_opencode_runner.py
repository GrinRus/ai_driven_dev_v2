from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from aidd.adapters.opencode.runner import (
    OpenCodeCommandContext,
    OpenCodeExitClassification,
    OpenCodeSubprocessSpec,
    assemble_command,
    build_execution_environment,
    build_subprocess_spec,
    command_preview,
    persist_attempt_runtime_log,
    run_subprocess_with_streaming,
)
from aidd.adapters.runtime_artifacts import RUNTIME_EXIT_METADATA_FILENAME


def _context(tmp_path: Path) -> OpenCodeCommandContext:
    workspace_root = tmp_path / ".aidd"
    return OpenCodeCommandContext(
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


def test_assemble_command_includes_stage_workspace_brief_and_prompt_packs(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    command = assemble_command(
        configured_command="opencode",
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
        "opencode",
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
        configured_command="opencode exec",
        context=context,
        repository_root=tmp_path,
    )

    assert command[:2] == ("opencode", "exec")


def test_command_preview_renders_shell_quoted_command(tmp_path: Path) -> None:
    context = _context(tmp_path)
    preview = command_preview(
        configured_command="opencode",
        context=context,
        repository_root=tmp_path,
    )

    assert preview.startswith("opencode ")
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
    assert env["AIDD_RUNTIME_ID"] == "opencode"
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
        configured_command="opencode",
        context=context,
        base_env={"BASE_FLAG": "1"},
        repository_root=tmp_path,
    )

    assert spec.cwd == context.workspace_root.resolve(strict=False)
    assert spec.command[0] == "opencode"
    assert spec.env["BASE_FLAG"] == "1"
    assert spec.env["AIDD_RUNTIME_ID"] == "opencode"


def test_run_subprocess_with_streaming_captures_output_and_callbacks(tmp_path: Path) -> None:
    spec = OpenCodeSubprocessSpec(
        command=(
            sys.executable,
            "-c",
            "import sys; print('stdout-line'); print('stderr-line', file=sys.stderr)",
        ),
        cwd=tmp_path,
        env=dict(os.environ),
    )
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    result = run_subprocess_with_streaming(
        spec=spec,
        on_stdout=stdout_chunks.append,
        on_stderr=stderr_chunks.append,
    )

    assert result.exit_code == 0
    assert result.stdout_text == "stdout-line\n"
    assert result.stderr_text == "stderr-line\n"
    assert "stdout-line\n" in result.runtime_log_text
    assert "stderr-line\n" in result.runtime_log_text
    assert result.exit_classification == OpenCodeExitClassification.SUCCESS
    assert stdout_chunks == ["stdout-line\n"]
    assert stderr_chunks == ["stderr-line\n"]


def test_persist_attempt_runtime_log_writes_runtime_log(tmp_path: Path) -> None:
    spec = OpenCodeSubprocessSpec(
        command=(sys.executable, "-c", "print('runtime-log-line')"),
        cwd=tmp_path,
        env=dict(os.environ),
    )
    run_result = run_subprocess_with_streaming(spec=spec)

    runtime_log_path = persist_attempt_runtime_log(
        attempt_path=tmp_path / "attempt-001",
        run_result=run_result,
    )

    assert runtime_log_path.exists()
    assert runtime_log_path.read_text(encoding="utf-8") == run_result.runtime_log_text
    runtime_exit_metadata_path = runtime_log_path.parent / RUNTIME_EXIT_METADATA_FILENAME
    assert runtime_exit_metadata_path.exists()
    runtime_exit_metadata = json.loads(runtime_exit_metadata_path.read_text(encoding="utf-8"))
    assert runtime_exit_metadata["exit_classification"] == OpenCodeExitClassification.SUCCESS.value


def test_run_subprocess_with_streaming_classifies_non_zero_exit(tmp_path: Path) -> None:
    spec = OpenCodeSubprocessSpec(
        command=(
            sys.executable,
            "-c",
            "import sys; print('boom', file=sys.stderr); raise SystemExit(3)",
        ),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    result = run_subprocess_with_streaming(spec=spec)

    assert result.exit_code == 3
    assert result.exit_classification == OpenCodeExitClassification.NON_ZERO_EXIT
    assert "boom\n" in result.stderr_text


def test_run_subprocess_with_streaming_classifies_timeout(tmp_path: Path) -> None:
    spec = OpenCodeSubprocessSpec(
        command=(sys.executable, "-c", "import time; time.sleep(2)"),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    result = run_subprocess_with_streaming(spec=spec, timeout_seconds=0.1)

    assert result.exit_classification == OpenCodeExitClassification.TIMEOUT
    assert result.exit_code != 0


def test_run_subprocess_with_streaming_classifies_cancelled(tmp_path: Path) -> None:
    spec = OpenCodeSubprocessSpec(
        command=(sys.executable, "-c", "import time; time.sleep(2)"),
        cwd=tmp_path,
        env=dict(os.environ),
    )
    poll_count = 0

    def cancel_requested() -> bool:
        nonlocal poll_count
        poll_count += 1
        return poll_count >= 2

    result = run_subprocess_with_streaming(spec=spec, cancel_requested=cancel_requested)

    assert result.exit_classification == OpenCodeExitClassification.CANCELLED
    assert result.exit_code != 0


def test_run_subprocess_with_streaming_rejects_non_positive_timeout(tmp_path: Path) -> None:
    spec = OpenCodeSubprocessSpec(
        command=(sys.executable, "-c", "print('ok')"),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    with pytest.raises(ValueError, match="greater than zero"):
        run_subprocess_with_streaming(spec=spec, timeout_seconds=0)


def test_assemble_command_rejects_empty_configured_command(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        assemble_command(configured_command="   ", context=_context(tmp_path))


def test_assemble_command_rejects_invalid_shell_syntax(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not valid shell syntax"):
        assemble_command(configured_command='"unterminated', context=_context(tmp_path))
