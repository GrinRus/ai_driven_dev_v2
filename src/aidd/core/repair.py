from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from aidd.core.run_store import RUN_ATTEMPT_PREFIX, run_attempts_root

_VALIDATOR_FINDING_PATTERN = re.compile(
    r"^- `(?P<code>[^`]+)` "
    r"\(`(?P<severity>critical|high|medium|low)`\) "
    r"in (?P<location>.+?): (?P<message>.+)$"
)


@dataclass(frozen=True, slots=True)
class ValidatorReportFinding:
    code: str
    severity: str
    message: str
    source_path: str | None

    def __post_init__(self) -> None:
        normalized_code = self.code.strip().upper()
        if not normalized_code:
            raise ValueError("Validator report finding code must not be empty.")
        object.__setattr__(self, "code", normalized_code)

        normalized_severity = self.severity.strip().lower()
        if normalized_severity not in {"critical", "high", "medium", "low"}:
            raise ValueError(f"Unsupported finding severity: {self.severity}")
        object.__setattr__(self, "severity", normalized_severity)

        normalized_message = self.message.strip()
        if not normalized_message:
            raise ValueError("Validator report finding message must not be empty.")
        object.__setattr__(self, "message", normalized_message)

        if self.source_path is None:
            return

        normalized_source_path = self.source_path.strip()
        if not normalized_source_path:
            object.__setattr__(self, "source_path", None)
            return
        if Path(normalized_source_path).is_absolute():
            raise ValueError("Validator report finding source path must be workspace-relative.")
        object.__setattr__(self, "source_path", normalized_source_path)


@dataclass(frozen=True, slots=True)
class RepairBudgetPolicy:
    default_max_repair_attempts: int = 2
    stage_max_repair_attempts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.default_max_repair_attempts < 0:
            raise ValueError("Default max repair attempts must be non-negative.")

        normalized: dict[str, int] = {}
        for stage, attempts in self.stage_max_repair_attempts.items():
            normalized_stage = stage.strip()
            if not normalized_stage:
                raise ValueError("Stage override key must not be empty.")
            if attempts < 0:
                raise ValueError(
                    f"Stage repair attempts override must be non-negative for '{normalized_stage}'."
                )
            normalized[normalized_stage] = attempts

        object.__setattr__(self, "stage_max_repair_attempts", normalized)


@dataclass(frozen=True, slots=True)
class StageRepairCounter:
    stage: str
    stage_attempt_count: int
    repair_attempts_used: int
    max_repair_attempts: int
    remaining_repair_attempts: int
    budget_exhausted: bool


def _extract_location_path(location: str) -> str | None:
    normalized = location.strip()
    if not normalized or normalized == "unknown location":
        return None

    if "`" in normalized:
        match = re.search(r"`([^`]+)`", normalized)
        if match is None:
            return None
        return match.group(1).strip() or None

    if ":" in normalized:
        path_part, maybe_line = normalized.rsplit(":", maxsplit=1)
        if maybe_line.isdigit():
            normalized = path_part

    return normalized or None


def _normalize_workspace_relative_path(
    *,
    path: str | Path,
    workspace_root: Path | None,
) -> str:
    normalized = str(path).strip()
    if not normalized:
        raise ValueError("Document path must not be empty.")

    candidate = Path(normalized)
    if not candidate.is_absolute():
        return candidate.as_posix()

    if workspace_root is None:
        raise ValueError(
            "Absolute document paths require workspace_root "
            "to compute workspace-relative references."
        )

    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    if not resolved_candidate.is_relative_to(resolved_workspace):
        raise ValueError(
            "Document path must stay inside workspace root when absolute paths are used: "
            f"{resolved_candidate}"
        )
    return resolved_candidate.relative_to(resolved_workspace).as_posix()


def parse_validator_report_findings(
    *,
    validator_report_markdown: str,
) -> tuple[ValidatorReportFinding, ...]:
    findings: list[ValidatorReportFinding] = []
    for raw_line in validator_report_markdown.splitlines():
        match = _VALIDATOR_FINDING_PATTERN.match(raw_line.strip())
        if match is None:
            continue

        findings.append(
            ValidatorReportFinding(
                code=match.group("code"),
                severity=match.group("severity"),
                message=match.group("message"),
                source_path=_extract_location_path(match.group("location")),
            )
        )

    return tuple(findings)


def _render_failed_checks(findings: tuple[ValidatorReportFinding, ...]) -> list[str]:
    lines = ["# Failed checks", ""]
    if not findings:
        lines.extend(["- none", ""])
        return lines

    for finding in findings:
        location = (
            f"`{finding.source_path}`" if finding.source_path is not None else "unknown location"
        )
        lines.append(
            f"- `{finding.code}` `{finding.severity}` in {location}: {finding.message}"
        )
    lines.append("")
    return lines


def _render_correction_items(findings: Iterable[ValidatorReportFinding]) -> list[str]:
    lines: list[str] = []
    for finding in findings:
        target = (
            f"`{finding.source_path}`"
            if finding.source_path is not None
            else "affected stage docs"
        )
        lines.append(f"- [`{finding.code}`] Update {target} to resolve: {finding.message}")
    if not lines:
        lines.append("- none")
    return lines


def _render_relevant_upstream_docs(
    *,
    validator_report_path: str | Path,
    prior_stage_artifacts: Iterable[str | Path],
    workspace_root: Path | None,
) -> list[str]:
    lines = ["# Relevant upstream docs", ""]
    seen: set[str] = set()
    ordered_paths: list[str] = []

    for candidate in (validator_report_path, *prior_stage_artifacts):
        normalized = _normalize_workspace_relative_path(
            path=candidate,
            workspace_root=workspace_root,
        )
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered_paths.append(normalized)

    if not ordered_paths:
        lines.extend(["- none", ""])
        return lines

    for path in ordered_paths:
        lines.append(f"- `{path}`")
    lines.append("")
    return lines


