from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

RuntimeEventCategory = Literal[
    "error",
    "warning",
    "question",
    "repair",
    "validator",
    "stage",
    "info",
]
FailureTaxonomyCategory = Literal[
    "environment",
    "adapter",
    "runtime",
    "validation",
    "scenario-verification",
    "none",
]


@dataclass(frozen=True, slots=True)
class CoarseRuntimeEvent:
    line_number: int
    category: RuntimeEventCategory
    message: str


@dataclass(frozen=True, slots=True)
class NormalizedRuntimeEvent:
    line_number: int
    event_kind: str
    source: str | None
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class FailureTaxonomyResult:
    category: FailureTaxonomyCategory
    reason: str


@dataclass(frozen=True, slots=True)
class FailureBoundarySelection:
    category: FailureTaxonomyCategory
    signal_source: str
    signal_line_number: int | None
    reason: str


VALIDATOR_FINDING_PATTERN = re.compile(
    r"^- `(?P<code>[^`]+)` \(`(?P<severity>[^`]+)`\) in (?P<location>.+?): (?P<message>.+)$"
)
VALIDATOR_VERDICT_PATTERN = re.compile(r"^- Verdict:\s*`(?P<verdict>pass|fail)`\s*$")


def _classify_runtime_log_line(line: str) -> RuntimeEventCategory:
    normalized = line.strip()
    lower = normalized.lower()
    if any(token in lower for token in ("error", "exception", "traceback", "failed")):
        return "error"
    if "warning" in lower:
        return "warning"
    if normalized.endswith("?") or any(
        token in lower for token in ("question", "clarify", "clarification")
    ):
        return "question"
    if "repair" in lower:
        return "repair"
    if "validator" in lower or "validation" in lower:
        return "validator"
    if any(token in lower for token in ("stage", "phase", "step")) and "->" in lower:
        return "stage"
    return "info"


def _classify_normalized_event(event: NormalizedRuntimeEvent) -> RuntimeEventCategory:
    normalized_kind = event.event_kind.strip().lower()
    if any(token in normalized_kind for token in ("error", "fail", "exception", "timeout")):
        return "error"
    if "warn" in normalized_kind:
        return "warning"
    if any(token in normalized_kind for token in ("question", "pause", "awaiting", "input")):
        return "question"
    if "repair" in normalized_kind:
        return "repair"
    if any(token in normalized_kind for token in ("validator", "validation")):
        return "validator"
    if "stage" in normalized_kind:
        return "stage"
    return "info"


