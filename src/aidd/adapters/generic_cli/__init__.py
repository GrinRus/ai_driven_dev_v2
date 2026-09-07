"""generic-cli adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="generic-cli",
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
