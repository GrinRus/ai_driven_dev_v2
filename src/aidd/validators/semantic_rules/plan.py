from __future__ import annotations

import re

from aidd.core.allowed_write_scope import (
    AllowedWriteScope,
    AllowedWriteScopeError,
    resolve_allowed_write_scope,
)
from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_SECTION_CODE,
    RISK_MITIGATION_PATTERN,
    SemanticDocumentContext,
    SemanticRule,
    extract_bullet_items,
    extract_milestone_ids,
    extract_risk_blocks,
    extract_top_level_bullet_blocks,
    normalized_heading,
    validate_placeholder_sections,
    work_item_root_from_output_path,
)

PLAN_SCOPE_MISMATCH_CODE = "SEM-PLAN-SCOPE-MISMATCH"
_BACKTICKED_TOKEN_PATTERN = re.compile(r"`([^`\n]+)`")
_WRITE_INTENT_PATTERN = re.compile(
    r"\b(?:add|creat|delet|edit|implement|introduc|modif|mov|remov|renam|updat|"
    r"writ)\w*\b",
    flags=re.IGNORECASE,
)
_READ_ONLY_INTENT_PATTERN = re.compile(
    r"\b(?:audit|check|inspect|read|reference|review|scan|verify)(?:ed|s|ing)?\b",
    flags=re.IGNORECASE,
)
_READ_ONLY_LABEL_PATTERN = re.compile(
    r"\b(?:artifact|command|evidence|reference|source|verification)\s*:\s*$",
    flags=re.IGNORECASE,
)


def _work_item(context: SemanticDocumentContext) -> str | None:
    root = work_item_root_from_output_path(context.output_path)
    return root.name if root is not None else None


def _looks_like_repository_path(token: str) -> bool:
    candidate = token.strip()
    if not candidate or any(character.isspace() for character in candidate):
        return False
    if "://" in candidate or candidate.startswith(("-", "$")):
        return False
    return (
        "/" in candidate
        or "\\" in candidate
        or candidate.startswith(".")
        or re.match(r"^[A-Za-z]:", candidate) is not None
        or any(marker in candidate for marker in ("*", "?", "[", "]"))
    )


def _proposed_write_paths(section_content: str) -> tuple[str, ...]:
    paths: list[str] = []
    blocks = extract_top_level_bullet_blocks(section_content)
    candidates = blocks or tuple(
        paragraph for paragraph in re.split(r"\n\s*\n", section_content) if paragraph.strip()
    )
    for block in candidates:
        block = re.sub(r"```.*?```|~~~.*?~~~", "", block, flags=re.DOTALL)
        if _WRITE_INTENT_PATTERN.search(block) is None:
            continue
        for line in block.splitlines():
            for token_match in _BACKTICKED_TOKEN_PATTERN.finditer(line):
                token = token_match.group(1)
                if not _looks_like_repository_path(token):
                    continue
                prefix = line[: token_match.start()]
                write_intents = tuple(_WRITE_INTENT_PATTERN.finditer(prefix))
                read_intents = tuple(_READ_ONLY_INTENT_PATTERN.finditer(prefix))
                last_write = write_intents[-1].start() if write_intents else -1
                last_read = read_intents[-1].start() if read_intents else -1
                if _READ_ONLY_LABEL_PATTERN.search(prefix) or last_read > last_write:
                    continue
                paths.append(token.strip())
    return tuple(dict.fromkeys(paths))


def _paths_outside_scope(
    paths: tuple[str, ...],
    scope: AllowedWriteScope,
) -> tuple[str, ...]:
    outside: list[str] = []
    for path in paths:
        try:
            allowed = scope.allows(path)
        except AllowedWriteScopeError:
            allowed = False
        if not allowed:
            outside.append(path)
    return tuple(outside)


