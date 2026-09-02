from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidd.config import ProjectConfig, ProjectSetConfig
from aidd.core.identifiers import SafeIdentifier
from aidd.core.project_set import (
    ResolvedProjectSet,
    persist_project_set_context,
    resolve_project_set,
)
from aidd.core.run_store import RUN_MANIFEST_FILENAME, work_item_runs_root
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
class WorkItemRequestProjection:
    """Structured read projection over operator-owned request Markdown."""

    title: str
    brief: str
    context: str
    constraints: str
    additional_information: str
    structured: bool


@dataclass(frozen=True, slots=True)
class OperatorRequestContext:
    """The operator-owned request boundary exposed by the local UI service."""

    work_item: str
    request_text: str
    request_path: Path
    intake_path: Path
    consumed: bool
    editable: bool
    disabled_reason: str | None = None
    title: str = ""
    brief: str = ""
    context: str = ""
    constraints: str = ""
    additional_information: str = ""
    structured: bool = False

    @property
    def markdown(self) -> str:
        return "# User request\n\n" f"{self.request_text}\n"


def _request_body(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].strip().lower() == "# user request":
        lines = lines[1:]
    return "\n".join(lines).strip()


_REQUEST_SECTION_ALIASES = {
    "title": "title",
    "brief": "brief",
    "requested outcome": "brief",
    "outcome": "brief",
    "context": "context",
    "detailed context": "context",
    "constraints": "constraints",
    "constraint": "constraints",
    "additional information": "additional_information",
    "additional info": "additional_information",
    "additional": "additional_information",
}


def _first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        normalized = re.sub(r"^\s{0,3}#+\s*", "", line).strip()
        if normalized:
            return normalized
    return ""


def _first_paragraph(text: str) -> str:
    paragraphs = [block.strip() for block in re.split(r"\n\s*\n", text.strip()) if block.strip()]
    return paragraphs[0] if paragraphs else ""


def project_work_item_request(markdown: str) -> WorkItemRequestProjection:
    """Project canonical and legacy request Markdown without rewriting it."""
    body = _request_body(markdown)
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if match:
            current = _REQUEST_SECTION_ALIASES.get(match.group(1).strip().casefold())
            if current is not None:
                sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)

    values = {
        key: "\n".join(lines).strip()
        for key, lines in sections.items()
    }
    structured = bool(values.get("title") and values.get("brief"))
    if structured:
        return WorkItemRequestProjection(
            title=values.get("title", ""),
            brief=values.get("brief", ""),
            context=values.get("context", ""),
            constraints=values.get("constraints", ""),
            additional_information=values.get("additional_information", ""),
            structured=True,
        )

    # Legacy request bodies have no stable field boundaries. Keep the complete
    # body in context while deriving only bounded navigation candidates.
    legacy_navigation_body = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    ).strip()
    return WorkItemRequestProjection(
        title=_first_meaningful_line(body),
        brief=_first_paragraph(legacy_navigation_body),
        context=body,
        constraints="",
        additional_information="",
        structured=False,
    )


def _request_context_consumed(*, workspace_root: Path, work_item: str) -> bool:
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    if not runs_root.is_dir():
        return False
    return any(
        child.is_dir() and (child / RUN_MANIFEST_FILENAME).is_file()
        for child in runs_root.iterdir()
    )


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
        request_title: str | None = None,
        request_brief: str | None = None,
        request_context: str | None = None,
        request_constraints: str | None = None,
        request_additional_information: str | None = None,
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
        request_value = request_brief if request_brief is not None else request_text
        if request_value is not None and request_value.strip():
            seeded_context = bootstrap.seed_request_context(
                work_item=normalized_work_item,
                request_text=request_value,
                project_root=project.project_root,
                force=force_context,
                request_title=request_title,
                request_brief=request_brief,
                request_context=request_context,
                request_constraints=request_constraints,
                request_additional_information=request_additional_information,
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

    def request_context(
        self,
        *,
        raw_project_root: str | Path,
        work_item: str,
    ) -> OperatorRequestContext:
        normalized_work_item = self._normalize_work_item(work_item)
        project = self.inspect_project(raw_project_root)
        context_root = work_item_context_root(
            root=project.workspace_root,
            work_item=normalized_work_item,
        )
        request_path = context_root / WORKITEM_CONTEXT_USER_REQUEST_FILENAME
        intake_path = context_root / "intake.md"
        request_markdown = ""
        if request_path.exists():
            try:
                request_markdown = request_path.read_text(encoding="utf-8")
                request_text = _request_body(request_markdown)
            except UnicodeDecodeError as exc:
                raise ValueError("Request context is not valid UTF-8 Markdown.") from exc
        else:
            request_text = ""
        projection = project_work_item_request(request_markdown)
        consumed = _request_context_consumed(
            workspace_root=project.workspace_root,
            work_item=normalized_work_item,
        )
        return OperatorRequestContext(
            work_item=normalized_work_item,
            request_text=request_text,
            request_path=request_path,
            intake_path=intake_path,
            consumed=consumed,
            editable=not consumed,
            disabled_reason=(
                "The request was consumed by an existing run; create a revision or intervention."
                if consumed
                else None
            ),
            title=projection.title,
            brief=projection.brief,
            context=projection.context,
            constraints=projection.constraints,
            additional_information=projection.additional_information,
            structured=projection.structured,
        )

    def write_request_context(
        self,
        *,
        raw_project_root: str | Path,
        work_item: str,
        request_text: str,
    ) -> OperatorRequestContext:
        context = self.request_context(raw_project_root=raw_project_root, work_item=work_item)
        if context.consumed:
            raise FileExistsError(context.disabled_reason or "Request context is consumed.")
        project = self.inspect_project(raw_project_root)
        bootstrap = WorkspaceBootstrapService(root=project.workspace_root)
        bootstrap.bootstrap_work_item(work_item=context.work_item)
        bootstrap.seed_request_context(
            work_item=context.work_item,
            request_text=request_text,
            project_root=project.project_root,
            force=True,
        )
        return self.request_context(
            raw_project_root=project.project_root,
            work_item=context.work_item,
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
        return SafeIdentifier.parse(work_item, label="work_item").value

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
    "OperatorRequestContext",
    "WorkItemRequestProjection",
    "project_work_item_request",
    "workspace_contains_work_items",
]
