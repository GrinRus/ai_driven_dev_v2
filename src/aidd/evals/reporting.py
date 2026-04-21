from __future__ import annotations

from pathlib import Path

FAILURE_CLASSES: tuple[str, ...] = (
    "pass",
    "document_fail",
    "model_fail",
    "env_fail",
    "permission_fail",
    "auth_fail",
    "timeout",
    "adapter_fail",
    "harness_fail",
    "needs_user_input",
)


def write_verdict(path: Path, status: str, summary: str) -> None:
    if status not in FAILURE_CLASSES:
        raise ValueError(f"Unknown failure class: {status}")
    path.write_text(
        f"# Verdict\n\n- Status: {status}\n- Summary: {summary}\n",
        encoding="utf-8",
    )
