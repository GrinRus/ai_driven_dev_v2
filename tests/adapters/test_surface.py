from __future__ import annotations

from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.adapters.surface import (
    default_execution_mode_for_surface,
    runtime_adapter_surfaces,
)


def test_runtime_adapter_surfaces_register_execution_and_conformance_callables() -> None:
    surfaces = {surface.runtime_id: surface for surface in runtime_adapter_surfaces()}

    assert set(surfaces) == {"generic-cli", "claude-code", "codex", "opencode", "qwen"}
    for surface in surfaces.values():
        assert callable(surface.execute_stage_request_fn)
        assert callable(surface.conformance_spec_builder)


def test_default_execution_mode_comes_from_registered_surface() -> None:
    modes = {
        surface.runtime_id: default_execution_mode_for_surface(surface)
        for surface in runtime_adapter_surfaces()
    }

    assert modes == {
        "generic-cli": RuntimeExecutionMode.ADAPTER_FLAGS,
        "claude-code": RuntimeExecutionMode.NATIVE,
        "codex": RuntimeExecutionMode.NATIVE,
        "opencode": RuntimeExecutionMode.NATIVE,
        "qwen": RuntimeExecutionMode.NATIVE,
    }
