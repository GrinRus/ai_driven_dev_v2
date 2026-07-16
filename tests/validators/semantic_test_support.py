from __future__ import annotations

import subprocess
from pathlib import Path

_SEMANTIC_FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "semantic"


def _write_rich_tasklist_for_evidence(workspace_root: Path, work_item: str) -> None:
    path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Tasklist

## Task summary

One bounded task supplies structured aggregate evidence.

## Ordered tasks

### TL-1 — Add evidence

- Outcome: Evidence is explicit.
- Dominant deliverable: `src/example.py` records the behavior.
- In scope: `src/example.py`.
- Acceptance criteria:
  - TL-1-AC1: The evidence-backed behavior is present.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: `pytest tests/test_example.py -q`
""",
        encoding="utf-8",
    )

def _git(project_root: Path, *args: str) -> None:
    subprocess.run(
        ("git", "-C", project_root.as_posix(), *args),
        check=True,
        capture_output=True,
        text=True,
    )


def _write_stage_contract(
    *,
    contracts_root: Path,
    required_inputs: tuple[str, ...],
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    (contracts_root / "idea.md").write_text(
        "\n".join(
            [
                "# Stage Contract: `idea`",
                "",
                "## Purpose",
                "",
                "Turn intake into an idea brief.",
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
                "",
                "## Validation focus",
                "",
                "- required heading coverage in `idea-brief.md` "
                "(`Problem statement`, `Desired outcome`, `Constraints`, `Open questions`),",
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

    idea_brief_contract = documents_root / "idea-brief.md"
    idea_brief_contract.write_text(
        "\n".join(
            [
                "# Document Contract: `idea-brief.md`",
                "",
                "## Required sections",
                "",
                "- `Problem statement`",
                "- `Desired outcome`",
                "- `Constraints`",
                "- `Open questions`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    for prompt_path in prompt_pack_paths:
        prompt_file = repo_root / prompt_path
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text("# Prompt\n", encoding="utf-8")


def _write_idea_brief(workspace_root: Path, body: str) -> Path:
    path = workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "idea-brief.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_research_notes(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "research" / "research-notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_plan_document(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "plan" / "plan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_tasklist_document(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "tasklist" / "tasklist.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_qa_report(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "qa" / "qa-report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_acceptance_criteria(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "context" / "acceptance-criteria.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_repository_state(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "context" / "repository-state.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_workspace_baseline(
    workspace_root: Path,
    work_item: str,
    body: str = (
        "# Workspace Baseline\n\n"
        "## Setup-Owned Workspace Baseline\n\n"
        "- Setup-owned context captured before stage execution.\n\n"
        "## Setup-Owned Files Present\n\n"
        "- `aidd.example.toml`\n"
    ),
) -> Path:
    path = workspace_root / "workitems" / work_item / "context" / "workspace-baseline.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_review_spec_report(workspace_root: Path, work_item: str, body: str) -> Path:
    path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "review-spec"
        / "review-spec-report.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_implementation_report(workspace_root: Path, work_item: str, body: str) -> Path:
    path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_review_report(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "review" / "review-report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path

