"""claude-code adapter."""

from aidd.adapters.base import RuntimeAdapterDescriptor, RuntimeAdapterRegistration

from .probe import probe

DESCRIPTOR = RuntimeAdapterDescriptor(
    runtime_id="claude-code",
    registration=RuntimeAdapterRegistration(
        runtime_id="claude-code",
        config_section="claude_code",
        support_tier="tier-1",
        default_command=(
            "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
        ),
        probe_command="claude",
        default_execution_mode="native",
        supported_execution_modes=("native", "adapter-flags"),
        brokered_default_command=(
            "claude -p --output-format stream-json --verbose --permission-mode default"
        ),
    ),
    protected_paths=(".claude", ".env"),
    credential_paths=(".claude/auth.json", ".claude/credentials.json", "claude.json"),
    config_paths=(".claude/settings.json", "claude.json"),
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
            "deferred-resume",
        }
    ),
)

__all__ = ["DESCRIPTOR", "probe"]
