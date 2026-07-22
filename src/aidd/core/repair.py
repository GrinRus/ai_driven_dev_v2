from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from aidd.core.models.run import RepairHistoryEntry
from aidd.core.run_store import (
    RUN_ATTEMPT_PREFIX,
    load_stage_metadata,
    persist_repair_history_entry,
    run_attempts_root,
)
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.validators.protocol import parse_validator_report

_IMMEDIATE_DOWNSTREAM_STAGE: dict[str, str] = {
    "idea": "research",
    "research": "plan",
    "plan": "review-spec",
    "review-spec": "tasklist",
    "tasklist": "implement",
    "implement": "review",
    "review": "qa",
}

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


@dataclass(frozen=True, slots=True)
class RepairHistoryPersistenceResult:
    stage_metadata_path: Path
    stage_result_path: Path


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
    report = parse_validator_report(validator_report_markdown)
    return tuple(
            ValidatorReportFinding(
                code=finding.code,
                severity=finding.severity,
                message=finding.message,
                source_path=finding.source_path,
            )
            for finding in report.findings
        )


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
        hint = _repair_hint_for_finding(finding)
        suffix = f" {hint}" if hint else ""
        lines.append(
            f"- [`{finding.code}`] Update {target} to resolve: {finding.message}{suffix}"
        )
    if not lines:
        lines.append("- none")
    return lines


def _repair_hint_for_finding(finding: ValidatorReportFinding) -> str:
    normalized_message = finding.message.lower()
    normalized_source_path = (finding.source_path or "").lower()
    if finding.code == "CROSS-TASKLIST-PLAN-MILESTONE":
        return (
            "Use only canonical milestone mapping locations: write the exact existing `M<n>` "
            "id in the task's `Outcome`, optional `Context`, a nested acceptance criterion, "
            "or its dedicated `Verification notes` entry. Do not add `Milestone` or "
            "`Plan milestone`; those fields are outside the rich-task grammar."
        )
    if finding.code == "INTERVIEW-MALFORMED-DOCUMENT":
        if "answers.md" in normalized_source_path or "answer" in normalized_message:
            return (
                "Rewrite answer bullets with exact interview syntax: replace forms like "
                "`- Q1 [resolved]: text` with `- Q1 [resolved] text`; do not use "
                "`- Q1: [resolved] text` or `A1` answer ids. If no operator answer is "
                "present, write exactly `- none`."
            )
        if "questions.md" in normalized_source_path or "question" in normalized_message:
            return (
                "Rewrite question bullets with exact interview syntax: use "
                "`- Q1 [blocking] text` or `- Q1 [non-blocking] text`; put alternatives, "
                "examples, or rationale in non-bullet continuation prose instead of nested "
                "bullets."
            )
        return (
            "Rewrite interview bullets with exact `questions.md` / `answers.md` syntax; "
            "do not put punctuation immediately after the marker and do not invent `A1` "
            "answer ids."
        )
    if (
        finding.code == "SEM-INCOMPLETE-SECTION"
        and "must use bullet items" in normalized_message
        and "`- none`" in finding.message
    ):
        return (
            "Render the section as top-level Markdown bullet items; if there are no entries, "
            "write exactly `- none`."
        )
    if (
        finding.code == "SEM-UNSUPPORTED-CLAIM"
        and "evidence reference to implementation output" in normalized_message
    ):
        return (
            "Add an explicit `Evidence:` line under each affected review finding that cites "
            "`implementation-report.md`, a changed implementation file path, or an "
            "acceptance-criteria id such as `AC-1`; remove or mark the finding `invalid` "
            "if no such evidence exists."
        )
    if finding.code == "SEM-MISSING-EVIDENCE-REF" and "review-spec" in normalized_source_path:
        return (
            "For each review-spec issue/no-defect item, add `Evidence:` naming a concrete "
            "upstream artifact, research/source id, target file path, or check result."
        )
    if finding.code == "SEM-UNSUPPORTED-CLAIM" and "review-spec" in normalized_source_path:
        return (
            "Either cite direct durable evidence and add `Reconciliation:` when contradicting "
            "upstream research/plan evidence, or downgrade the claim to a bounded low/info "
            "observation or question."
        )
    if finding.code in {"CROSS-QA-REVIEW-RISK", "CROSS-QA-UPSTREAM-EVIDENCE"}:
        return (
            "Replace fuzzy or basename-only QA references with an exact upstream `RV-*`, "
            "`REV-*`, `AR-*`, or evidence id, or with a full workspace-relative path to an "
            "existing review/implementation artifact."
        )
    if finding.code == "CROSS-QA-UPSTREAM-VERDICT":
        return (
            "Align QA with upstream review evidence: unresolved `must-fix` or rejected review "
            "requires `QA verdict: not-ready` and release recommendation `hold`."
        )
    if (
        finding.code == "SEM-UNVERIFIABLE-CHECK-CLAIM"
        and (
            "ignored workspace residue" in normalized_message
            or "ignored residue" in normalized_message
            or "workspace residue" in normalized_message
        )
    ):
        return (
            "Check ignored residue after all review commands. Remove the residue and cite "
            "post-cleanup evidence, or record an active `RV-*` finding with direct residue "
            "evidence. Do not write `Findings: none` while residue exists."
        )
    if (
        finding.code == "SEM-UNVERIFIABLE-CHECK-CLAIM"
        and "outcome claim without executable command evidence" in normalized_message
    ):
        return (
            "Rewrite each affected verification note so the same bullet contains the "
            "exact command/check evidence and observed result, such as "
            "`uv run pytest -q` -> pass. If the check was not run, write "
            "`not-run: <reason>` instead of a pass/success claim."
        )
    if (
        finding.code == "SEM-UNVERIFIABLE-CHECK-CLAIM"
        and "must include observed command outcome" in normalized_message
    ):
        return (
            "Keep the command/check evidence and add the observed result on the same "
            "verification bullet, such as `-> pass`, `-> fail`, or `exit code N`."
        )
    return ""


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
        lines.append("Repair budget status: `repair-budget-final-attempt`.")
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


