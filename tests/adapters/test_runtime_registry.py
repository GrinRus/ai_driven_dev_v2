from __future__ import annotations

from aidd.adapters.runtime_registry import (
    RuntimeExecutionMode,
    get_runtime_definition,
    runtime_ids,
)


def test_runtime_registry_covers_maintained_runtimes() -> None:
    assert runtime_ids() == ("generic-cli", "claude-code", "codex", "opencode")


def test_codex_and_opencode_default_to_native_execution() -> None:
    codex = get_runtime_definition("codex")
    opencode = get_runtime_definition("opencode")

    assert codex.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert codex.default_command == "codex exec --full-auto --skip-git-repo-check --json -"
    assert opencode.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert opencode.default_command == "opencode run --format json --dangerously-skip-permissions"
