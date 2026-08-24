const SURFACE_ROLLOUT_STATES = new Set(["parity_closed"]);

const SURFACE_PARITY_MANIFEST = Object.freeze([
  {
    id: "guided-setup",
    owner: "W36-E4-S1",
    rollout: "parity_closed",
    fixture: "setup",
    journey: "W36-E7-S1-T1",
    removalGate: "W36-E4-S1-T7"
  },
  {
    id: "active-studio",
    owner: "W36-E5-S4",
    rollout: "parity_closed",
    fixture: "running",
    journey: "W36-E7-S1-T2",
    removalGate: "W36-E5-S4-T5"
  },
  {
    id: "runtime-validation-recovery",
    owner: "W36-E5-S6",
    rollout: "parity_closed",
    fixture: "runtime-failure",
    journey: "W36-E7-S1-T3",
    removalGate: "W36-E5-S6-T6"
  },
  {
    id: "review-qa",
    owner: "W36-E5-S7",
    rollout: "parity_closed",
    fixture: "qa-decision",
    journey: "W36-E7-S1-T4",
    removalGate: "W36-E5-S7-T5"
  },
  {
    id: "history",
    owner: "W36-E5-S8",
    rollout: "parity_closed",
    fixture: "history",
    journey: "W36-E7-S1-T5",
    removalGate: "W36-E5-S8-T7"
  },
  {
    id: "question-recovery",
    owner: "W36-E5-S5",
    rollout: "parity_closed",
    fixture: "blocking-question",
    journey: "W36-E7-S1-T6",
    removalGate: "W36-E5-S5-T5"
  },
  {
    id: "document-evidence",
    owner: "W36-E5-S4",
    rollout: "parity_closed",
    fixture: "qa-decision",
    journey: "W36-E7-S1-T7",
    removalGate: "W36-E5-S4-T5"
  },
  {
    id: "flow-complete",
    owner: "W36-E5-S9",
    rollout: "parity_closed",
    fixture: "terminal-handoff",
    journey: "W36-E7-S1-T8",
    removalGate: "W36-E5-S9-T9"
  },
  {
    id: "implement",
    owner: "W36-E5-S7",
    rollout: "parity_closed",
    fixture: "implement-task",
    journey: "W36-E7-S1-T9",
    removalGate: "W36-E5-S7-T5"
  },
  {
    id: "intervention-recovery",
    owner: "W36-E5-S5",
    rollout: "parity_closed",
    fixture: "remediation-stale",
    journey: "W36-E7-S1-T10",
    removalGate: "W36-E5-S5-T6"
  },
  {
    id: "approval-recovery",
    owner: "W36-E5-S5",
    rollout: "parity_closed",
    fixture: "pending-approval",
    journey: "W36-E7-S1-T11",
    removalGate: "W36-E5-S5-T7"
  },
  {
    id: "inbox",
    owner: "W36-E5-S3",
    rollout: "parity_closed",
    fixture: "no-run",
    journey: "W36-E7-S1-T12",
    removalGate: "W36-E5-S3-T5"
  }
].map((entry) => Object.freeze(entry)));

// Wave 42 acceptance uses a separate fixture registry so the historical Wave 36
// packaged-browser journey ids remain stable. Each target reference resolves to
// a deterministic local route and one synthetic state fixture; no entry may
// imply provider credentials, wall-clock state, or generated identifiers.
const PROVIDER_FREE_ROUTE_MANIFEST = Object.freeze([
  {
    id: "project-work-items",
    target: "01-project-work-items.png",
    fixture: "no-run",
    route: "?mode=inbox",
    routeIntent: "inbox",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER"}
  },
  {
    id: "create-work-item",
    target: "02-create-work-item.png",
    fixture: "setup",
    route: "?ui=studio",
    routeIntent: "setup",
    viewport: "1280x900",
    context: {project: "."}
  },
  {
    id: "work-item-launch",
    target: "03-work-item-launch.png",
    fixture: "no-run",
    route: "?mode=studio&work_item=WI-BROWSER&view=overview",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER"}
  },
  {
    id: "task-workspace",
    target: "04-task-workspace.png",
    fixture: "implementation-task-ready",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=implement&work_tab=tasks&task_id=TL-2",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "implement"}
  },
  {
    id: "active-task-run",
    target: "05-active-task-run.png",
    fixture: "running",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=idea&attempt=1",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "idea", attempt: 1}
  },
  {
    id: "decision-workbench",
    target: "06-decision-workbench.png",
    fixture: "blocking-question",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=idea&view=recovery",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "idea", recovery_target: "questions"}
  },
  {
    id: "validation-repair",
    target: "07-validation-repair.png",
    fixture: "validation-repair",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=plan&view=recovery",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "plan", recovery_target: "validation"}
  },
  {
    id: "markdown-workspace",
    target: "08-markdown-workspace.png",
    fixture: "qa-decision",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=qa&view=artifacts",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "qa", document: "qa-report.md"}
  },
  {
    id: "implementation-review",
    target: "09-implementation-review.png",
    fixture: "implementation-finalized",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=implement",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "implement", document: "implementation-report.md"}
  },
  {
    id: "review-qa-remediation",
    target: "10-review-qa-remediation.png",
    fixture: "review-qa-rejected",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=review&view=recovery",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "review", recovery_target: "remediation"}
  },
  {
    id: "run-history",
    target: "11-run-history.png",
    fixture: "history",
    route: "?mode=history&work_item=WI-BROWSER&run_id=run-browser&stage=implement",
    routeIntent: "history",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "implement", history_frame: "attempt-0001"}
  },
  {
    id: "flow-complete",
    target: "12-flow-complete.png",
    fixture: "terminal-handoff",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=qa",
    routeIntent: "studio",
    viewport: "1280x900",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "qa"}
  },
  {
    id: "mobile-decision",
    target: "13-mobile-decision.png",
    fixture: "blocking-question",
    route: "?mode=studio&work_item=WI-BROWSER&run_id=run-browser&stage=idea&view=recovery",
    routeIntent: "studio",
    viewport: "390x844",
    context: {project: ".", work_item: "WI-BROWSER", run: "run-browser", stage: "idea", recovery_target: "questions"}
  }
].map((entry) => Object.freeze({
  ...entry,
  context: Object.freeze(entry.context),
  provider: "local",
  requiresLiveProvider: false,
  credentialMode: "none",
  clockMode: "fixed",
  idMode: "deterministic"
})));

