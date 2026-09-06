from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from aidd.validators.protocol import parse_validator_report

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
class RuntimeProviderDiagnosticSummary:
    model_profiles: tuple[str, ...]
    retry_signals: tuple[str, ...]
    rate_limit_signals: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FailureBoundarySelection:
    category: FailureTaxonomyCategory
    signal_source: str
    signal_line_number: int | None
    reason: str


@dataclass(frozen=True, slots=True)
class _FailureCandidate:
    rank: int
    source_order: int
    selection: FailureBoundarySelection


PROFILE_KEY_LABELS = {
    "claudecodeversion": "runtime_version",
    "model": "model",
    "modelid": "model",
    "modelname": "model",
    "outputstyle": "output_style",
    "profile": "profile",
    "profileid": "profile",
    "provider": "provider",
    "providerid": "provider",
    "runtimeversion": "runtime_version",
    "version": "runtime_version",
}
PROFILE_LABEL_ORDER = ("provider", "model", "profile", "output_style", "runtime_version")
SIGNAL_KEY_LABELS = {
    "attempt": "attempt",
    "error": "error",
    "errorstatus": "error_status",
    "event": "event",
    "maxretries": "max_retries",
    "retrydelayms": "retry_delay_ms",
    "stopreason": "stop_reason",
    "subtype": "subtype",
    "type": "type",
}


def _normalize_payload_key(key: str) -> str:
    return key.replace("_", "").replace("-", "").strip().lower()


def _scalar_text(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int | float):
        return str(value)
    return None


def _walk_payload_items(value: object) -> tuple[tuple[str, object], ...]:
    items: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str):
                items.append((key, child))
            items.extend(_walk_payload_items(child))
    elif isinstance(value, list):
        for child in value:
            items.extend(_walk_payload_items(child))
    return tuple(items)


def _single_line(value: str, *, limit: int = 240) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _profile_signal_for_event(event: NormalizedRuntimeEvent) -> str | None:
    values: dict[str, str] = {}
    for key, value in _walk_payload_items(event.payload):
        label = PROFILE_KEY_LABELS.get(_normalize_payload_key(key))
        scalar = _scalar_text(value)
        if label is not None and scalar is not None and label not in values:
            values[label] = scalar
    if "model" not in values and "provider" not in values and "profile" not in values:
        return None

    parts = [
        f"{label}={values[label]}"
        for label in PROFILE_LABEL_ORDER
        if label in values
    ]
    return f"line {event.line_number}: {_single_line('; '.join(parts))}"


def _event_signal_for_event(event: NormalizedRuntimeEvent) -> str:
    values: dict[str, str] = {}
    if event.source is not None:
        values["source"] = event.source
    for key, value in _walk_payload_items(event.payload):
        label = SIGNAL_KEY_LABELS.get(_normalize_payload_key(key))
        scalar = _scalar_text(value)
        if label is not None and scalar is not None and label not in values:
            values[label] = scalar
    if not values:
        values["event"] = event.event_kind
    signal = "; ".join(f"{key}={value}" for key, value in values.items())
    return f"line {event.line_number}: {_single_line(signal)}"


def _event_contains_signal(event: NormalizedRuntimeEvent, tokens: tuple[str, ...]) -> bool:
    normalized_kind = event.event_kind.replace("-", "_").lower()
    if any(token in normalized_kind for token in tokens):
        return True
    for key, value in _walk_payload_items(event.payload):
        key_text = _normalize_payload_key(key)
        if key_text not in SIGNAL_KEY_LABELS and not any(
            token in key_text for token in tokens
        ):
            continue
        scalar = _scalar_text(value)
        value_text = "" if scalar is None else scalar[:300].replace("-", "_").lower()
        haystack = f"{key_text} {value_text}"
        if any(token in haystack for token in tokens):
            return True
    return False


def _append_distinct_limited(items: list[str], value: str, *, limit: int = 5) -> None:
    if value in items or len(items) >= limit:
        return
    items.append(value)


