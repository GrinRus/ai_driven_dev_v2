from __future__ import annotations

from pathlib import Path


def resolve_stage_brief_path_for_execution(
    *,
    stage_brief_path: Path,
    workspace_root: Path,
) -> Path:
    if stage_brief_path.is_absolute():
        return stage_brief_path.resolve(strict=False)
    return (workspace_root / stage_brief_path).resolve(strict=False)


def resolve_prompt_pack_path_for_execution(
    *,
    prompt_pack_path: Path,
    repository_root: Path | None,
) -> Path:
    if prompt_pack_path.is_absolute():
        return prompt_pack_path.resolve(strict=False)

    base_dir = (repository_root or Path.cwd()).resolve(strict=False)
    return (base_dir / prompt_pack_path).resolve(strict=False)


def resolve_prompt_pack_paths_for_execution(
    *,
    prompt_pack_paths: tuple[Path, ...],
    repository_root: Path | None,
) -> tuple[Path, ...]:
    return tuple(
        resolve_prompt_pack_path_for_execution(
            prompt_pack_path=prompt_pack_path,
            repository_root=repository_root,
        )
        for prompt_pack_path in prompt_pack_paths
    )


__all__ = [
    "resolve_prompt_pack_path_for_execution",
    "resolve_prompt_pack_paths_for_execution",
    "resolve_stage_brief_path_for_execution",
]
