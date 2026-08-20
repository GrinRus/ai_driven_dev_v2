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
    observation_mode: str
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
    assert evidence.observation_mode == "scripted-provider-free-rehearsal" or (
        evidence.confidence is not None
    )
    serialized = json.dumps(asdict(evidence), sort_keys=True).lower()
    for forbidden in ("credential", "provider_token", "random uuid"):
        assert forbidden not in serialized


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
