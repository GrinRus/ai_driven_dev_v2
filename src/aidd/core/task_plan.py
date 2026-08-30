from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum

from aidd.core.identifiers import SafeIdentifier

_TASK_ID_TEXT = r"(?:[A-Z][A-Z0-9]{0,15}-\d+|T\d+)"
_TASK_HEADING_PATTERN = re.compile(r"^###\s+(\S+)(?:\s+(.+?))\s*$")
_FIELD_LINE_PATTERN = re.compile(
    r"^\s*[-*]\s+([^:]+?)\s*:\s*(.*?)\s*$",
)
_DEPENDENCY_ENTRY_PATTERN = re.compile(
    r"^\s*[-*]\s+([^:\s]+)\s*:\s*(.*?)\s*$"
)
_VERIFICATION_ENTRY_PATTERN = _DEPENDENCY_ENTRY_PATTERN
_TASK_ID_PATTERN = re.compile(rf"\b({_TASK_ID_TEXT})\b")
_TASK_ID_FULL_PATTERN = re.compile(rf"^{_TASK_ID_TEXT}$")
_NONE_DEPENDENCY_PATTERN = re.compile(r"^\s*none(?:\s|[.,;:—–-]|$)", re.IGNORECASE)
_IMPLICIT_VERIFICATION_ONLY_PATTERN = re.compile(
    r"\bverification[- ]only\s+(?:task|output|deliverable|check|step)\b|"
    r"\b(?:no|without)\s+(?:any\s+)?(?:task[- ]local\s+)?repository\s+"
    r"(?:edit|edits|change|changes|diff|differences)\b",
    re.IGNORECASE,
)
_FIELD_LABELS = frozenset(
    {
        "outcome",
        "dominant deliverable",
        "in scope",
        "context",
        "implementation constraints",
        "out of scope",
        "execution mode",
        "acceptance criteria",
    }
)


def _strip_markdown_wrappers(value: str) -> str:
    """Normalize presentation wrappers around a syntactic label or identifier.

    This helper is intentionally limited to tokens whose executable meaning is
    validated separately. It must not be applied to field values, paths, or
    task titles, where emphasis may be meaningful content rather than syntax.
    """

    normalized = value.strip()
    wrappers = ("**", "__", "`", "*", "_")
    changed = True
    while changed and normalized:
        changed = False
        for wrapper in wrappers:
            if (
                len(normalized) >= len(wrapper) * 2
                and normalized.startswith(wrapper)
                and normalized.endswith(wrapper)
            ):
                normalized = normalized[len(wrapper) : -len(wrapper)].strip()
                changed = True
                break
    return normalized


def _normalized_task_id(value: str) -> str | None:
    normalized = _strip_markdown_wrappers(value)
    if _TASK_ID_FULL_PATTERN.fullmatch(normalized) is None:
        return None
    return normalized.upper()


def _parse_task_heading(line: str) -> tuple[str, str] | None:
    match = _TASK_HEADING_PATTERN.match(line.strip())
    if match is None:
        return None
    raw_id = match.group(1)
    task_id = _normalized_task_id(raw_id)
    if task_id is None and raw_id[-1:] in "-—–:":
        task_id = _normalized_task_id(raw_id[:-1])
    if task_id is None:
        return None
    title = match.group(2).strip()
    title = re.sub(r"^[-—–:]\s*", "", title).strip()
    if not title:
        return None
    return task_id, title


