from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def test_eval_summary_prints_latest_report(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    older = workspace_root / "reports" / "evals" / "run-001" / "summary.md"
    newer = workspace_root / "reports" / "evals" / "run-002" / "summary.md"
    older.parent.mkdir(parents=True, exist_ok=True)
    newer.parent.mkdir(parents=True, exist_ok=True)
    older.write_text("# Eval Summary\n\nolder\n", encoding="utf-8")
    newer.write_text("# Eval Summary\n\nnewer\n", encoding="utf-8")
    os.utime(older, (1_700_000_000, 1_700_000_000))
    os.utime(newer, (1_700_000_200, 1_700_000_200))

    result = runner.invoke(
        app,
        ["eval", "summary", "--root", str(workspace_root)],
    )

    normalized_output = result.stdout.replace("\n", "")
    assert result.exit_code == 0
    assert "Latest eval report:" in result.stdout
    assert "run-002/summary.md" in normalized_output
    assert "# Eval Summary" in result.stdout
    assert "newer" in result.stdout


def test_eval_summary_rejects_missing_reports(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    result = runner.invoke(
        app,
        ["eval", "summary", "--root", str(workspace_root)],
    )

    assert result.exit_code != 0
    assert "No eval reports found under" in result.output
