from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from aidd.core.models.run import RepairHistoryEntry
from aidd.core.stage_registry import resolve_expected_output_documents
from aidd.core.stages import next_stage
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
_VALIDATION_SUMMARY_PATTERN = re.compile(
    r"(?P<prefix>#{1,6}\s+Validation summary\s*\n+)(?P<body>.*?)(?=\n#{1,6}\s+|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_TERMINAL_STATUS_PATTERN = re.compile(r"\b(succeeded|failed|blocked|needs-input)\b")
_STALE_NON_SUCCESS_STATUS_PATTERN = re.compile(r"\b(failed|blocked|needs-input)\b")
_VALIDATOR_PASS_CLAIM_PATTERN = re.compile(
    r"(validator(?: report)? verdict\s*[:(][^`\n]*`?)pass\b(`?)",
    re.IGNORECASE,
)
_VALIDATOR_VERDICT_LINE_PATTERN = re.compile(
    r"(?P<prefix>^\s*[-*]\s*Validator verdict\s*:\s*)"
    r"`?(?:pass|fail|not-run|unknown|missing)`?(?P<suffix>.*)$",
    re.IGNORECASE | re.MULTILINE,
)
_STALE_VALIDATOR_VERDICT_LINE_PATTERN = re.compile(
    r"^\s*[-*]\s*Validator verdict\s*:\s*`?(?:fail|not-run|unknown|missing)`?",
    re.IGNORECASE | re.MULTILINE,
)
_VALIDATION_PASS_LINE_PATTERN = re.compile(r"(validation\s+`)pass(`)", re.IGNORECASE)
_STALE_TERMINAL_STATUS_NOTE_PATTERN = re.compile(
    r"^\s*[-*]\s+.*\b(?:"
    r"stage\s+ended|ended\s+as|ended\s+with|terminal\s+status|"
    r"status\s+is|declared\s+status|stage\s+stopped|run\s+stopped"
    r")\b.*`?(?:failed|blocked|needs-input)`?.*$",
    re.IGNORECASE,
)
_VALIDATION_PASS_NORMALIZATION_MARKER = "stale runtime draft status/verdict was normalized"
_NEXT_ACTIONS_PATTERN = re.compile(
    r"(?P<prefix>#{1,6}\s+Next actions\s*\n+)(?P<body>.*?)(?=\n#{1,6}\s+|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_PRODUCED_OUTPUTS_PATTERN = re.compile(
    r"(?P<prefix>#{1,6}\s+Produced outputs\s*\n+)(?P<body>.*?)(?=\n#{1,6}\s+|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_BLOCKERS_PATTERN = re.compile(
    r"(?P<prefix>#{1,6}\s+Blockers\s*\n+)(?P<body>.*?)(?=\n#{1,6}\s+|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_EMPTY_SUCCESS_BLOCKER_LINE_PATTERN = re.compile(
    r"^(?:[-*]\s*)?(?:blockers?\s*:\s*)?"
    r"(?:none|no blockers?|no known blockers?)\s*[.`]?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class CanonicalStageResultProjection:
    """Lifecycle-owned fields used to render a stage-result document.

    Runtime-authored Markdown is deliberately absent from this projection.  The caller
    supplies only durable lifecycle state and retained evidence, which keeps terminal
    status, validation, and next-action fields independent from a model draft.
    """

    stage: str
    work_item: str
    status: str
    attempt_number: int
    attempt_mode: str = "initial"
    attempt_outcome: str = "completed"
    repair_history: tuple[RepairHistoryEntry, ...] = ()
    produced_output_paths: tuple[str | Path, ...] = ()
    missing_output_paths: tuple[str | Path, ...] = ()
    validator_verdict: str | None = None
    validator_report_path: str | Path | None = None
    repair_brief_path: str | Path | None = None
    blockers: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    terminal_notes: tuple[str, ...] = ()
    repair_budget_status: str | None = None


def _canonical_terminal_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized == "repair-needed":
        # The document contract intentionally exposes only terminal vocabulary.  The
        # lifecycle state remains available in the terminal notes and metadata.
        return "failed"
    if normalized not in {"succeeded", "failed", "blocked", "needs-input"}:
        raise ValueError(f"Unsupported canonical stage-result status: {status}")
    return normalized


def _canonical_relative_path(*, workspace_root: Path | None, path: str | Path) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate.as_posix()
    if workspace_root is None:
        raise ValueError("Absolute stage-result paths require workspace_root")
    return _workspace_relative_path(workspace_root, candidate)


def _canonical_trigger(attempt_mode: str) -> str:
    normalized = attempt_mode.strip().lower()
    if normalized in {"initial", "repair", "intervention", "resume", "repair-extension"}:
        return normalized
    return "repair" if normalized else "initial"


def _canonical_verdict(*, status: str, validator_verdict: str | None) -> str:
    if validator_verdict is None:
        return "pass" if status == "succeeded" else "fail"
    normalized = validator_verdict.strip().lower()
    if normalized in {"pass", "fail", "not-run"}:
        return normalized
    if normalized in {"repair", "blocked", "unknown", "missing"}:
        return "fail"
    raise ValueError(f"Unsupported canonical validator verdict: {validator_verdict}")


def _canonical_attempt_lines(
    *,
    attempt_number: int,
    attempt_mode: str,
    attempt_outcome: str,
    repair_history: Iterable[RepairHistoryEntry],
) -> tuple[str, ...]:
    if attempt_number < 1:
        raise ValueError("Stage-result attempt number must be >= 1")
    entries = tuple(repair_history)
    records: list[tuple[int, str, str]] = []
    for entry in entries:
        line = f"- Attempt `{entry.attempt_number}` (`{entry.trigger}`) -> {entry.outcome}."
        evidence: list[str] = []
        if entry.validator_report_path:
            evidence.append(f"validator: `{entry.validator_report_path}`")
        if entry.repair_brief_path:
            evidence.append(f"repair brief: `{entry.repair_brief_path}`")
        if evidence:
            line += f" Evidence: {', '.join(evidence)}."
        records.append((entry.attempt_number, entry.trigger, line))
    if not any(entry.attempt_number == attempt_number for entry in entries):
        trigger = _canonical_trigger(attempt_mode)
        outcome = attempt_outcome.strip() or "completed"
        records.append(
            (attempt_number, trigger, f"- Attempt `{attempt_number}` (`{trigger}`) -> {outcome}.")
        )
    return tuple(line for _, _, line in sorted(records, key=lambda item: (item[0], item[1])))


def _canonical_default_next_actions(
    *, stage: str, status: str, budget: str | None
) -> tuple[str, ...]:
    if status == "succeeded":
        downstream = next_stage(stage)
        if downstream is None:
            return ("- Inspect the terminal handoff and retained final artifacts.",)
        return (f"- Advance to the immediate canonical `{downstream}` stage.",)
    if status == "blocked":
        return ("- Resolve the blocking question or operator request, then resume this stage.",)
    if status == "needs-input":
        return ("- Record the requested operator input, then resume this stage.",)
    if budget == "repair-budget-exhausted":
        return (
            "- Inspect canonical validator evidence and request a separate manual intervention; "
            "no automatic repair remains.",
        )
    return ("- Review the canonical validator report and prepare the next bounded repair attempt.",)


def _project_set_evidence_lines(
    *, workspace_root: Path | None, work_item: str
) -> tuple[str, ...]:
    if workspace_root is None:
        return ()
    context_path = (
        workspace_root
        / "workitems"
        / work_item
        / "context"
        / "project-set.md"
    )
    if not context_path.exists():
        return ()
    try:
        context_text = context_path.read_text(encoding="utf-8")
    except OSError:
        context_text = ""
    projects = tuple(
        (match.group(1), match.group(2))
        for line in context_text.splitlines()
        if (
            match := re.match(
                r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", line.strip()
            )
        )
    )
    context_relative = _workspace_relative_path(workspace_root, context_path)
    lines: list[str] = [
        "## Project-set evidence",
        "",
        f"- Context: `{context_relative}`",
    ]
    if projects:
        lines.append("- Declared project roots:")
        lines.extend(
            f"  - `{project_id}` at `{project_root}`"
            for project_id, project_root in projects
        )
    else:
        lines.append("- No declared project roots were recorded in the context document.")
    lines.extend(
        [
            "- Canonical lifecycle records preserve per-project ownership for this stage.",
            "",
        ]
    )
    return tuple(lines)


def render_stage_result_from_lifecycle_state(
    projection: CanonicalStageResultProjection,
    *,
    workspace_root: Path | None = None,
) -> str:
    """Render a byte-stable stage-result exclusively from lifecycle state.

    The output intentionally has no timestamps, UUIDs, or copied runtime prose, so repeated
    reconciliation of the same projection produces identical bytes.
    """

    stage = projection.stage.strip()
    work_item = projection.work_item.strip()
    if not stage or not work_item:
        raise ValueError("Stage and work item are required for canonical stage-result rendering")
    status = _canonical_terminal_status(projection.status)
    validator_verdict = _canonical_verdict(
        status=status,
        validator_verdict=projection.validator_verdict,
    )
    validator_report = (
        _canonical_relative_path(
            workspace_root=workspace_root,
            path=projection.validator_report_path,
        )
        if projection.validator_report_path is not None
        else None
    )
    repair_brief = (
        _canonical_relative_path(workspace_root=workspace_root, path=projection.repair_brief_path)
        if projection.repair_brief_path is not None
        else None
    )

    stage_root_prefix = f"workitems/{work_item}/stages/{stage}/"
    supplied_output_paths = tuple(
        _canonical_relative_path(workspace_root=workspace_root, path=path)
        for path in projection.produced_output_paths
    )
    declared_output_paths = (
        tuple(
            _canonical_relative_path(workspace_root=workspace_root, path=path)
            for path in resolve_expected_output_documents(
                stage=stage,
                work_item=work_item,
                workspace_root=workspace_root or Path("."),
            )
        )
        if status == "succeeded"
        else ()
    )
    output_paths = tuple(dict.fromkeys((*supplied_output_paths, *declared_output_paths)))
    output_paths = tuple(dict.fromkeys((*output_paths, f"{stage_root_prefix}stage-result.md")))
    if validator_report is not None:
        output_paths = tuple(dict.fromkeys((*output_paths, validator_report)))
    if repair_brief is not None:
        output_paths = tuple(dict.fromkeys((*output_paths, repair_brief)))

    missing_paths = tuple(
        _canonical_relative_path(workspace_root=workspace_root, path=path)
        for path in projection.missing_output_paths
    )
    blockers = tuple(item.strip() for item in projection.blockers if item.strip())
    if status == "succeeded":
        blocker_lines = ("- none",) if not blockers else tuple(f"- {item}" for item in blockers)
    elif blockers:
        blocker_lines = tuple(f"- {item}" for item in blockers)
    else:
        blocker_lines = (f"- Stage ended with status `{status}` and needs operator action.",)

    budget = projection.repair_budget_status.strip() if projection.repair_budget_status else None
    next_actions = projection.next_actions or _canonical_default_next_actions(
        stage=stage,
        status=status,
        budget=budget,
    )
    attempt_lines = _canonical_attempt_lines(
        attempt_number=projection.attempt_number,
        attempt_mode=projection.attempt_mode,
        attempt_outcome=projection.attempt_outcome,
        repair_history=projection.repair_history,
    )
    notes = [f"- Canonical lifecycle status: `{projection.status.strip().lower()}`."]
    notes.append(f"- Canonical validator verdict: `{validator_verdict}`.")
    if status != "succeeded" and validator_report is not None:
        notes.append(
            "- Canonical AIDD validation found open findings; terminal status and "
            "validator verdict claims must not remain `succeeded` or `pass`."
        )
    if budget is not None:
        notes.append(f"- Repair budget status: `{budget}`.")
    notes.extend(
        f"- {note.strip().lstrip('- ').strip()}"
        for note in projection.terminal_notes
        if note.strip()
        and "todo" not in note.lower()
        and note.strip().lower().lstrip("- ").startswith("terminal state notes") is False
    )
    if repair_brief is not None:
        notes.append(f"- Repair decision context recorded in `{repair_brief}`.")
    project_set_evidence = _project_set_evidence_lines(
        workspace_root=workspace_root,
        work_item=work_item,
    )

    lines = [
        "# Stage Result",
        "",
        "## Stage",
        "",
        f"- Stage: `{stage}`",
        "",
        "## Attempt history",
        "",
        *attempt_lines,
        "",
        "## Status",
        "",
        f"- Status: `{status}`",
        "",
        "## Produced outputs",
        "",
        *(f"- `{path}`" for path in output_paths),
        *(f"- Missing required output: `{path}`" for path in missing_paths),
        "",
        "## Validation summary",
        "",
        f"- Validator verdict: {validator_verdict}",
        (
            f"- Validator report: `{validator_report}`"
            if validator_report is not None
            else "- Validator report: not available; validation was not reached."
        ),
        "",
        "## Blockers",
        "",
        *blocker_lines,
        "",
        "## Next actions",
        "",
        *next_actions,
        "",
        *project_set_evidence,
        "## Terminal state notes",
        "",
        *notes,
        "",
    ]
    return "\n".join(lines)


def write_stage_result_from_lifecycle_state(
    projection: CanonicalStageResultProjection,
    *,
    workspace_root: Path,
) -> Path:
    stage_result_path = (
        workspace_stage_root(
            root=workspace_root,
            work_item=projection.work_item,
            stage=projection.stage,
        )
        / "stage-result.md"
    )
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    stage_result_path.write_text(
        render_stage_result_from_lifecycle_state(projection, workspace_root=workspace_root),
        encoding="utf-8",
    )
    return stage_result_path


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
    """Canonicalize the Status section to one lifecycle-owned marker.

    Runtime drafts can contain a mixture of legacy bare markers and newer labelled
    markers, sometimes with conflicting values after a repair.  The lifecycle state
    is authoritative, so discard the draft body and write the contract's single
    labelled status line while leaving every other section byte-for-byte intact.
    """
    match = _STATUS_SECTION_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Status\n\n- Status: `failed`\n"

    replacement_body = "- Status: `failed`\n"
    return markdown[: match.start("body")] + replacement_body + markdown[match.end("body") :]


def _replace_or_add_success_status_section(markdown: str) -> str:
    """Canonicalize the Status section to exactly one successful marker."""
    match = _STATUS_SECTION_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Status\n\n- Status: `succeeded`\n"

    replacement_body = "- Status: `succeeded`\n"
    return markdown[: match.start("body")] + replacement_body + markdown[match.end("body") :]


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


def _replace_or_add_validator_pass_claim(markdown: str) -> str:
    match = _VALIDATION_SUMMARY_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Validation summary\n\n- Validator verdict: `pass`\n"

    body = match.group("body")
    verdict_matches = tuple(_VALIDATOR_VERDICT_LINE_PATTERN.finditer(body))
    if not verdict_matches:
        prefix = "" if not body or body.endswith("\n") else "\n"
        replacement_body = body + prefix + "- Validator verdict: `pass`\n"
    else:
        first_verdict_seen = False

        def _canonical_verdict(match: re.Match[str]) -> str:
            nonlocal first_verdict_seen
            if first_verdict_seen:
                return ""
            first_verdict_seen = True
            return f"{match.group('prefix')}`pass`{match.group('suffix')}"

        replacement_body = _VALIDATOR_VERDICT_LINE_PATTERN.sub(
            _canonical_verdict,
            body,
        )
    return markdown[: match.start("body")] + replacement_body + markdown[match.end("body") :]


def _append_validator_pass_terminal_note(markdown: str) -> str:
    note = (
        "\n\n- Canonical AIDD validation passed; stale runtime draft status/verdict "
        "was normalized to `succeeded` / `pass` before publication.\n"
    )
    if _VALIDATION_PASS_NORMALIZATION_MARKER in markdown.lower():
        return markdown

    match = _TERMINAL_NOTES_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Terminal state notes" + note

    return markdown[: match.end("body")] + note + markdown[match.end("body") :]


def _replace_success_next_action(markdown: str, *, stage: str) -> str:
    downstream = next_stage(stage)
    if downstream is None:
        return markdown
    replacement = f"- Continue to `{downstream}`.\n"
    match = _NEXT_ACTIONS_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + f"\n\n## Next actions\n\n{replacement}"
    return markdown[: match.start("body")] + replacement + markdown[match.end("body") :]


def _replace_success_produced_outputs(
    markdown: str,
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> str:
    paths = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
    )
    body = "".join(
        f"- `{_workspace_relative_path(workspace_root, path)}`\n" for path in paths
    )
    match = _PRODUCED_OUTPUTS_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Produced outputs\n\n" + body
    return markdown[: match.start("body")] + body + markdown[match.end("body") :]


def _replace_success_blockers(markdown: str) -> str:
    match = _BLOCKERS_PATTERN.search(markdown)
    if match is None:
        return markdown.rstrip() + "\n\n## Blockers\n\n- none\n"
    return markdown[: match.start("body")] + "- none\n" + markdown[match.end("body") :]


def normalize_success_stage_result_blockers_if_empty(stage_result_path: Path) -> bool:
    """Canonicalize an explicitly empty blocker claim before semantic validation."""

    if not stage_result_path.exists():
        return False
    markdown = stage_result_path.read_text(encoding="utf-8", errors="replace")
    status_match = _STATUS_SECTION_PATTERN.search(markdown)
    blockers_match = _BLOCKERS_PATTERN.search(markdown)
    if status_match is None or blockers_match is None:
        return False
    statuses = {
        match.group(1).lower()
        for match in _TERMINAL_STATUS_PATTERN.finditer(status_match.group("body"))
    }
    if statuses != {"succeeded"}:
        return False

    body_lines = tuple(
        line.strip() for line in blockers_match.group("body").splitlines() if line.strip()
    )
    if body_lines and not all(
        _EMPTY_SUCCESS_BLOCKER_LINE_PATTERN.fullmatch(line) for line in body_lines
    ):
        return False

    normalized = _replace_success_blockers(markdown)
    if normalized == markdown:
        return False
    stage_result_path.write_text(normalized, encoding="utf-8")
    return True


def _replace_stale_terminal_status_notes_for_validation_pass(markdown: str) -> str:
    match = _TERMINAL_NOTES_PATTERN.search(markdown)
    if match is None:
        return markdown

    replacement_note = (
        "- Canonical AIDD validation passed; stale runtime draft status/verdict "
        "was normalized to `succeeded` / `pass` before publication, and stale "
        "terminal-status text was removed. Inspect the primary stage report for "
        "product-quality decisions such as review rejection, QA readiness, or "
        "remediation requirements.\n"
    )
    replacement_lines: list[str] = []
    replaced = False
    inserted_replacement = False
    for line in match.group("body").splitlines(keepends=True):
        if _STALE_TERMINAL_STATUS_NOTE_PATTERN.match(line):
            replaced = True
            if not inserted_replacement:
                replacement_lines.append(replacement_note)
                inserted_replacement = True
            continue
        replacement_lines.append(line)

    if not replaced:
        return markdown

    return (
        markdown[: match.start("body")] + "".join(replacement_lines) + markdown[match.end("body") :]
    )


def _has_stale_failure_claim_for_validation_pass(markdown: str) -> bool:
    status_match = _STATUS_SECTION_PATTERN.search(markdown)
    has_stale_status = (
        status_match is not None
        and _STALE_NON_SUCCESS_STATUS_PATTERN.search(status_match.group("body")) is not None
    )
    validation_summary_match = _VALIDATION_SUMMARY_PATTERN.search(markdown)
    has_stale_validator_verdict = (
        validation_summary_match is not None
        and _STALE_VALIDATOR_VERDICT_LINE_PATTERN.search(validation_summary_match.group("body"))
        is not None
    )
    return has_stale_status or has_stale_validator_verdict


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


def reconcile_stage_result_after_validation_pass(
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
    has_stale_failure_claim = _has_stale_failure_claim_for_validation_pass(text)
    updated = _replace_success_produced_outputs(
        _replace_success_next_action(
            _replace_success_blockers(
                _replace_or_add_validator_pass_claim(_replace_or_add_success_status_section(text))
            ),
            stage=stage,
        ),
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    if has_stale_failure_claim:
        updated = _replace_stale_terminal_status_notes_for_validation_pass(updated)
        updated = _append_validator_pass_terminal_note(updated)
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
    "CanonicalStageResultProjection",
    "ensure_repair_brief_records_exhausted_budget",
    "ensure_stage_result_references_repair_brief",
    "exhausted_budget_validation_finding",
    "force_stage_result_failed_for_exhausted_budget",
    "normalize_success_stage_result_blockers_if_empty",
    "reconcile_stage_result_after_validation_pass",
    "repair_brief_exhausts_terminal_budget",
    "render_stage_result_from_lifecycle_state",
    "strip_stage_result_success_claims_for_validator_findings",
    "write_stage_result_from_lifecycle_state",
]
