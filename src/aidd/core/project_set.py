from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.config import ProjectConfig, ProjectSetConfig


@dataclass(frozen=True, slots=True)
class ResolvedProject:
    id: str
    root: Path
    relative_root: str
    role: str | None


@dataclass(frozen=True, slots=True)
class ResolvedProjectSet:
    repository_root: Path
    projects: tuple[ResolvedProject, ...]

    def project_ids(self) -> tuple[str, ...]:
        return tuple(project.id for project in self.projects)


def _reject_absolute_root(project: ProjectConfig) -> None:
    if project.root.is_absolute():
        raise ValueError(
            f"Project `{project.id}` root must be repository-relative: "
            f"{project.root.as_posix()}."
        )


def _resolve_project_root(
    *,
    repository_root: Path,
    project: ProjectConfig,
) -> Path:
    _reject_absolute_root(project)
    candidate = repository_root / project.root
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(
            f"Project `{project.id}` root does not exist: {project.root.as_posix()}."
        ) from exc
    if not resolved.is_dir():
        raise ValueError(
            f"Project `{project.id}` root must be a directory: {project.root.as_posix()}."
        )
    return resolved


def resolve_project_set(
    *,
    repository_root: Path,
    project_set: ProjectSetConfig,
) -> ResolvedProjectSet:
    resolved_repository_root = repository_root.resolve(strict=True)
    resolved_projects: list[ResolvedProject] = []
    seen_roots: dict[Path, str] = {}

    for project in project_set.projects:
        resolved_root = _resolve_project_root(
            repository_root=resolved_repository_root,
            project=project,
        )
        if not resolved_root.is_relative_to(resolved_repository_root):
            raise ValueError(
                f"Project `{project.id}` root must stay inside repository root: "
                f"{project.root.as_posix()}."
            )
        existing_id = seen_roots.get(resolved_root)
        if existing_id is not None:
            raise ValueError(
                f"Project `{project.id}` root duplicates project `{existing_id}`: "
                f"{project.root.as_posix()}."
            )
        seen_roots[resolved_root] = project.id
        resolved_projects.append(
            ResolvedProject(
                id=project.id,
                root=resolved_root,
                relative_root=resolved_root.relative_to(resolved_repository_root).as_posix(),
                role=project.role,
            )
        )

    return ResolvedProjectSet(
        repository_root=resolved_repository_root,
        projects=tuple(resolved_projects),
    )
