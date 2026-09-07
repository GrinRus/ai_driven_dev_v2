"""codex adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor, RuntimeAdapterRegistration

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="codex",
    registration=RuntimeAdapterRegistration(
        runtime_id="codex",
        config_section="codex",
        support_tier="tier-2",
        default_command=(
            "codex exec --dangerously-bypass-approvals-and-sandbox "
            "--skip-git-repo-check --json -"
        ),
        probe_command="codex",
        default_execution_mode="native",
        supported_execution_modes=("native", "adapter-flags"),
        brokered_default_command=(
            "codex exec --sandbox workspace-write --skip-git-repo-check --json -"
        ),
        supported_selectors=("model", "reasoning_effort"),
        selector_execution_modes=("native", "adapter-flags"),
    ),
    protected_paths=(".codex", ".env"),
    credential_paths=(".codex/auth.json", ".codex/credentials.json", "codex.json"),
    config_paths=(".codex/config.toml", "codex.json"),
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
            "live-decisions",
            "native-transport",
        }
    ),
)

__all__ = ["DESCRIPTOR", "probe"]