def summarize_runtime_provider_diagnostics(
    normalized_events: tuple[NormalizedRuntimeEvent, ...],
) -> RuntimeProviderDiagnosticSummary:
    model_profiles: list[str] = []
    retry_signals: list[str] = []
    rate_limit_signals: list[str] = []

    for event in normalized_events:
        if profile_signal := _profile_signal_for_event(event):
            _append_distinct_limited(model_profiles, profile_signal)

        event_signal = _event_signal_for_event(event)
        if _event_contains_signal(
            event,
            ("retry", "api_retry", "maxretries", "retrydelayms"),
        ):
            _append_distinct_limited(retry_signals, event_signal)
        if _event_contains_signal(
            event,
            ("rate_limit", "ratelimit", "rate limit", "429"),
        ):
            _append_distinct_limited(rate_limit_signals, event_signal)

    return RuntimeProviderDiagnosticSummary(
        model_profiles=tuple(model_profiles),
        retry_signals=tuple(retry_signals),
        rate_limit_signals=tuple(rate_limit_signals),
    )


def _classify_runtime_log_line(line: str) -> RuntimeEventCategory:
    normalized = line.strip()
    lower = normalized.lower()
    if lower.startswith("stage run result:"):
        return "stage"
    if "validator" in lower or "validation" in lower:
        return "validator"
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

        event_kind = str(
            payload.get("event_kind")
            or payload.get("event")
            or payload.get("type")
            or ""
        ).strip().lower()
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


def parse_validator_report_failures_text(
    validator_report_text: str,
) -> tuple[CoarseRuntimeEvent, ...]:
    report = parse_validator_report(validator_report_text)
    findings = tuple(
        CoarseRuntimeEvent(
            line_number=finding.report_line_number,
            category="validator",
            message=(
                f"{finding.code} ({finding.severity}) in "
                + (
                    "unknown location"
                    if finding.source_path is None
                    else f"`{finding.source_path}`"
                    + (
                        f":{finding.source_line_number}"
                        if finding.source_line_number is not None
                        else ""
                    )
                )
                + f": {finding.message}"
            ),
        )
        for finding in report.findings
    )

    return findings


def _is_environment_signal(message: str) -> bool:
    normalized = message.lower().replace("_", " ").replace("-", " ")
    return bool(
        re.search(r"\b(?:http(?: status)?|status code)\s+[45]\d\d\b", normalized)
    ) or any(
        token in normalized
        for token in (
            "certificate verify failed",
            "connection reset",
            "network unreachable",
            "connection refused",
            "no space left",
            "no such file or directory",
            "executable not found",
            "not found",
            "dns",
            "name resolution",
            "temporary failure in name resolution",
            "tls",
            "unable to resolve host",
            "timed out",
            "timeout",
        )
    )


def _is_adapter_signal(message: str) -> bool:
    normalized = message.lower().replace("_", " ").replace("-", " ")
    if "protocol mismatch" in normalized:
        return True
    if "adapter" not in normalized:
        return False
    if "adapter outcome: success" in normalized:
        return False
    return any(
        token in normalized
        for token in (
            "fail",
            "failure",
            "failed",
            "error",
            "mismatch",
            "timeout",
            "timed out",
            "non zero",
        )
    )


def _is_noop_signal(message: str) -> bool:
    normalized = message.lower()
    return any(
        token in normalized
        for token in (
            "no runnable stages found",
            "failure classification: unsupported-runtime",
            "unsupported-runtime classification",
        )
    )


