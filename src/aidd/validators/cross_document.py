from __future__ import annotations


def references_upstream(text: str, token: str) -> bool:
    return token in text