class TaskPlanIssueKind(StrEnum):
    INVALID_HEADING = "invalid-heading"
    MISSING_TASK_CARDS = "missing-task-cards"
    DUPLICATE_TASK_ID = "duplicate-task-id"
    MIXED_TASK_ID_STYLE = "mixed-task-id-style"
    DUPLICATE_MAPPED_ENTRY = "duplicate-mapped-entry"
    MISSING_MAPPED_ENTRY = "missing-mapped-entry"
    UNKNOWN_MAPPED_TASK_ID = "unknown-mapped-task-id"
    EMPTY_DEPENDENCY = "empty-dependency"
    UNKNOWN_DEPENDENCY = "unknown-dependency"
    SELF_DEPENDENCY = "self-dependency"
    FORWARD_DEPENDENCY = "forward-dependency"
    DEPENDENCY_CYCLE = "dependency-cycle"
    DUPLICATE_FIELD = "duplicate-field"
    MISSING_FIELD = "missing-field"
    MISSING_ACCEPTANCE = "missing-acceptance"
    MALFORMED_ACCEPTANCE_ID = "malformed-acceptance-id"
    DUPLICATE_ACCEPTANCE_ID = "duplicate-acceptance-id"
    UNSAFE_SCOPE_PATH = "unsafe-scope-path"
    MISSING_SCOPE_PATH = "missing-scope-path"
    MISSING_VERIFICATION = "missing-verification"
    INVALID_EXECUTION_MODE = "invalid-execution-mode"
    DUPLICATE_GLOBAL_ACCEPTANCE_ID = "duplicate-global-acceptance-id"


class TaskPlanIssueRelation(StrEnum):
    ROOT = "root"
    RELATED = "related"


@dataclass(frozen=True, slots=True)
class TaskPlanParseIssue:
    kind: TaskPlanIssueKind | str
    message: str
    task_id: str | None = None
    line_number: int | None = None
    field: str | None = None
    missing_fields: tuple[str, ...] = ()
    relation: TaskPlanIssueRelation = TaskPlanIssueRelation.ROOT

    @property
    def source_line_number(self) -> int | None:
        """Alias used by evidence consumers that call the location a source line."""

        return self.line_number

    def __str__(self) -> str:
        return self.message


def _issue(
    kind: TaskPlanIssueKind | str,
    message: str,
    *,
    task_id: str | None = None,
    line_number: int | None = None,
    field: str | None = None,
    missing_fields: tuple[str, ...] = (),
    relation: TaskPlanIssueRelation = TaskPlanIssueRelation.ROOT,
) -> TaskPlanParseIssue:
    return TaskPlanParseIssue(
        kind=kind,
        message=message,
        task_id=task_id,
        line_number=line_number,
        field=field,
        missing_fields=missing_fields,
        relation=relation,
    )


class TaskPlanParseError(ValueError):
    def __init__(self, issues: tuple[TaskPlanParseIssue | str, ...]) -> None:
        self.issues = tuple(
            issue
            if isinstance(issue, TaskPlanParseIssue)
            else _issue("legacy", issue)
            for issue in issues
        )
        self.messages = tuple(issue.message for issue in self.issues)
        super().__init__("Invalid tasklist: " + "; ".join(self.messages))


class TaskExecutionMode(StrEnum):
    REPOSITORY_CHANGE = "repository-change"
    VERIFICATION_ONLY = "verification-only"


@dataclass(frozen=True, slots=True)
class TaskAcceptanceCriterion:
    id: str
    text: str


@dataclass(frozen=True, slots=True)
class TaskCard:
    id: str
    title: str
    outcome: str
    dominant_deliverable: str
    in_scope: str
    scope_paths: tuple[str, ...]
    acceptance_criteria: tuple[TaskAcceptanceCriterion, ...]
    dependencies: tuple[str, ...]
    verification: str
    execution_mode: TaskExecutionMode = TaskExecutionMode.REPOSITORY_CHANGE
    context: str | None = None
    implementation_constraints: str | None = None
    out_of_scope: str | None = None


@dataclass(frozen=True, slots=True)
class TaskPlan:
    source_sha256: str
    tasks: tuple[TaskCard, ...]

    def by_id(self) -> dict[str, TaskCard]:
        return {task.id: task for task in self.tasks}

    def ordered_ids(self) -> tuple[str, ...]:
        return tuple(task.id for task in self.tasks)

    def ready_task_ids(self, succeeded: set[str]) -> tuple[str, ...]:
        return tuple(
            task.id
            for task in self.tasks
            if task.id not in succeeded
            and all(dependency in succeeded for dependency in task.dependencies)
        )


