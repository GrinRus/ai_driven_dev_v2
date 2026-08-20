"""Provider-free replay support for the Wave 43 failure corpus.

The corpus is a sanitized evidence bundle, not a second validation engine.  This module
only loads the retained case metadata and replays each case through an existing parser or
the existing repair-budget arithmetic so later ownership work can use stable regression
evidence without requiring a provider credential.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aidd.core.interview import (
    InterviewMarkdownParseError,
    parse_answer_entries,
    parse_question_entries,
)
from aidd.core.repair import remaining_repair_attempts, repair_attempts_used
from aidd.core.task_plan import TaskPlanParseError, parse_task_plan
from aidd.validators.protocol import parse_validator_report
from aidd.validators.semantic_rules.placeholders import find_placeholder_occurrences

FAILURE_CORPUS_SCHEMA_VERSION = 1
DEFAULT_FAILURE_CORPUS_ROOT = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "w43-e1-s1-failure-corpus"
)

FailureReplayKind = Literal[
    "interview",
    "service-document",
    "rich-tasklist",
    "validator",
    "repair-budget",
]


class FailureCorpusError(ValueError):
    """Raised when the sanitized corpus is malformed or unsafe to replay."""


@dataclass(frozen=True, slots=True)
class FailureCorpusCase:
    case_id: str
    replay_kind: FailureReplayKind
    runtime: str
    stage: str
    attempt_mode: str
    primary_cause: str
    related_findings: tuple[str, ...]
    first_decisive_boundary: dict[str, object]
    automatic_repair_budget: dict[str, int]
    fixtures: dict[str, str]
    expected_signals: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FailureCorpus:
    schema_version: int
    corpus_id: str
    source: dict[str, object]
    cases: tuple[FailureCorpusCase, ...]
    root: Path


@dataclass(frozen=True, slots=True)
class FailureReplay:
    case_id: str
    observed_signals: tuple[str, ...]
    primary_signal: str
    related_signals: tuple[str, ...]
    repair_attempts_used: int
    remaining_repair_attempts: int
    budget_exhausted: bool


_CASE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]+$")
_UNSAFE_FIXTURE_TEXT = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9]{12,}|ghp_[A-Za-z0-9]{20,}|api[_ -]?key\s*[:=]|authorization\s*:)"
)
_ALLOWED_REPLAY_KINDS = {
    "interview",
    "service-document",
    "rich-tasklist",
    "validator",
    "repair-budget",
}


def _required_string(mapping: dict[str, object], key: str, *, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FailureCorpusError(f"{context}.{key} must be a non-empty string.")
    return value.strip()


def _load_case(raw: object, *, index: int) -> FailureCorpusCase:
    context = f"cases[{index}]"
    if not isinstance(raw, dict):
        raise FailureCorpusError(f"{context} must be an object.")
    case_id = _required_string(raw, "case_id", context=context)
    if _CASE_ID_PATTERN.fullmatch(case_id) is None:
        raise FailureCorpusError(f"{context}.case_id is not a stable lowercase id.")
    replay_kind = _required_string(raw, "replay_kind", context=context)
    if replay_kind not in _ALLOWED_REPLAY_KINDS:
        raise FailureCorpusError(f"{context}.replay_kind is unsupported: {replay_kind!r}.")
    first_boundary = raw.get("first_decisive_boundary")
    if not isinstance(first_boundary, dict):
        raise FailureCorpusError(f"{context}.first_decisive_boundary must be an object.")
    for key in ("category", "signal", "source"):
        _required_string(first_boundary, key, context=f"{context}.first_decisive_boundary")

    budget = raw.get("automatic_repair_budget")
    if not isinstance(budget, dict):
        raise FailureCorpusError(f"{context}.automatic_repair_budget must be an object.")
    normalized_budget: dict[str, int] = {}
    for key in ("max", "consumed"):
        value = budget.get(key)
        if not isinstance(value, int) or value < 0:
            raise FailureCorpusError(
                f"{context}.automatic_repair_budget.{key} must be a non-negative integer."
            )
        normalized_budget[key] = value
    if normalized_budget["consumed"] > normalized_budget["max"]:
        raise FailureCorpusError(f"{context}.automatic_repair_budget.consumed exceeds max.")

    fixtures = raw.get("fixtures")
    if not isinstance(fixtures, dict) or not fixtures:
        raise FailureCorpusError(f"{context}.fixtures must be a non-empty object.")
    normalized_fixtures: dict[str, str] = {}
    for name, path in fixtures.items():
        if not isinstance(name, str) or not isinstance(path, str) or not path.strip():
            raise FailureCorpusError(f"{context}.fixtures entries must be non-empty strings.")
        candidate = Path(path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise FailureCorpusError(f"{context}.fixtures.{name} must stay corpus-relative.")
        normalized_fixtures[name] = candidate.as_posix()

    expected = raw.get("expected_signals")
    if not isinstance(expected, list) or not expected or not all(
        isinstance(item, str) and item.strip() for item in expected
    ):
        raise FailureCorpusError(f"{context}.expected_signals must be a non-empty list.")
    related = raw.get("related_findings", [])
    if not isinstance(related, list) or not all(isinstance(item, str) for item in related):
        raise FailureCorpusError(f"{context}.related_findings must be a string list.")

    return FailureCorpusCase(
        case_id=case_id,
        replay_kind=replay_kind,  # type: ignore[arg-type]
        runtime=_required_string(raw, "runtime", context=context),
        stage=_required_string(raw, "stage", context=context),
        attempt_mode=_required_string(raw, "attempt_mode", context=context),
        primary_cause=_required_string(raw, "primary_cause", context=context),
        related_findings=tuple(item.strip() for item in related if item.strip()),
        first_decisive_boundary=dict(first_boundary),
        automatic_repair_budget=normalized_budget,
        fixtures=normalized_fixtures,
        expected_signals=tuple(item.strip() for item in expected),
    )


def load_failure_corpus(root: Path = DEFAULT_FAILURE_CORPUS_ROOT) -> FailureCorpus:
    """Load and validate the sanitized Wave 43 corpus manifest."""

    manifest_path = root / "failure-corpus.json"
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FailureCorpusError(
            f"Unable to load failure corpus manifest: {manifest_path}"
        ) from error
    if not isinstance(raw, dict):
        raise FailureCorpusError("Failure corpus manifest must be a JSON object.")
    version = raw.get("schema_version")
    if version != FAILURE_CORPUS_SCHEMA_VERSION:
        raise FailureCorpusError(f"Unsupported failure corpus schema version: {version!r}.")
    corpus_id = _required_string(raw, "corpus_id", context="manifest")
    source = raw.get("source")
    if not isinstance(source, dict):
        raise FailureCorpusError("manifest.source must be an object.")
    for key in ("kind", "source_ref"):
        _required_string(source, key, context="manifest.source")
    if source.get("credentials_removed") is not True:
        raise FailureCorpusError("manifest.source.credentials_removed must be true.")
    raw_cases = raw.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise FailureCorpusError("manifest.cases must be a non-empty list.")
    cases = tuple(_load_case(item, index=index) for index, item in enumerate(raw_cases))
    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise FailureCorpusError("Failure corpus case ids must be unique.")
    corpus_root = root.resolve(strict=False)
    for case in cases:
        for fixture in case.fixtures.values():
            path = (corpus_root / fixture).resolve(strict=False)
            if not path.is_relative_to(corpus_root) or not path.is_file():
                raise FailureCorpusError(f"Missing or escaping corpus fixture: {fixture}")
            if _UNSAFE_FIXTURE_TEXT.search(path.read_text(encoding="utf-8")):
                raise FailureCorpusError(f"Potential credential material in fixture: {fixture}")
    return FailureCorpus(
        schema_version=version,
        corpus_id=corpus_id,
        source=dict(source),
        cases=cases,
        root=corpus_root,
    )


def _read_fixture(corpus: FailureCorpus, case: FailureCorpusCase, name: str) -> str:
    try:
        path = corpus.root / case.fixtures[name]
    except KeyError as error:
        raise FailureCorpusError(f"Case {case.case_id} is missing fixture {name!r}.") from error
    return path.read_text(encoding="utf-8")


def replay_failure_case(corpus: FailureCorpus, case: FailureCorpusCase) -> FailureReplay:
    """Replay one retained case using an existing parser or lifecycle calculation."""

    observed: list[str] = []
    if case.replay_kind == "interview":
        for fixture_name, parser, signal in (
            ("questions", parse_question_entries, "INTERVIEW-MALFORMED-DOCUMENT"),
            ("answers", parse_answer_entries, "INTERVIEW-MALFORMED-DOCUMENT"),
        ):
            try:
                parser(_read_fixture(corpus, case, fixture_name))
            except InterviewMarkdownParseError as error:
                observed.append(signal)
                if error.kind == "duplicate-id":
                    observed.append(
                        "CROSS-DUPLICATE-QUESTION-ID"
                        if fixture_name == "questions"
                        else "CROSS-DUPLICATE-ANSWER-ID"
                    )
    elif case.replay_kind == "service-document":
        document = _read_fixture(corpus, case, "document")
        if "Stage not run yet." in document or find_placeholder_occurrences(document):
            observed.append("STRUCT-STALE-STAGE-RESULT-PLACEHOLDER")
    elif case.replay_kind == "rich-tasklist":
        try:
            parse_task_plan(_read_fixture(corpus, case, "tasklist"))
        except TaskPlanParseError:
            observed.append("RICH-TASKLIST-PARSE-ERROR")
    elif case.replay_kind == "validator":
        report = parse_validator_report(_read_fixture(corpus, case, "validator-report"))
        observed.extend(finding.code for finding in report.findings)
    elif case.replay_kind == "repair-budget":
        state = json.loads(_read_fixture(corpus, case, "state"))
        if not isinstance(state, dict):
            raise FailureCorpusError(f"Case {case.case_id} lifecycle state must be an object.")
        budget = case.automatic_repair_budget
        attempt_count = state.get("stage_attempt_count")
        max_repair_attempts = state.get("max_repair_attempts")
        if not isinstance(attempt_count, int) or not isinstance(max_repair_attempts, int):
            raise FailureCorpusError(
                f"Case {case.case_id} lifecycle state must include integer attempt and "
                "budget values."
            )
        if max_repair_attempts != budget["max"]:
            raise FailureCorpusError(
                f"Case {case.case_id} lifecycle budget drifted from its manifest."
            )
        used = repair_attempts_used(stage_attempt_count=attempt_count)
        remaining = remaining_repair_attempts(
            repair_attempts_used=used,
            max_repair_attempts=max_repair_attempts,
        )
        if remaining == 0:
            observed.append("CROSS-REPAIR-BUDGET-EXHAUSTED")
    else:  # pragma: no cover - manifest validation makes this unreachable
        raise FailureCorpusError(f"Unsupported replay kind: {case.replay_kind!r}.")

    unique_observed = tuple(dict.fromkeys(observed))
    missing = set(case.expected_signals) - set(unique_observed)
    if missing:
        raise FailureCorpusError(
            f"Case {case.case_id} replay did not reproduce signals: {', '.join(sorted(missing))}."
        )
    primary = str(case.first_decisive_boundary["signal"])
    if primary not in unique_observed:
        raise FailureCorpusError(
            f"Case {case.case_id} primary boundary {primary!r} was not observed during replay."
        )
    related = tuple(signal for signal in unique_observed if signal != primary)
    budget = case.automatic_repair_budget
    used = budget["consumed"]
    remaining = max(0, budget["max"] - used)
    return FailureReplay(
        case_id=case.case_id,
        observed_signals=unique_observed,
        primary_signal=primary,
        related_signals=related,
        repair_attempts_used=used,
        remaining_repair_attempts=remaining,
        budget_exhausted=remaining == 0,
    )


__all__ = [
    "DEFAULT_FAILURE_CORPUS_ROOT",
    "FAILURE_CORPUS_SCHEMA_VERSION",
    "FailureCorpus",
    "FailureCorpusCase",
    "FailureCorpusError",
    "FailureReplay",
    "load_failure_corpus",
    "replay_failure_case",
]
