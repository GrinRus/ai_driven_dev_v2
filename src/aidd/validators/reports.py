from __future__ import annotations

from pathlib import Path

def write_report(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
