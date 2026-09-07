"""Read the references actually linked by a skill without flattening other skills."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def skill_text_with_references(name: str) -> str:
    skills = Path(__file__).resolve().parents[1] / ".agents/skills"
    pending = [skills / name / "SKILL.md"]
    seen: set[Path] = set()
    texts: list[str] = []
    while pending:
        path = pending.pop(0).resolve()
        if path in seen:
            continue
        seen.add(path)
        text = path.read_text(encoding="utf-8")
        texts.append(text)
        for target in re.findall(r"\[[^\]\n]*\]\(([^\s)]+)\)", text):
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            reference = (path.parent / unquote(parsed.path)).resolve()
            if (
                reference.is_relative_to(skills)
                and "references" in reference.relative_to(skills).parts
                and reference.suffix == ".md"
            ):
                pending.append(reference)
    return "\n\n".join(texts)
