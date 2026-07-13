from __future__ import annotations

import re
from dataclasses import dataclass

from aidd.core.task_plan import TaskPlanParseError, parse_task_plan
from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    MISSING_EVIDENCE_LINK_CODE,
    SemanticDocumentContext,
    SemanticSection,
    extract_qa_release_recommendation,
    extract_qa_verdict,
)

_ENTRY_PATTERN = re.compile(
    r"^-\s+Task:\s*`(?P<task>[^`]+)`;\s*"
    r"Acceptance:\s*`(?P<acceptance>[^`]+)`;\s*"
    r"Status:\s*`(?P<status>pass|fail|not-verified)`;\s*"
    r"Evidence:\s*(?P<evidence>[^;]+)(?:;\s*Notes:\s*.*)?$",
    re.IGNORECASE,
)
_TASK_ID_PATTERN = re.compile(r"\b((?:[A-Z][A-Z0-9]{0,15}-\d+)|T\d+)\b(?!-AC)")
_ACCEPTANCE_ID_PATTERN = re.compile(
    r"\b((?:[A-Z][A-Z0-9]{0,15}-\d+|T\d+)-AC[1-9]\d*)\b"
)
_EVIDENCE_PATTERN = re.compile(r"`[^`]+`|\bEV-\d+\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class _EvidenceEntry:
    task_id: str
    acceptance_id: str
    status: str
    evidence: str
    raw_line: str


def _entries(section: SemanticSection) -> tuple[tuple[_EvidenceEntry, ...], tuple[str, ...]]:
    parsed: list[_EvidenceEntry] = []
    malformed: list[str] = []
    for raw_line in section.content.splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        match = _ENTRY_PATTERN.fullmatch(line)
        if match is None:
            malformed.append(line)
            continue
        parsed.append(
            _EvidenceEntry(
                task_id=match.group("task").upper(),
                acceptance_id=match.group("acceptance").upper(),
                status=match.group("status").lower(),
                evidence=match.group("evidence").strip(),
                raw_line=line,
            )
        )
    return tuple(parsed), tuple(malformed)


def _finding(
    context: SemanticDocumentContext,
    section: SemanticSection,
    message: str,
) -> ValidationFinding:
    return context.finding(
        code=MISSING_EVIDENCE_LINK_CODE,
        message=message,
        severity="high",
        location=section.location,
    )


def validate_aggregate_task_evidence(
    *,
    context: SemanticDocumentContext,
    evidence: SemanticSection,
) -> tuple[ValidationFinding, ...]:
    workitems_index = context.output_path.parts.index("workitems")
    work_item = context.output_path.parts[workitems_index + 1]
    tasklist_path = (
        context.workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    if not tasklist_path.exists():
        return ()
    try:
        plan = parse_task_plan(tasklist_path.read_text(encoding="utf-8"))
    except TaskPlanParseError:
        return ()
    section = context.section_by_candidates(candidates=("Task acceptance evidence",))
    entries, malformed = _entries(section)
    findings: list[ValidationFinding] = []
    if malformed or not entries:
        findings.append(
            _finding(
                context,
                section if section.content else evidence,
                "Section `Task acceptance evidence` must contain one structured top-level "
                "entry per task acceptance criterion.",
            )
        )

    expected = {
        (task.id, criterion.id)
        for task in plan.tasks
        for criterion in task.acceptance_criteria
    }
    observed: list[tuple[str, str]] = []
    non_pass = False
    for entry in entries:
        pair = (entry.task_id, entry.acceptance_id)
        observed.append(pair)
        non_pass = non_pass or entry.status != "pass"
        if pair not in expected:
            findings.append(
                _finding(
                    context,
                    section,
                    f"Task acceptance evidence references unknown or mismatched pair "
                    f"`{entry.task_id}` / `{entry.acceptance_id}`.",
                )
            )
        task_ids = {match.group(1).upper() for match in _TASK_ID_PATTERN.finditer(entry.raw_line)}
        acceptance_ids = {
            match.group(1).upper()
            for match in _ACCEPTANCE_ID_PATTERN.finditer(entry.raw_line)
        }
        if task_ids != {entry.task_id} or acceptance_ids != {entry.acceptance_id}:
            findings.append(
                _finding(
                    context,
                    section,
                    "Each task acceptance evidence entry must name exactly one matching task "
                    "and acceptance id.",
                )
            )
        if _EVIDENCE_PATTERN.search(entry.evidence) is None:
            findings.append(
                _finding(
                    context,
                    section,
                    f"Task acceptance evidence for `{entry.acceptance_id}` must cite an "
                    "`EV-N` id or backticked artifact path.",
                )
            )

    missing = sorted(expected - set(observed))
    duplicate = sorted({pair for pair in observed if observed.count(pair) > 1})
    if missing:
        findings.append(
            _finding(
                context,
                section,
                "Task acceptance evidence is missing: "
                + ", ".join(f"{task}/{acceptance}" for task, acceptance in missing)
                + ".",
            )
        )
    if duplicate:
        findings.append(
            _finding(
                context,
                section,
                "Task acceptance evidence contains duplicates: "
                + ", ".join(f"{task}/{acceptance}" for task, acceptance in duplicate)
                + ".",
            )
        )

    document = "\n".join(context.markdown_lines)
    if non_pass and context.stage == "review":
        status = re.search(
            r"Review status\s*:\s*(approved-with-conditions|approved|rejected)",
            document,
            re.IGNORECASE,
        )
        if status is None or status.group(1).lower() != "rejected":
            findings.append(
                _finding(
                    context,
                    section,
                    "Review task acceptance status `fail` or `not-verified` requires "
                    "`Review status: rejected`.",
                )
            )
    if non_pass and context.stage == "qa":
        verdict = extract_qa_verdict(document, prefer_labeled=True)
        recommendation = extract_qa_release_recommendation(document)
        if verdict != "not-ready" or recommendation != "hold":
            findings.append(
                _finding(
                    context,
                    section,
                    "QA task acceptance status `fail` or `not-verified` requires "
                    "`QA verdict: not-ready` and release recommendation `hold`.",
                )
            )
    return tuple(dict.fromkeys(findings))


__all__ = ["validate_aggregate_task_evidence"]
