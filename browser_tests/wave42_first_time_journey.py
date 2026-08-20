"""Contract and evidence helpers for the Wave 42 first-time operator journey."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

WAVE42_FIRST_TIME_JOURNEY_SCHEMA = "wave42-first-time-operator-journey-v1"
JOURNEY_STEP_IDS = (
    "create",
    "choose-runner",
    "launch",
    "answer-question",
    "resume-session",
)
EnvironmentStatus = Literal["provider-free", "environment-blocked"]
CompletionStatus = Literal["completed", "not-completed", "stopped-for-safety"]
ObservationMode = Literal[
    "scripted-provider-free-rehearsal",
    "uncoached-human-observation",
]


@dataclass(frozen=True, slots=True)
class JourneyStepEvidence:
    step_id: str
    action: str
    outcome: str
    elapsed_ms: int


@dataclass(frozen=True, slots=True)
class FirstTimeJourneyEvidence:
    schema: str
    session_id: str
    observation_mode: ObservationMode
    environment_status: EnvironmentStatus
    completion: CompletionStatus
    elapsed_ms: int
    wrong_actions: int
    first_wrong_action: str | None
    assistance: str
    confidence: int | None
    first_decisive_confusion: str | None
    resulting_tasks: tuple[str, ...]
    default_routing_decision: str
    durable_outcome: str
    steps: tuple[JourneyStepEvidence, ...]


def validate_first_time_journey_evidence(
    evidence: FirstTimeJourneyEvidence,
) -> None:
    """Fail closed when the journey record is incomplete or claims unsupported evidence."""

    assert evidence.schema == WAVE42_FIRST_TIME_JOURNEY_SCHEMA
    assert evidence.session_id.strip()
    assert evidence.observation_mode in {
        "scripted-provider-free-rehearsal",
        "uncoached-human-observation",
    }
    assert evidence.environment_status in {"provider-free", "environment-blocked"}
    assert evidence.completion in {"completed", "not-completed", "stopped-for-safety"}
    assert evidence.elapsed_ms >= 0
    assert evidence.wrong_actions >= 0
    assert evidence.confidence is None or 1 <= evidence.confidence <= 5
    assert evidence.default_routing_decision.strip()
    assert evidence.durable_outcome.strip()
    assert tuple(step.step_id for step in evidence.steps) == JOURNEY_STEP_IDS
    assert all(step.elapsed_ms >= 0 for step in evidence.steps)
    if evidence.environment_status == "environment-blocked":
        # A blocked environment can record why the observation did not happen, but
        # it must never be represented as a completed session or as participant
        # confidence. This keeps an unavailable participant/runtime fail-closed.
        assert evidence.observation_mode == "uncoached-human-observation"
        assert evidence.completion != "completed"
        assert evidence.confidence is None
        assert evidence.durable_outcome.lower().startswith("environment-blocked:")
    elif evidence.observation_mode == "uncoached-human-observation":
        assert evidence.confidence is not None
    else:
        assert evidence.confidence is None
    serialized = json.dumps(asdict(evidence), sort_keys=True).lower()
    for forbidden in ("credential", "provider_token", "random uuid"):
        assert forbidden not in serialized


def environment_blocked_first_time_journey_evidence(
    *,
    session_id: str,
    blocker: str,
    default_routing_decision: str,
) -> FirstTimeJourneyEvidence:
    """Build a sanitized blocker record without inventing human evidence."""

    normalized_blocker = blocker.strip()
    assert normalized_blocker
    steps = tuple(
        JourneyStepEvidence(
            step_id=step_id,
            action="Run the uncoached first-time operator step.",
            outcome=f"not run: environment-blocked ({normalized_blocker})",
            elapsed_ms=0,
        )
        for step_id in JOURNEY_STEP_IDS
    )
    evidence = FirstTimeJourneyEvidence(
        schema=WAVE42_FIRST_TIME_JOURNEY_SCHEMA,
        session_id=session_id,
        observation_mode="uncoached-human-observation",
        environment_status="environment-blocked",
        completion="not-completed",
        elapsed_ms=0,
        wrong_actions=0,
        first_wrong_action=None,
        assistance="none",
        confidence=None,
        first_decisive_confusion=None,
        resulting_tasks=(),
        default_routing_decision=default_routing_decision,
        durable_outcome=f"environment-blocked: {normalized_blocker}",
        steps=steps,
    )
    validate_first_time_journey_evidence(evidence)
    return evidence


def write_first_time_journey_evidence(
    path: Path,
    evidence: FirstTimeJourneyEvidence,
) -> None:
    """Write bounded JSON evidence only after its contract has been validated."""

    validate_first_time_journey_evidence(evidence)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(asdict(evidence), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
