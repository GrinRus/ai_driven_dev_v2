from __future__ import annotations

from pathlib import Path

import pytest

from aidd.config import ProjectConfig, ProjectSetConfig
from aidd.core.project_set import (
    persist_project_set_context,
    render_project_set_context,
    resolve_project_set,
)


def _project_set(*projects: ProjectConfig) -> ProjectSetConfig:
    return ProjectSetConfig(projects=projects)


def test_resolve_project_set_accepts_declared_local_roots(tmp_path: Path) -> None:
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "services" / "web").mkdir(parents=True)

    resolved = resolve_project_set(
        repository_root=tmp_path,
        project_set=_project_set(
            ProjectConfig(id="api", root=Path("services/api"), role="primary"),
            ProjectConfig(id="web", root=Path("services/web")),
        ),
    )

    assert resolved.repository_root == tmp_path.resolve()
    assert resolved.project_ids() == ("api", "web")
    assert resolved.projects[0].relative_root == "services/api"
    assert resolved.projects[0].role == "primary"


def test_render_project_set_context_lists_stable_project_ids(tmp_path: Path) -> None:
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "apps" / "web").mkdir(parents=True)
    resolved = resolve_project_set(
        repository_root=tmp_path,
        project_set=_project_set(
            ProjectConfig(id="api", root=Path("services/api"), role="primary"),
            ProjectConfig(id="web", root=Path("apps/web")),
        ),
    )

    markdown = render_project_set_context(resolved)

    assert "| `api` | `services/api` | `primary` |" in markdown
    assert "| `web` | `apps/web` | `unspecified` |" in markdown
    assert "Multi-repository orchestration is out of scope" in markdown


def test_persist_project_set_context_writes_work_item_context(tmp_path: Path) -> None:
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "apps" / "web").mkdir(parents=True)
    resolved = resolve_project_set(
        repository_root=tmp_path,
        project_set=_project_set(
            ProjectConfig(id="api", root=Path("services/api")),
            ProjectConfig(id="web", root=Path("apps/web")),
        ),
    )

    context_path = persist_project_set_context(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-PROJECT-SET",
        project_set=resolved,
    )

    assert context_path == (
        tmp_path / ".aidd" / "workitems" / "WI-PROJECT-SET" / "context" / "project-set.md"
    )
    assert "`api`" in context_path.read_text(encoding="utf-8")


def test_resolve_project_set_rejects_duplicate_roots(tmp_path: Path) -> None:
    (tmp_path / "services" / "api").mkdir(parents=True)

    with pytest.raises(ValueError, match="duplicates project `api`"):
        resolve_project_set(
            repository_root=tmp_path,
            project_set=_project_set(
                ProjectConfig(id="api", root=Path("services/api")),
                ProjectConfig(id="api-copy", root=Path("services/api")),
            ),
        )


def test_resolve_project_set_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        resolve_project_set(
            repository_root=tmp_path,
            project_set=_project_set(ProjectConfig(id="api", root=Path("services/api"))),
        )


def test_resolve_project_set_rejects_absolute_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="repository-relative"):
        resolve_project_set(
            repository_root=tmp_path,
            project_set=_project_set(ProjectConfig(id="api", root=tmp_path)),
        )


def test_resolve_project_set_rejects_parent_escape(tmp_path: Path) -> None:
    outside_root = tmp_path.parent / "aidd-outside-project"
    outside_root.mkdir(exist_ok=True)

    with pytest.raises(ValueError, match="inside repository root"):
        resolve_project_set(
            repository_root=tmp_path,
            project_set=_project_set(
                ProjectConfig(id="outside", root=Path("../aidd-outside-project"))
            ),
        )


def test_resolve_project_set_rejects_symlink_escape(tmp_path: Path) -> None:
    outside_root = tmp_path.parent / "aidd-symlink-outside-project"
    outside_root.mkdir(exist_ok=True)
    link_path = tmp_path / "linked"
    link_path.symlink_to(outside_root, target_is_directory=True)

    with pytest.raises(ValueError, match="inside repository root"):
        resolve_project_set(
            repository_root=tmp_path,
            project_set=_project_set(ProjectConfig(id="linked", root=Path("linked"))),
        )
