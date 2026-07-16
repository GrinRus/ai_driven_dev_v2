from __future__ import annotations

import ast
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_unreferenced_interview_capability_helper_is_absent() -> None:
    interview_path = REPOSITORY_ROOT / "src/aidd/core/interview.py"
    tree = ast.parse(interview_path.read_text(encoding="utf-8"))
    defined_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert "interview_supported" not in defined_names
