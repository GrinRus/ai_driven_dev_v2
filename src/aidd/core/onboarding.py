from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.config import ProjectConfig, ProjectSetConfig
from aidd.core.project_set import (
    ResolvedProjectSet,
    persist_project_set_context,
    resolve_project_set,
)
from aidd.core.workspace import (
    WORKITEM_CONTEXT_USER_REQUEST_FILENAME,
    WORKITEM_METADATA_FILENAME,
    WORKSPACE_WORKITEMS_DIRNAME,
    WorkItemContextSeedResult,
    WorkspaceBootstrapService,
    work_item_context_root,
    workspace_workitems_root,
)


@dataclass(frozen=True, slots=True)
class OnboardingWorkItemSummary:
    work_item: str
    has_request_context: bool


@dataclass(frozen=True, slots=True)
class OnboardingProjectSummary:
    project_root: Path
    workspace_root: Path
    workspace_exists: bool
    work_items: tuple[OnboardingWorkItemSummary, ...]


@dataclass(frozen=True, slots=True)
class OnboardingWorkItemCreation:
    project: OnboardingProjectSummary
    work_item: str
    work_item_root: Path
    seeded_context: WorkItemContextSeedResult | None
    project_set_context_path: Path | None = None


@dataclass(frozen=True, slots=True)
class OnboardingProjectDeclaration:
    id: str
    root: Path
    role: str | None = None


class OnboardingService:
    def __init__(self, *, launch_root: Path, workspace_root: Path = Path(".aidd")) -> None:
        self._launch_root = launch_root
        self._workspace_root = workspace_root

    def inspect_project(self, raw_project_root: str | Path) -> OnboardingProjectSummary:
        project_root = self._resolve_project_root(raw_project_root)
        workspace_root = self._resolve_workspace_root(project_root=project_root)
        return OnboardingProjectSummary(
            project_root=project_root,
            workspace_root=workspace_root,
            workspace_exists=workspace_root.exists(),
            work_items=self._discover_work_items(workspace_root),
        )

    def create_work_item(
        self,
        *,
        raw_project_root: str | Path,
        work_item: str,
        request_text: str | None = None,
        force_context: bool = False,
        project_set: tuple[OnboardingProjectDeclaration, ...] = (),
    ) -> OnboardingWorkItemCreation:
        normalized_work_item = self._normalize_work_item(work_item)
        project = self.inspect_project(raw_project_root)
        resolved_project_set: ResolvedProjectSet | None = None
        if project_set:
            resolved_project_set = self.resolve_project_set(
                raw_project_root=project.project_root,
                project_set=project_set,
            )
        bootstrap = WorkspaceBootstrapService(root=project.workspace_root)
        work_item_root = bootstrap.bootstrap_work_item(work_item=normalized_work_item)
        seeded_context: WorkItemContextSeedResult | None = None
        if request_text is not None and request_text.strip():
            seeded_context = bootstrap.seed_request_context(
                work_item=normalized_work_item,
                request_text=request_text,
                project_root=project.project_root,
                force=force_context,
            )
        project_set_context_path: Path | None = None
        if resolved_project_set is not None:
            project_set_context_path = persist_project_set_context(
                workspace_root=project.workspace_root,
                work_item=normalized_work_item,
                project_set=resolved_project_set,
            )
        return OnboardingWorkItemCreation(
            project=self.inspect_project(project.project_root),
            work_item=normalized_work_item,
            work_item_root=work_item_root,
            seeded_context=seeded_context,
            project_set_context_path=project_set_context_path,
        )

    def resolve_project_set(
        self,
        *,
        raw_project_root: str | Path,
        project_set: tuple[OnboardingProjectDeclaration, ...],
    ) -> ResolvedProjectSet:
        project_root = self._resolve_project_root(raw_project_root)
        return resolve_project_set(
            repository_root=project_root,
            project_set=ProjectSetConfig(
                projects=tuple(
                    ProjectConfig(id=project.id, root=project.root, role=project.role)
                    for project in project_set
                )
            ),
        )

    def _resolve_project_root(self, raw_project_root: str | Path) -> Path:
        raw_path = Path(raw_project_root).expanduser()
        if any(part == ".." for part in raw_path.parts):
            raise ValueError("Project root must not contain parent traversal.")
        candidate = raw_path if raw_path.is_absolute() else self._launch_root / raw_path
        try:
            resolved_candidate = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ValueError(f"Project root does not exist: {candidate.as_posix()}.") from exc
        if not resolved_candidate.is_dir():
            raise ValueError(f"Project root must be a directory: {candidate.as_posix()}.")
        if not raw_path.is_absolute():
            launch_root = self._launch_root.resolve(strict=True)
            if not resolved_candidate.is_relative_to(launch_root):
                raise ValueError("Project root must stay inside the UI launch root.")
        return resolved_candidate

    def _resolve_workspace_root(self, *, project_root: Path) -> Path:
        raw_workspace = self._workspace_root
        if raw_workspace.is_absolute():
            raise ValueError("Setup mode requires a project-relative AIDD workspace root.")
        if any(part == ".." for part in raw_workspace.parts):
            raise ValueError("AIDD workspace root must not contain parent traversal.")
        resolved_workspace = (project_root / raw_workspace).resolve(strict=False)
        if not resolved_workspace.is_relative_to(project_root):
            raise ValueError("AIDD workspace root must stay inside the selected project root.")
        return resolved_workspace

    def _normalize_work_item(self, work_item: str) -> str:
        normalized_work_item = work_item.strip()
        if not normalized_work_item:
            raise ValueError("work_item is required.")
        if normalized_work_item in {".", ".."}:
            raise ValueError("work_item must be a plain identifier.")
        if "/" in normalized_work_item or "\\" in normalized_work_item:
            raise ValueError("work_item must not contain path separators.")
        work_item_path = Path(normalized_work_item)
        if work_item_path.is_absolute() or any(part == ".." for part in work_item_path.parts):
            raise ValueError("work_item must not contain parent traversal.")
        return normalized_work_item

    def _discover_work_items(
        self,
        workspace_root: Path,
    ) -> tuple[OnboardingWorkItemSummary, ...]:
        workitems_root = workspace_workitems_root(workspace_root)
        if not workitems_root.is_dir():
            return ()
        items: list[OnboardingWorkItemSummary] = []
        for path in sorted(workitems_root.iterdir(), key=lambda item: item.name):
            if not path.is_dir():
                continue
            if not (path / WORKITEM_METADATA_FILENAME).exists():
                continue
            context_root = work_item_context_root(root=workspace_root, work_item=path.name)
            items.append(
                OnboardingWorkItemSummary(
                    work_item=path.name,
                    has_request_context=(
                        context_root / WORKITEM_CONTEXT_USER_REQUEST_FILENAME
                    ).exists(),
                )
            )
        return tuple(items)


def workspace_contains_work_items(workspace_root: Path) -> bool:
    return (workspace_root / WORKSPACE_WORKITEMS_DIRNAME).is_dir()


__all__ = [
    "OnboardingProjectDeclaration",
    "OnboardingProjectSummary",
    "OnboardingService",
    "OnboardingWorkItemCreation",
    "OnboardingWorkItemSummary",
    "workspace_contains_work_items",
]