def parse_events_jsonl_text(events_jsonl_text: str) -> tuple[NormalizedRuntimeEvent, ...]:
    events: list[NormalizedRuntimeEvent] = []
    for line_number, raw_line in enumerate(events_jsonl_text.splitlines(), start=1):
        normalized_line = raw_line.strip()
        if not normalized_line:
            continue
        try:
            payload = json.loads(normalized_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in events.jsonl at line {line_number}.") from exc
        if not isinstance(payload, dict):
            payload_type = type(payload).__name__
            raise ValueError(
                "events.jsonl line "
                f"{line_number} must be a JSON object, got {payload_type}."
            )

        event_kind = str(payload.get("event") or payload.get("type") or "").strip().lower()
        source_value = payload.get("source")
        source = source_value.strip().lower() if isinstance(source_value, str) else None
        events.append(
            NormalizedRuntimeEvent(
                line_number=line_number,
                event_kind=event_kind or "unknown",
                source=source,
                payload=payload,
            )
        )
    return tuple(events)


def parse_events_jsonl(events_jsonl_path: Path) -> tuple[NormalizedRuntimeEvent, ...]:
    if not events_jsonl_path.exists() or not events_jsonl_path.is_file():
        raise ValueError(f"events.jsonl file does not exist: {events_jsonl_path.as_posix()}")
    return parse_events_jsonl_text(events_jsonl_path.read_text(encoding="utf-8"))


def coarse_events_from_normalized_events(
    normalized_events: tuple[NormalizedRuntimeEvent, ...],
) -> tuple[CoarseRuntimeEvent, ...]:
    coarse_events: list[CoarseRuntimeEvent] = []
    for event in normalized_events:
        message = (
            str(event.payload.get("message")).strip()
            if isinstance(event.payload.get("message"), str)
            else event.event_kind
        )
        coarse_events.append(
            CoarseRuntimeEvent(
                line_number=event.line_number,
                category=_classify_normalized_event(event),
                message=message or event.event_kind,
            )
        )
    return tuple(coarse_events)


def parse_validator_report_failures_text(
    validator_report_text: str,
) -> tuple[CoarseRuntimeEvent, ...]:
    findings: list[CoarseRuntimeEvent] = []
    verdict: str | None = None
    verdict_line_number: int | None = None

    for line_number, raw_line in enumerate(validator_report_text.splitlines(), start=1):
        normalized_line = raw_line.strip()
        if not normalized_line:
            continue
        if verdict_match := VALIDATOR_VERDICT_PATTERN.match(normalized_line):
            verdict = verdict_match.group("verdict")
            verdict_line_number = line_number
            continue
        if finding_match := VALIDATOR_FINDING_PATTERN.match(normalized_line):
            code = finding_match.group("code")
            severity = finding_match.group("severity")
            location = finding_match.group("location")
            message = finding_match.group("message")
            findings.append(
                CoarseRuntimeEvent(
                    line_number=line_number,
                    category="validator",
                    message=(
                        f"{code} ({severity}) in {location}: {message}"
                    ),
                )
            )

    if findings:
        return tuple(findings)
    if verdict == "fail":
        return (
            CoarseRuntimeEvent(
                line_number=verdict_line_number or 1,
                category="validator",
                message="validator report verdict is fail",
            ),
        )
    return tuple()


def parse_validator_report_failures(
    validator_report_path: Path,
) -> tuple[CoarseRuntimeEvent, ...]:
    if not validator_report_path.exists() or not validator_report_path.is_file():
        raise ValueError(
            f"validator-report.md file does not exist: {validator_report_path.as_posix()}"
        )
    return parse_validator_report_failures_text(
        validator_report_path.read_text(encoding="utf-8")
    )


def parse_stage_metadata_validation_failures_text(
    stage_metadata_text: str,
) -> tuple[CoarseRuntimeEvent, ...]:
    try:
        payload = json.loads(stage_metadata_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON in stage metadata payload.") from exc
    if not isinstance(payload, dict):
        raise ValueError("stage metadata payload must be a JSON object.")

    stage = str(payload.get("stage") or "").strip() or "unknown"
    events: list[CoarseRuntimeEvent] = []

    status_history = payload.get("status_history")
    if isinstance(status_history, list):
        for index, item in enumerate(status_history, start=1):
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "").strip().lower()
            changed_at_utc = str(item.get("changed_at_utc") or "").strip() or "unknown"
            if status == "failed":
                category: RuntimeEventCategory = "error"
            elif status == "blocked":
                category = "question"
            elif status == "repair_needed":
                category = "validator"
            else:
                continue
            events.append(
                CoarseRuntimeEvent(
                    line_number=index,
                    category=category,
                    message=f"stage `{stage}` status `{status}` at `{changed_at_utc}`",
                )
            )

    repair_history = payload.get("repair_history")
    if isinstance(repair_history, list):
        base_index = len(events)
        for offset, item in enumerate(repair_history, start=1):
            if not isinstance(item, dict):
                continue
            outcome = str(item.get("outcome") or "").strip().lower()
            if "fail" not in outcome:
                continue
            attempt_number = item.get("attempt_number")
            events.append(
                CoarseRuntimeEvent(
                    line_number=base_index + offset,
                    category="validator",
                    message=(
                        f"repair attempt `{attempt_number}` recorded failing outcome `{outcome}`"
                    ),
                )
            )

    return tuple(events)


def parse_stage_metadata_validation_failures(
    stage_metadata_path: Path,
) -> tuple[CoarseRuntimeEvent, ...]:
    if not stage_metadata_path.exists() or not stage_metadata_path.is_file():
        raise ValueError(
            f"stage metadata file does not exist: {stage_metadata_path.as_posix()}"
        )
    return parse_stage_metadata_validation_failures_text(
        stage_metadata_path.read_text(encoding="utf-8")
    )


def _is_environment_signal(message: str) -> bool:
    normalized = message.lower().replace("_", " ").replace("-", " ")
    return any(
        token in normalized
        for token in (
            "network unreachable",
            "connection refused",
            "no space left",
            "no such file or directory",
            "not found",
            "dns",
            "unable to resolve host",
            "timed out",
        )
    )


def _is_adapter_signal(message: str) -> bool:
    normalized = message.lower()
    return any(token in normalized for token in ("adapter", "protocol mismatch"))


def classify_failure_taxonomy(
    *,
    runtime_events: tuple[CoarseRuntimeEvent, ...] = (),
    normalized_events: tuple[NormalizedRuntimeEvent, ...] = (),
    validator_failures: tuple[CoarseRuntimeEvent, ...] = (),
    stage_metadata_failures: tuple[CoarseRuntimeEvent, ...] = (),
    aidd_exit_code: int | None = None,
    verification_exit_code: int | None = None,
) -> FailureTaxonomyResult:
    for event in runtime_events:
        if _is_environment_signal(event.message):
            return FailureTaxonomyResult(
                category="environment",
                reason=f"runtime log signal: {event.message}",
            )
    for normalized_event in normalized_events:
        if _is_environment_signal(normalized_event.event_kind):
            return FailureTaxonomyResult(
                category="environment",
                reason=f"normalized event signal: {normalized_event.event_kind}",
            )

    for event in runtime_events:
        if _is_adapter_signal(event.message):
            return FailureTaxonomyResult(
                category="adapter",
                reason=f"runtime log signal: {event.message}",
            )
    for normalized_event in normalized_events:
        if _is_adapter_signal(normalized_event.event_kind):
            return FailureTaxonomyResult(
                category="adapter",
                reason=f"normalized event signal: {normalized_event.event_kind}",
            )

    if aidd_exit_code not in (None, 0):
        return FailureTaxonomyResult(
            category="runtime",
            reason=f"AIDD run exited with non-zero status {aidd_exit_code}.",
        )
    for event in runtime_events:
        if event.category == "error":
            return FailureTaxonomyResult(
                category="runtime",
                reason=f"runtime error signal: {event.message}",
            )

    validation_signals = (*validator_failures, *stage_metadata_failures)
    if validation_signals:
        return FailureTaxonomyResult(
            category="validation",
            reason=f"validation signal: {validation_signals[0].message}",
        )

    if verification_exit_code not in (None, 0):
        return FailureTaxonomyResult(
            category="scenario-verification",
            reason=f"verification exited with non-zero status {verification_exit_code}.",
        )

    return FailureTaxonomyResult(
        category="none",
        reason="No failure signal detected.",
    )


def select_first_failure_boundary(
    *,
    runtime_events: tuple[CoarseRuntimeEvent, ...] = (),
    normalized_events: tuple[NormalizedRuntimeEvent, ...] = (),
    validator_failures: tuple[CoarseRuntimeEvent, ...] = (),
    stage_metadata_failures: tuple[CoarseRuntimeEvent, ...] = (),
    aidd_exit_code: int | None = None,
    verification_exit_code: int | None = None,
) -> FailureBoundarySelection:
    ranked_candidates: list[tuple[int, int, FailureBoundarySelection]] = []

    def _push_candidate(
        *,
        rank: int,
        line_number: int | None,
        selection: FailureBoundarySelection,
    ) -> None:
        ranked_candidates.append(
            (
                rank,
                line_number if line_number is not None else 10**9,
                selection,
            )
        )

    for event in runtime_events:
        if _is_environment_signal(event.message):
            _push_candidate(
                rank=0,
                line_number=event.line_number,
                selection=FailureBoundarySelection(
                    category="environment",
                    signal_source="runtime.log",
                    signal_line_number=event.line_number,
                    reason=event.message,
                ),
            )
        elif _is_adapter_signal(event.message):
            _push_candidate(
                rank=1,
                line_number=event.line_number,
                selection=FailureBoundarySelection(
                    category="adapter",
                    signal_source="runtime.log",
                    signal_line_number=event.line_number,
                    reason=event.message,
                ),
            )
        elif event.category == "error":
            _push_candidate(
                rank=2,
                line_number=event.line_number,
                selection=FailureBoundarySelection(
                    category="runtime",
                    signal_source="runtime.log",
                    signal_line_number=event.line_number,
                    reason=event.message,
                ),
            )

    for normalized_event in normalized_events:
        if _is_environment_signal(normalized_event.event_kind):
            _push_candidate(
                rank=0,
                line_number=normalized_event.line_number,
                selection=FailureBoundarySelection(
                    category="environment",
                    signal_source="events.jsonl",
                    signal_line_number=normalized_event.line_number,
                    reason=normalized_event.event_kind,
                ),
            )
        elif _is_adapter_signal(normalized_event.event_kind):
            _push_candidate(
                rank=1,
                line_number=normalized_event.line_number,
                selection=FailureBoundarySelection(
                    category="adapter",
                    signal_source="events.jsonl",
                    signal_line_number=normalized_event.line_number,
                    reason=normalized_event.event_kind,
                ),
            )
        elif any(
            token in normalized_event.event_kind
            for token in ("error", "fail", "exception", "timeout")
        ):
            _push_candidate(
                rank=2,
                line_number=normalized_event.line_number,
                selection=FailureBoundarySelection(
                    category="runtime",
                    signal_source="events.jsonl",
                    signal_line_number=normalized_event.line_number,
                    reason=normalized_event.event_kind,
                ),
            )

    for event in (*validator_failures, *stage_metadata_failures):
        _push_candidate(
            rank=3,
            line_number=event.line_number,
            selection=FailureBoundarySelection(
                category="validation",
                signal_source="validator-or-stage-metadata",
                signal_line_number=event.line_number,
                reason=event.message,
            ),
        )

    if aidd_exit_code not in (None, 0):
        _push_candidate(
            rank=2,
            line_number=None,
            selection=FailureBoundarySelection(
                category="runtime",
                signal_source="aidd-exit-code",
                signal_line_number=None,
                reason=f"AIDD exited with {aidd_exit_code}",
            ),
        )

    if verification_exit_code not in (None, 0):
        _push_candidate(
            rank=4,
            line_number=None,
            selection=FailureBoundarySelection(
                category="scenario-verification",
                signal_source="verification-exit-code",
                signal_line_number=None,
                reason=f"verification exited with {verification_exit_code}",
            ),
        )

    if not ranked_candidates:
        return FailureBoundarySelection(
            category="none",
            signal_source="none",
            signal_line_number=None,
            reason="No failure signal detected.",
        )

    ranked_candidates.sort(key=lambda item: (item[0], item[1]))
    return ranked_candidates[0][2]


def parse_runtime_log_text(runtime_log_text: str) -> tuple[CoarseRuntimeEvent, ...]:
    events: list[CoarseRuntimeEvent] = []
    for line_number, raw_line in enumerate(runtime_log_text.splitlines(), start=1):
        normalized_line = raw_line.strip()
        if not normalized_line:
            continue
        events.append(
            CoarseRuntimeEvent(
                line_number=line_number,
                category=_classify_runtime_log_line(normalized_line),
                message=normalized_line,
            )
        )
    return tuple(events)


def parse_runtime_log(runtime_log_path: Path) -> tuple[CoarseRuntimeEvent, ...]:
    if not runtime_log_path.exists() or not runtime_log_path.is_file():
        raise ValueError(f"runtime.log file does not exist: {runtime_log_path.as_posix()}")
    return parse_runtime_log_text(runtime_log_path.read_text(encoding="utf-8"))


def summarize_first_failure(
    *, runtime_log_path: Path | None = None, runtime_log_text: str | None = None
) -> str:
    if runtime_log_path is None and runtime_log_text is None:
        raise ValueError("Either runtime_log_path or runtime_log_text must be provided.")

    events = (
        parse_runtime_log(runtime_log_path)
        if runtime_log_path is not None
        else parse_runtime_log_text(runtime_log_text or "")
    )
    for event in events:
        if event.category == "error":
            return f"line {event.line_number}: {event.message}"
    return "no failure signal found"