def _format_attempt_history_line(entry: RepairHistoryEntry) -> str:
    line = f"- Attempt `{entry.attempt_number}` (`{entry.trigger}`) -> {entry.outcome}."
    evidence_items: list[str] = []
    if entry.validator_report_path is not None:
        evidence_items.append(f"validator: `{entry.validator_report_path}`")
    if entry.repair_brief_path is not None:
        evidence_items.append(f"repair brief: `{entry.repair_brief_path}`")
    if evidence_items:
        line += f" Evidence: {', '.join(evidence_items)}."
    return line


def _dedupe_paths(paths: Iterable[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for path in paths:
        normalized = path.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return tuple(deduped)


def _existing_declared_stage_output_paths(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> tuple[str, ...]:
    try:
        from aidd.core.stage_registry import load_stage_manifest

        manifest = load_stage_manifest(stage=stage)
    except Exception:
        return ()

    stage_root = workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage)
    existing_paths: list[str] = []
    for output_path in manifest.required_output_paths:
        candidate = stage_root / output_path
        if candidate.exists():
            existing_paths.append(f"workitems/{work_item}/stages/{stage}/{output_path}")
    return tuple(existing_paths)


def _successful_stage_result_next_action(stage: str) -> str:
    next_stage = _IMMEDIATE_DOWNSTREAM_STAGE.get(stage)
    if next_stage is None:
        return "- Inspect terminal handoff and final artifacts."
    return f"- Advance to the immediate canonical `{next_stage}` stage."


def render_stage_result_with_repair_history(
    *,
    stage: str,
    work_item: str | None,
    status: str,
    repair_history: Iterable[RepairHistoryEntry],
    produced_output_paths: Iterable[str | Path] = (),
    validator_report_path: str | Path | None = None,
    repair_brief_path: str | Path | None = None,
    workspace_root: Path | None = None,
) -> str:
    normalized_stage = stage.strip()
    if not normalized_stage:
        raise ValueError("Stage must not be empty for stage-result rendering.")

    normalized_status = status.strip().lower()
    if not normalized_status:
        raise ValueError("Status must not be empty for stage-result rendering.")

    history_entries = tuple(
        sorted(
            repair_history,
            key=lambda entry: (entry.attempt_number, entry.trigger),
        )
    )
    normalized_validator_report_path = (
        _normalize_workspace_relative_path(
            path=validator_report_path,
            workspace_root=workspace_root,
        )
        if validator_report_path is not None
        else None
    )
    normalized_repair_brief_path = (
        _normalize_workspace_relative_path(path=repair_brief_path, workspace_root=workspace_root)
        if repair_brief_path is not None
        else None
    )
    normalized_produced_output_paths = tuple(
        _normalize_workspace_relative_path(path=path, workspace_root=workspace_root)
        for path in produced_output_paths
    )

    common_output_paths = [
        (
            f"workitems/{work_item}/stages/{normalized_stage}/stage-result.md"
            if work_item is not None
            else "stage-result.md"
        )
    ]
    if normalized_validator_report_path is not None:
        common_output_paths.append(normalized_validator_report_path)
    if normalized_repair_brief_path is not None:
        common_output_paths.append(normalized_repair_brief_path)
    produced_outputs = _dedupe_paths(
        (
            *normalized_produced_output_paths,
            *common_output_paths,
        )
    )

    lines = [
        "# Stage",
        "",
        normalized_stage,
        "",
        "## Attempt history",
        "",
    ]
    if history_entries:
        lines.extend(_format_attempt_history_line(entry) for entry in history_entries)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Status",
            "",
            f"- `{normalized_status}`",
            "",
            "## Produced outputs",
            "",
            *(f"- `{path}`" for path in produced_outputs),
        ]
    )

    lines.extend(
        [
            "",
            "## Validation summary",
            "",
            f"- Validator verdict: {'pass' if normalized_status == 'succeeded' else 'fail'}",
            (
                f"- Validator findings: see `{normalized_validator_report_path}`."
                if normalized_validator_report_path is not None
                else "- Validator findings: none recorded."
            ),
            "",
            "## Blockers",
            "",
        ]
    )
    if normalized_status == "succeeded":
        lines.append("- none")
    else:
        lines.append(f"- Stage ended with status `{normalized_status}` and needs operator action.")

    lines.extend(
        [
            "",
            "## Next actions",
            "",
        ]
    )
    if normalized_status == "succeeded":
        lines.append(_successful_stage_result_next_action(normalized_stage))
    elif normalized_status == "failed":
        lines.append("- Review validator report and decide whether to reopen scope or stop.")
    else:
        lines.append("- Resolve blockers and rerun the stage when policy allows.")

    lines.extend(
        [
            "",
            "## Terminal state notes",
            "",
            f"- Repair history entries recorded: `{len(history_entries)}`.",
        ]
    )
    if normalized_status == "failed" and history_entries:
        lines.append("- Repair budget status: `repair-budget-exhausted`.")
    if normalized_status != "succeeded" and normalized_validator_report_path is not None:
        lines.append(
            "- Canonical AIDD validation found open findings; terminal status and "
            "validator verdict claims must not remain `succeeded` or `pass`."
        )
    if normalized_repair_brief_path is not None:
        lines.append(
            f"- Repair decision context recorded in `{normalized_repair_brief_path}`."
        )
    lines.append("")
    return "\n".join(lines)


