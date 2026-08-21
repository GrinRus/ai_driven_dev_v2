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


class TaskPlanParseError(ValueError):
    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("Invalid tasklist: " + "; ".join(issues))


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


def _section_lines(markdown: str, heading: str) -> list[str]:
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
    return lines[start:end]


def _parse_task_blocks(
    markdown: str,
) -> tuple[list[tuple[str, str, list[str]]], list[str]]:
    lines = _section_lines(markdown, "Ordered tasks")
    issues: list[str] = []
    blocks: list[tuple[str, str, list[str]]] = []
    current_id: str | None = None
    current_title = ""
    current_lines: list[str] = []
    for line in lines:
        heading = _parse_task_heading(line)
        if heading is not None:
            if current_id is not None:
                blocks.append((current_id, current_title, current_lines))
            current_id, current_title = heading
            current_lines = []
            continue
        if current_id is not None:
            current_lines.append(line)
    if current_id is not None:
        blocks.append((current_id, current_title, current_lines))
    if not blocks:
        issues.append("`Ordered tasks` must contain H3 task cards with stable task ids.")
    ids = [task_id for task_id, _, _ in blocks]
    duplicate_ids = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
    if duplicate_ids:
        issues.append("Duplicate task ids: " + ", ".join(duplicate_ids) + ".")
    styles = {"compact" if re.fullmatch(r"T\d+", task_id) else "prefixed" for task_id in ids}
    if len(styles) > 1:
        issues.append("Task cards must not mix compact and prefixed task id styles.")
    return blocks, issues


def _parse_mapped_section(
    markdown: str,
    heading: str,
    pattern: re.Pattern[str],
) -> tuple[dict[str, str], list[str]]:
    entries: dict[str, str] = {}
    issues: list[str] = []
    for line in _section_lines(markdown, heading):
        if not line.strip():
            continue
        match = pattern.match(line)
        if match is None:
            continue
        task_id = _normalized_task_id(match.group(1))
        if task_id is None:
            continue
        if task_id in entries:
            issues.append(f"Section `{heading}` contains duplicate entry `{task_id}`.")
        entries[task_id] = match.group(2).strip()
    return entries, issues


def _parse_card_fields(
    task_id: str,
    lines: list[str],
) -> tuple[dict[str, str], tuple[TaskAcceptanceCriterion, ...], list[str]]:
    fields: dict[str, str] = {}
    acceptance: list[TaskAcceptanceCriterion] = []
    issues: list[str] = []
    in_acceptance = False
    for line in lines:
        if in_acceptance:
            criterion_match = re.match(
                r"^\s{2,}[-*]\s+([^:\s]+)\s*:\s*(.+?)\s*$",
                line,
            )
            if criterion_match is not None:
                criterion_id = _strip_markdown_wrappers(criterion_match.group(1)).upper()
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
                issues.append(f"Task `{task_id}` repeats field `{label}`.")
            fields[key] = field_match.group(2).strip()
            in_acceptance = key == "acceptance criteria"
            continue
        if line.strip() and not line.lstrip().startswith(("-", "*")):
            in_acceptance = False

    for label in ("outcome", "dominant deliverable", "in scope"):
        if not fields.get(label, "").strip():
            issues.append(f"Task `{task_id}` is missing required field `{label}`.")
    expected_acceptance_pattern = re.compile(rf"^{re.escape(task_id)}-AC[1-9]\d*$")
    if not acceptance:
        issues.append(f"Task `{task_id}` must declare at least one acceptance criterion.")
    acceptance_ids = [criterion.id for criterion in acceptance]
    for acceptance_id in acceptance_ids:
        if expected_acceptance_pattern.fullmatch(acceptance_id) is None:
            issues.append(f"Task `{task_id}` has malformed acceptance id `{acceptance_id}`.")
    duplicates = sorted({item for item in acceptance_ids if acceptance_ids.count(item) > 1})
    if duplicates:
        issues.append(f"Task `{task_id}` has duplicate acceptance ids: {', '.join(duplicates)}.")
    return fields, tuple(acceptance), issues


