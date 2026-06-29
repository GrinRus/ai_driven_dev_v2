from __future__ import annotations

import re
from pathlib import Path

from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    IMPLEMENT_FILE_ENTRY_PATTERN,
    INCOMPLETE_SECTION_CODE,
    REVIEW_ACCEPTANCE_CRITERIA_PATTERN,
    REVIEW_FINDING_ID_PATTERN,
    REVIEW_SPEC_RATIONALE_PATTERN,
    UNSUPPORTED_CLAIM_CODE,
    UNVERIFIABLE_CHECK_CLAIM_CODE,
    SemanticDocumentContext,
    SemanticRule,
    SemanticSection,
    extract_bullet_items,
    extract_review_disposition,
    extract_review_finding_blocks,
    extract_review_spec_decision,
    has_explicit_severity,
    is_live_setup_workspace_context,
    validate_placeholder_sections,
    work_item_root_from_output_path,
)

NO_REVIEW_FINDINGS_PATTERN = re.compile(
    r"\b(?:"
    r"no\s+(?:material\s+)?(?:review\s+)?(?:findings?|issues?|defects?)"
    r"(?:\s+(?:were\s+)?(?:identified|found|observed))?|"
    r"findings?\s*:\s*none"
    r")\b",
    flags=re.IGNORECASE,
)
WORKSPACE_HYGIENE_CLEAN_CLAIM_PATTERN = re.compile(
    r"\b(?:"
    r"cleanup\s+(?:passed|complete|clean)|"
    r"workspace\s+(?:is\s+)?clean|"
    r"workspace\s+hygiene\s+(?:is\s+)?(?:clean|passed)|"
    r"no\s+(?:new\s+)?(?:ignored\s+)?(?:workspace\s+)?residue|"
    r"(?:ignored\s+)?residue\s+(?:absent|clean|none)|"
    r"no\s+(?:new\s+)?(?:coverage/|\.coverage|__pycache__|build|dist)"
    r")\b",
    flags=re.IGNORECASE,
)
RESIDUE_FINDING_PATTERN = re.compile(
    r"\b(?:"
    r"workspace\s+pollution|workspace\s+hygiene|ignored\s+residue|"
    r"coverage/|\.coverage|\.pytest_cache|\.ruff_cache|\.pdm-build|"
    r"__pycache__|build/|dist/|dependency-cache"
    r")\b",
    flags=re.IGNORECASE,
)
BASELINE_PATH_PATTERN = re.compile(r"`([^`]+)`")
LIVE_BASELINE_HEADING_PATTERN = re.compile(
    r"^##\s+Live setup workspace baseline\s*$",
    flags=re.IGNORECASE | re.MULTILINE,
)
NEXT_TOP_LEVEL_HEADING_PATTERN = re.compile(r"^##\s+", flags=re.MULTILINE)
LIVE_RESIDUE_TOP_LEVEL_DIRS = (
    "coverage",
    ".pytest_cache",
    ".ruff_cache",
    ".pdm-build",
    "__pycache__",
    "build",
    "dist",
)
LIVE_RESIDUE_TOP_LEVEL_FILE_PREFIXES = (".coverage",)
MAX_RESIDUE_PATHS = 12


def _review_sections(
    context: SemanticDocumentContext,
) -> tuple[SemanticSection, SemanticSection, SemanticSection]:
    findings_section = context.section_by_candidates(candidates=("Findings",))
    approval = context.section_by_candidates(candidates=("Approval status", "Verdict"))
    required_changes = context.section_by_candidates(
        candidates=("Required changes", "Required follow-up"),
    )
    return findings_section, approval, required_changes


def _validate_finding_entry(
    *,
    context: SemanticDocumentContext,
    findings_section: SemanticSection,
    finding_item: str,
) -> tuple[int, tuple[ValidationFinding, ...]]:
    findings: list[ValidationFinding] = []
    if REVIEW_FINDING_ID_PATTERN.search(finding_item) is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each finding must include a stable id "
                    "(for example `RV-1` or `REV-001`)."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    if not has_explicit_severity(finding_item):
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each finding must include explicit severity "
                    "(critical/high/medium/low/info/none)."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    review_disposition = extract_review_disposition(finding_item)
    if review_disposition is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each finding must include explicit disposition "
                    "(`must-fix`, `follow-up`, `accepted-risk`, or `invalid`)."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    if REVIEW_SPEC_RATIONALE_PATTERN.search(finding_item) is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each finding must include rationale "
                    "(for example `Rationale:` or `because ...`)."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    has_implementation_evidence = IMPLEMENT_FILE_ENTRY_PATTERN.search(finding_item) is not None
    has_acceptance_reference = (
        REVIEW_ACCEPTANCE_CRITERIA_PATTERN.search(finding_item) is not None
    )
    if not has_implementation_evidence and not has_acceptance_reference:
        findings.append(
            context.finding(
                code=UNSUPPORTED_CLAIM_CODE,
                message=(
                    "Finding is missing evidence reference to implementation output "
                    "or acceptance criteria."
                ),
                severity="high",
                location=findings_section.location,
            )
        )

    unresolved_must_fix_count = 1 if review_disposition == "must-fix" else 0
    return unresolved_must_fix_count, tuple(findings)


