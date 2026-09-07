"""Test-only adapter metadata used to prove external extension seams."""

from aidd.adapters.base import RuntimeAdapterDescriptor, RuntimeAdapterRegistration

FAKE_RUNTIME_ID = "fake-external"

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id=FAKE_RUNTIME_ID,
    registration=RuntimeAdapterRegistration(
        runtime_id=FAKE_RUNTIME_ID,
        config_section="fake_external",
        support_tier="test-only",
        default_command="fake-external-runtime --json -",
        probe_command="fake-external-runtime",
        default_execution_mode="native",
        supported_execution_modes=("native",),
        brokered_default_command="fake-external-runtime --safe --json -",
    ),
    protected_paths=(".fake-external",),
    credential_paths=(".fake-external/auth.json",),
    config_paths=(".fake-external/settings.toml",),
    capabilities=frozenset(
        {
            "raw-log-stream",
            "structured-log-stream",
            "questions",
            "non-interactive",
            "working-directory",
            "env-injection",
            "permission-policy",
        }
    ),
)

__all__ = ["DESCRIPTOR", "FAKE_RUNTIME_ID"]