def _section_lines_with_numbers(markdown: str, heading: str) -> list[tuple[int, str]]:
    target = heading.casefold()
    lines = markdown.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        match = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if match and match.group(1).strip().casefold() == target:
            start = index + 1
            break
    if start is None:
        return []
    end = len(lines)
    for index in range(start, len(lines)):
        if re.match(r"^##\s+", lines[index].strip()):
            end = index
            break
    return [(index + 1, lines[index]) for index in range(start, end)]


def _section_lines(markdown: str, heading: str) -> list[str]:
    return [line for _, line in _section_lines_with_numbers(markdown, heading)]


def _section_heading_line(markdown: str, heading: str) -> int | None:
    target = heading.casefold()
    for index, line in enumerate(markdown.splitlines()):
        match = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if match and match.group(1).strip().casefold() == target:
            return index + 1
    return None


@dataclass(frozen=True, slots=True)
class _TaskBlock:
    task_id: str
    title: str
    lines: tuple[tuple[int, str], ...]
    heading_line: int


def _parse_task_blocks(
    markdown: str,
) -> tuple[list[_TaskBlock], list[TaskPlanParseIssue]]:
    lines = _section_lines_with_numbers(markdown, "Ordered tasks")
    issues: list[TaskPlanParseIssue] = []
    blocks: list[_TaskBlock] = []
    current_id: str | None = None
    current_title = ""
    current_heading_line = _section_heading_line(markdown, "Ordered tasks") or 1
    current_lines: list[tuple[int, str]] = []
    malformed_heading_lines: list[int] = []
    for line_number, line in lines:
        heading = _parse_task_heading(line)
        if heading is not None:
            if current_id is not None:
                blocks.append(
                    _TaskBlock(
                        task_id=current_id,
                        title=current_title,
                        lines=tuple(current_lines),
                        heading_line=current_heading_line,
                    )
                )
            current_id, current_title = heading
            current_heading_line = line_number
            current_lines = []
            continue
        if line.lstrip().startswith("###"):
            malformed_heading_lines.append(line_number)
        if current_id is not None:
            current_lines.append((line_number, line))
    if current_id is not None:
        blocks.append(
            _TaskBlock(
                task_id=current_id,
                title=current_title,
                lines=tuple(current_lines),
                heading_line=current_heading_line,
            )
        )
    for line_number in malformed_heading_lines:
        issues.append(
            _issue(
                TaskPlanIssueKind.INVALID_HEADING,
                "`Ordered tasks` contains a malformed H3 task heading with a missing or "
                "ambiguous stable task id.",
                line_number=line_number,
            )
        )
    if not blocks:
        issues.append(
            _issue(
                TaskPlanIssueKind.MISSING_TASK_CARDS,
                "`Ordered tasks` must contain H3 task cards with stable task ids.",
                line_number=_section_heading_line(markdown, "Ordered tasks"),
                relation=(
                    TaskPlanIssueRelation.RELATED
                    if malformed_heading_lines
                    else TaskPlanIssueRelation.ROOT
                ),
            )
        )
    ids = [block.task_id for block in blocks]
    duplicate_ids = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
    if duplicate_ids:
        duplicate_id = duplicate_ids[0]
        duplicate_line = next(
            block.heading_line for block in blocks if block.task_id == duplicate_id
        )
        issues.append(
            _issue(
                TaskPlanIssueKind.DUPLICATE_TASK_ID,
                "Duplicate task ids: " + ", ".join(duplicate_ids) + ".",
                task_id=duplicate_id,
                line_number=duplicate_line,
            )
        )
    styles = {"compact" if re.fullmatch(r"T\d+", task_id) else "prefixed" for task_id in ids}
    if len(styles) > 1:
        issues.append(
            _issue(
                TaskPlanIssueKind.MIXED_TASK_ID_STYLE,
                "Task cards must not mix compact and prefixed task id styles.",
                line_number=blocks[0].heading_line if blocks else None,
            )
        )
    return blocks, issues


