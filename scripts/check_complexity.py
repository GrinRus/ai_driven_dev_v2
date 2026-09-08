"""Enforce the reviewed source complexity baseline."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from radon.complexity import cc_rank, cc_visit  # type: ignore[import-untyped]

_HIGH_COMPLEXITY_GRADES = frozenset({"E", "F"})
_DEFAULT_BASELINE = Path("docs/quality/complexity-baseline.json")
_DEFAULT_SOURCE_ROOT = Path("src")


class _ComplexityBlock(Protocol):
    complexity: int
    fullname: str
    lineno: int


@dataclass(frozen=True)
class ComplexityEntry:
    """Stable identity and reviewed complexity for one source block."""

    block_id: str
    complexity: int
    grade: str
    line: int


@dataclass(frozen=True)
class ComplexityFinding:
    """One actionable baseline mismatch."""

    block_id: str
    message: str


def _grade(complexity: int) -> str:
    return cast(str, cc_rank(complexity))


def _block_id(path: Path, project_root: Path, block: _ComplexityBlock) -> str:
    try:
        display_path = path.relative_to(project_root)
    except ValueError:
        display_path = path
    return f"{display_path.as_posix()}::{block.fullname}"


def scan_high_complexity(source_root: Path, *, project_root: Path) -> tuple[ComplexityEntry, ...]:
    """Return deterministic E/F blocks below ``source_root``."""

    entries: list[ComplexityEntry] = []
    for path in sorted(source_root.rglob("*.py")):
        blocks = cast(
            tuple[_ComplexityBlock, ...], tuple(cc_visit(path.read_text(encoding="utf-8")))
        )
        for block in blocks:
            grade = _grade(block.complexity)
            if grade in _HIGH_COMPLEXITY_GRADES:
                entries.append(
                    ComplexityEntry(
                        block_id=_block_id(path, project_root, block),
                        complexity=block.complexity,
                        grade=grade,
                        line=block.lineno,
                    )
                )
    return tuple(sorted(entries, key=lambda entry: entry.block_id))


def _load_baseline(path: Path) -> dict[str, ComplexityEntry]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError(f"{path}: expected schema_version 1")
    if payload.get("scope") != "src/**/*.py" or payload.get("threshold") != "E":
        raise ValueError(f"{path}: expected src/**/*.py scope with E threshold")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        raise ValueError(f"{path}: entries must be a list")

    entries: dict[str, ComplexityEntry] = {}
    for index, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            raise ValueError(f"{path}: entries[{index}] must be an object")
        block_id = raw_entry.get("id")
        complexity = raw_entry.get("complexity")
        grade = raw_entry.get("grade")
        line = raw_entry.get("line", 0)
        if (
            not isinstance(block_id, str)
            or not isinstance(complexity, int)
            or not isinstance(grade, str)
            or not isinstance(line, int)
        ):
            raise ValueError(f"{path}: entries[{index}] has invalid fields")
        expected_grade = _grade(complexity)
        if grade != expected_grade or expected_grade not in _HIGH_COMPLEXITY_GRADES:
            raise ValueError(
                f"{path}: entries[{index}] grade must be {_HIGH_COMPLEXITY_GRADES} for complexity"
            )
        if block_id in entries:
            raise ValueError(f"{path}: duplicate entry id {block_id}")
        entries[block_id] = ComplexityEntry(block_id, complexity, grade, line)
    return entries


def find_baseline_mismatches(
    baseline: dict[str, ComplexityEntry], current: tuple[ComplexityEntry, ...]
) -> tuple[ComplexityFinding, ...]:
    """Compare current E/F blocks with the reviewed baseline."""

    current_by_id = {entry.block_id: entry for entry in current}
    findings: list[ComplexityFinding] = []
    for entry in current:
        reviewed = baseline.get(entry.block_id)
        if reviewed is None:
            findings.append(
                ComplexityFinding(
                    entry.block_id,
                    f"new {entry.grade}-complexity block ({entry.complexity}); "
                    "review and baseline it",
                )
            )
        elif entry.complexity > reviewed.complexity:
            findings.append(
                ComplexityFinding(
                    entry.block_id,
                    f"complexity increased from {reviewed.complexity} to {entry.complexity}",
                )
            )
    for block_id in sorted(set(baseline) - set(current_by_id)):
        findings.append(
            ComplexityFinding(
                block_id, "baseline entry is missing from the source; remove or reslice it"
            )
        )
    return tuple(findings)


def check_complexity(
    *, baseline_path: Path = _DEFAULT_BASELINE, source_root: Path = _DEFAULT_SOURCE_ROOT
) -> tuple[ComplexityFinding, ...]:
    """Return baseline mismatches for the repository source tree."""

    project_root = Path.cwd()
    baseline = _load_baseline(baseline_path)
    current = scan_high_complexity(source_root, project_root=project_root)
    return find_baseline_mismatches(baseline, current)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=_DEFAULT_BASELINE)
    parser.add_argument("--source-root", type=Path, default=_DEFAULT_SOURCE_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        findings = check_complexity(baseline_path=args.baseline, source_root=args.source_root)
    except (OSError, ValueError, SyntaxError) as error:
        print(f"complexity check error: {error}", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            print(f"{finding.block_id}: {finding.message}", file=sys.stderr)
        return 1
    print(f"complexity baseline is clean: {args.baseline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
