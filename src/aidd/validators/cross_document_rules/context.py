from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


def read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def extract_section_lines(markdown_text: str, heading: str) -> list[tuple[int, str]]:
    target = heading.strip().lower()
    in_section = False
    section_lines: list[tuple[int, str]] = []
    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        stripped = line.strip()
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading_match:
            section_title = heading_match.group(2).strip().lower()
            if in_section and section_title != target:
                break
            in_section = section_title == target
            continue
        if in_section:
            section_lines.append((line_number, line))
    return section_lines


def heading_line_number(markdown_text: str, heading: str) -> int | None:
    target = heading.strip().lower()
    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if match is not None and match.group(2).strip().lower() == target:
            return line_number
    return None


def level_two_section_text(markdown: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        markdown,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group("body").strip() if match is not None else ""


@dataclass(frozen=True, slots=True)
class CrossDocumentContext:
    stage: str
    work_item: str
    workspace_root: Path
    stage_root: Path
    questions_path: Path
    questions_text: str | None
    answers_path: Path
    answers_text: str | None
    repair_brief_path: Path
    repair_brief_text: str | None
    stage_result_path: Path
    stage_result_text: str | None
    project_set_path: Path
    project_set_text: str | None
    tasklist_path: Path
    tasklist_text: str | None
    plan_path: Path
    plan_text: str | None
    review_path: Path
    review_text: str | None
    qa_path: Path
    qa_text: str | None
    upstream_review_path: Path
    upstream_review_text: str | None
    implementation_output_root: Path
    implementation_report_path: Path
    implementation_text: str | None
    published_tasklist_path: Path

    @classmethod
    def load(
        cls,
        *,
        stage: str,
        work_item: str,
        workspace_root: Path,
    ) -> CrossDocumentContext:
        work_item_root = workspace_root / "workitems" / work_item
        stage_root = work_item_root / "stages" / stage
        questions_path = stage_root / "questions.md"
        answers_path = stage_root / "answers.md"
        repair_brief_path = stage_root / "repair-brief.md"
        stage_result_path = stage_root / "stage-result.md"
        project_set_path = work_item_root / "context" / "project-set.md"
        tasklist_path = stage_root / "tasklist.md"
        plan_path = work_item_root / "stages" / "plan" / "output" / "plan.md"
        review_path = stage_root / "review-report.md"
        qa_path = stage_root / "qa-report.md"
        upstream_review_path = (
            work_item_root / "stages" / "review" / "output" / "review-report.md"
        )
        implementation_output_root = work_item_root / "stages" / "implement" / "output"
        implementation_report_path = implementation_output_root / "implementation-report.md"
        published_tasklist_path = (
            work_item_root / "stages" / "tasklist" / "output" / "tasklist.md"
        )
        return cls(
            stage=stage,
            work_item=work_item,
            workspace_root=workspace_root,
            stage_root=stage_root,
            questions_path=questions_path,
            questions_text=read_optional(questions_path),
            answers_path=answers_path,
            answers_text=read_optional(answers_path),
            repair_brief_path=repair_brief_path,
            repair_brief_text=read_optional(repair_brief_path),
            stage_result_path=stage_result_path,
            stage_result_text=read_optional(stage_result_path),
            project_set_path=project_set_path,
            project_set_text=read_optional(project_set_path),
            tasklist_path=tasklist_path,
            tasklist_text=read_optional(tasklist_path),
            plan_path=plan_path,
            plan_text=read_optional(plan_path),
            review_path=review_path,
            review_text=read_optional(review_path),
            qa_path=qa_path,
            qa_text=read_optional(qa_path),
            upstream_review_path=upstream_review_path,
            upstream_review_text=read_optional(upstream_review_path),
            implementation_output_root=implementation_output_root,
            implementation_report_path=implementation_report_path,
            implementation_text=read_optional(implementation_report_path),
            published_tasklist_path=published_tasklist_path,
        )
