from __future__ import annotations

import os
from pathlib import Path

import pytest

from aidd.evals.reporting import resolve_latest_eval_summary_report_path


def test_resolve_latest_eval_summary_report_path_prefers_newest_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    eval_root = workspace_root / "reports" / "evals"
    first = eval_root / "run-001" / "summary.md"
    second = eval_root / "run-002" / "summary.md"
    first.parent.mkdir(parents=True, exist_ok=True)
    second.parent.mkdir(parents=True, exist_ok=True)
    first.write_text("# Eval Summary\n\nrun-001\n", encoding="utf-8")
    second.write_text("# Eval Summary\n\nrun-002\n", encoding="utf-8")
    os.utime(first, (1_700_000_000, 1_700_000_000))
    os.utime(second, (1_700_000_100, 1_700_000_100))

    latest = resolve_latest_eval_summary_report_path(workspace_root=workspace_root)

    assert latest == second


def test_resolve_latest_eval_summary_report_path_accepts_root_level_summary(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    summary_path = workspace_root / "reports" / "evals" / "summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("# Eval Summary\n", encoding="utf-8")

    latest = resolve_latest_eval_summary_report_path(workspace_root=workspace_root)

    assert latest == summary_path


def test_resolve_latest_eval_summary_report_path_rejects_missing_eval_reports_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="No eval reports found under"):
        resolve_latest_eval_summary_report_path(workspace_root=tmp_path / ".aidd")


def test_resolve_latest_eval_summary_report_path_rejects_missing_summary_files(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    (workspace_root / "reports" / "evals" / "run-001").mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="No eval summary reports found"):
        resolve_latest_eval_summary_report_path(workspace_root=workspace_root)
