from __future__ import annotations

from dataclasses import dataclass

from aidd.core.stages import STAGES


@dataclass(frozen=True, slots=True)
class SelfRepairProbe:
    stage: str
    probe_id: str
    description: str


SELF_REPAIR_PROBES: tuple[SelfRepairProbe, ...] = (
    SelfRepairProbe(
        stage="idea",
        probe_id="idea-missing-headings",
        description="Missing required headings in idea-stage output documents.",
    ),
    SelfRepairProbe(
        stage="idea",
        probe_id="idea-placeholder-content",
        description="Placeholder semantic content remains in the idea brief.",
    ),
    SelfRepairProbe(
        stage="idea",
        probe_id="idea-blocking-question-mismatch",
        description="Blocking question state conflicts with stage-result status.",
    ),
    SelfRepairProbe(
        stage="research",
        probe_id="research-missing-citations",
        description="Research finding lacks required citation evidence.",
    ),
    SelfRepairProbe(
        stage="research",
        probe_id="research-unsupported-claim",
        description="Research output makes an unsupported implementation claim.",
    ),
    SelfRepairProbe(
        stage="research",
        probe_id="research-resume-malformed-question",
        description="A resumed interview candidate contains a duplicate stable question id.",
    ),
    SelfRepairProbe(
        stage="research",
        probe_id="research-safe-question-candidate",
        description="Safe candidate presentation preserves question meaning and QID order.",
    ),
    SelfRepairProbe(
        stage="plan",
        probe_id="plan-malformed-repair-brief",
        description="Repair control evidence is malformed or model-authored.",
    ),
    SelfRepairProbe(
        stage="plan",
        probe_id="plan-weak-dependencies",
        description="Plan milestones have weak or missing dependency ordering.",
    ),
    SelfRepairProbe(
        stage="plan",
        probe_id="plan-validator-status-mismatch",
        description="Stage result claims pass while canonical validator findings remain.",
    ),
    SelfRepairProbe(
        stage="plan",
        probe_id="plan-service-placeholder",
        description="A service-owned placeholder is mistaken for runtime-authored stage content.",
    ),
    SelfRepairProbe(
        stage="plan",
        probe_id="plan-ownership-conflict",
        description="Contradictory runtime and service drafts cross the ownership boundary.",
    ),
    SelfRepairProbe(
        stage="plan",
        probe_id="plan-root-cause-cascade",
        description="A primary validation finding is retained with its related cascade evidence.",
    ),
    SelfRepairProbe(
        stage="review-spec",
        probe_id="review-spec-sign-off-conflict",
        description="Review spec signs off while required changes remain unresolved.",
    ),
    SelfRepairProbe(
        stage="tasklist",
        probe_id="tasklist-bundled-task",
        description="Task list bundles multiple independently verifiable changes.",
    ),
    SelfRepairProbe(
        stage="tasklist",
        probe_id="tasklist-broken-dependency",
        description="Task dependency reference is missing or points to no task.",
    ),
    SelfRepairProbe(
        stage="tasklist",
        probe_id="tasklist-safe-presentation",
        description="Safe Markdown presentation variants preserve executable task semantics.",
    ),
    SelfRepairProbe(
        stage="tasklist",
        probe_id="tasklist-eleven-malformed-cards",
        description="Eleven malformed cards retain located parse findings and fail closed.",
    ),
    SelfRepairProbe(
        stage="tasklist",
        probe_id="tasklist-one-malformed-card",
        description="A single malformed card retains its root finding and source location.",
    ),
    SelfRepairProbe(
        stage="implement",
        probe_id="implement-unverifiable-touched-files",
        description="Implementation result claims touched files without evidence.",
    ),
    SelfRepairProbe(
        stage="implement",
        probe_id="implement-no-op-without-reason",
        description="Implementation performs no change without an explicit reason.",
    ),
    SelfRepairProbe(
        stage="implement",
        probe_id="implement-resume-non-repair-accounting",
        description=(
            "Interview resume creates a non-repair attempt without consuming repair budget."
        ),
    ),
    SelfRepairProbe(
        stage="review",
        probe_id="review-approval-with-unresolved-must-fix",
        description="Review approves work while a must-fix item remains open.",
    ),
    SelfRepairProbe(
        stage="qa",
        probe_id="qa-ready-without-verification-evidence",
        description="QA declares ready/proceed without verification evidence.",
    ),
)


def probes_for_stage(stage: str) -> tuple[SelfRepairProbe, ...]:
    return tuple(probe for probe in SELF_REPAIR_PROBES if probe.stage == stage)


def validate_probe_catalog() -> None:
    stages_with_probes = {probe.stage for probe in SELF_REPAIR_PROBES}
    missing = [stage for stage in STAGES if stage not in stages_with_probes]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing self-repair probes for stages: {missing_text}")


__all__ = [
    "SELF_REPAIR_PROBES",
    "SelfRepairProbe",
    "probes_for_stage",
    "validate_probe_catalog",
]