def _parse_mapped_section(
    markdown: str,
    heading: str,
    pattern: re.Pattern[str],
) -> tuple[dict[str, tuple[str, int]], list[TaskPlanParseIssue]]:
    entries: dict[str, tuple[str, int]] = {}
    issues: list[TaskPlanParseIssue] = []
    for line_number, line in _section_lines_with_numbers(markdown, heading):
        if not line.strip():
            continue
        match = pattern.match(line)
        if match is None:
            continue
        task_id = _normalized_task_id(match.group(1))
        if task_id is None:
            continue
        if task_id in entries:
            issues.append(
                _issue(
                    TaskPlanIssueKind.DUPLICATE_MAPPED_ENTRY,
                    f"Section `{heading}` contains duplicate entry `{task_id}`.",
                    task_id=task_id,
                    line_number=line_number,
                )
            )
        entries[task_id] = (match.group(2).strip(), line_number)
    return entries, issues


def _parse_card_fields(
    task_id: str,
    lines: tuple[tuple[int, str], ...],
    heading_line: int,
) -> tuple[
    dict[str, str],
    dict[str, int],
    tuple[TaskAcceptanceCriterion, ...],
    tuple[int, ...],
    list[TaskPlanParseIssue],
]:
    fields: dict[str, str] = {}
    field_lines: dict[str, int] = {}
    acceptance: list[TaskAcceptanceCriterion] = []
    acceptance_lines: list[int] = []
    issues: list[TaskPlanParseIssue] = []
    in_acceptance = False
    for line_number, line in lines:
        if in_acceptance:
            criterion_match = re.match(
                r"^\s{2,}[-*]\s+([^:\s]+)\s*:\s*(.+?)\s*$",
                line,
            )
            if criterion_match is not None:
                criterion_id = _strip_markdown_wrappers(criterion_match.group(1)).upper()
                acceptance_lines.append(line_number)
                acceptance.append(
                    TaskAcceptanceCriterion(
                        id=criterion_id,
                        text=criterion_match.group(2).strip(),
                    )
                )
                continue
        field_match = _FIELD_LINE_PATTERN.match(line)
        if field_match is not None:
            label = _strip_markdown_wrappers(field_match.group(1))
            key = label.casefold()
            if key not in _FIELD_LABELS:
                if line.strip() and not line.lstrip().startswith(("-", "*")):
                    in_acceptance = False
                continue
            if key in fields:
                issues.append(
                    _issue(
                        TaskPlanIssueKind.DUPLICATE_FIELD,
                        f"Task `{task_id}` repeats field `{label}`.",
                        task_id=task_id,
                        line_number=line_number,
                        field=key,
                    )
                )
            fields[key] = field_match.group(2).strip()
            field_lines[key] = line_number
            in_acceptance = key == "acceptance criteria"
            continue
        if line.strip() and not line.lstrip().startswith(("-", "*")):
            in_acceptance = False

    for label in ("outcome", "dominant deliverable", "in scope"):
        if not fields.get(label, "").strip():
            issues.append(
                _issue(
                    TaskPlanIssueKind.MISSING_FIELD,
                    f"Task `{task_id}` is missing required field `{label}`.",
                    task_id=task_id,
                    line_number=heading_line,
                    field=label,
                    missing_fields=(label,),
                )
            )
    if "execution mode" not in fields:
        implicit_verification_line = next(
            (
                line_number
                for line_number, line in lines
                if _IMPLICIT_VERIFICATION_ONLY_PATTERN.search(line)
            ),
            None,
        )
        if implicit_verification_line is not None:
            issues.append(
                _issue(
                    TaskPlanIssueKind.MISSING_FIELD,
                    f"Task `{task_id}` describes verification-only work but is missing "
                    "required field `execution mode`; declare `Execution mode: "
                    "verification-only` explicitly.",
                    task_id=task_id,
                    line_number=implicit_verification_line,
                    field="execution mode",
                    missing_fields=("execution mode",),
                )
            )
    expected_acceptance_pattern = re.compile(rf"^{re.escape(task_id)}-AC[1-9]\d*$")
    if not acceptance:
        issues.append(
            _issue(
                TaskPlanIssueKind.MISSING_ACCEPTANCE,
                f"Task `{task_id}` must declare at least one acceptance criterion.",
                task_id=task_id,
                line_number=field_lines.get("acceptance criteria", heading_line),
                field="acceptance criteria",
            )
        )
    acceptance_ids = [criterion.id for criterion in acceptance]
    for acceptance_id, line_number in zip(acceptance_ids, acceptance_lines, strict=True):
        if expected_acceptance_pattern.fullmatch(acceptance_id) is None:
            issues.append(
                _issue(
                    TaskPlanIssueKind.MALFORMED_ACCEPTANCE_ID,
                    f"Task `{task_id}` has malformed acceptance id `{acceptance_id}`.",
                    task_id=task_id,
                    line_number=line_number,
                    field="acceptance criteria",
                )
            )
    duplicates = sorted({item for item in acceptance_ids if acceptance_ids.count(item) > 1})
    if duplicates:
        duplicate_id = duplicates[0]
        duplicate_line = next(
            line_number
            for criterion, line_number in zip(acceptance_ids, acceptance_lines, strict=True)
            if criterion == duplicate_id
        )
        issues.append(
            _issue(
                TaskPlanIssueKind.DUPLICATE_ACCEPTANCE_ID,
                f"Task `{task_id}` has duplicate acceptance ids: {', '.join(duplicates)}.",
                task_id=task_id,
                line_number=duplicate_line,
                field="acceptance criteria",
            )
        )
    return fields, field_lines, tuple(acceptance), tuple(acceptance_lines), issues


