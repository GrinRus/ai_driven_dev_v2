from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

from aidd.adapters.generic_cli.runner import (
    RUNTIME_EXIT_METADATA_FILENAME,
    GenericCliExitClassification,
    GenericCliRunResult,
    GenericCliRuntimeArtifacts,
    GenericCliStageContext,
    GenericCliSubprocessSpec,
    _resolve_exit_classification,
    assemble_command,
    build_execution_environment,
    build_subprocess_spec,
    command_preview,
    persist_attempt_runtime_artifacts,
    run_subprocess_with_streaming,
)
from aidd.core.run_store import RUN_RUNTIME_LOG_FILENAME


def _context() -> GenericCliStageContext:
    return GenericCliStageContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        prompt_pack_path=Path("prompt-packs/stages/plan/system.md"),
    )


def test_assemble_command_appends_stage_context_and_prompt_pack() -> None:
    command = assemble_command(
        configured_command="python -m generic_runtime",
        context=_context(),
    )

    assert command == (
        "python",
        "-m",
        "generic_runtime",
        "--stage",
        "plan",
        "--work-item",
        "WI-001",
        "--run-id",
        "run-001",
        "--prompt-pack",
        "prompt-packs/stages/plan/system.md",
    )


def test_assemble_command_respects_shell_quoted_base_tokens() -> None:
    command = assemble_command(
        configured_command='runtime --profile "fast lane"',
        context=_context(),
    )

    assert command[:3] == ("runtime", "--profile", "fast lane")


def test_assemble_command_rejects_empty_configured_command() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        assemble_command(configured_command="   ", context=_context())


def test_assemble_command_rejects_invalid_shell_syntax() -> None:
    with pytest.raises(ValueError, match="not valid shell syntax"):
        assemble_command(configured_command='"unterminated', context=_context())


def test_command_preview_renders_shell_escaped_output() -> None:
    preview = command_preview(
        configured_command='runtime --profile "fast lane"',
        context=_context(),
    )

    assert preview.startswith("runtime --profile 'fast lane'")
    assert "--prompt-pack prompt-packs/stages/plan/system.md" in preview


def test_build_execution_environment_injects_stage_and_run_metadata() -> None:
    env = build_execution_environment(
        workspace_root=Path(".aidd"),
        context=_context(),
    )

    assert env["AIDD_WORKSPACE_ROOT"] == ".aidd"
    assert env["AIDD_STAGE"] == "plan"
    assert env["AIDD_WORK_ITEM"] == "WI-001"
    assert env["AIDD_RUN_ID"] == "run-001"
    assert env["AIDD_PROMPT_PACK_PATH"] == "prompt-packs/stages/plan/system.md"
    assert env["AIDD_RUNTIME_ID"] == "generic-cli"


def test_build_execution_environment_preserves_non_aidd_env_keys() -> None:
    env = build_execution_environment(
        workspace_root=Path(".aidd"),
        context=_context(),
        base_env={"PATH": "/usr/bin", "AIDD_STAGE": "stale"},
    )

    assert env["PATH"] == "/usr/bin"
    assert env["AIDD_STAGE"] == "plan"