const PROVIDER_FREE_FIXTURES = new Set([
  "no-run",
  "setup",
  "implementation-finalized",
  "implementation-task-ready",
  "running",
  "blocking-question",
  "validation-repair",
  "review-qa-rejected",
  "qa-decision",
  "remediation-stale",
  "history",
  "terminal-handoff"
]);
const PROVIDER_FREE_ROUTE_INTENTS = new Set(["setup", "inbox", "studio", "history"]);
const PROVIDER_FREE_IDENTIFIER = /^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,159})$/;

function validateProviderFreeRouteManifest(entries = PROVIDER_FREE_ROUTE_MANIFEST) {
  const ids = new Set();
  const targets = new Set();
  for (const entry of entries) {
    if (!entry.id || ids.has(entry.id)) throw new Error(`Duplicate provider-free route: ${entry.id}`);
    ids.add(entry.id);
    if (!entry.target || targets.has(entry.target) || !/^\d{2}-[a-z0-9-]+\.png$/.test(entry.target)) {
      throw new Error(`Invalid provider-free target filename: ${entry.target || "empty"}`);
    }
    targets.add(entry.target);
    if (!PROVIDER_FREE_FIXTURES.has(entry.fixture)) {
      throw new Error(`Unknown provider-free fixture for ${entry.id}: ${entry.fixture}`);
    }
    if (!String(entry.route || "").startsWith("?") || String(entry.route).includes("http")) {
      throw new Error(`Provider-free route must be a local query: ${entry.id}`);
    }
    if (!PROVIDER_FREE_ROUTE_INTENTS.has(entry.routeIntent)) {
      throw new Error(`Unknown provider-free route intent for ${entry.id}: ${entry.routeIntent}`);
    }
    if (entry.provider !== "local" || entry.requiresLiveProvider !== false
      || entry.credentialMode !== "none" || entry.clockMode !== "fixed" || entry.idMode !== "deterministic") {
      throw new Error(`Provider-free policy violation for ${entry.id}`);
    }
    if (!/^\d{3,4}x\d{3,4}$/.test(entry.viewport)) {
      throw new Error(`Invalid provider-free viewport for ${entry.id}`);
    }
    for (const [key, value] of Object.entries(entry.context || {})) {
      if (["work_item", "run", "stage", "document", "recovery_target", "history_frame"].includes(key)
        && (!PROVIDER_FREE_IDENTIFIER.test(String(value)) || /random|timestamp|Date|Math/.test(String(value)))) {
        throw new Error(`Non-deterministic provider-free context for ${entry.id}: ${key}`);
      }
    }
  }
  if (entries.length !== 13) throw new Error(`Expected 13 provider-free routes, got ${entries.length}`);
  return entries;
}

validateProviderFreeRouteManifest();

function validateSurfaceParityManifest(entries = SURFACE_PARITY_MANIFEST) {
  const ids = new Set();
  for (const entry of entries) {
    if (!entry.id || ids.has(entry.id)) throw new Error(`Duplicate surface owner: ${entry.id}`);
    ids.add(entry.id);
    if (!SURFACE_ROLLOUT_STATES.has(entry.rollout)) {
      throw new Error(`Unsupported rollout state for ${entry.id}: ${entry.rollout}`);
    }
    for (const key of ["owner", "fixture", "journey", "removalGate"]) {
      if (!String(entry[key] || "").trim()) {
        throw new Error(`Missing ${key} for surface ${entry.id}`);
      }
    }
  }
  return entries;
}

validateSurfaceParityManifest();
