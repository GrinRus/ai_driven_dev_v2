from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def test_init_without_request_reports_not_runnable_until_intake_exists(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    result = runner.invoke(
        app,
        [
            "init",
            "--work-item",
            "WI-001",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "No intake context was seeded" in result.stdout
    assert not (
        workspace_root / "workitems" / "WI-001" / "context" / "intake.md"
    ).exists()


def test_init_request_seeds_context_documents(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    result = runner.invoke(
        app,
        [
            "init",
            "--work-item",
            "WI-001",
            "--request",
            "Implement a small operator workflow.",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.output
    context_root = workspace_root / "workitems" / "WI-001" / "context"
    assert "Seeded request context" in result.stdout
    assert "Implement a small operator workflow." in (
        context_root / "intake.md"
    ).read_text(encoding="utf-8")
    assert "Implement a small operator workflow." in (
        context_root / "user-request.md"
    ).read_text(encoding="utf-8")
    assert "Project root:" in (context_root / "repository-state.md").read_text(
        encoding="utf-8"
    )


def test_init_request_file_seeds_context_documents(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    request_file = tmp_path / "request.md"
    request_file.write_text("Implement request from a file.\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "init",
            "--work-item",
            "WI-001",
            "--request-file",
            str(request_file),
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Implement request from a file." in (
        workspace_root / "workitems" / "WI-001" / "context" / "user-request.md"
    ).read_text(encoding="utf-8")


def test_init_request_preserves_existing_context_without_force(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    first = runner.invoke(
        app,
        [
            "init",
            "--work-item",
            "WI-001",
            "--request",
            "Original request.",
            "--root",
            str(workspace_root),
        ],
    )
    assert first.exit_code == 0, first.output

    second = runner.invoke(
        app,
        [
            "init",
            "--work-item",
            "WI-001",
            "--request",
            "Replacement request.",
            "--root",
            str(workspace_root),
        ],
    )

    assert second.exit_code != 0
    assert "Use --force-context" in second.output
    assert "Original request." in (
        workspace_root / "workitems" / "WI-001" / "context" / "intake.md"
    ).read_text(encoding="utf-8")


def test_init_request_force_overwrites_existing_context(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    runner.invoke(
        app,
        [
            "init",
            "--work-item",
            "WI-001",
            "--request",
            "Original request.",
            "--root",
            str(workspace_root),
        ],
    )

    result = runner.invoke(
        app,
        [
            "init",
            "--work-item",
            "WI-001",
            "--request",
            "Replacement request.",
            "--force-context",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Updated request context" in result.stdout
    assert "Replacement request." in (
        workspace_root / "workitems" / "WI-001" / "context" / "intake.md"
    ).read_text(encoding="utf-8")
