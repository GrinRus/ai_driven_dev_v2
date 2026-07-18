const SURFACE_ROLLOUT_STATES = new Set(["legacy_only", "candidate", "parity_closed"]);

const SURFACE_PARITY_MANIFEST = Object.freeze([
  {
    id: "guided-setup",
    owner: "W36-E4-S1",
    rollout: "parity_closed",
    rollbackRenderer: "operator-onboarding",
    fixture: "setup",
    journey: "W36-E7-S1-T1",
    removalGate: "W36-E4-S1-T7"
  },
  {
    id: "active-studio",
    owner: "W36-E5-S4",
    rollout: "parity_closed",
    rollbackRenderer: "operator-stage-cockpit",
    fixture: "running",
    journey: "W36-E7-S1-T2",
    removalGate: "W36-E5-S4-T5"
  },
  {
    id: "runtime-validation-recovery",
    owner: "W36-E5-S6",
    rollout: "legacy_only",
    rollbackRenderer: "operator-stage-cockpit",
    fixture: "runtime-failure",
    journey: "W36-E7-S1-T3",
    removalGate: "W36-E5-S6-T6"
  },
  {
    id: "review-qa",
    owner: "W36-E5-S7",
    rollout: "legacy_only",
    rollbackRenderer: "operator-control-center",
    fixture: "qa-decision",
    journey: "W36-E7-S1-T4",
    removalGate: "W36-E5-S7-T5"
  },
  {
    id: "history",
    owner: "W36-E5-S8",
    rollout: "legacy_only",
    rollbackRenderer: "operator-next-flow-view",
    fixture: "history",
    journey: "W36-E7-S1-T5",
    removalGate: "W36-E5-S8-T7"
  },
  {
    id: "question-recovery",
    owner: "W36-E5-S5",
    rollout: "candidate",
    rollbackRenderer: "operator-questions",
    fixture: "blocking-question",
    journey: "W36-E7-S1-T6",
    removalGate: "W36-E5-S5-T5"
  },
  {
    id: "document-evidence",
    owner: "W36-E5-S4",
    rollout: "parity_closed",
    rollbackRenderer: "operator-artifacts-documents",
    fixture: "qa-decision",
    journey: "W36-E7-S1-T7",
    removalGate: "W36-E5-S4-T5"
  },
  {
    id: "flow-complete",
    owner: "W36-E5-S9",
    rollout: "legacy_only",
    rollbackRenderer: "operator-next-flow-view",
    fixture: "terminal-handoff",
    journey: "W36-E7-S1-T8",
    removalGate: "W36-E5-S9-T9"
  },
  {
    id: "implement",
    owner: "W36-E5-S7",
    rollout: "legacy_only",
    rollbackRenderer: "operator-control-center",
    fixture: "implement-task",
    journey: "W36-E7-S1-T9",
    removalGate: "W36-E5-S7-T5"
  },
  {
    id: "intervention-recovery",
    owner: "W36-E5-S5",
    rollout: "candidate",
    rollbackRenderer: "operator-approvals-interventions",
    fixture: "remediation-stale",
    journey: "W36-E7-S1-T10",
    removalGate: "W36-E5-S5-T6"
  },
  {
    id: "approval-recovery",
    owner: "W36-E5-S5",
    rollout: "legacy_only",
    rollbackRenderer: "operator-approvals-interventions",
    fixture: "pending-approval",
    journey: "W36-E7-S1-T11",
    removalGate: "W36-E5-S5-T7"
  },
  {
    id: "inbox",
    owner: "W36-E5-S3",
    rollout: "parity_closed",
    rollbackRenderer: "operator-control-center",
    fixture: "no-run",
    journey: "W36-E7-S1-T12",
    removalGate: "W36-E5-S3-T5"
  }
].map((entry) => Object.freeze(entry)));

function validateSurfaceParityManifest(entries = SURFACE_PARITY_MANIFEST) {
  const ids = new Set();
  for (const entry of entries) {
    if (!entry.id || ids.has(entry.id)) throw new Error(`Duplicate surface owner: ${entry.id}`);
    ids.add(entry.id);
    if (!SURFACE_ROLLOUT_STATES.has(entry.rollout)) {
      throw new Error(`Unsupported rollout state for ${entry.id}: ${entry.rollout}`);
    }
    for (const key of ["owner", "rollbackRenderer", "fixture", "journey", "removalGate"]) {
      if (!String(entry[key] || "").trim()) {
        throw new Error(`Missing ${key} for surface ${entry.id}`);
      }
    }
  }
  return entries;
}

function surfaceParityEntry(surfaceId) {
  return SURFACE_PARITY_MANIFEST.find((entry) => entry.id === surfaceId) || null;
}

validateSurfaceParityManifest();
