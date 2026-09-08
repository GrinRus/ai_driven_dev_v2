from __future__ import annotations

from pathlib import Path

import pytest

from aidd.adapters.base import RuntimeAdapterDescriptor, RuntimeAdapterRegistration
from aidd.adapters.registry import runtime_adapter_descriptors
from aidd.runtime_catalog import (
    RuntimeExecutionMode,
    RuntimeSelector,
    get_runtime_definition,
    runtime_ids,
)


def test_runtime_registry_covers_maintained_runtimes() -> None:
    assert runtime_ids() == (
        "generic-cli",
        "claude-code",
        "codex",
        "opencode",
        "qwen",
    )


def test_native_provider_defaults() -> None:
    claude_code = get_runtime_definition("claude-code")
    codex = get_runtime_definition("codex")
    opencode = get_runtime_definition("opencode")
    qwen = get_runtime_definition("qwen")

    assert claude_code.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert (
        claude_code.default_command
        == "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
    )
    assert codex.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert codex.default_command == (
        "codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json -"
    )
    assert codex.brokered_default_command == (
        "codex exec --sandbox workspace-write --skip-git-repo-check --json -"
    )
    assert opencode.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert opencode.default_command == "opencode run --format json --dangerously-skip-permissions"
    assert qwen.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert qwen.default_command == "qwen --approval-mode auto --output-format stream-json"
    assert qwen.brokered_default_command == (
        "qwen --approval-mode default --output-format stream-json"
    )


def test_catalog_projects_adapter_owned_registration_without_compatibility_drift() -> None:
    descriptors = runtime_adapter_descriptors()

    assert tuple(descriptor.runtime_id for descriptor in descriptors) == runtime_ids()
    for descriptor in descriptors:
        registration = descriptor.registration
        assert registration is not None
        definition = get_runtime_definition(descriptor.runtime_id)

        assert definition.runtime_id == registration.runtime_id
        assert definition.config_section == registration.config_section
        assert definition.support_tier == registration.support_tier
        assert definition.default_command == registration.default_command
        assert definition.probe_command == registration.probe_command
        assert definition.default_execution_mode.value == registration.default_execution_mode
        assert tuple(mode.value for mode in definition.supported_execution_modes) == (
            registration.supported_execution_modes
        )
        assert definition.brokered_default_command == registration.brokered_default_command
        assert {selector.value for selector in definition.supported_selectors} == set(
            registration.supported_selectors
        )
        assert tuple(mode.value for mode in definition.selector_execution_modes) == (
            registration.selector_execution_modes
        )


def test_runtime_catalog_has_no_built_in_provider_registration_literals() -> None:
    catalog_source = (Path(__file__).parents[2] / "src" / "aidd" / "runtime_catalog.py").read_text(
        encoding="utf-8"
    )

    for provider_literal in (".claude", ".codex", ".opencode", ".qwen", "auth.json"):
        assert provider_literal not in catalog_source


@pytest.mark.parametrize(
    "registration",
    (
        RuntimeAdapterRegistration(
            runtime_id="fake",
            config_section="fake",
            support_tier="tier-1",
            default_command="fake",
            probe_command="fake",
            default_execution_mode="native",
            supported_execution_modes=("native",),
        ),
    ),
)
def test_descriptor_registration_is_adapter_id_bound(
    registration: RuntimeAdapterRegistration,
) -> None:
    descriptor = RuntimeAdapterDescriptor(runtime_id="fake", registration=registration)
    assert descriptor.registration is registration

    with pytest.raises(ValueError, match="registration.runtime_id"):
        RuntimeAdapterDescriptor(
            runtime_id="other",
            registration=registration,
        )


def test_catalog_keeps_typed_selector_projection() -> None:
    codex = get_runtime_definition("codex")

    assert codex.supported_selectors == frozenset(RuntimeSelector)
    assert codex.selector_execution_modes == (
        RuntimeExecutionMode.NATIVE,
        RuntimeExecutionMode.ADAPTER_FLAGS,
    )
