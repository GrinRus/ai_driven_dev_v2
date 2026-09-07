"""generic-cli adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor, RuntimeAdapterRegistration

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="generic-cli",
    registration=RuntimeAdapterRegistration(
        runtime_id="generic-cli",
        config_section="generic_cli",
        support_tier="tier-1",
        default_command="python",
        probe_command="python",
        default_execution_mode="adapter-flags",
        supported_execution_modes=("adapter-flags",),
        brokered_default_command="python",
    ),
    protected_paths=(".env",),
    credential_paths=("auth.json", "credentials", "credentials.json", "token.json", "tokens.json"),
    config_paths=("settings.json",),
    capabilities=frozenset(
        {
            "raw-log-stream",
            "non-interactive",
            "working-directory",
            "env-injection",
            "permission-policy",
        }
    ),
)

__all__ = ["DESCRIPTOR", "probe"]
