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


@dataclass(frozen=True, slots=True)
class GenericCliSubprocessSpec:
    command: tuple[str, ...]
    cwd: Path
    env: dict[str, str]


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


def _resolve_prompt_pack_path_for_execution(
    *,
    prompt_pack_path: Path,
    repository_root: Path | None,
) -> Path:
    if prompt_pack_path.is_absolute():
        return prompt_pack_path.resolve(strict=False)

    base_dir = (repository_root or Path.cwd()).resolve(strict=False)
    return (base_dir / prompt_pack_path).resolve(strict=False)


def build_subprocess_spec(
    *,
    configured_command: str,
    workspace_root: Path,
    context: GenericCliStageContext,
    base_env: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> GenericCliSubprocessSpec:
    resolved_workspace_root = workspace_root.resolve(strict=False)
    resolved_prompt_pack_path = _resolve_prompt_pack_path_for_execution(
        prompt_pack_path=context.prompt_pack_path,
        repository_root=repository_root,
    )
    resolved_context = GenericCliStageContext(
        stage=context.stage,
        work_item=context.work_item,
        run_id=context.run_id,
        prompt_pack_path=resolved_prompt_pack_path,
    )
    return GenericCliSubprocessSpec(
        command=assemble_command(
            configured_command=configured_command,
            context=resolved_context,
        ),
        cwd=resolved_workspace_root,
        env=build_execution_environment(
            workspace_root=resolved_workspace_root,
            context=resolved_context,
            base_env=base_env,
        ),
    )