def _scope_findings(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    work_item = _work_item(context)
    if work_item is None:
        return ()
    try:
        scope = resolve_allowed_write_scope(context.workspace_root, work_item)
    except AllowedWriteScopeError as exc:
        return (
            context.finding(
                code=PLAN_SCOPE_MISMATCH_CODE,
                message=(
                    "Canonical allowed write scope is malformed; proposed Plan writes cannot "
                    "be validated: " + "; ".join(exc.issues)
                ),
                severity="high",
                location=context.location(),
            ),
        )
    if scope is None:
        return ()

    findings: list[ValidationFinding] = []
    for section_name in ("Milestones", "Implementation strategy"):
        section = context.section_by_candidates(candidates=(section_name,))
        outside = _paths_outside_scope(_proposed_write_paths(section.content), scope)
        if not outside:
            continue
        findings.append(
            context.finding(
                code=PLAN_SCOPE_MISMATCH_CODE,
                message=(
                    f"Section `{section_name}` proposes repository writes outside canonical "
                    "`context/allowed-write-scope.md`: "
                    + ", ".join(f"`{path}`" for path in outside)
                    + ". Keep the change inside an allowed path or raise a blocking question; "
                    "do not broaden the authored scope."
                ),
                severity="high",
                location=section.location,
            )
        )
    return tuple(findings)


def _plan_milestone_ids(context: SemanticDocumentContext) -> set[str]:
    milestones = context.section_by_candidates(candidates=("Milestones",))
    if not milestones.content:
        return set()
    return extract_milestone_ids(milestones.content)


def validate_plan(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    findings.extend(_scope_findings(context))
    plan_milestone_ids = _plan_milestone_ids(context)

    for section in context.iter_required_sections():
        normalized_section = normalized_heading(section.name)
        compact_content = re.sub(r"\s+", " ", section.content).strip()
        bullet_items = extract_bullet_items(section.content)

        if normalized_section == "milestones":
            if not bullet_items:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Milestones` must use bullet items "
                            "with stable milestone ids (for example `M1`)."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif not plan_milestone_ids:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Milestones` must declare stable milestone ids "
                            "(for example `M1`, `M2`) for sequencing and "
                            "verification mapping."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

        if normalized_section == "dependencies":
            if not bullet_items:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Dependencies` must use bullet items "
                            "so ordering constraints are explicit."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif compact_content.lower() in {"none", "- none"}:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Dependencies` cannot be `none`; list explicit "
                            "upstream or sequencing constraints."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

        if normalized_section == "risks":
            risk_blocks = extract_risk_blocks(section.content)
            if not risk_blocks:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Risks` must use bullet items with "
                            "concrete mitigation direction."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif compact_content.lower() in {"none", "- none"}:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Risks` cannot be `none`; include concrete delivery "
                            "risks with mitigation intent."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif any(RISK_MITIGATION_PATTERN.search(item) is None for item in risk_blocks):
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Each `Risks` item must include mitigation direction "
                            "(for example `mitigation:`)."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

        if normalized_section == "verification notes":
            if not bullet_items:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Verification notes` must use bullet "
                            "items mapped to milestone ids."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif compact_content.lower() in {"none", "- none"}:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Verification notes` cannot be `none`; map checks "
                            "to milestone ids (for example `M1`)."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            else:
                referenced_milestone_ids = extract_milestone_ids(section.content)
                if not referenced_milestone_ids:
                    findings.append(
                        context.finding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Section `Verification notes` must reference milestone ids "
                                "(for example `M1`) to keep checks tied to "
                                "planned increments."
                            ),
                            severity="medium",
                            location=section.location,
                        )
                    )
                else:
                    unknown_milestone_ids = sorted(
                        referenced_milestone_ids - plan_milestone_ids
                    )
                    if unknown_milestone_ids:
                        unknown_ids_text = ", ".join(unknown_milestone_ids)
                        findings.append(
                            context.finding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Verification notes` references "
                                    f"unknown milestone ids: {unknown_ids_text}."
                                ),
                                severity="medium",
                                location=section.location,
                            )
                        )

    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="plan",
        document_name="plan.md",
        validate=validate_plan,
    ),
)
