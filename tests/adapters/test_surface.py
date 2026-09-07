from __future__ import annotations

import sys
from dataclasses import replace

import pytest

from aidd.adapters.base import CapabilityReport, RuntimeAdapterDescriptor
from aidd.adapters.surface import (
    RUNTIME_ADAPTER_SURFACES,
    get_runtime_adapter_descriptor,
    get_runtime_adapter_surface,
)
from aidd.runtime_catalog import RuntimeExecutionMode, runtime_ids


def test_runtime_adapter_surfaces_register_execution_and_conformance_callables() -> None:
    surfaces = RUNTIME_ADAPTER_SURFACES

    assert set(surfaces) == {"generic-cli", "claude-code", "codex", "opencode", "qwen"}
    for runtime_id, surface in surfaces.items():
        assert surface.runtime_id == runtime_id
        assert callable(surface.execute_stage_request_fn)
        assert callable(surface.conformance_spec_builder)


def test_default_execution_mode_comes_from_registered_surface() -> None:
    modes = {
        surface.runtime_id: surface.default_execution_mode
        for surface in RUNTIME_ADAPTER_SURFACES.values()
    }
    assert modes == {
        "generic-cli": RuntimeExecutionMode.ADAPTER_FLAGS,
        "claude-code": RuntimeExecutionMode.NATIVE,
        "codex": RuntimeExecutionMode.NATIVE,
        "opencode": RuntimeExecutionMode.NATIVE,
        "qwen": RuntimeExecutionMode.NATIVE,
    }


def test_every_maintained_runtime_resolves_a_stable_descriptor() -> None:
    assert tuple(RUNTIME_ADAPTER_SURFACES) == runtime_ids()

    expected_markers = {
        "generic-cli": {
            "protected_paths": (".env",),
            "credential_paths": ("auth.json", "credentials.json"),
            "config_paths": ("settings.json",),
        },
        "claude-code": {
            "protected_paths": (".claude", ".env"),
            "credential_paths": (".claude/auth.json", "claude.json"),
            "config_paths": (".claude/settings.json",),
        },
        "codex": {
            "protected_paths": (".codex", ".env"),
            "credential_paths": (".codex/auth.json", "codex.json"),
            "config_paths": (".codex/config.toml",),
        },
        "opencode": {
            "protected_paths": (".opencode", ".env"),
            "credential_paths": (".opencode/auth.json", "opencode.json"),
            "config_paths": (".opencode/config.json",),
        },
        "qwen": {
            "protected_paths": (".qwen", ".env"),
            "credential_paths": (".qwen/auth.json", "qwen.json"),
            "config_paths": (".qwen/settings.json",),
        },
    }

    for runtime_id in runtime_ids():
        descriptor = get_runtime_adapter_descriptor(runtime_id)
        surface = get_runtime_adapter_surface(runtime_id)

        assert descriptor is surface.descriptor
        assert descriptor.runtime_id == runtime_id
        assert isinstance(descriptor.protected_paths, tuple)
        assert isinstance(descriptor.credential_paths, tuple)
        assert isinstance(descriptor.config_paths, tuple)
        assert descriptor.capabilities
        assert descriptor.to_dict()["runtime_id"] == runtime_id
        for field_name, markers in expected_markers[runtime_id].items():
            assert set(markers).issubset(getattr(descriptor, field_name))


def test_adapter_descriptor_contract_is_immutable_and_non_secret() -> None:
    descriptor = RuntimeAdapterDescriptor(
        runtime_id="fake-runtime",
        protected_paths=(".fake-runtime", "project/.runtime"),
        credential_paths=(".fake-runtime/auth.json",),
        config_paths=(".fake-runtime/settings.json",),
        capabilities=("questions", "structured-logs"),
    )

    assert descriptor.supports_capability("questions")
    assert not descriptor.supports_capability("unknown")
    assert descriptor.to_dict() == {
        "runtime_id": "fake-runtime",
        "protected_paths": [".fake-runtime", "project/.runtime"],
        "credential_paths": [".fake-runtime/auth.json"],
        "config_paths": [".fake-runtime/settings.json"],
        "capabilities": ["questions", "structured-logs"],
    }
    with pytest.raises((AttributeError, TypeError)):
        descriptor.runtime_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "kwargs",
    (
        {"runtime_id": "", "protected_paths": ()},
        {"runtime_id": "fake", "protected_paths": ("/absolute",)},
        {"runtime_id": "fake", "protected_paths": ("../outside",)},
        {"runtime_id": "fake", "credential_paths": ("bad\\path",)},
        {"runtime_id": "fake", "config_paths": ("",)},
        {"runtime_id": "fake", "capabilities": ("not valid",)},
    ),
)
def test_adapter_descriptor_rejects_unsafe_metadata(kwargs: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        RuntimeAdapterDescriptor(**kwargs)


def test_surface_descriptor_accessor_fails_closed_for_unregistered_runtime() -> None:
    with pytest.raises(ValueError, match="Unsupported runtime id"):
        get_runtime_adapter_descriptor("not-registered")


def test_builtin_conformance_probe_uses_its_actual_transport_capabilities(monkeypatch) -> None:
    def forbidden_probe(_command: str) -> CapabilityReport:
        raise AssertionError("Built-in execution must not probe an external provider.")

    monkeypatch.setenv("PATH", "")
    surface = replace(get_runtime_adapter_surface("generic-cli"), probe=forbidden_probe)
    report = surface.probe_configured_command(
        configured_command="generic-cli-live-conformance", provider_command="python"
    )

    assert report.execution_command_available is True
    assert report.provider.available is True
    assert report.provider.command == "generic-cli-live-conformance"
    assert report.provider.preferred_transport == "in-process"
    assert report.provider.supports_permission_policy is True
    assert report.provider.supports_live_decisions is True


@pytest.mark.parametrize(
    ("runtime_id", "command"),
    (
        ("generic-cli", "generic-cli-live-conformance --unknown"),
        ("codex", "generic-cli-live-conformance"),
        ("generic-cli", "missing-aidd-fixture-runtime"),
        ("generic-cli", "'unterminated"),
        ("generic-cli", ""),
    ),
)
def test_execution_probe_rejects_unavailable_commands(monkeypatch, runtime_id, command) -> None:
    monkeypatch.setenv("PATH", "")
    surface = replace(
        get_runtime_adapter_surface(runtime_id),
        probe=lambda command: CapabilityReport(runtime_id, available=True, command=command),
    )

    report = surface.probe_configured_command(
        configured_command=command, provider_command="provider-fixture"
    )

    assert report.provider.available is True
    assert report.execution_command_available is False


def test_execution_probe_keeps_provider_and_command_availability_distinct() -> None:
    surface = replace(
        get_runtime_adapter_surface("generic-cli"),
        probe=lambda command: CapabilityReport("generic-cli", available=False, command=command),
    )
    report = surface.probe_configured_command(
        configured_command=sys.executable, provider_command="missing-provider"
    )

    assert report.provider.available is False
    assert report.execution_command_available is True
