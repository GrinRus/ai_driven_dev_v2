from __future__ import annotations

from aidd.adapters.runtime_registry import (
    RuntimeExecutionMode,
    get_runtime_definition,
    runtime_ids,
)


def test_runtime_registry_covers_maintained_runtimes() -> None:
    assert runtime_ids() == ("generic-cli", "claude-code", "codex", "opencode")


def test_native_provider_defaults() -> None:
    claude_code = get_runtime_definition("claude-code")
    codex = get_runtime_definition("codex")
    opencode = get_runtime_definition("opencode")

    assert claude_code.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert (
        claude_code.default_command
        == "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
    )
    assert codex.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert codex.default_command == "codex exec --full-auto --skip-git-repo-check --json -"
    assert opencode.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert opencode.default_command == "opencode run --format json --dangerously-skip-permissions"
