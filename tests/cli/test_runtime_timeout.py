from __future__ import annotations

from pathlib import Path

from aidd.cli.support import _runtime_timeout_for_runtime
from aidd.config import AiddConfig, RuntimeConfig
from aidd.runtime_catalog import RuntimeExecutionMode


def _config() -> AiddConfig:
    return AiddConfig(
        workspace_root=Path(".aidd"),
        runtime_configs={
            "generic-cli": RuntimeConfig("python", RuntimeExecutionMode.ADAPTER_FLAGS, None, {}),
            "claude-code": RuntimeConfig(
                "claude",
                RuntimeExecutionMode.NATIVE,
                1200,
                {"research": 1500, "implement": 1800},
            ),
            "codex": RuntimeConfig("codex", RuntimeExecutionMode.NATIVE, 900, {}),
            "opencode": RuntimeConfig("opencode", RuntimeExecutionMode.NATIVE, 900, {}),
            "qwen": RuntimeConfig("qwen", RuntimeExecutionMode.NATIVE, 900, {}),
        },
        max_repair_attempts=2,
    )


def test_runtime_timeout_prefers_stage_specific_override() -> None:
    cfg = _config()

    assert (
        _runtime_timeout_for_runtime(
            runtime="claude-code",
            cfg=cfg,
            stage="research",
        )
        == 1500
    )
    assert (
        _runtime_timeout_for_runtime(
            runtime="claude-code",
            cfg=cfg,
            stage="qa",
        )
        == 1200
    )
    assert _runtime_timeout_for_runtime(runtime="codex", cfg=cfg, stage="plan") == 900
