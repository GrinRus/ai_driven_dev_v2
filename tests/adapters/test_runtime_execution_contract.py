from __future__ import annotations

from aidd.adapters.claude_code.runner import ClaudeCodeRunResult, ClaudeCodeSubprocessSpec
from aidd.adapters.codex.runner import CodexRunResult, CodexSubprocessSpec
from aidd.adapters.generic_cli.runner import GenericCliRunResult, GenericCliSubprocessSpec
from aidd.adapters.opencode.runner import OpenCodeRunResult, OpenCodeSubprocessSpec
from aidd.adapters.runtime_execution import RuntimeRunResult, RuntimeSubprocessSpec


def test_adapter_specs_share_runtime_subprocess_contract() -> None:
    assert issubclass(GenericCliSubprocessSpec, RuntimeSubprocessSpec)
    assert issubclass(ClaudeCodeSubprocessSpec, RuntimeSubprocessSpec)
    assert issubclass(CodexSubprocessSpec, RuntimeSubprocessSpec)
    assert issubclass(OpenCodeSubprocessSpec, RuntimeSubprocessSpec)


def test_adapter_results_share_runtime_run_result_contract() -> None:
    assert issubclass(GenericCliRunResult, RuntimeRunResult)
    assert issubclass(ClaudeCodeRunResult, RuntimeRunResult)
    assert issubclass(CodexRunResult, RuntimeRunResult)
    assert issubclass(OpenCodeRunResult, RuntimeRunResult)


def test_runtime_run_result_exposes_common_contract_names() -> None:
    result = RuntimeRunResult[str](
        exit_code=2,
        stdout_text="out",
        stderr_text="err",
        runtime_log_text="log",
        exit_classification="non-zero",
    )

    assert result.stdout == "out"
    assert result.stderr == "err"
    assert result.runtime_log == "log"
    assert result.normalized_exit_classification == "non-zero"
