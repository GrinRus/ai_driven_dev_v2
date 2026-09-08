"""Validate the reviewed line/branch coverage baseline for critical Python modules."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_BASELINE = Path("docs/quality/critical-coverage-baseline.json")
_DEFAULT_REPORT = Path("coverage-critical.json")
_CATEGORIES = frozenset({"lifecycle", "evidence", "adapters", "scenario-gates"})
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class CoverageEntry:
    """Reviewed coverage for one source module."""

    path: str
    category: str
    statements: int
    covered_statements: int
    branches: int
    covered_branches: int
    line_percent: float
    branch_percent: float


@dataclass(frozen=True)
class CoverageFinding:
    """One invalid or regressed coverage observation."""

    path: str
    message: str


def _as_non_negative_int(value: object, *, field: str, path: Path) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{path}: {field} must be a non-negative integer")
    return value


def _as_percent(value: object, *, field: str, path: Path) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100:
        raise ValueError(f"{path}: {field} must be a number from 0 to 100")
    return float(value)


def _load_baseline(path: Path) -> tuple[str, tuple[str, ...], tuple[CoverageEntry, ...]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError(f"{path}: expected schema_version 1")

    revision = payload.get("revision")
    if not isinstance(revision, str) or _SHA_RE.fullmatch(revision) is None:
        raise ValueError(f"{path}: revision must be a 40-character lowercase SHA")

    command = payload.get("command")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part.strip() for part in command)
    ):
        raise ValueError(f"{path}: command must be a non-empty list of strings")

    test_paths = payload.get("test_paths")
    if (
        not isinstance(test_paths, list)
        or not test_paths
        or any(
            not isinstance(test_path, str) or not test_path.startswith("tests/")
            for test_path in test_paths
        )
    ):
        raise ValueError(f"{path}: test_paths must list repository tests")

    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError(f"{path}: entries must be a non-empty list")

    entries: list[CoverageEntry] = []
    seen_paths: set[str] = set()
    for index, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            raise ValueError(f"{path}: entries[{index}] must be an object")
        source_path = raw_entry.get("path")
        category = raw_entry.get("category")
        if (
            not isinstance(source_path, str)
            or not source_path.startswith("src/")
            or not source_path.endswith(".py")
            or "/cli/static/" in source_path
        ):
            raise ValueError(f"{path}: entries[{index}] must identify non-UI src Python")
        if not isinstance(category, str) or category not in _CATEGORIES:
            raise ValueError(f"{path}: entries[{index}] has an unknown category")
        if source_path in seen_paths:
            raise ValueError(f"{path}: duplicate entry path {source_path}")
        seen_paths.add(source_path)

        statements = _as_non_negative_int(
            raw_entry.get("statements"), field="statements", path=path
        )
        covered_statements = _as_non_negative_int(
            raw_entry.get("covered_statements"), field="covered_statements", path=path
        )
        branches = _as_non_negative_int(raw_entry.get("branches"), field="branches", path=path)
        covered_branches = _as_non_negative_int(
            raw_entry.get("covered_branches"), field="covered_branches", path=path
        )
        if covered_statements > statements or covered_branches > branches:
            raise ValueError(f"{path}: entries[{index}] covered counts exceed totals")
        line_percent = _as_percent(raw_entry.get("line_percent"), field="line_percent", path=path)
        branch_percent = _as_percent(
            raw_entry.get("branch_percent"), field="branch_percent", path=path
        )
        entries.append(
            CoverageEntry(
                path=source_path,
                category=category,
                statements=statements,
                covered_statements=covered_statements,
                branches=branches,
                covered_branches=covered_branches,
                line_percent=line_percent,
                branch_percent=branch_percent,
            )
        )
    return revision, tuple(test_paths), tuple(sorted(entries, key=lambda entry: entry.path))


def _load_report(path: Path) -> dict[str, dict[str, int | float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(raw_files, dict):
        raise ValueError(f"{path}: expected coverage JSON files object")
    report: dict[str, dict[str, int | float]] = {}
    for source_path, raw_file in raw_files.items():
        if not isinstance(source_path, str) or not isinstance(raw_file, dict):
            raise ValueError(f"{path}: invalid coverage file entry")
        summary = raw_file.get("summary")
        if not isinstance(summary, dict):
            raise ValueError(f"{path}: {source_path}: missing summary")
        report[source_path] = {
            "statements": _as_non_negative_int(
                summary.get("num_statements"), field=f"{source_path}.num_statements", path=path
            ),
            "covered_statements": _as_non_negative_int(
                summary.get("covered_lines"), field=f"{source_path}.covered_lines", path=path
            ),
            "branches": _as_non_negative_int(
                summary.get("num_branches"), field=f"{source_path}.num_branches", path=path
            ),
            "covered_branches": _as_non_negative_int(
                summary.get("covered_branches"),
                field=f"{source_path}.covered_branches",
                path=path,
            ),
            "line_percent": _as_percent(
                summary.get("percent_covered"), field=f"{source_path}.percent_covered", path=path
            ),
            "branch_percent": _as_percent(
                summary.get("percent_branches_covered"),
                field=f"{source_path}.percent_branches_covered",
                path=path,
            ),
        }
    return report


def find_coverage_findings(
    baseline: tuple[CoverageEntry, ...], report: dict[str, dict[str, int | float]]
) -> tuple[CoverageFinding, ...]:
    """Return missing modules or line/branch regressions against ``baseline``."""

    findings: list[CoverageFinding] = []
    for entry in baseline:
        observed = report.get(entry.path)
        if observed is None:
            findings.append(CoverageFinding(entry.path, "module is missing from coverage report"))
            continue
        for metric in ("line_percent", "branch_percent"):
            reviewed = getattr(entry, metric)
            actual = float(observed[metric])
            # Baselines retain six decimal places; tolerate only their rounding residue.
            if actual + 1e-6 < reviewed:
                findings.append(
                    CoverageFinding(
                        entry.path,
                        f"{metric} regressed from {reviewed:.6f} to {actual:.6f}",
                    )
                )
    return tuple(findings)


def check_critical_coverage(
    *,
    baseline_path: Path = _DEFAULT_BASELINE,
    report_path: Path = _DEFAULT_REPORT,
) -> tuple[CoverageFinding, ...]:
    """Validate a report against the reviewed critical-module baseline."""

    _, _, baseline = _load_baseline(baseline_path)
    return find_coverage_findings(baseline, _load_report(report_path))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=_DEFAULT_BASELINE)
    parser.add_argument("--report", type=Path, default=_DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        findings = check_critical_coverage(
            baseline_path=args.baseline,
            report_path=args.report,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"critical coverage check error: {error}", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            print(f"{finding.path}: {finding.message}", file=sys.stderr)
        return 1
    print(f"critical coverage baseline is clean: {args.baseline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