def _declares_no_review_findings(text: str) -> bool:
    normalized = text.strip().strip("`").strip().rstrip(".").strip()
    normalized = re.sub(r"^[-*]\s+", "", normalized).strip()
    if not normalized:
        return False
    if normalized.lower() == "none":
        return True
    return NO_REVIEW_FINDINGS_PATTERN.search(normalized) is not None


def _contains_no_review_findings_declaration(text: str) -> bool:
    return any(_declares_no_review_findings(line) for line in text.splitlines())


def _normalize_repo_relative_path(raw_path: str) -> str | None:
    candidate = raw_path.strip().strip("`").strip()
    if not candidate:
        return None
    if candidate.startswith(("git ", "flow-state.json field ")):
        return None
    candidate = candidate.removeprefix("./").strip()
    if not candidate:
        return None
    if Path(candidate).is_absolute():
        return None
    return candidate.rstrip("/")


def _live_baseline_section(repository_state_text: str) -> str:
    match = LIVE_BASELINE_HEADING_PATTERN.search(repository_state_text)
    if match is None:
        return ""
    next_match = NEXT_TOP_LEVEL_HEADING_PATTERN.search(
        repository_state_text,
        match.end(),
    )
    if next_match is None:
        return repository_state_text[match.end() :]
    return repository_state_text[match.end() : next_match.start()]


def _live_setup_baseline_paths(context: SemanticDocumentContext) -> tuple[str, ...]:
    work_item_root = work_item_root_from_output_path(context.output_path)
    if work_item_root is None:
        return tuple()

    repository_state_path = work_item_root / "context" / "repository-state.md"
    if not repository_state_path.exists():
        return tuple()

    repository_state_text = repository_state_path.read_text(
        encoding="utf-8",
        errors="replace",
    )
    baseline_section = _live_baseline_section(repository_state_text)
    paths: list[str] = []
    seen: set[str] = set()
    for match in BASELINE_PATH_PATTERN.finditer(baseline_section):
        normalized = _normalize_repo_relative_path(match.group(1))
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        paths.append(normalized)
    return tuple(paths)


def _is_baseline_path(path: str, baseline_paths: tuple[str, ...]) -> bool:
    normalized = path.rstrip("/")
    for baseline_path in baseline_paths:
        if normalized == baseline_path:
            return True
        if normalized.startswith(f"{baseline_path}/"):
            return True
        if baseline_path.startswith(f"{normalized}/"):
            return True
    return False


def _repo_relative(path: Path, project_root: Path) -> str:
    return path.resolve(strict=False).relative_to(
        project_root.resolve(strict=False)
    ).as_posix()


def _bounded_existing_path_samples(path: Path, project_root: Path) -> tuple[str, ...]:
    paths: list[str] = []
    queue = [path]
    while queue and len(paths) < MAX_RESIDUE_PATHS:
        candidate = queue.pop(0)
        try:
            paths.append(_repo_relative(candidate, project_root))
        except ValueError:
            continue
        if not candidate.is_dir():
            continue
        try:
            children = sorted(candidate.iterdir(), key=lambda item: item.name)
        except OSError:
            continue
        queue.extend(children[: max(0, MAX_RESIDUE_PATHS - len(paths))])
    return tuple(paths)


def _active_live_residue_paths(context: SemanticDocumentContext) -> tuple[str, ...]:
    if not is_live_setup_workspace_context(context):
        return tuple()
    if context.workspace_root.name != ".aidd":
        return tuple()

    project_root = context.workspace_root.parent
    baseline_paths = _live_setup_baseline_paths(context)
    candidate_paths: list[str] = []

    for directory_name in LIVE_RESIDUE_TOP_LEVEL_DIRS:
        residue_path = project_root / directory_name
        if not residue_path.exists():
            continue
        candidate_paths.extend(_bounded_existing_path_samples(residue_path, project_root))

    try:
        top_level_children = tuple(project_root.iterdir())
    except OSError:
        top_level_children = tuple()
    for child in sorted(top_level_children, key=lambda item: item.name):
        if not child.is_file():
            continue
        if not any(
            child.name.startswith(prefix)
            for prefix in LIVE_RESIDUE_TOP_LEVEL_FILE_PREFIXES
        ):
            continue
        candidate_paths.append(_repo_relative(child, project_root))

    active_paths: list[str] = []
    seen: set[str] = set()
    for candidate_path in candidate_paths:
        normalized = candidate_path.rstrip("/")
        if _is_baseline_path(normalized, baseline_paths):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        active_paths.append(normalized)
        if len(active_paths) >= MAX_RESIDUE_PATHS:
            break
    return tuple(active_paths)


def _contains_workspace_hygiene_clean_claim(text: str) -> bool:
    return WORKSPACE_HYGIENE_CLEAN_CLAIM_PATTERN.search(text) is not None


