from __future__ import annotations

from pathlib import Path

from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.cli.main import _runtime_timeout_for_runtime
from aidd.config import AiddConfig


def _config() -> AiddConfig:
    return AiddConfig(
        workspace_root=Path(".aidd"),
        generic_cli_command="python",
        claude_code_command="claude",
        codex_command="codex",
        opencode_command="opencode",
        generic_cli_execution_mode=RuntimeExecutionMode.ADAPTER_FLAGS,
        claude_code_execution_mode=RuntimeExecutionMode.NATIVE,
        codex_execution_mode=RuntimeExecutionMode.NATIVE,
        opencode_execution_mode=RuntimeExecutionMode.NATIVE,
        generic_cli_timeout_seconds=None,
        claude_code_timeout_seconds=1200,
        codex_timeout_seconds=900,
        opencode_timeout_seconds=900,
        generic_cli_stage_timeout_seconds={},
        claude_code_stage_timeout_seconds={"research": 1500, "implement": 1800},
        codex_stage_timeout_seconds={},
        opencode_stage_timeout_seconds={},
        log_mode="both",
        max_repair_attempts=2,
    )


def test_runtime_timeout_prefers_stage_specific_override() -> None:
    cfg = _config()

    assert _runtime_timeout_for_runtime(
        runtime="claude-code",
        cfg=cfg,
        stage="research",
    ) == 1500
    assert _runtime_timeout_for_runtime(
        runtime="claude-code",
        cfg=cfg,
        stage="qa",
    ) == 1200
    assert _runtime_timeout_for_runtime(runtime="codex", cfg=cfg, stage="plan") == 900
