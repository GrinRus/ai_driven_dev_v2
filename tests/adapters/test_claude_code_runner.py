from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest

from aidd.adapters.claude_code.runner import (
    ClaudeCodeCommandContext,
    ClaudeCodeConfigFlag,
    ClaudeCodeExitClassification,
    ClaudeCodeLaunchOptions,
    ClaudeCodeQuestionDetection,
    ClaudeCodeQuestionPersistence,
    ClaudeCodeQuestionRouting,
    ClaudeCodeResumeDecision,
    ClaudeCodeRunResult,
    ClaudeCodeRuntimeArtifacts,
    ClaudeCodeSubprocessSpec,
    _resolve_exit_classification,
    assemble_command,
    build_execution_environment,
    build_subprocess_spec,
    command_preview,
    detect_question_or_pause_events,
    normalize_structured_events,
    persist_attempt_runtime_log,
    persist_normalized_events_jsonl,
    persist_surfaced_questions,
    prepare_resume_after_answers,
    route_questions_with_file_fallback,
    run_subprocess_with_streaming,
)
from aidd.core.interview import (
    AdapterQuestionEvent,
    QuestionPolicy,
    persist_answers_document,
    persist_questions_document,
)
from aidd.core.run_store import persist_stage_status


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


def _write_dry_run_fixture_script(tmp_path: Path) -> Path:
    script_path = tmp_path / "claude_dry_run_fixture.py"
    script_path.write_text(
        "import argparse\n"
        "import time\n"
        "\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--stage', required=True)\n"
        "parser.add_argument('--work-item', required=True)\n"
        "parser.add_argument('--run-id', required=True)\n"
        "parser.add_argument('--workspace-root', required=True)\n"
        "parser.add_argument('--stage-brief', required=True)\n"
        "parser.add_argument('--prompt-pack', action='append', default=[])\n"
        "parser.add_argument('--sleep-seconds', type=float, default=0.0)\n"
        "parser.add_argument('--exit-code', type=int, default=0)\n"
        "parser.add_argument('--emit-json-events', action='store_true')\n"
        "args, _unknown = parser.parse_known_args()\n"
        "print(f'fixture-start stage={args.stage}', flush=True)\n"
        "print(f'fixture-prompt-packs={len(args.prompt_pack)}', flush=True)\n"
        "if args.emit_json_events:\n"
        "    print('{\"event\":\"fixture_tick\",\"ok\":true}', flush=True)\n"
        "if args.sleep_seconds > 0:\n"
        "    time.sleep(args.sleep_seconds)\n"
        "print('fixture-end', flush=True)\n"
        "raise SystemExit(args.exit_code)\n",
        encoding="utf-8",
    )
    return script_path


