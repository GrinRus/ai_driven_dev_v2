from __future__ import annotations

from pathlib import Path

from aidd.evals.reporting import write_verdict


def test_write_verdict(tmp_path: Path) -> None:
    verdict_path = tmp_path / "verdict.md"
    write_verdict(verdict_path, "pass", "all good")
    assert "pass" in verdict_path.read_text(encoding="utf-8")