def _has_active_residue_finding(findings_section: SemanticSection) -> bool:
    for finding_block in extract_review_finding_blocks(findings_section.content):
        if REVIEW_FINDING_ID_PATTERN.search(finding_block) is None:
            continue
        if RESIDUE_FINDING_PATTERN.search(finding_block) is not None:
            return True
    return False


def _validate_live_workspace_hygiene_truthfulness(
    *,
    context: SemanticDocumentContext,
    findings_section: SemanticSection,
    approval_status: str | None,
) -> tuple[ValidationFinding, ...]:
    active_residue_paths = _active_live_residue_paths(context)
    if not active_residue_paths:
        return tuple()
    if _has_active_residue_finding(findings_section):
        return tuple()

    document_text = "\n".join(context.markdown_lines)
    has_clean_review_claim = (
        approval_status == "approved"
        or _contains_no_review_findings_declaration(findings_section.content)
        or _contains_workspace_hygiene_clean_claim(document_text)
    )
    if not has_clean_review_claim:
        return tuple()

    residue_summary = ", ".join(active_residue_paths[:5])
    if len(active_residue_paths) > 5:
        residue_summary += ", ..."
    return (
        context.finding(
            code=UNVERIFIABLE_CHECK_CLAIM_CODE,
            message=(
                "Live review cannot declare approved/no findings or cleanup passed while "
                f"non-baseline ignored workspace residue exists after review: {residue_summary}. "
                "Check ignored residue after all review commands, remove it with evidence, "
                "or record an active review finding."
            ),
            severity="high",
            location=findings_section.location,
        ),
    )


def _validate_findings_section(
    *,
    context: SemanticDocumentContext,
    findings_section: SemanticSection,
) -> tuple[int, tuple[ValidationFinding, ...]]:
    finding_items = extract_review_finding_blocks(findings_section.content)
    if _contains_no_review_findings_declaration(
        findings_section.content
    ) and REVIEW_FINDING_ID_PATTERN.search(findings_section.content) is None:
        return 0, tuple()
    if _declares_no_review_findings(findings_section.content) and (
        not finding_items
        or all(_declares_no_review_findings(finding_item) for finding_item in finding_items)
    ):
        return 0, tuple()

    if not finding_items:
        return 0, (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Findings` must include finding entries with stable ids, "
                    "severity, disposition, and rationale."
                ),
                severity="medium",
                location=findings_section.location,
            ),
        )

    findings: list[ValidationFinding] = []
    unresolved_must_fix_count = 0
    for finding_item in finding_items:
        must_fix_count, item_findings = _validate_finding_entry(
            context=context,
            findings_section=findings_section,
            finding_item=finding_item,
        )
        unresolved_must_fix_count += must_fix_count
        findings.extend(item_findings)
    return unresolved_must_fix_count, tuple(findings)


def _validate_approval_status(
    *,
    context: SemanticDocumentContext,
    approval: SemanticSection,
    unresolved_must_fix_count: int,
) -> tuple[str | None, tuple[ValidationFinding, ...]]:
    approval_status = extract_review_spec_decision(approval.content)
    if approval_status is None:
        return None, (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Approval status` must declare one explicit state: "
                    "`approved`, `approved-with-conditions`, or `rejected`."
                ),
                severity="medium",
                location=approval.location,
            ),
        )
    if approval_status == "approved" and unresolved_must_fix_count > 0:
        return approval_status, (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Approval status cannot be `approved` while unresolved "
                    "`must-fix` findings remain."
                ),
                severity="high",
                location=approval.location,
            ),
        )
    return approval_status, tuple()


def _validate_required_changes(
    *,
    context: SemanticDocumentContext,
    required_changes: SemanticSection,
    approval_status: str | None,
) -> tuple[ValidationFinding, ...]:
    required_changes_items = extract_bullet_items(required_changes.content)
    has_required_change_entries = any(item.lower() != "none" for item in required_changes_items)
    if (
        approval_status in {"approved-with-conditions", "rejected"}
        and not has_required_change_entries
    ):
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message="Non-approved outcomes must include concrete required-change entries.",
                severity="medium",
                location=required_changes.location,
            ),
        )
    return tuple()


def validate_review_report(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings_section, approval, required_changes = _review_sections(context)
    unresolved_must_fix_count, finding_findings = _validate_findings_section(
        context=context,
        findings_section=findings_section,
    )
    approval_status, approval_findings = _validate_approval_status(
        context=context,
        approval=approval,
        unresolved_must_fix_count=unresolved_must_fix_count,
    )

    findings: list[ValidationFinding] = []
    findings.extend(finding_findings)
    findings.extend(approval_findings)
    findings.extend(
        _validate_required_changes(
            context=context,
            required_changes=required_changes,
            approval_status=approval_status,
        )
    )
    findings.extend(
        _validate_live_workspace_hygiene_truthfulness(
            context=context,
            findings_section=findings_section,
            approval_status=approval_status,
        )
    )
    findings.extend(validate_placeholder_sections(context))
    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="review",
        document_name="review-report.md",
        validate=validate_review_report,
    ),
)
