from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ClaudeCodeCommandContext:
    stage: str
    work_item: str
    run_id: str
    workspace_root: Path
    stage_brief_path: Path
    prompt_pack_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("Stage context requires a non-empty stage id.")
        if not self.work_item.strip():
            raise ValueError("Stage context requires a non-empty work item id.")
        if not self.run_id.strip():
            raise ValueError("Stage context requires a non-empty run id.")
        if str(self.workspace_root).strip() == "":
            raise ValueError("Stage context requires a workspace root path.")
        if str(self.stage_brief_path).strip() == "":
            raise ValueError("Stage context requires a stage brief path.")
        if not self.prompt_pack_paths:
            raise ValueError("Stage context requires at least one prompt-pack path.")
        if any(str(path).strip() == "" for path in self.prompt_pack_paths):
            raise ValueError("Stage context prompt-pack paths must not be empty.")


@dataclass(frozen=True, slots=True)
class ClaudeCodeConfigFlag:
    flag: str
    value: str | None = None

    def __post_init__(self) -> None:
        if not self.flag.strip():
            raise ValueError("Config flag name must not be empty.")

    @property
    def normalized_flag(self) -> str:
        stripped = self.flag.strip()
        if stripped.startswith("--"):
            return stripped
        return f"--{stripped}"


@dataclass(frozen=True, slots=True)
class ClaudeCodeLaunchOptions:
    sandbox_mode: str | None = None
    permission_mode: str | None = None
    config_flags: tuple[ClaudeCodeConfigFlag, ...] = ()

    def __post_init__(self) -> None:
        if self.sandbox_mode is not None and not self.sandbox_mode.strip():
            raise ValueError("Sandbox mode must not be blank when provided.")
        if self.permission_mode is not None and not self.permission_mode.strip():
            raise ValueError("Permission mode must not be blank when provided.")


def _resolve_stage_brief_path_for_execution(
    *,
    stage_brief_path: Path,
    workspace_root: Path,
) -> Path:
    if stage_brief_path.is_absolute():
        return stage_brief_path.resolve(strict=False)

    return (workspace_root / stage_brief_path).resolve(strict=False)


def _resolve_prompt_pack_paths_for_execution(
    *,
    prompt_pack_paths: tuple[Path, ...],
    repository_root: Path | None,
) -> tuple[Path, ...]:
    base_dir = (repository_root or Path.cwd()).resolve(strict=False)
    resolved: list[Path] = []
    for prompt_path in prompt_pack_paths:
        if prompt_path.is_absolute():
            resolved.append(prompt_path.resolve(strict=False))
            continue
        resolved.append((base_dir / prompt_path).resolve(strict=False))
    return tuple(resolved)


def _assemble_launch_flags(options: ClaudeCodeLaunchOptions | None) -> tuple[str, ...]:
    if options is None:
        return ()

    launch_flags: list[str] = []
    if options.sandbox_mode is not None:
        launch_flags.extend(("--sandbox", options.sandbox_mode.strip()))

    if options.permission_mode is not None:
        normalized_permission_mode = options.permission_mode.strip()
        if normalized_permission_mode == "bypass":
            launch_flags.append("--dangerously-skip-permissions")
        else:
            launch_flags.extend(("--permission-mode", normalized_permission_mode))

    for config_flag in options.config_flags:
        launch_flags.append(config_flag.normalized_flag)
        if config_flag.value is not None:
            launch_flags.append(config_flag.value)
    return tuple(launch_flags)


def assemble_command(
    *,
    configured_command: str,
    context: ClaudeCodeCommandContext,
    launch_options: ClaudeCodeLaunchOptions | None = None,
    repository_root: Path | None = None,
) -> tuple[str, ...]:
    stripped = configured_command.strip()
    if not stripped:
        raise ValueError("Configured claude-code command must not be empty.")

    try:
        base_tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(
            "Configured claude-code command is not valid shell syntax: "
            f"{configured_command!r}"
        ) from exc
    if not base_tokens:
        raise ValueError("Configured claude-code command must produce at least one token.")

    resolved_workspace_root = context.workspace_root.resolve(strict=False)
    resolved_stage_brief_path = _resolve_stage_brief_path_for_execution(
        stage_brief_path=context.stage_brief_path,
        workspace_root=resolved_workspace_root,
    )
    resolved_prompt_pack_paths = _resolve_prompt_pack_paths_for_execution(
        prompt_pack_paths=context.prompt_pack_paths,
        repository_root=repository_root,
    )
    launch_flags = _assemble_launch_flags(launch_options)

    command: list[str] = [
        *base_tokens,
        *launch_flags,
        "--stage",
        context.stage,
        "--work-item",
        context.work_item,
        "--run-id",
        context.run_id,
        "--workspace-root",
        resolved_workspace_root.as_posix(),
        "--stage-brief",
        resolved_stage_brief_path.as_posix(),
    ]
    for prompt_pack_path in resolved_prompt_pack_paths:
        command.extend(("--prompt-pack", prompt_pack_path.as_posix()))

    return tuple(command)


def command_preview(
    *,
    configured_command: str,
    context: ClaudeCodeCommandContext,
    launch_options: ClaudeCodeLaunchOptions | None = None,
    repository_root: Path | None = None,
) -> str:
    return " ".join(
        shlex.quote(token)
        for token in assemble_command(
            configured_command=configured_command,
            context=context,
            launch_options=launch_options,
            repository_root=repository_root,
        )
    )