def render_repair_brief(
    *,
    validator_report_markdown: str,
    validator_report_path: str | Path,
    prior_stage_artifacts: Iterable[str | Path],
    stage_attempt_count: int,
    max_repair_attempts: int,
    workspace_root: Path | None = None,
) -> str:
    if stage_attempt_count < 0:
        raise ValueError("Stage attempt count must be non-negative.")
    if max_repair_attempts < 0:
        raise ValueError("Max repair attempts must be non-negative.")

    findings = parse_validator_report_findings(validator_report_markdown=validator_report_markdown)
    mandatory_fixes = tuple(
        finding for finding in findings if finding.severity in {"critical", "high"}
    )
    optional_fixes = tuple(finding for finding in findings if finding.severity in {"medium", "low"})

    next_attempt_number = stage_attempt_count + 1
    max_attempt_number = max_repair_attempts + 1
    remaining_after_this_attempt = max(0, max_attempt_number - next_attempt_number)
    rerun_allowed_after_this_attempt = remaining_after_this_attempt > 0

    lines: list[str] = []
    lines.extend(_render_failed_checks(findings))
    lines.extend(
        [
            "# Required corrections",
            "",
            "## Mandatory fixes",
            "",
            *_render_correction_items(mandatory_fixes),
            "",
            "## Optional quality improvements",
            "",
            *_render_correction_items(optional_fixes),
            "",
        ]
    )
    lines.extend(
        _render_relevant_upstream_docs(
            validator_report_path=validator_report_path,
            prior_stage_artifacts=prior_stage_artifacts,
            workspace_root=workspace_root,
        )
    )

    lines.append(
        "Repair attempt context: "
        f"attempt `{next_attempt_number}` of max `{max_attempt_number}`; "
        f"remaining retries after this attempt: `{remaining_after_this_attempt}`."
    )
    lines.append(
        "Rerun allowed after this attempt: "
        f"`{'yes' if rerun_allowed_after_this_attempt else 'no'}`."
    )
    if remaining_after_this_attempt == 0:
        lines.append("Repair budget status: `repair-budget-exhausted`.")
    else:
        lines.append("Repair budget status: `repair-budget-available`.")
    lines.append("")
    return "\n".join(lines)


def generate_repair_brief(
    *,
    validator_report_path: Path,
    prior_stage_artifacts: Iterable[str | Path],
    stage_attempt_count: int,
    max_repair_attempts: int,
    workspace_root: Path | None = None,
) -> str:
    report_markdown = validator_report_path.read_text(encoding="utf-8")
    return render_repair_brief(
        validator_report_markdown=report_markdown,
        validator_report_path=validator_report_path,
        prior_stage_artifacts=prior_stage_artifacts,
        stage_attempt_count=stage_attempt_count,
        max_repair_attempts=max_repair_attempts,
        workspace_root=workspace_root,
    )


def write_repair_brief(*, path: Path, repair_brief_markdown: str) -> None:
    path.write_text(repair_brief_markdown, encoding="utf-8")


def default_repair_budget() -> int:
    return RepairBudgetPolicy().default_max_repair_attempts


def effective_repair_budget(
    *,
    stage: str,
    policy: RepairBudgetPolicy | None = None,
) -> int:
    resolved_policy = policy or RepairBudgetPolicy()
    normalized_stage = stage.strip()
    if not normalized_stage:
        raise ValueError("Stage must not be empty when resolving repair budget.")

    if normalized_stage in resolved_policy.stage_max_repair_attempts:
        return resolved_policy.stage_max_repair_attempts[normalized_stage]
    return resolved_policy.default_max_repair_attempts


def count_stage_attempts(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> int:
    attempts_root = run_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if not attempts_root.exists():
        return 0

    count = 0
    for child in attempts_root.iterdir():
        if not child.is_dir() or not child.name.startswith(RUN_ATTEMPT_PREFIX):
            continue

        suffix = child.name.removeprefix(RUN_ATTEMPT_PREFIX)
        if suffix.isdigit():
            count += 1

    return count


def repair_attempts_used(*, stage_attempt_count: int) -> int:
    if stage_attempt_count < 0:
        raise ValueError("Stage attempt count must be non-negative.")

    # The first stage attempt is the initial run, not a repair run.
    return max(0, stage_attempt_count - 1)


def remaining_repair_attempts(*, repair_attempts_used: int, max_repair_attempts: int) -> int:
    if repair_attempts_used < 0:
        raise ValueError("Repair attempts used must be non-negative.")
    if max_repair_attempts < 0:
        raise ValueError("Max repair attempts must be non-negative.")

    return max(0, max_repair_attempts - repair_attempts_used)


def evaluate_stage_repair_counter(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    policy: RepairBudgetPolicy | None = None,
) -> StageRepairCounter:
    resolved_policy = policy or RepairBudgetPolicy()
    stage_attempt_count = count_stage_attempts(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    max_repair_attempts = effective_repair_budget(stage=stage, policy=resolved_policy)
    used = repair_attempts_used(stage_attempt_count=stage_attempt_count)
    remaining = remaining_repair_attempts(
        repair_attempts_used=used,
        max_repair_attempts=max_repair_attempts,
    )

    return StageRepairCounter(
        stage=stage,
        stage_attempt_count=stage_attempt_count,
        repair_attempts_used=used,
        max_repair_attempts=max_repair_attempts,
        remaining_repair_attempts=remaining,
        budget_exhausted=remaining == 0,
    )
