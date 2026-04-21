from __future__ import annotations


def has_non_placeholder_text(text: str) -> bool:
    lowered = text.lower()
    return "no " not in lowered or "yet" not in lowered