def test_build_subprocess_spec_exposes_workspace_and_prompt_pack_paths(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd"
    prompt_pack_path = Path("prompt-packs/stages/plan/system.md")
    spec = build_subprocess_spec(
        configured_command="runtime --profile fast",
        workspace_root=workspace_root,
        context=GenericCliStageContext(
            stage="plan",
            work_item="WI-001",
            run_id="run-001",
            prompt_pack_path=prompt_pack_path,
        ),
        repository_root=repository_root,
    )

    expected_prompt_pack_path = (repository_root / prompt_pack_path).resolve(strict=False)
    assert spec.cwd == workspace_root.resolve(strict=False)
    assert spec.command[-2:] == ("--prompt-pack", expected_prompt_pack_path.as_posix())
    assert spec.env["AIDD_WORKSPACE_ROOT"] == workspace_root.resolve(strict=False).as_posix()
    assert spec.env["AIDD_PROMPT_PACK_PATH"] == expected_prompt_pack_path.as_posix()


def test_run_subprocess_with_streaming_returns_stdout_and_stderr(tmp_path: Path) -> None:
    script = (
        "import sys, time\n"
        "print('out-1', flush=True)\n"
        "print('err-1', file=sys.stderr, flush=True)\n"
        "time.sleep(0.05)\n"
        "print('out-2', flush=True)\n"
    )
    spec = GenericCliSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    stdout_events: list[str] = []
    stderr_events: list[str] = []
    result = run_subprocess_with_streaming(
        spec=spec,
        on_stdout=stdout_events.append,
        on_stderr=stderr_events.append,
    )

    assert isinstance(result, GenericCliRunResult)
    assert result.exit_code == 0
    assert "out-1\n" in result.stdout_text
    assert "out-2\n" in result.stdout_text
    assert "err-1\n" in result.stderr_text
    assert "out-1\n" in result.runtime_log_text
    assert "err-1\n" in result.runtime_log_text
    assert result.exit_classification is GenericCliExitClassification.SUCCESS
    assert stdout_events
    assert stderr_events


def test_run_subprocess_with_streaming_emits_early_stdout_before_process_end(
    tmp_path: Path,
) -> None:
    script = (
        "import time\n"
        "print('out-early', flush=True)\n"
        "time.sleep(0.2)\n"
        "print('out-late', flush=True)\n"
    )
    spec = GenericCliSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    callback_times: list[float] = []
    started_at = time.monotonic()
    run_subprocess_with_streaming(
        spec=spec,
        on_stdout=lambda _chunk: callback_times.append(time.monotonic()),
    )
    finished_at = time.monotonic()

    assert callback_times
    assert callback_times[0] - started_at < 0.15
    assert finished_at - callback_times[0] > 0.05


def test_persist_attempt_runtime_artifacts_writes_log_and_exit_metadata(tmp_path: Path) -> None:
    attempt_path = tmp_path / "attempt-0001"
    run_result = GenericCliRunResult(
        exit_code=17,
        stdout_text="out-1\nout-2\n",
        stderr_text="err-1\n",
        runtime_log_text="out-1\nerr-1\nout-2\n",
        exit_classification=GenericCliExitClassification.NON_ZERO_EXIT,
    )

    artifacts = persist_attempt_runtime_artifacts(
        attempt_path=attempt_path,
        run_result=run_result,
    )

    assert isinstance(artifacts, GenericCliRuntimeArtifacts)
    assert artifacts.runtime_log_path == attempt_path / RUN_RUNTIME_LOG_FILENAME
    assert artifacts.runtime_exit_metadata_path == attempt_path / RUNTIME_EXIT_METADATA_FILENAME
    assert artifacts.runtime_log_path.read_text(encoding="utf-8") == run_result.runtime_log_text

    exit_metadata = json.loads(artifacts.runtime_exit_metadata_path.read_text(encoding="utf-8"))
    assert exit_metadata == {
        "schema_version": 1,
        "exit_code": 17,
        "exit_classification": "non_zero_exit",
        "stdout_char_count": len(run_result.stdout_text),
        "stderr_char_count": len(run_result.stderr_text),
        "runtime_log_char_count": len(run_result.runtime_log_text),
    }


def test_resolve_exit_classification_prefers_stop_reason_over_exit_code() -> None:
    timeout_classification = _resolve_exit_classification(
        exit_code=0,
        stop_reason=GenericCliExitClassification.TIMEOUT,
    )
    cancelled_classification = _resolve_exit_classification(
        exit_code=7,
        stop_reason=GenericCliExitClassification.CANCELLED,
    )

    assert timeout_classification is GenericCliExitClassification.TIMEOUT
    assert cancelled_classification is GenericCliExitClassification.CANCELLED


def test_resolve_exit_classification_uses_exit_code_without_stop_reason() -> None:
    success_classification = _resolve_exit_classification(exit_code=0, stop_reason=None)
    non_zero_classification = _resolve_exit_classification(exit_code=3, stop_reason=None)

    assert success_classification is GenericCliExitClassification.SUCCESS
    assert non_zero_classification is GenericCliExitClassification.NON_ZERO_EXIT
