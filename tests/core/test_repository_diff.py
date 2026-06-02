from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aidd.core.repository_diff import resolve_repository_diff


def _git(project_root: Path, *args: str) -> None:
    subprocess.run(
        ("git", "-C", project_root.as_posix(), *args),
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(project_root: Path) -> None:
    project_root.mkdir()
    _git(project_root, "init")
    _git(project_root, "config", "user.email", "aidd@example.test")
    _git(project_root, "config", "user.name", "AIDD Test")
    project_root.joinpath("app.py").write_text("print('old')\n", encoding="utf-8")
    project_root.joinpath("delete_me.py").write_text("remove me\n", encoding="utf-8")
    _git(project_root, "add", "app.py", "delete_me.py")
    _git(project_root, "commit", "-m", "initial")


def _write_implementation_report(workspace_root: Path, *, text: str | None = None) -> None:
    report_root = workspace_root / "workitems" / "WI-UI" / "stages" / "implement"
    report_root.mkdir(parents=True, exist_ok=True)
    report_root.joinpath("implementation-report.md").write_text(
        text
        or "\n".join(
            (
                "# Implementation Report",
                "",
                "## Touched files",
                "",
                "- `app.py`",
                "- `missing.py`",
            )
        ),
        encoding="utf-8",
    )
    context_root = report_root / "context"
    context_root.mkdir()
    context_root.joinpath("allowed-write-scope.md").write_text(
        "# Allowed Write Scope\n\n- `app.py`\n",
        encoding="utf-8",
    )


def test_repository_diff_separates_source_changes_from_aidd_artifacts(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    workspace_root = project_root / ".aidd"
    _write_implementation_report(workspace_root)

    project_root.joinpath("app.py").write_text("print('new')\n", encoding="utf-8")
    project_root.joinpath("new_file.py").write_text("print('new file')\n", encoding="utf-8")
    project_root.joinpath("delete_me.py").unlink()

    view = resolve_repository_diff(
        project_root=project_root,
        workspace_root=workspace_root,
        work_item="WI-UI",
    )

    source_by_path = {item.path: item for item in view.source_files}
    assert source_by_path["app.py"].status == "modified"
    assert source_by_path["app.py"].mentioned_in_report is True
    assert source_by_path["app.py"].allowed_scope_status == "inside"
    assert source_by_path["new_file.py"].status == "untracked"
    assert source_by_path["new_file.py"].allowed_scope_status == "outside"
    assert source_by_path["delete_me.py"].status == "deleted"
    assert any(item.path.startswith(".aidd/") for item in view.aidd_artifacts)
    assert view.mentioned_but_unchanged == ("missing.py",)


def test_repository_diff_bounds_large_untracked_preview(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    workspace_root = project_root / ".aidd"
    _write_implementation_report(workspace_root, text="# Implementation Report\n")
    project_root.joinpath("large.txt").write_text("x" * (40 * 1024), encoding="utf-8")

    view = resolve_repository_diff(
        project_root=project_root,
        workspace_root=workspace_root,
        work_item="WI-UI",
    )

    large_file = next(item for item in view.source_files if item.path == "large.txt")
    assert large_file.status == "untracked"
    assert large_file.truncated is True
    assert len(large_file.diff.encode("utf-8")) < 34 * 1024


def test_repository_diff_includes_staged_added_diff(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    workspace_root = project_root / ".aidd"
    _write_implementation_report(
        workspace_root,
        text="# Implementation Report\n\n## Touched files\n\n- `staged_added.py`\n",
    )
    project_root.joinpath("staged_added.py").write_text("print('staged')\n", encoding="utf-8")
    _git(project_root, "add", "staged_added.py")

    view = resolve_repository_diff(
        project_root=project_root,
        workspace_root=workspace_root,
        work_item="WI-UI",
    )

    staged_added = next(item for item in view.source_files if item.path == "staged_added.py")
    assert staged_added.status == "added"
    assert staged_added.mentioned_in_report is True
    assert "+print('staged')" in staged_added.diff


def test_repository_diff_handles_renamed_and_space_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    workspace_root = project_root / ".aidd"
    _write_implementation_report(
        workspace_root,
        text="# Implementation Report\n\n## Touched files\n\n- `renamed app.py`\n",
    )
    _git(project_root, "mv", "app.py", "renamed app.py")
    project_root.joinpath("space file.py").write_text("print('space')\n", encoding="utf-8")

    view = resolve_repository_diff(
        project_root=project_root,
        workspace_root=workspace_root,
        work_item="WI-UI",
    )

    source_by_path = {item.path: item for item in view.source_files}
    assert source_by_path["renamed app.py"].status == "renamed"
    assert source_by_path["renamed app.py"].mentioned_in_report is True
    assert source_by_path["space file.py"].status == "untracked"
    assert "+print('space')" in source_by_path["space file.py"].diff
    assert "app.py" not in source_by_path


def test_repository_diff_rejects_symlink_escape(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _init_repo(project_root)
    workspace_root = project_root / ".aidd"
    _write_implementation_report(workspace_root)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    project_root.joinpath("escape.txt").symlink_to(outside)

    with pytest.raises(ValueError, match="inside project root"):
        resolve_repository_diff(
            project_root=project_root,
            workspace_root=workspace_root,
            work_item="WI-UI",
        )
