from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.check_critical_coverage import (
    _load_baseline,
    check_critical_coverage,
    main,
)


def _write_baseline(path: Path, *, entries: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "revision": "0" * 40,
                "command": ["uv", "run", "pytest"],
                "test_paths": ["tests/test_critical_coverage.py"],
                "entries": entries,
            }
        ),
        encoding="utf-8",
    )


def _write_report(path: Path, *, line_percent: float = 80.0, branch_percent: float = 70.0) -> None:
    path.write_text(
        json.dumps(
            {
                "files": {
                    "src/aidd/core/example.py": {
                        "summary": {
                            "num_statements": 10,
                            "covered_lines": 8,
                            "num_branches": 10,
                            "covered_branches": 7,
                            "percent_covered": line_percent,
                            "percent_branches_covered": branch_percent,
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_repository_critical_coverage_baseline_has_reviewed_modules() -> None:
    revision, test_paths, entries = _load_baseline(
        Path("docs/quality/critical-coverage-baseline.json")
    )

    assert len(revision) == 40
    assert test_paths
    assert {entry.category for entry in entries} == {
        "lifecycle",
        "evidence",
        "adapters",
        "scenario-gates",
    }
    assert all("/cli/static/" not in entry.path for entry in entries)


def test_critical_coverage_detects_line_and_branch_regressions(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    report_path = tmp_path / "coverage.json"
    _write_baseline(
        baseline_path,
        entries=[
            {
                "path": "src/aidd/core/example.py",
                "category": "lifecycle",
                "statements": 10,
                "covered_statements": 8,
                "branches": 10,
                "covered_branches": 7,
                "line_percent": 80.0,
                "branch_percent": 70.0,
            }
        ],
    )
    _write_report(report_path, line_percent=79.99, branch_percent=69.99)

    findings = check_critical_coverage(baseline_path=baseline_path, report_path=report_path)

    assert [finding.path for finding in findings] == [
        "src/aidd/core/example.py",
        "src/aidd/core/example.py",
    ]
    assert main(["--baseline", str(baseline_path), "--report", str(report_path)]) == 1


def test_critical_coverage_rejects_ui_owned_baseline_entry(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    _write_baseline(
        baseline_path,
        entries=[
            {
                "path": "src/aidd/cli/static/app.py",
                "category": "lifecycle",
                "statements": 1,
                "covered_statements": 1,
                "branches": 0,
                "covered_branches": 0,
                "line_percent": 100.0,
                "branch_percent": 100.0,
            }
        ],
    )

    with pytest.raises(ValueError, match="non-UI"):
        _load_baseline(baseline_path)
