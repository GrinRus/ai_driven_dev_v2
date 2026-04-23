from __future__ import annotations

import sys
from pathlib import Path

import pytest

from aidd.adapters.base import RuntimeStartRequest
from aidd.adapters.executor import RuntimeExecutionContext, execute_runtime_stage, probe_runtime

RUNTIME_IDS: tuple[str, ...] = (
    "generic-cli",
    "claude-code",
    "codex",
    "opencode",
    "pi-mono",
)


def _write_runtime_wrapper(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "import argparse",
                "import sys",
                "",
                "parser = argparse.ArgumentParser(add_help=False)",
                "parser.add_argument('--stage')",
                "parser.add_argument('--work-item')",
                "parser.add_argument('--run-id')",
                "parser.add_argument('--workspace-root')",
                "parser.add_argument('--stage-brief')",
                "parser.add_argument('--prompt-pack', action='append', default=[])",
                "args, _ = parser.parse_known_args()",
                "print(f'wrapper-ok:{args.stage}:{args.work_item}', flush=True)",
                "print('wrapper-stderr', file=sys.stderr, flush=True)",
                "raise SystemExit(0)",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _build_request(tmp_path: Path) -> RuntimeStartRequest:
    workspace_root = tmp_path / ".aidd"
    workspace_root.mkdir(parents=True, exist_ok=True)
    stage_brief_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "stage-brief.md"
    )
    stage_brief_path.parent.mkdir(parents=True, exist_ok=True)
    stage_brief_path.write_text("# Stage Brief\n", encoding="utf-8")

    prompt_pack = tmp_path / "prompt-packs" / "stages" / "idea" / "run.md"
    prompt_pack.parent.mkdir(parents=True, exist_ok=True)
    prompt_pack.write_text("# Prompt\n", encoding="utf-8")

    attempt_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-001"
        / "run-001"
        / "stages"
        / "idea"
        / "attempts"
        / "attempt-0001"
    )
    attempt_path.mkdir(parents=True, exist_ok=True)

    return RuntimeStartRequest(
        stage="idea",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        attempt_path=attempt_path,
        stage_brief_path=stage_brief_path,
        prompt_pack_paths=(prompt_pack,),
        repository_root=tmp_path,
    )


@pytest.mark.parametrize("runtime_id", RUNTIME_IDS)
def test_runtime_adapter_conformance_stage_execution(runtime_id: str, tmp_path: Path) -> None:
    wrapper = tmp_path / "runtime_wrapper.py"
    _write_runtime_wrapper(wrapper)
    request = _build_request(tmp_path)

    result = execute_runtime_stage(
        RuntimeExecutionContext(
            runtime_id=runtime_id,
            configured_command=f"{sys.executable} {wrapper.as_posix()}",
            request=request,
        )
    )

    assert result.runtime_id == runtime_id
    assert result.exit_classification == "success"
    assert result.runtime_log_path.exists()
    runtime_log_text = result.runtime_log_path.read_text(encoding="utf-8")
    assert "wrapper-ok:idea:WI-001" in runtime_log_text
    assert "wrapper-stderr" in runtime_log_text


@pytest.mark.parametrize("runtime_id", RUNTIME_IDS)
def test_runtime_adapter_conformance_probe_contract(runtime_id: str) -> None:
    report = probe_runtime(runtime_id=runtime_id, command="definitely-missing-aidd-runtime")

    assert report.runtime_id == runtime_id
    assert report.available is False
    assert isinstance(report.supports_tool_calls, bool)
    assert isinstance(report.supports_raw_log_stream, bool)
    assert isinstance(report.supports_structured_log_stream, bool)
    assert isinstance(report.supports_log_access, bool)
    assert isinstance(report.supports_questions, bool)
    assert isinstance(report.supports_resume, bool)
    assert isinstance(report.supports_interrupts, bool)
    assert isinstance(report.supports_subagents, bool)
    assert isinstance(report.supports_hooks, bool)
    assert isinstance(report.supports_non_interactive_mode, bool)
    assert isinstance(report.supports_working_directory_control, bool)
    assert isinstance(report.supports_env_injection, bool)
