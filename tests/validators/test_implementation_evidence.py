from __future__ import annotations

import pytest

from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_ARTIFACT_REFERENCE_PATTERN,
    IMPLEMENT_ASSERTION_REFERENCE_PATTERN,
    has_implementation_command_evidence,
)


@pytest.mark.parametrize(
    "evidence",
    (
        "`uv run pytest tests/test_example.py -q` -> pass",
        "$ custom-check --verify\nObserved: passed",
        "Command: custom-check --verify\nObserved: passed",
        "```sh\ncustom-check --verify\n```\nObserved: passed",
        "`./scripts/verify` -> exit code 0",
        "`sh -c 'test ! -e .pytest_cache'` -> exit code 0",
        "`bash -c 'git diff --quiet'` -> pass",
        "`zsh -c 'test -f pyproject.toml'` -> pass",
        "Reused the same verification command as `TL-2`; outcome passed.",
    ),
)
def test_command_evidence_accepts_only_explicit_command_shapes(evidence: str) -> None:
    assert has_implementation_command_evidence(evidence)


@pytest.mark.parametrize(
    "evidence",
    (
        "pytest passed.",
        "Checked with ruff and it succeeded.",
        "sh passed.",
        "The `pytest` tool passed.",
        "The full test suite passed.",
        "`138 passed`.",
        "`context/verification.log` shows pass.",
    ),
)
def test_command_evidence_rejects_prose_and_non_command_backticks(evidence: str) -> None:
    assert not has_implementation_command_evidence(evidence)


@pytest.mark.parametrize(
    ("evidence", "is_structured_reference"),
    (
        ("`reports/verification.log` records pass.", True),
        ("Observed `exit_code == 0`.", True),
        ("Observed `result.stderr == ''`.", True),
        ("The verification looked correct.", False),
    ),
)
def test_artifact_and_assertion_reference_shapes(
    evidence: str,
    is_structured_reference: bool,
) -> None:
    has_reference = bool(
        IMPLEMENT_ARTIFACT_REFERENCE_PATTERN.search(evidence)
        or IMPLEMENT_ASSERTION_REFERENCE_PATTERN.search(evidence)
    )
    assert has_reference is is_structured_reference
