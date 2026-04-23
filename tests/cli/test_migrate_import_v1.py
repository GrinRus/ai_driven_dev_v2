from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_migrate_import_v1_copies_allowed_assets_and_skips_blocked_paths(tmp_path: Path) -> None:
    source_root = tmp_path / "v1"
    destination_root = tmp_path / "v2"
    destination_root.mkdir(parents=True, exist_ok=True)

    _write(source_root / "contracts" / "documents" / "stage-brief.md", "# Stage Brief\n")
    _write(source_root / "contracts" / "stages" / "idea.md", "# Stage Contract: `idea`\n")
    _write(source_root / "prompt-packs" / "stages" / "idea" / "run.md", "# Prompt\n")
    _write(source_root / "prompt-packs" / "hooks" / "dont-import.md", "# Hook\n")
    _write(source_root / "prompt-packs" / "stages" / "idea" / "skip.json", "{}\n")
    _write(source_root / "harness" / "scenarios" / "smoke" / "idea.yaml", "id: SCN-1\n")

    result = runner.invoke(
        app,
        [
            "migrate",
            "import-v1",
            str(source_root),
            "--destination-root",
            str(destination_root),
        ],
    )

    assert result.exit_code == 0
    assert "copied=4" in result.stdout
    assert "skipped_blocked=1" in result.stdout
    assert "skipped_extension=1" in result.stdout

    assert (destination_root / "contracts" / "documents" / "stage-brief.md").exists()
    assert (destination_root / "contracts" / "stages" / "idea.md").exists()
    assert (destination_root / "prompt-packs" / "stages" / "idea" / "run.md").exists()
    assert (destination_root / "harness" / "scenarios" / "smoke" / "idea.yaml").exists()
    assert not (destination_root / "prompt-packs" / "hooks" / "dont-import.md").exists()


def test_migrate_import_v1_respects_overwrite_flag(tmp_path: Path) -> None:
    source_root = tmp_path / "v1"
    destination_root = tmp_path / "v2"
    destination_root.mkdir(parents=True, exist_ok=True)

    source_file = source_root / "contracts" / "documents" / "stage-brief.md"
    destination_file = destination_root / "contracts" / "documents" / "stage-brief.md"
    _write(source_file, "# Stage Brief\n\nsource\n")
    _write(destination_file, "# Stage Brief\n\nexisting\n")

    no_overwrite_result = runner.invoke(
        app,
        [
            "migrate",
            "import-v1",
            str(source_root),
            "--destination-root",
            str(destination_root),
            "--include",
            "contracts",
            "--no-overwrite",
        ],
    )

    assert no_overwrite_result.exit_code == 0
    assert "copied=0" in no_overwrite_result.stdout
    assert "skipped_existing=1" in no_overwrite_result.stdout
    assert destination_file.read_text(encoding="utf-8") == "# Stage Brief\n\nexisting\n"

    overwrite_result = runner.invoke(
        app,
        [
            "migrate",
            "import-v1",
            str(source_root),
            "--destination-root",
            str(destination_root),
            "--include",
            "contracts",
            "--overwrite",
        ],
    )

    assert overwrite_result.exit_code == 0
    assert "copied=1" in overwrite_result.stdout
    assert destination_file.read_text(encoding="utf-8") == "# Stage Brief\n\nsource\n"
