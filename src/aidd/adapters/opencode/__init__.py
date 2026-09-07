"""opencode adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor, RuntimeAdapterRegistration

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="opencode",
    registration=RuntimeAdapterRegistration(
        runtime_id="opencode",
        config_section="opencode",
        support_tier="tier-3",
        default_command="opencode run --format json --dangerously-skip-permissions",
        probe_command="opencode",
        default_execution_mode="native",
        supported_execution_modes=("native", "adapter-flags"),
        brokered_default_command="opencode run --format json",
    ),
    protected_paths=(".opencode", ".env"),
    credential_paths=(".opencode/auth.json", ".opencode/credentials.json", "opencode.json"),
    config_paths=(".opencode/config.json", "opencode.json"),
    capabilities=frozenset(
        {
            "raw-log-stream",
            "structured-log-stream",
            "questions",
            "resume",
            "subagents",
            "non-interactive",
            "working-directory",
            "env-injection",
            "permission-policy",
        }
    ),
)

__all__ = ["DESCRIPTOR", "probe"]
