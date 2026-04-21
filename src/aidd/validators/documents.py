from __future__ import annotations

from pathlib import Path


def missing_required_headings(path: Path, headings: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    missing: list[str] = []
    for heading in headings:
        needle = f"# {heading}"
        if needle not in text and f"## {heading}" not in text:
            missing.append(heading)
    return missing
