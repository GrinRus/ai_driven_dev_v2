from __future__ import annotations

from pathlib import Path

from aidd.validators.models import ValidationFinding
from aidd.validators.structural import (
    MISSING_REQUIRED_DOCUMENT_CODE,
    MarkdownHeading,
    extract_document_headings,
    extract_markdown_headings,
    validate_required_document_existence,
)


def _write_stage_contract(
    *,
    contracts_root: Path,
    stage: str,
    required_inputs: tuple[str, ...],
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    (contracts_root / f"{stage}.md").write_text(
        "\n".join(
            [
                f"# Stage Contract: `{stage}`",
                "",
                "## Purpose",
                "",
                "Validate required document presence.",
                "",
                "## Primary output",
                "",
                *[f"- `{item}`" for item in required_outputs],
                "",
                "## Required inputs",
                "",
                *[f"- `{item}`" for item in required_inputs],
                "",
                "## Prompt pack",
                "",
                *[f"- `{item}`" for item in prompt_pack_paths],
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _touch_contract_references(
    *,
    repo_root: Path,
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    documents_root = repo_root / "contracts" / "documents"
    documents_root.mkdir(parents=True, exist_ok=True)
    for output in required_outputs:
        (documents_root / output).write_text("# Contract\n", encoding="utf-8")

    for prompt_path in prompt_pack_paths:
        prompt_file = repo_root / prompt_path
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text("# Prompt\n", encoding="utf-8")


def _write_workspace_markdown(workspace_root: Path, relative_path: str) -> None:
    path = workspace_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Document\n", encoding="utf-8")


def test_validate_required_document_existence_passes_when_all_required_docs_exist(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_inputs = ("context/intake.md", "../research/output/research-report.md")
    required_outputs = ("qa-report.md", "stage-result.md")
    prompt_paths = ("prompt-packs/stages/qa/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        stage="qa",
        required_inputs=required_inputs,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    workspace_root = tmp_path / ".aidd"
    _write_workspace_markdown(workspace_root, "workitems/WI-001/context/intake.md")
    _write_workspace_markdown(
        workspace_root,
        "workitems/WI-001/stages/research/output/research-report.md",
    )
    _write_workspace_markdown(workspace_root, "workitems/WI-001/stages/qa/qa-report.md")
    _write_workspace_markdown(workspace_root, "workitems/WI-001/stages/qa/stage-result.md")

    findings = validate_required_document_existence(
        stage="qa",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == ()


def test_validate_required_document_existence_reports_missing_input_and_output(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_inputs = ("context/intake.md", "../research/output/research-report.md")
    required_outputs = ("qa-report.md", "stage-result.md")
    prompt_paths = ("prompt-packs/stages/qa/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        stage="qa",
        required_inputs=required_inputs,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    workspace_root = tmp_path / ".aidd"
    _write_workspace_markdown(
        workspace_root,
        "workitems/WI-001/stages/research/output/research-report.md",
    )
    _write_workspace_markdown(workspace_root, "workitems/WI-001/stages/qa/qa-report.md")

    findings = validate_required_document_existence(
        stage="qa",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=MISSING_REQUIRED_DOCUMENT_CODE,
            message="Missing required document: workitems/WI-001/context/intake.md",
        ),
        ValidationFinding(
            code=MISSING_REQUIRED_DOCUMENT_CODE,
            message="Missing required document: workitems/WI-001/stages/qa/stage-result.md",
        ),
    )


def test_validate_required_document_existence_deduplicates_manifest_paths(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_inputs = ("stage-result.md",)
    required_outputs = ("stage-result.md",)
    prompt_paths = ("prompt-packs/stages/qa/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        stage="qa",
        required_inputs=required_inputs,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    workspace_root = tmp_path / ".aidd"
    findings = validate_required_document_existence(
        stage="qa",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=MISSING_REQUIRED_DOCUMENT_CODE,
            message="Missing required document: workitems/WI-001/stages/qa/stage-result.md",
        ),
    )


def test_extract_markdown_headings_returns_level_title_and_line_number() -> None:
    markdown = """# QA Report
Intro paragraph.

```md
## Ignored heading in fence
```

## Residual risks ##
### Follow-up checks
#NoSpaceHeading
    ## Indented code line
"""

    headings = extract_markdown_headings(markdown)

    assert headings == (
        MarkdownHeading(level=1, title="QA Report", line_number=1),
        MarkdownHeading(level=2, title="Residual risks", line_number=8),
        MarkdownHeading(level=3, title="Follow-up checks", line_number=9),
    )


def test_extract_document_headings_reads_workspace_markdown(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "qa" / "qa-report.md"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_text(
        "\n".join(
            [
                "---",
                "doc_kind: qa-report",
                "---",
                "# QA Report",
                "",
                "## Release recommendation",
                "",
                "Body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    headings = extract_document_headings(path=doc_path, workspace_root=workspace_root)

    assert headings == (
        MarkdownHeading(level=1, title="QA Report", line_number=4),
        MarkdownHeading(level=2, title="Release recommendation", line_number=6),
    )