def _parse_scope_paths(task_id: str, value: str) -> tuple[tuple[str, ...], list[str]]:
    paths: list[str] = []
    issues: list[str] = []
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
            issues.append(f"Task `{task_id}` has unsafe in-scope path `{raw_value}`.")
            continue
        paths.append(candidate)
    if not paths:
        issues.append(
            f"Task `{task_id}` field `in scope` must contain at least one backticked "
            "repository-relative file or directory path."
        )
    return tuple(dict.fromkeys(paths)), issues


def _validate_dependency_graph(
    task_ids: tuple[str, ...],
    dependencies: dict[str, tuple[str, ...]],
) -> list[str]:
    issues: list[str] = []
    known = set(task_ids)
    positions = {task_id: index for index, task_id in enumerate(task_ids)}
    for task_id, task_dependencies in dependencies.items():
        unknown = sorted(set(task_dependencies) - known)
        if unknown:
            issues.append(
                f"Task `{task_id}` references unknown dependencies: {', '.join(unknown)}."
            )
        if task_id in task_dependencies:
            issues.append(f"Task `{task_id}` cannot depend on itself.")
        forward = tuple(
            dependency
            for dependency in task_dependencies
            if dependency in positions and positions[dependency] >= positions[task_id]
        )
        if forward:
            issues.append(
                f"Task `{task_id}` references dependencies that do not appear earlier in "
                f"`Ordered tasks`: {', '.join(forward)}."
            )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            issues.append(f"Task dependency graph contains a cycle at `{task_id}`.")
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
    task_ids = tuple(task_id for task_id, _, _ in blocks)
    known_ids = set(task_ids)
    for section_name, entries in (
        ("Dependencies", dependency_entries),
        ("Verification notes", verification_entries),
    ):
        missing = sorted(known_ids - set(entries))
        unknown = sorted(set(entries) - known_ids)
        if missing:
            issues.append(f"Section `{section_name}` is missing task ids: {', '.join(missing)}.")
        if unknown:
            issues.append(
                f"Section `{section_name}` references unknown task ids: {', '.join(unknown)}."
            )

    parsed_dependencies: dict[str, tuple[str, ...]] = {}
    for task_id in task_ids:
        dependency_text = dependency_entries.get(task_id, "")
        # Dependency entries may carry a short human-readable rationale after the
        # machine-readable value (for example, ``T1: none — establishes M1``).
        # Only the leading dependency value defines the graph; milestone/review
        # ids in the rationale must not turn a valid ``none`` into a dependency.
        if _NONE_DEPENDENCY_PATTERN.match(dependency_text.strip("` .")):
            parsed_dependencies[task_id] = ()
        else:
            parsed_dependencies[task_id] = tuple(
                dict.fromkeys(
                    match.group(1).upper() for match in _TASK_ID_PATTERN.finditer(dependency_text)
                )
            )
            if not parsed_dependencies[task_id]:
                issues.append(f"Task `{task_id}` dependencies must be `none` or task ids.")

    issues.extend(_validate_dependency_graph(task_ids, parsed_dependencies))
    cards: list[TaskCard] = []
    all_acceptance_ids: list[str] = []
    for task_id, title, lines in blocks:
        SafeIdentifier.parse(task_id, label="task id")
        fields, acceptance, field_issues = _parse_card_fields(task_id, lines)
        issues.extend(field_issues)
        scope_paths, scope_issues = _parse_scope_paths(task_id, fields.get("in scope", ""))
        issues.extend(scope_issues)
        all_acceptance_ids.extend(item.id for item in acceptance)
        verification = verification_entries.get(task_id, "").strip()
        if not verification or verification.casefold().strip("` .") == "none":
            issues.append(f"Task `{task_id}` must declare concrete verification.")
        execution_mode_value = fields.get(
            "execution mode",
            TaskExecutionMode.REPOSITORY_CHANGE.value,
        ).casefold()
        try:
            execution_mode = TaskExecutionMode(execution_mode_value)
        except ValueError:
            issues.append(
                f"Task `{task_id}` execution mode must be `repository-change` or "
                "`verification-only`."
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
        issues.append(
            "Acceptance ids must be globally unique: " + ", ".join(duplicate_acceptance) + "."
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
    "TaskPlan",
    "TaskPlanParseError",
    "parse_task_plan",
]
