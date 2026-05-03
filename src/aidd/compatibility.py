from __future__ import annotations

from enum import StrEnum
from typing import Any

LEGACY_RAW_PROVIDER_COMMAND_UPGRADE = "legacy-raw-provider-command-upgrade"
LEGACY_ARTIFACT_INDEX_WITHOUT_PROMPT_PROVENANCE = (
    "legacy-artifact-index-without-prompt-provenance"
)

COMPATIBILITY_INVENTORY: dict[str, str] = {
    LEGACY_RAW_PROVIDER_COMMAND_UPGRADE: (
        "Config files that set a provider command to the raw probe binary, such as "
        "`codex`, are upgraded to the native default command when no explicit mode is set."
    ),
    LEGACY_ARTIFACT_INDEX_WITHOUT_PROMPT_PROVENANCE: (
        "Run artifact indexes written before prompt-pack provenance existed are accepted "
        "with an empty provenance list."
    ),
}


def should_upgrade_legacy_raw_provider_command(
    *,
    section: dict[str, Any],
    command: str,
    probe_command: str,
    default_execution_mode: StrEnum,
    native_mode: StrEnum,
) -> bool:
    return (
        "mode" not in section
        and command == probe_command
        and default_execution_mode is native_mode
    )


def legacy_prompt_pack_provenance_payload(payload: dict[str, Any]) -> list[Any]:
    raw_prompt_pack_provenance = payload.get("prompt_pack_provenance", [])
    if isinstance(raw_prompt_pack_provenance, list):
        return raw_prompt_pack_provenance
    return []
