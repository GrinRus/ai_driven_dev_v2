from __future__ import annotations

from pathlib import Path

from semantic_test_support import (
    _write_rich_tasklist_for_evidence,
)

from aidd.validators.semantic import (
    has_non_placeholder_text,
)
from aidd.validators.semantic_rules.common import SemanticDocumentContext
from aidd.validators.task_evidence import validate_aggregate_task_evidence


def test_structured_task_evidence_accepts_one_exact_entry_per_criterion(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-EVIDENCE"
    _write_rich_tasklist_for_evidence(workspace_root, work_item)
    output_path = (
        workspace_root / "workitems" / work_item / "stages" / "review" / "review-report.md"
    )
    markdown = (
        "# Review Report\n\n"
        "## Verdict\n\n- Review status: approved\n\n"
        "## Task acceptance evidence\n\n"
        "- Task: `TL-1`; Acceptance: `TL-1-AC1`; Status: `pass`; "
        "Evidence: `stages/implement/task.md`; Notes: verified.\n"
    )
    context = SemanticDocumentContext.from_markdown(
        stage="review",
        output_path=output_path,
        workspace_root=workspace_root,
        required_sections=(),
        markdown_text=markdown,
    )

    findings = validate_aggregate_task_evidence(
        context=context,
        evidence=context.section_by_candidates(candidates=("Task acceptance evidence",)),
    )

    assert findings == ()


def test_structured_task_evidence_rejects_duplicate_and_non_pass_approved_entry(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-EVIDENCE"
    _write_rich_tasklist_for_evidence(workspace_root, work_item)
    output_path = (
        workspace_root / "workitems" / work_item / "stages" / "review" / "review-report.md"
    )
    entry = (
        "- Task: `TL-1`; Acceptance: `TL-1-AC1`; Status: `fail`; "
        "Evidence: EV-1; Notes: failed.\n"
    )
    markdown = (
        "# Review Report\n\n"
        "## Verdict\n\n- Review status: approved\n\n"
        "## Task acceptance evidence\n\n"
        f"{entry}{entry}"
    )
    context = SemanticDocumentContext.from_markdown(
        stage="review",
        output_path=output_path,
        workspace_root=workspace_root,
        required_sections=(),
        markdown_text=markdown,
    )

    findings = validate_aggregate_task_evidence(
        context=context,
        evidence=context.section_by_candidates(candidates=("Task acceptance evidence",)),
    )
    messages = "\n".join(finding.message for finding in findings)

    assert "contains duplicates" in messages
    assert "requires `Review status: rejected`" in messages

def test_has_non_placeholder_text_detects_placeholders() -> None:
    assert has_non_placeholder_text("Final answer with concrete detail.")
    assert not has_non_placeholder_text("TBD: fill this section later.")
    assert not has_non_placeholder_text("`TBD`")
    assert not has_non_placeholder_text("- `N/A`")
    assert not has_non_placeholder_text("- `...`")
    assert has_non_placeholder_text(
        "No placeholder content (`TBD`, `TODO`, `N/A`, `...`) remains."
    )
    assert has_non_placeholder_text(
        "No placeholder content (TBD, TODO, N/A, ...) detected."
    )
    assert has_non_placeholder_text(
        '- No\n  ambiguous "TBD" entries remain in the report.'
    )
    assert has_non_placeholder_text(
        "- No\n  `N/A` values are used for required evidence."
    )
    assert has_non_placeholder_text(
        "TSV header-only input is exercised with `data-tool insert ... --tsv`."
    )
    assert has_non_placeholder_text(
        "```\nAssertionError: Cannot transform a table\n```\n"
        "Then call `transform(...)` only when the table exists."
    )
    assert has_non_placeholder_text(
        "The final frame is `db.py:1888 ... AssertionError: Cannot transform "
        "a table that\ndoesn't exist yet` invoked from `cli.py:1180`."
    )
    assert has_non_placeholder_text(
        'The prose says "edit `cli.py:1179` ... so the transform call is skipped".'
    )
    assert not has_non_placeholder_text("Placeholder: TBD")
    assert not has_non_placeholder_text("- Evidence state:\n  TBD define signal.")

