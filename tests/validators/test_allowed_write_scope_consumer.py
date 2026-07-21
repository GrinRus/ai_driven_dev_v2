from __future__ import annotations

from pathlib import Path

import pytest

from aidd.validators.semantic import MISSING_DIFF_EVIDENCE_CODE, validate_semantic_outputs


def _write_report(workspace_root: Path, work_item: str, touched_path: str) -> None:
    context_root = workspace_root / "workitems" / work_item / "context"
    context_root.mkdir(parents=True, exist_ok=True)
    (context_root / "task-selection.md").write_text(
        "# Task Selection\n\nTask id: `TL-1`\n",
        encoding="utf-8",
    )
    report = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# Implementation Report\n\n"
        "## Selected task\n\n- `TL-1` completed.\n\n"
        "## Change summary\n\nCompleted the bounded implementation.\n\n"
        f"## Touched files\n\n- `{touched_path}` - updated behavior.\n\n"
        "## Verification notes\n\n- `pytest -q` -> pass.\n\n"
        "## Follow-up notes\n\n- none\n",
        encoding="utf-8",
    )


def _write_scope(workspace_root: Path, work_item: str, markdown: str) -> None:
    path = workspace_root / "workitems" / work_item / "context" / "allowed-write-scope.md"
    path.write_text(markdown, encoding="utf-8")


@pytest.mark.parametrize(
    ("scope_path", "touched_path", "allowed"),
    (
        ("src", "src/app.py", True),
        ("src", "src2/app.py", False),
        ("src/app.py", "src/app.py", True),
        ("src/app.py", "src/app.py/child", True),
        ("src", "../src/app.py", False),
        ("src", r"src\app.py", False),
    ),
)
def test_semantic_validator_uses_canonical_scope_parity(
    tmp_path: Path,
    scope_path: str,
    touched_path: str,
    allowed: bool,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SCOPE"
    _write_report(workspace_root, work_item, touched_path)
    _write_scope(workspace_root, work_item, f"# Allowed Write Scope\n\n- `{scope_path}`\n")

    findings = validate_semantic_outputs(
        stage="implement", work_item=work_item, workspace_root=workspace_root
    )
    scope_findings = [
        finding
        for finding in findings
        if finding.code == MISSING_DIFF_EVIDENCE_CODE
        and "allowed write scope" in finding.message
    ]

    assert bool(scope_findings) is not allowed


def test_semantic_validator_treats_missing_scope_as_unrestricted(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SCOPE-MISSING"
    _write_report(workspace_root, work_item, "anywhere/file.py")

    findings = validate_semantic_outputs(
        stage="implement", work_item=work_item, workspace_root=workspace_root
    )

    assert not any(
        finding.code == MISSING_DIFF_EVIDENCE_CODE
        and "allowed write scope" in finding.message
        for finding in findings
    )


def test_semantic_validator_ignores_backticked_code_in_touched_file_description(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SCOPE-DESCRIPTION-CODE"
    _write_report(workspace_root, work_item, "src/hono-base.ts")
    report = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    report.write_text(
        report.read_text(encoding="utf-8").replace(
            "updated behavior.",
            "assign the normalized value to `context.error`.",
        ),
        encoding="utf-8",
    )
    _write_scope(
        workspace_root,
        work_item,
        "# Allowed Write Scope\n\n- `src/hono-base.ts`\n",
    )

    findings = validate_semantic_outputs(
        stage="implement", work_item=work_item, workspace_root=workspace_root
    )

    assert not any(
        finding.code == MISSING_DIFF_EVIDENCE_CODE
        and "allowed write scope" in finding.message
        for finding in findings
    )


@pytest.mark.parametrize(
    "markdown",
    (
        "# Allowed Write Scope\n\n- none\n",
        "# Allowed Write Scope\n\n- `../src`\n",
        "# Allowed Write Scope\n\n- `/src`\n",
        "# Allowed Write Scope\n\n- `C:\\src`\n",
        "# Allowed Write Scope\n\n- `src/**`\n",
    ),
)
def test_semantic_validator_reports_malformed_scope(
    tmp_path: Path, markdown: str
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SCOPE-INVALID"
    _write_report(workspace_root, work_item, "src/app.py")
    _write_scope(workspace_root, work_item, markdown)

    findings = validate_semantic_outputs(
        stage="implement", work_item=work_item, workspace_root=workspace_root
    )

    assert any(
        finding.code == MISSING_DIFF_EVIDENCE_CODE
        and "Invalid allowed write scope" in finding.message
        for finding in findings
    )