def _failure_candidates(
    *,
    runtime_events: tuple[CoarseRuntimeEvent, ...] = (),
    normalized_events: tuple[NormalizedRuntimeEvent, ...] = (),
    validator_failures: tuple[CoarseRuntimeEvent, ...] = (),
    stage_metadata_failures: tuple[CoarseRuntimeEvent, ...] = (),
    aidd_exit_code: int | None = None,
    verification_exit_code: int | None = None,
) -> tuple[_FailureCandidate, ...]:
    candidates: list[_FailureCandidate] = []
    source_order = 0

    def _push_candidate(
        *,
        rank: int,
        selection: FailureBoundarySelection,
    ) -> None:
        nonlocal source_order
        candidates.append(
            _FailureCandidate(
                rank=rank,
                source_order=source_order,
                selection=selection,
            )
        )
        source_order += 1

    for event in runtime_events:
        if _is_environment_signal(event.message):
            _push_candidate(
                rank=0,
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
                selection=FailureBoundarySelection(
                    category="adapter",
                    signal_source="runtime.log",
                    signal_line_number=event.line_number,
                    reason=event.message,
                ),
            )
        elif _is_noop_signal(event.message):
            _push_candidate(
                rank=2,
                selection=FailureBoundarySelection(
                    category="scenario-verification",
                    signal_source="runtime.log",
                    signal_line_number=event.line_number,
                    reason=event.message,
                ),
            )
        elif event.category == "error":
            _push_candidate(
                rank=4,
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
                selection=FailureBoundarySelection(
                    category="adapter",
                    signal_source="events.jsonl",
                    signal_line_number=normalized_event.line_number,
                    reason=normalized_event.event_kind,
                ),
            )
        elif _is_noop_signal(normalized_event.event_kind):
            _push_candidate(
                rank=2,
                selection=FailureBoundarySelection(
                    category="scenario-verification",
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
                rank=4,
                selection=FailureBoundarySelection(
                    category="runtime",
                    signal_source="events.jsonl",
                    signal_line_number=normalized_event.line_number,
                    reason=normalized_event.event_kind,
                ),
            )

    for event in stage_metadata_failures:
        _push_candidate(
            rank=3,
            selection=FailureBoundarySelection(
                category="validation",
                signal_source="stage-metadata",
                signal_line_number=event.line_number,
                reason=event.message,
            ),
        )

    for event in validator_failures:
        _push_candidate(
            rank=3,
            selection=FailureBoundarySelection(
                category="validation",
                signal_source="validator-report",
                signal_line_number=event.line_number,
                reason=event.message,
            ),
        )

    if aidd_exit_code not in (None, 0):
        _push_candidate(
            rank=4,
            selection=FailureBoundarySelection(
                category="runtime",
                signal_source="aidd-exit-code",
                signal_line_number=None,
                reason=f"AIDD exited with {aidd_exit_code}",
            ),
        )

    if verification_exit_code not in (None, 0):
        _push_candidate(
            rank=5,
            selection=FailureBoundarySelection(
                category="scenario-verification",
                signal_source="verification-exit-code",
                signal_line_number=None,
                reason=f"verification exited with {verification_exit_code}",
            ),
        )

    return tuple(candidates)


def _select_failure_boundary(
    *,
    runtime_events: tuple[CoarseRuntimeEvent, ...] = (),
    normalized_events: tuple[NormalizedRuntimeEvent, ...] = (),
    validator_failures: tuple[CoarseRuntimeEvent, ...] = (),
    stage_metadata_failures: tuple[CoarseRuntimeEvent, ...] = (),
    aidd_exit_code: int | None = None,
    verification_exit_code: int | None = None,
) -> FailureBoundarySelection:
    candidates = _failure_candidates(
        runtime_events=runtime_events,
        normalized_events=normalized_events,
        validator_failures=validator_failures,
        stage_metadata_failures=stage_metadata_failures,
        aidd_exit_code=aidd_exit_code,
        verification_exit_code=verification_exit_code,
    )
    if not candidates:
        return FailureBoundarySelection(
            category="none",
            signal_source="none",
            signal_line_number=None,
            reason="No failure signal detected.",
        )

    return min(
        candidates,
        key=lambda candidate: (
            candidate.rank,
            (
                candidate.selection.signal_line_number
                if candidate.selection.signal_line_number is not None
                else 10**9
            ),
            candidate.source_order,
        ),
    ).selection


def select_first_failure_boundary(
    *,
    runtime_events: tuple[CoarseRuntimeEvent, ...] = (),
    normalized_events: tuple[NormalizedRuntimeEvent, ...] = (),
    validator_failures: tuple[CoarseRuntimeEvent, ...] = (),
    stage_metadata_failures: tuple[CoarseRuntimeEvent, ...] = (),
    aidd_exit_code: int | None = None,
    verification_exit_code: int | None = None,
) -> FailureBoundarySelection:
    return _select_failure_boundary(
        runtime_events=runtime_events,
        normalized_events=normalized_events,
        validator_failures=validator_failures,
        stage_metadata_failures=stage_metadata_failures,
        aidd_exit_code=aidd_exit_code,
        verification_exit_code=verification_exit_code,
    )


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
