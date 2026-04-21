from __future__ import annotations

import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GenericCliStageContext:
    stage: str
    work_item: str
    run_id: str
    prompt_pack_path: Path

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("Stage context requires a non-empty stage id.")
        if not self.work_item.strip():
            raise ValueError("Stage context requires a non-empty work item id.")
        if not self.run_id.strip():
            raise ValueError("Stage context requires a non-empty run id.")
        if str(self.prompt_pack_path).strip() == "":
            raise ValueError("Stage context requires a prompt-pack path.")


def assemble_command(
    *,
    configured_command: str,
    context: GenericCliStageContext,
) -> tuple[str, ...]:
    stripped = configured_command.strip()
    if not stripped:
        raise ValueError("Configured generic-cli command must not be empty.")

    try:
        base_tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(
            f"Configured generic-cli command is not valid shell syntax: {configured_command!r}"
        ) from exc

    if not base_tokens:
        raise ValueError("Configured generic-cli command must produce at least one token.")

    return (
        *base_tokens,
        "--stage",
        context.stage,
        "--work-item",
        context.work_item,
        "--run-id",
        context.run_id,
        "--prompt-pack",
        context.prompt_pack_path.as_posix(),
    )


def command_preview(
    *,
    configured_command: str,
    context: GenericCliStageContext,
) -> str:
    return " ".join(shlex.quote(token) for token in assemble_command(
        configured_command=configured_command,
        context=context,
    ))


def build_execution_environment(
    *,
    workspace_root: Path,
    context: GenericCliStageContext,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = dict(base_env or {})
    env.update(
        {
            "AIDD_WORKSPACE_ROOT": workspace_root.as_posix(),
            "AIDD_STAGE": context.stage,
            "AIDD_WORK_ITEM": context.work_item,
            "AIDD_RUN_ID": context.run_id,
            "AIDD_PROMPT_PACK_PATH": context.prompt_pack_path.as_posix(),
            "AIDD_RUNTIME_ID": "generic-cli",
        }
    )
    return env
