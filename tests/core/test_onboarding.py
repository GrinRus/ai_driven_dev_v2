from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.onboarding import (
    OnboardingProjectDeclaration,
    OnboardingService,
)


def test_onboarding_inspects_empty_project(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    service = OnboardingService(launch_root=tmp_path)

    summary = service.inspect_project("project")

    assert summary.project_root == project_root.resolve()
    assert summary.workspace_root == project_root.resolve() / ".aidd"
    assert summary.workspace_exists is False
    assert summary.work_items == ()


def test_onboarding_rejects_missing_file_parent_and_symlink_escape(tmp_path: Path) -> None:
    service = OnboardingService(launch_root=tmp_path)

    with pytest.raises(ValueError, match="does not exist"):
        service.inspect_project("missing")

    file_path = tmp_path / "file.txt"
    file_path.write_text("not a directory", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a directory"):
        service.inspect_project("file.txt")

    with pytest.raises(ValueError, match="parent traversal"):
        service.inspect_project("../outside")

    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "linked"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="stay inside"):
        service.inspect_project("linked")


def test_onboarding_rejects_workspace_symlink_escape(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    outside_workspace = tmp_path / "outside-aidd"
    project_root.mkdir()
    outside_workspace.mkdir()
    (project_root / ".aidd").symlink_to(outside_workspace, target_is_directory=True)
    service = OnboardingService(launch_root=tmp_path)

    with pytest.raises(ValueError, match="selected project root"):
        service.inspect_project("project")


def test_onboarding_create_work_item_seeds_request_context(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    service = OnboardingService(launch_root=tmp_path)

    created = service.create_work_item(
        raw_project_root="project",
        work_item="WI-001",
        request_text="Implement a small onboarding smoke.",
    )

    assert created.work_item == "WI-001"
    assert created.work_item_root == project_root.resolve() / ".aidd" / "workitems" / "WI-001"
    assert created.seeded_context is not None
    assert created.seeded_context.user_request_path.read_text(encoding="utf-8").endswith(
        "Implement a small onboarding smoke.\n"
    )
    refreshed = service.inspect_project("project")
    assert [(item.work_item, item.has_request_context) for item in refreshed.work_items] == [
        ("WI-001", True)
    ]


def test_onboarding_rejects_unsafe_work_item_ids(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    service = OnboardingService(launch_root=tmp_path)

    for work_item in (
        "",
        "../WI-ESCAPE",
        "WI/NESTED",
        "WI\\NESTED",
        "/WI-ABS",
        ".",
        "..",
        "bad$id",
        "X" * 129,
    ):
        with pytest.raises(ValueError, match="work_item"):
            service.create_work_item(
                raw_project_root="project",
                work_item=work_item,
                request_text="Do not escape workspace.",
            )
        assert not (project_root / ".aidd").exists()


def test_onboarding_preserves_existing_request_context_without_force(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    service = OnboardingService(launch_root=tmp_path)
    service.create_work_item(
        raw_project_root="project",
        work_item="WI-001",
        request_text="First request.",
    )

    with pytest.raises(FileExistsError, match="already exist"):
        service.create_work_item(
            raw_project_root="project",
            work_item="WI-001",
            request_text="Second request.",
        )

    created = service.create_work_item(
        raw_project_root="project",
        work_item="WI-001",
        request_text="Second request.",
        force_context=True,
    )
    assert created.seeded_context is not None
    assert created.seeded_context.overwritten is True


def test_onboarding_project_set_validation_and_context(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    api_root = project_root / "services" / "api"
    web_root = project_root / "apps" / "web"
    api_root.mkdir(parents=True)
    web_root.mkdir(parents=True)
    service = OnboardingService(launch_root=tmp_path)

    resolved = service.resolve_project_set(
        raw_project_root="project",
        project_set=(
            OnboardingProjectDeclaration(id="api", root=Path("services/api"), role="primary"),
            OnboardingProjectDeclaration(id="web", root=Path("apps/web")),
        ),
    )

    assert resolved.project_ids() == ("api", "web")

    created = service.create_work_item(
        raw_project_root="project",
        work_item="WI-SET",
        request_text="Coordinate api and web.",
        project_set=(
            OnboardingProjectDeclaration(id="api", root=Path("services/api"), role="primary"),
            OnboardingProjectDeclaration(id="web", root=Path("apps/web")),
        ),
    )
    assert created.project_set_context_path is not None
    context = created.project_set_context_path.read_text(encoding="utf-8")
    assert "| `api` | `services/api` | `primary` |" in context
    assert "| `web` | `apps/web` | `unspecified` |" in context


def test_onboarding_project_set_rejects_root_escape(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project_root / "linked").symlink_to(outside, target_is_directory=True)
    service = OnboardingService(launch_root=tmp_path)

    with pytest.raises(ValueError, match="stay inside repository root"):
        service.resolve_project_set(
            raw_project_root="project",
            project_set=(OnboardingProjectDeclaration(id="linked", root=Path("linked")),),
        )


def test_onboarding_create_validates_project_set_before_writing(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    service = OnboardingService(launch_root=tmp_path)

    with pytest.raises(ValueError, match="repository-relative"):
        service.create_work_item(
            raw_project_root="project",
            work_item="WI-PARTIAL",
            request_text="This must not create partial onboarding state.",
            project_set=(
                OnboardingProjectDeclaration(id="outside", root=outside),
            ),
        )

    assert not (project_root / ".aidd").exists()