def _parse_scope_paths(
    task_id: str,
    value: str,
    *,
    line_number: int,
) -> tuple[tuple[str, ...], list[TaskPlanParseIssue]]:
    paths: list[str] = []
    issues: list[TaskPlanParseIssue] = []
    for raw_value in re.findall(r"`([^`]+)`", value):
        candidate = raw_value.strip().strip("/")
        invalid = (
            not candidate
            or candidate in {".", ".."}
            or raw_value.startswith(("/", "\\"))
            or re.match(r"^[A-Za-z]:[\\/]", raw_value) is not None
            or "\\" in raw_value
            or ".." in candidate.split("/")
            or any(marker in candidate for marker in ("*", "?", "[", "]"))
            or re.fullmatch(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*", candidate)
            is None
        )
        if invalid:
            issues.append(
                _issue(
                    TaskPlanIssueKind.UNSAFE_SCOPE_PATH,
                    f"Task `{task_id}` has unsafe in-scope path `{raw_value}`.",
                    task_id=task_id,
                    line_number=line_number,
                    field="in scope",
                )
            )
            continue
        paths.append(candidate)
    if not paths:
        issues.append(
            _issue(
                TaskPlanIssueKind.MISSING_SCOPE_PATH,
                f"Task `{task_id}` field `in scope` must contain at least one backticked "
                "repository-relative file or directory path.",
                task_id=task_id,
                line_number=line_number,
                field="in scope",
                relation=(
                    TaskPlanIssueRelation.RELATED
                    if issues
                    else TaskPlanIssueRelation.ROOT
                ),
            )
        )
    return tuple(dict.fromkeys(paths)), issues


def _validate_dependency_graph(
    task_ids: tuple[str, ...],
    dependencies: dict[str, tuple[str, ...]],
    dependency_lines: dict[str, int],
) -> list[TaskPlanParseIssue]:
    issues: list[TaskPlanParseIssue] = []
    known = set(task_ids)
    positions = {task_id: index for index, task_id in enumerate(task_ids)}
    for task_id, task_dependencies in dependencies.items():
        unknown = sorted(set(task_dependencies) - known)
        if unknown:
            issues.append(
                _issue(
                    TaskPlanIssueKind.UNKNOWN_DEPENDENCY,
                    f"Task `{task_id}` references unknown dependencies: {', '.join(unknown)}.",
                    task_id=task_id,
                    line_number=dependency_lines.get(task_id),
                    field="dependencies",
                )
            )
        if task_id in task_dependencies:
            issues.append(
                _issue(
                    TaskPlanIssueKind.SELF_DEPENDENCY,
                    f"Task `{task_id}` cannot depend on itself.",
                    task_id=task_id,
                    line_number=dependency_lines.get(task_id),
                    field="dependencies",
                )
            )
        forward = tuple(
            dependency
            for dependency in task_dependencies
            if dependency in positions and positions[dependency] >= positions[task_id]
        )
        if forward:
            issues.append(
                _issue(
                    TaskPlanIssueKind.FORWARD_DEPENDENCY,
                    f"Task `{task_id}` references dependencies that do not appear earlier in "
                    f"`Ordered tasks`: {', '.join(forward)}.",
                    task_id=task_id,
                    line_number=dependency_lines.get(task_id),
                    field="dependencies",
                )
            )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            issues.append(
                _issue(
                    TaskPlanIssueKind.DEPENDENCY_CYCLE,
                    f"Task dependency graph contains a cycle at `{task_id}`.",
                    task_id=task_id,
                    line_number=dependency_lines.get(task_id),
                    field="dependencies",
                )
            )
            return
        visiting.add(task_id)
        for dependency in dependencies.get(task_id, ()):
            if dependency in known:
                visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in task_ids:
        visit(task_id)
    return issues


def parse_task_plan(markdown: str) -> TaskPlan:
    blocks, issues = _parse_task_blocks(markdown)
    dependency_entries, dependency_issues = _parse_mapped_section(
        markdown,
        "Dependencies",
        _DEPENDENCY_ENTRY_PATTERN,
    )
    verification_entries, verification_issues = _parse_mapped_section(
        markdown,
        "Verification notes",
        _VERIFICATION_ENTRY_PATTERN,
    )
    issues.extend(dependency_issues)
    issues.extend(verification_issues)
    task_ids = tuple(block.task_id for block in blocks)
    known_ids = set(task_ids)
    for section_name, entries in (
        ("Dependencies", dependency_entries),
        ("Verification notes", verification_entries),
    ):
        missing = sorted(known_ids - set(entries))
        unknown = sorted(set(entries) - known_ids)
        if missing:
            issues.append(
                _issue(
                    TaskPlanIssueKind.MISSING_MAPPED_ENTRY,
                    f"Section `{section_name}` is missing task ids: {', '.join(missing)}.",
                    line_number=_section_heading_line(markdown, section_name),
                    field=section_name.casefold(),
                )
            )
        if unknown:
            unknown_id = unknown[0]
            unknown_line = entries[unknown_id][1]
            issues.append(
                _issue(
                    TaskPlanIssueKind.UNKNOWN_MAPPED_TASK_ID,
                    f"Section `{section_name}` references unknown task ids: {', '.join(unknown)}.",
                    task_id=unknown_id,
                    line_number=unknown_line,
                    field=section_name.casefold(),
                )
            )

    parsed_dependencies: dict[str, tuple[str, ...]] = {}
    dependency_lines: dict[str, int] = {}
    for task_id in task_ids:
        dependency_entry = dependency_entries.get(task_id)
        if dependency_entry is None:
            parsed_dependencies[task_id] = ()
            continue
        dependency_text, dependency_line = dependency_entry
        dependency_lines[task_id] = dependency_line
        # Dependency entries may carry a short human-readable rationale after the
        # machine-readable value (for example, ``T1: none — establishes M1``).
        # Only the leading dependency value defines the graph; milestone/review
        # ids in the rationale must not turn a valid ``none`` into a dependency.
        dependency_clause = re.split(
            r"\s+[—–]\s+", dependency_text, maxsplit=1
        )[0].strip()
        if _NONE_DEPENDENCY_PATTERN.match(dependency_clause.strip("` .")):
            parsed_dependencies[task_id] = ()
        else:
            parsed_dependencies[task_id] = tuple(
                dict.fromkeys(
                    match.group(1).upper()
                    for match in _TASK_ID_PATTERN.finditer(dependency_clause)
                )
            )
            if not parsed_dependencies[task_id]:
                issues.append(
                    _issue(
                        TaskPlanIssueKind.EMPTY_DEPENDENCY,
                        f"Task `{task_id}` dependencies must be `none` or task ids.",
                        task_id=task_id,
                        line_number=dependency_line,
                        field="dependencies",
                    )
                )

    issues.extend(_validate_dependency_graph(task_ids, parsed_dependencies, dependency_lines))
    cards: list[TaskCard] = []
    all_acceptance_ids: list[str] = []
    acceptance_lines_by_id: dict[str, int] = {}
    for block in blocks:
        task_id = block.task_id
        title = block.title
        SafeIdentifier.parse(task_id, label="task id")
        fields, field_lines, acceptance, acceptance_lines, field_issues = _parse_card_fields(
            task_id,
            block.lines,
            block.heading_line,
        )
        issues.extend(field_issues)
        if "in scope" in fields:
            scope_paths, scope_issues = _parse_scope_paths(
                task_id,
                fields["in scope"],
                line_number=field_lines["in scope"],
            )
            issues.extend(scope_issues)
        else:
            scope_paths = ()
        all_acceptance_ids.extend(item.id for item in acceptance)
        for acceptance_id, acceptance_line in zip(acceptance, acceptance_lines, strict=True):
            acceptance_lines_by_id.setdefault(acceptance_id.id, acceptance_line)
        verification_entry = verification_entries.get(task_id)
        verification = verification_entry[0].strip() if verification_entry is not None else ""
        if verification_entry is not None and (
            not verification or verification.casefold().strip("` .") == "none"
        ):
            issues.append(
                _issue(
                    TaskPlanIssueKind.MISSING_VERIFICATION,
                    f"Task `{task_id}` must declare concrete verification.",
                    task_id=task_id,
                    line_number=verification_entry[1],
                    field="verification notes",
                )
            )
        execution_mode_value = fields.get(
            "execution mode",
            TaskExecutionMode.REPOSITORY_CHANGE.value,
        ).casefold()
        try:
            execution_mode = TaskExecutionMode(execution_mode_value)
        except ValueError:
            issues.append(
                _issue(
                    TaskPlanIssueKind.INVALID_EXECUTION_MODE,
                    f"Task `{task_id}` execution mode must be `repository-change` or "
                    "`verification-only`.",
                    task_id=task_id,
                    line_number=field_lines.get("execution mode", block.heading_line),
                    field="execution mode",
                )
            )
            execution_mode = TaskExecutionMode.REPOSITORY_CHANGE
        cards.append(
            TaskCard(
                id=task_id,
                title=title,
                outcome=fields.get("outcome", ""),
                dominant_deliverable=fields.get("dominant deliverable", ""),
                in_scope=fields.get("in scope", ""),
                scope_paths=scope_paths,
                acceptance_criteria=acceptance,
                dependencies=parsed_dependencies.get(task_id, ()),
                verification=verification,
                execution_mode=execution_mode,
                context=fields.get("context") or None,
                implementation_constraints=(fields.get("implementation constraints") or None),
                out_of_scope=fields.get("out of scope") or None,
            )
        )
    duplicate_acceptance = sorted(
        {item for item in all_acceptance_ids if all_acceptance_ids.count(item) > 1}
    )
    if duplicate_acceptance:
        duplicate_id = duplicate_acceptance[0]
        issues.append(
            _issue(
                TaskPlanIssueKind.DUPLICATE_GLOBAL_ACCEPTANCE_ID,
                "Acceptance ids must be globally unique: "
                + ", ".join(duplicate_acceptance)
                + ".",
                task_id=duplicate_id.split("-AC", maxsplit=1)[0],
                line_number=acceptance_lines_by_id.get(duplicate_id),
                field="acceptance criteria",
            )
        )
    if issues:
        raise TaskPlanParseError(tuple(dict.fromkeys(issues)))
    return TaskPlan(
        source_sha256=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        tasks=tuple(cards),
    )


__all__ = [
    "TaskAcceptanceCriterion",
    "TaskCard",
    "TaskExecutionMode",
    "TaskPlanIssueKind",
    "TaskPlanIssueRelation",
    "TaskPlanParseIssue",
    "TaskPlan",
    "TaskPlanParseError",
    "parse_task_plan",
]
