from __future__ import annotations

import json
from pathlib import Path

from scripts.check_complexity import check_complexity, main


def _write_branchy_module(path: Path, *, branches: int = 40) -> None:
    body = "\n".join(
        f"    if value == {index}:\n        return {index}" for index in range(branches)
    )
    path.write_text(f"def branchy(value: int) -> int:\n{body}\n    return -1\n", encoding="utf-8")


def _write_baseline(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {"schema_version": 1, "scope": "src/**/*.py", "threshold": "E", "entries": entries}
        ),
        encoding="utf-8",
    )


def test_repository_complexity_baseline_is_current() -> None:
    assert check_complexity() == ()


def test_new_e_or_f_block_fails_the_ratchet(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    _write_branchy_module(source_root / "new_module.py")
    baseline_path = tmp_path / "complexity-baseline.json"
    _write_baseline(baseline_path, [])
    monkeypatch.chdir(tmp_path)

    findings = check_complexity(baseline_path=baseline_path, source_root=source_root)

    assert len(findings) == 1
    assert findings[0].block_id == "src/new_module.py::branchy"
    assert "new F-complexity block" in findings[0].message
    assert main(["--baseline", str(baseline_path), "--source-root", str(source_root)]) == 1


def test_existing_block_cannot_increase_above_reviewed_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    _write_branchy_module(source_root / "module.py")
    baseline_path = tmp_path / "complexity-baseline.json"
    _write_baseline(
        baseline_path,
        [{"id": "src/module.py::branchy", "line": 1, "complexity": 31, "grade": "E"}],
    )
    monkeypatch.chdir(tmp_path)

    findings = check_complexity(baseline_path=baseline_path, source_root=source_root)

    assert len(findings) == 1
    assert "complexity increased from 31" in findings[0].message