def _prepare_dry_run_workspace(
    *,
    repository_root: Path,
    workspace_root: Path,
) -> None:
    (workspace_root / "stages/plan").mkdir(parents=True, exist_ok=True)
    (workspace_root / "stages/plan/stage-brief.md").write_text(
        "# Stage Brief\n\nDry-run fixture input.\n",
        encoding="utf-8",
    )
    prompt_pack_root = repository_root / "prompt-packs/stages/plan"
    prompt_pack_root.mkdir(parents=True, exist_ok=True)
    (prompt_pack_root / "system.md").write_text(
        "# System\n\nDry-run system prompt.\n",
        encoding="utf-8",
    )
    (prompt_pack_root / "task.md").write_text(
        "# Task\n\nDry-run task prompt.\n",
        encoding="utf-8",
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


def test_resolve_exit_classification_prefers_stop_reason_over_exit_code() -> None:
    timeout_classification = _resolve_exit_classification(
        exit_code=0,
        stop_reason=ClaudeCodeExitClassification.TIMEOUT,
    )
    cancelled_classification = _resolve_exit_classification(
        exit_code=7,
        stop_reason=ClaudeCodeExitClassification.USER_CANCELLED,
    )

    assert timeout_classification is ClaudeCodeExitClassification.TIMEOUT
    assert cancelled_classification is ClaudeCodeExitClassification.USER_CANCELLED


def test_resolve_exit_classification_maps_non_zero_exit_to_runtime_class() -> None:
    classification = _resolve_exit_classification(exit_code=3, stop_reason=None)

    assert classification is ClaudeCodeExitClassification.RUNTIME_NON_ZERO_EXIT


def test_run_subprocess_with_streaming_classifies_adapter_failures(tmp_path: Path) -> None:
    spec = ClaudeCodeSubprocessSpec(
        command=("definitely-missing-aidd-claude-command",),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    result = run_subprocess_with_streaming(spec=spec)

    assert result.exit_classification is ClaudeCodeExitClassification.ADAPTER_FAILURE
    assert result.exit_code == -1
    assert "adapter-failure" in result.runtime_log_text


def test_run_subprocess_with_streaming_classifies_timeout(tmp_path: Path) -> None:
    script = (
        "import time\n"
        "print('started', flush=True)\n"
        "time.sleep(5)\n"
        "print('finished', flush=True)\n"
    )
    spec = ClaudeCodeSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    result = run_subprocess_with_streaming(spec=spec, timeout_seconds=0.5)

    assert isinstance(result, ClaudeCodeRunResult)
    assert result.exit_classification is ClaudeCodeExitClassification.TIMEOUT
    assert "started\n" in result.runtime_log_text
    assert "finished\n" not in result.runtime_log_text


def test_run_subprocess_with_streaming_classifies_runtime_non_zero_exit(tmp_path: Path) -> None:
    script = (
        "import sys\n"
        "print('out-before-exit', flush=True)\n"
        "print('err-before-exit', file=sys.stderr, flush=True)\n"
        "raise SystemExit(3)\n"
    )
    spec = ClaudeCodeSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    result = run_subprocess_with_streaming(spec=spec)

    assert result.exit_code == 3
    assert result.exit_classification is ClaudeCodeExitClassification.RUNTIME_NON_ZERO_EXIT
    assert "out-before-exit\n" in result.stdout_text
    assert "err-before-exit\n" in result.stderr_text


def test_run_subprocess_with_streaming_classifies_cancellation(tmp_path: Path) -> None:
    script = (
        "import time\n"
        "print('ready', flush=True)\n"
        "time.sleep(5)\n"
        "print('never-reached', flush=True)\n"
    )
    spec = ClaudeCodeSubprocessSpec(
        command=(sys.executable, "-c", script),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    cancel_event = threading.Event()
    first_stdout_seen = threading.Event()

    def _on_stdout(chunk: str) -> None:
        if "ready" in chunk:
            first_stdout_seen.set()

    def _request_cancel() -> bool:
        if first_stdout_seen.is_set():
            cancel_event.set()
        return cancel_event.is_set()

    result = run_subprocess_with_streaming(
        spec=spec,
        on_stdout=_on_stdout,
        cancel_requested=_request_cancel,
    )

    assert result.exit_classification is ClaudeCodeExitClassification.USER_CANCELLED
    assert "ready\n" in result.runtime_log_text
    assert "never-reached\n" not in result.runtime_log_text


def test_run_subprocess_with_streaming_emits_stdout_and_stderr_callbacks(tmp_path: Path) -> None:
    script = (
        "import sys, time\n"
        "print('out-1', flush=True)\n"
        "print('err-1', file=sys.stderr, flush=True)\n"
        "time.sleep(0.05)\n"
        "print('out-2', flush=True)\n"
    )
    spec = ClaudeCodeSubprocessSpec(
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

    assert result.exit_classification is ClaudeCodeExitClassification.SUCCESS
    assert "out-1\n" in result.stdout_text
    assert "out-2\n" in result.stdout_text
    assert "err-1\n" in result.stderr_text
    assert "out-1\n" in result.runtime_log_text
    assert "err-1\n" in result.runtime_log_text
    assert stdout_events
    assert stderr_events


def test_run_subprocess_with_streaming_emits_stdout_before_process_end(tmp_path: Path) -> None:
    script = (
        "import time\n"
        "print('out-early', flush=True)\n"
        "time.sleep(0.2)\n"
        "print('out-late', flush=True)\n"
    )
    spec = ClaudeCodeSubprocessSpec(
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


def test_build_subprocess_spec_run_fixture_launch_success(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd" / "workitems" / "WI-001"
    fixture_script = _write_dry_run_fixture_script(tmp_path)
    _prepare_dry_run_workspace(repository_root=repository_root, workspace_root=workspace_root)
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
    spec = build_subprocess_spec(
        configured_command=f"{sys.executable} {fixture_script.as_posix()}",
        context=context,
        repository_root=repository_root,
    )

    result = run_subprocess_with_streaming(spec=spec)

    assert result.exit_classification is ClaudeCodeExitClassification.SUCCESS
    assert result.exit_code == 0
    assert "fixture-start stage=plan\n" in result.runtime_log_text
    assert "fixture-prompt-packs=2\n" in result.runtime_log_text
    assert "fixture-end\n" in result.runtime_log_text


def test_build_subprocess_spec_run_fixture_timeout(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd" / "workitems" / "WI-001"
    fixture_script = _write_dry_run_fixture_script(tmp_path)
    _prepare_dry_run_workspace(repository_root=repository_root, workspace_root=workspace_root)
    context = ClaudeCodeCommandContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=Path("stages/plan/stage-brief.md"),
        prompt_pack_paths=(Path("prompt-packs/stages/plan/system.md"),),
    )
    spec = build_subprocess_spec(
        configured_command=f"{sys.executable} {fixture_script.as_posix()} --sleep-seconds 5",
        context=context,
        repository_root=repository_root,
    )

    result = run_subprocess_with_streaming(spec=spec, timeout_seconds=0.1)

    assert result.exit_classification is ClaudeCodeExitClassification.TIMEOUT
    assert "fixture-start stage=plan\n" in result.runtime_log_text
    assert "fixture-end\n" not in result.runtime_log_text


def test_build_subprocess_spec_run_fixture_cancelled(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd" / "workitems" / "WI-001"
    fixture_script = _write_dry_run_fixture_script(tmp_path)
    _prepare_dry_run_workspace(repository_root=repository_root, workspace_root=workspace_root)
    context = ClaudeCodeCommandContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=Path("stages/plan/stage-brief.md"),
        prompt_pack_paths=(Path("prompt-packs/stages/plan/system.md"),),
    )
    spec = build_subprocess_spec(
        configured_command=f"{sys.executable} {fixture_script.as_posix()} --sleep-seconds 5",
        context=context,
        repository_root=repository_root,
    )

    cancel_event = threading.Event()
    first_stdout_seen = threading.Event()

    def _on_stdout(chunk: str) -> None:
        if "fixture-start" in chunk:
            first_stdout_seen.set()

    def _request_cancel() -> bool:
        if first_stdout_seen.is_set():
            cancel_event.set()
        return cancel_event.is_set()

    result = run_subprocess_with_streaming(
        spec=spec,
        on_stdout=_on_stdout,
        cancel_requested=_request_cancel,
    )

    assert result.exit_classification is ClaudeCodeExitClassification.USER_CANCELLED
    assert "fixture-start stage=plan\n" in result.runtime_log_text
    assert "fixture-end\n" not in result.runtime_log_text


def test_persist_attempt_runtime_log_writes_runtime_log_file(tmp_path: Path) -> None:
    attempt_path = tmp_path / "attempt-0001"
    run_result = ClaudeCodeRunResult(
        exit_code=0,
        stdout_text="out-1\n",
        stderr_text="err-1\n",
        runtime_log_text="out-1\nerr-1\n",
        exit_classification=ClaudeCodeExitClassification.SUCCESS,
    )

    artifacts = persist_attempt_runtime_log(
        attempt_path=attempt_path,
        run_result=run_result,
    )

    assert isinstance(artifacts, ClaudeCodeRuntimeArtifacts)
    assert artifacts.runtime_log_path == attempt_path / "runtime.log"
    assert artifacts.runtime_log_path.read_text(encoding="utf-8") == run_result.runtime_log_text


def test_normalize_structured_events_collects_json_from_stdout_and_stderr() -> None:
    run_result = ClaudeCodeRunResult(
        exit_code=0,
        stdout_text='{"event":"run_started","id":"abc"}\nnot-json\n',
        stderr_text='{"level":"warn","msg":"slow"}\n',
        runtime_log_text="",
        exit_classification=ClaudeCodeExitClassification.SUCCESS,
    )

    events = normalize_structured_events(run_result=run_result)

    assert events == (
        {"event": "run_started", "id": "abc", "source": "stdout"},
        {"level": "warn", "msg": "slow", "source": "stderr"},
    )


def test_detect_question_or_pause_events_from_runtime_events() -> None:
    detection = detect_question_or_pause_events(
        normalized_events=(
            {
                "event": "question_raised",
                "question_id": "Q7",
                "question": "Need database access?",
                "policy": "non-blocking",
                "source": "stdout",
            },
            {
                "event": "input_required",
                "paused": True,
                "source": "stderr",
            },
        )
    )

    assert isinstance(detection, ClaudeCodeQuestionDetection)
    assert detection.pause_detected is True
    assert detection.question_events[0].question_id == "Q7"
    assert detection.question_events[0].policy is QuestionPolicy.NON_BLOCKING
    assert detection.question_events[0].text == "Need database access?"
    assert detection.question_events[1].policy is QuestionPolicy.BLOCKING
    assert detection.question_events[1].text == "Runtime paused and requires operator input."


def test_detect_question_or_pause_events_ignores_non_question_events() -> None:
    detection = detect_question_or_pause_events(
        normalized_events=(
            {"event": "run_started", "source": "stdout"},
            {"event": "token", "message": "chunk", "source": "stdout"},
        )
    )

    assert detection.pause_detected is False
    assert detection.question_events == ()


def test_route_questions_with_file_fallback_uses_runtime_detection_when_present() -> None:
    runtime_detection = ClaudeCodeQuestionDetection(
        question_events=(
            AdapterQuestionEvent(
                question_id="Q1",
                text="Runtime-native question",
                policy=QuestionPolicy.BLOCKING,
            ),
        ),
        pause_detected=True,
    )

    routing = route_questions_with_file_fallback(
        workspace_root=Path(".aidd"),
        work_item="WI-001",
        stage="plan",
        runtime_detection=runtime_detection,
    )

    assert isinstance(routing, ClaudeCodeQuestionRouting)
    assert routing.used_file_fallback is False
    assert routing.pause_detected is True
    assert routing.question_events[0].text == "Runtime-native question"


def test_route_questions_with_file_fallback_reads_unresolved_blocking_questions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_questions_markdown=(
            "# Questions\n\n## Questions\n\n"
            "- `Q1` `[blocking]` Need repository URL?\n"
            "- `Q2` `[non-blocking]` Preferred naming?\n"
        ),
    )
    persist_answers_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_answers_markdown=(
            "# Answers\n\n## Answers\n\n"
            "- `Q2` `[resolved]` Use snake_case.\n"
        ),
    )

    routing = route_questions_with_file_fallback(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        runtime_detection=ClaudeCodeQuestionDetection(
            question_events=(),
            pause_detected=False,
        ),
    )

    assert routing.used_file_fallback is True
    assert routing.pause_detected is True
    assert routing.question_events == (
        AdapterQuestionEvent(
            question_id="Q1",
            text="Need repository URL?",
            policy=QuestionPolicy.BLOCKING,
        ),
    )


def test_persist_surfaced_questions_writes_questions_and_stage_metadata(
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

    persistence = persist_surfaced_questions(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_question_events=(
            AdapterQuestionEvent(
                question_id="Q1",
                text="Need repository URL?",
                policy=QuestionPolicy.BLOCKING,
            ),
        ),
    )

    assert isinstance(persistence, ClaudeCodeQuestionPersistence)
    assert persistence.metadata_updated is True
    assert persistence.unresolved_blocking_question_ids == ("Q1",)
    assert persistence.questions_path.exists()
    questions_text = persistence.questions_path.read_text(encoding="utf-8")
    assert "`Q1` `[blocking]` Need repository URL?" in questions_text

    metadata_payload = json.loads(persistence.stage_metadata_path.read_text(encoding="utf-8"))
    assert metadata_payload["claude_question_artifact"] == {
        "questions_path": "workitems/WI-001/stages/plan/questions.md",
        "unresolved_blocking_question_ids": ["Q1"],
    }


def test_persist_surfaced_questions_skips_metadata_update_when_file_missing(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    persistence = persist_surfaced_questions(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_question_events=(
            AdapterQuestionEvent(
                question_id="Q1",
                text="Need repository URL?",
                policy=QuestionPolicy.BLOCKING,
            ),
        ),
    )

    assert persistence.metadata_updated is False
    assert persistence.questions_path.exists()


def test_prepare_resume_after_answers_blocks_on_unresolved_questions(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_questions_markdown=(
            "# Questions\n\n## Questions\n\n"
            "- `Q1` `[blocking]` Need repository URL?\n"
        ),
    )

    resume = prepare_resume_after_answers(
        configured_command="claude",
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        run_id="run-001",
    )

    assert isinstance(resume, ClaudeCodeResumeDecision)
    assert resume.can_resume is False
    assert resume.resume_command is None
    assert resume.unresolved_blocking_question_ids == ("Q1",)


def test_prepare_resume_after_answers_builds_resume_command_when_unblocked(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_questions_markdown=(
            "# Questions\n\n## Questions\n\n"
            "- `Q1` `[blocking]` Need repository URL?\n"
        ),
    )
    persist_answers_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_answers_markdown=(
            "# Answers\n\n## Answers\n\n"
            "- `Q1` `[resolved]` Repository is github.com/acme/app.\n"
        ),
    )

    resume = prepare_resume_after_answers(
        configured_command='claude --profile "team alpha"',
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        run_id="run-001",
    )

    assert resume.can_resume is True
    assert resume.unresolved_blocking_question_ids == ()
    assert resume.resume_command == (
        "claude",
        "--profile",
        "team alpha",
        "resume",
        "--run-id",
        "run-001",
        "--stage",
        "plan",
        "--work-item",
        "WI-001",
    )


def test_question_and_resume_integration_paths(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    native_detection = detect_question_or_pause_events(
        normalized_events=(
            {
                "event": "question_raised",
                "question_id": "Q1",
                "question": "Runtime-native question?",
                "policy": "blocking",
                "source": "stdout",
            },
        )
    )
    native_routing = route_questions_with_file_fallback(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        runtime_detection=native_detection,
    )
    assert native_routing.used_file_fallback is False
    assert native_routing.question_events[0].text == "Runtime-native question?"

    persist_questions_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_questions_markdown=(
            "# Questions\n\n## Questions\n\n"
            "- `Q2` `[blocking]` Need repository URL?\n"
        ),
    )
    file_routing = route_questions_with_file_fallback(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        runtime_detection=ClaudeCodeQuestionDetection(
            question_events=(),
            pause_detected=False,
        ),
    )
    assert file_routing.used_file_fallback is True
    assert file_routing.question_events[0].question_id == "Q2"

    blocked_resume = prepare_resume_after_answers(
        configured_command="claude",
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        run_id="run-001",
    )
    assert blocked_resume.can_resume is False
    assert blocked_resume.unresolved_blocking_question_ids == ("Q2",)

    persist_answers_document(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        stage_output_answers_markdown=(
            "# Answers\n\n## Answers\n\n"
            "- `Q2` `[resolved]` Repository is github.com/acme/app.\n"
        ),
    )
    unblocked_resume = prepare_resume_after_answers(
        configured_command="claude",
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        run_id="run-001",
    )
    assert unblocked_resume.can_resume is True


def test_persist_normalized_events_jsonl_writes_events_when_available(tmp_path: Path) -> None:
    attempt_path = tmp_path / "attempt-0001"
    run_result = ClaudeCodeRunResult(
        exit_code=0,
        stdout_text='{"event":"run_started","id":"abc"}\n',
        stderr_text='{"event":"warn","msg":"slow"}\n',
        runtime_log_text="",
        exit_classification=ClaudeCodeExitClassification.SUCCESS,
    )

    events_path = persist_normalized_events_jsonl(
        attempt_path=attempt_path,
        run_result=run_result,
    )

    assert events_path == attempt_path / "events.jsonl"
    lines = events_path.read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(line) for line in lines] == [
        {"event": "run_started", "id": "abc", "source": "stdout"},
        {"event": "warn", "msg": "slow", "source": "stderr"},
    ]


def test_persist_normalized_events_jsonl_returns_none_without_json_lines(tmp_path: Path) -> None:
    attempt_path = tmp_path / "attempt-0001"
    run_result = ClaudeCodeRunResult(
        exit_code=0,
        stdout_text="plain text only\n",
        stderr_text="still plain text\n",
        runtime_log_text="",
        exit_classification=ClaudeCodeExitClassification.SUCCESS,
    )

    events_path = persist_normalized_events_jsonl(
        attempt_path=attempt_path,
        run_result=run_result,
    )

    assert events_path is None
    assert not (attempt_path / "events.jsonl").exists()


def test_artifact_persistence_and_classification_regression(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd" / "workitems" / "WI-001"
    fixture_script = _write_dry_run_fixture_script(tmp_path)
    _prepare_dry_run_workspace(repository_root=repository_root, workspace_root=workspace_root)
    context = ClaudeCodeCommandContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=Path("stages/plan/stage-brief.md"),
        prompt_pack_paths=(Path("prompt-packs/stages/plan/system.md"),),
    )
    spec = build_subprocess_spec(
        configured_command=(
            f"{sys.executable} {fixture_script.as_posix()} "
            "--emit-json-events --exit-code 3"
        ),
        context=context,
        repository_root=repository_root,
    )
    result = run_subprocess_with_streaming(spec=spec)

    assert result.exit_classification is ClaudeCodeExitClassification.RUNTIME_NON_ZERO_EXIT

    attempt_path = tmp_path / "attempt-0001"
    runtime_artifacts = persist_attempt_runtime_log(
        attempt_path=attempt_path,
        run_result=result,
    )
    events_path = persist_normalized_events_jsonl(
        attempt_path=attempt_path,
        run_result=result,
    )

    assert "fixture-start stage=plan\n" in runtime_artifacts.runtime_log_path.read_text(
        encoding="utf-8"
    )
    assert events_path is not None
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    assert {"event": "fixture_tick", "ok": True, "source": "stdout"} in events


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
