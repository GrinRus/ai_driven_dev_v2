from __future__ import annotations

import re
from pathlib import Path

from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.validators.models import ValidationFinding, ValidationIssueLocation

_REPAIR_BUDGET_EXHAUSTED_TOKEN = "repair-budget-exhausted"
_STATUS_SECTION_PATTERN = re.compile(
    r"(?P<prefix>#{1,6}\s+Status\s*\n+)(?P<body>.*?)(?=\n#{1,6}\s+|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_TERMINAL_NOTES_PATTERN = re.compile(
    r"(?P<prefix>#{1,6}\s+Terminal state notes\s*\n+)(?P<body>.*?)(?=\n#{1,6}\s+|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_TERMINAL_STATUS_PATTERN = re.compile(r"\b(succeeded|failed|blocked|needs-input)\b")
_VALIDATOR_PASS_CLAIM_PATTERN = re.compile(
    r"(validator(?: report)? verdict\s*[:(][^`\n]*`?)pass\b(`?)",
    re.IGNORECASE,
)
_VALIDATION_PASS_LINE_PATTERN = re.compile(r"(validation\s+`)pass(`)", re.IGNORECASE)


def _workspace_relative_path(workspace_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _text_exhausts_terminal_budget(text: str) -> bool:
    normalized = text.lower()
    return _REPAIR_BUDGET_EXHAUSTED_TOKEN in normalized


def repair_brief_exhausts_terminal_budget(
    *,
    repair_brief_path: Path | None,
    repair_context_markdown: str | None,
) -> bool:
    if repair_context_markdown is not None and _text_exhausts_terminal_budget(
        repair_context_markdown
    ):
        return True
    if repair_brief_path is None or not repair_brief_path.exists():
        return False
    text = repair_brief_path.read_text(encoding="utf-8", errors="replace")
    return _text_exhausts_terminal_budget(text)


def ensure_repair_brief_records_exhausted_budget(repair_brief_path: Path | None) -> None:
    if repair_brief_path is None or not repair_brief_path.exists():
        return
    text = repair_brief_path.read_text(encoding="utf-8", errors="replace")
    if _REPAIR_BUDGET_EXHAUSTED_TOKEN in text.lower():
        return
    repair_brief_path.write_text(
        text.rstrip() + "\n\nRepair budget status: `repair-budget-exhausted`.\n",
        encoding="utf-8",
    )


def ensure_stage_result_references_repair_brief(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    repair_brief_path: Path | None,
) -> Path | None:
    if repair_brief_path is None or not repair_brief_path.exists():
        return None

    stage_result_path = (
        workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage)
        / "stage-result.md"
    )
    if not stage_result_path.exists():
        return None

    text = stage_result_path.read_text(encoding="utf-8", errors="replace")
    if "repair-brief.md" in text:
        return stage_result_path

    repair_brief_reference = _workspace_relative_path(workspace_root, repair_brief_path)
    note = f"- Repair decision context recorded in `{repair_brief_reference}`.\n"
    match = _TERMINAL_NOTES_PATTERN.search(text)
    if match is None:
        updated = text.rstrip() + "\n\n## Terminal state notes\n\n" + note
    else:
        body = match.group("body")
        prefix = "" if body.endswith("\n") or not body else "\n"
        updated = text[: match.end("body")] + prefix + note + text[match.end("body") :]

    stage_result_path.write_text(updated, encoding="utf-8")
    return stage_result_path


def _replace_or_add_status_section(markdown: str) -> str:
    match = _STATUS_SECTION_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Status\n\nfailed\n"

    body = match.group("body")
    replacement_body = _TERMINAL_STATUS_PATTERN.sub("failed", body, count=1)
    if replacement_body == body:
        replacement_body = "- `failed`\n"
    return (
        markdown[: match.start("body")]
        + replacement_body
        + markdown[match.end("body") :]
    )


def _append_exhausted_budget_terminal_note(markdown: str) -> str:
    note = (
        "\n\n- Repair budget status: `repair-budget-exhausted`; terminal status is "
        "`failed` because no rerun is allowed after this attempt.\n"
    )
    if _REPAIR_BUDGET_EXHAUSTED_TOKEN in markdown.lower():
        return markdown

    match = _TERMINAL_NOTES_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Terminal state notes" + note

    return markdown[: match.end("body")] + note + markdown[match.end("body") :]


def _replace_success_claims_for_exhausted_budget(markdown: str) -> str:
    updated = _VALIDATOR_PASS_CLAIM_PATTERN.sub(r"\1fail\2", markdown)
    return _VALIDATION_PASS_LINE_PATTERN.sub(r"\1fail\2", updated)


def _append_validator_failure_terminal_note(markdown: str) -> str:
    note = (
        "\n\n- Canonical AIDD validation found open findings; terminal status and "
        "validator verdict claims must not remain `succeeded` or `pass`.\n"
    )
    if "canonical aidd validation found open findings" in markdown.lower():
        return markdown

    match = _TERMINAL_NOTES_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Terminal state notes" + note

    return markdown[: match.end("body")] + note + markdown[match.end("body") :]


def strip_stage_result_success_claims_for_validator_findings(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> Path | None:
    stage_result_path = (
        workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage)
        / "stage-result.md"
    )
    if not stage_result_path.exists():
        return None

    text = stage_result_path.read_text(encoding="utf-8", errors="replace")
    updated = _replace_success_claims_for_exhausted_budget(
        _append_validator_failure_terminal_note(_replace_or_add_status_section(text))
    )
    if updated == text:
        return stage_result_path

    stage_result_path.write_text(updated, encoding="utf-8")
    return stage_result_path


def force_stage_result_failed_for_exhausted_budget(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> Path:
    stage_result_path = (
        workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage)
        / "stage-result.md"
    )
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    if stage_result_path.exists():
        text = stage_result_path.read_text(encoding="utf-8", errors="replace")
    else:
        text = (
            "# Stage result\n\n"
            f"## Stage\n\n{stage}\n\n"
            "## Attempt history\n\n- unavailable\n\n"
            "## Status\n\nfailed\n\n"
            "## Produced outputs\n\n- missing required outputs; repair budget exhausted\n\n"
            "## Validation summary\n\n- validation stopped after repair budget exhaustion\n\n"
            "## Blockers\n\n- repair budget exhausted\n\n"
            "## Next actions\n\n- inspect validator report and reopen manually if appropriate\n\n"
            "## Terminal state notes\n\n"
        )
    updated = _replace_success_claims_for_exhausted_budget(
        _append_exhausted_budget_terminal_note(_replace_or_add_status_section(text))
    )
    stage_result_path.write_text(updated, encoding="utf-8")
    return stage_result_path


def exhausted_budget_validation_finding(
    *,
    workspace_root: Path,
    stage_result_path: Path,
) -> ValidationFinding:
    return ValidationFinding(
        code="CROSS-REPAIR-BUDGET-EXHAUSTED",
        severity="critical",
        message=(
            "Repair budget is exhausted for this attempt; stage progression is stopped "
            "with terminal status `failed`."
        ),
        location=ValidationIssueLocation(
            workspace_relative_path=_workspace_relative_path(workspace_root, stage_result_path)
        ),
    )


__all__ = [
    "ensure_repair_brief_records_exhausted_budget",
    "ensure_stage_result_references_repair_brief",
    "exhausted_budget_validation_finding",
    "force_stage_result_failed_for_exhausted_budget",
    "repair_brief_exhausts_terminal_budget",
    "strip_stage_result_success_claims_for_validator_findings",
]