def persist_repair_history_snapshot(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
    trigger: str,
    outcome: str,
    stage_status: str,
    validator_report_path: Path | None = None,
    repair_brief_path: Path | None = None,
    changed_at_utc: datetime | None = None,
) -> RepairHistoryPersistenceResult:
    stage_metadata_path = persist_repair_history_entry(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        trigger=trigger,
        outcome=outcome,
        validator_report_path=validator_report_path,
        repair_brief_path=repair_brief_path,
        changed_at_utc=changed_at_utc,
    )
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if metadata is None:
        raise RuntimeError("Stage metadata is missing after persisting repair history.")

    stage_result_path = (
        workspace_stage_root(root=workspace_root, work_item=work_item, stage=stage)
        / "stage-result.md"
    )
    produced_output_paths = _existing_declared_stage_output_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    stage_result_markdown = render_stage_result_with_repair_history(
        stage=stage,
        work_item=work_item,
        status=stage_status,
        repair_history=metadata.repair_history,
        produced_output_paths=produced_output_paths,
        validator_report_path=validator_report_path,
        repair_brief_path=repair_brief_path,
        workspace_root=workspace_root,
    )
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    stage_result_path.write_text(stage_result_markdown, encoding="utf-8")

    return RepairHistoryPersistenceResult(
        stage_metadata_path=stage_metadata_path,
        stage_result_path=stage_result_path,
    )


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
