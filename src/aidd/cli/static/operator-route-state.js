const OPERATOR_ROUTE_MODES = new Set(["inbox", "studio", "history"]);
const OPERATOR_ROUTE_VIEWS = new Set(["overview", "recovery", "artifacts", "logs"]);
const OPERATOR_ROUTE_STAGES = new Set([
  "idea",
  "research",
  "plan",
  "review-spec",
  "tasklist",
  "implement",
  "review",
  "qa"
]);
const OPERATOR_ROUTE_IDENTIFIER = /^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,159})$/;

function routeWarning(code, field, value) {
  return Object.freeze({code, field, value: String(value || "")});
}

function routeIdentifier(params, field, warnings) {
  const value = String(params.get(field) || "").trim();
  if (!value) return "";
  if (!OPERATOR_ROUTE_IDENTIFIER.test(value) || value === "." || value === "..") {
    warnings.push(routeWarning("invalid-value", field, value));
    return "";
  }
  return value;
}

function routeAttempt(params, field, warnings) {
  const value = String(params.get(field) || "").trim();
  if (!value) return null;
  if (!/^[1-9][0-9]{0,8}$/.test(value)) {
    warnings.push(routeWarning("invalid-value", field, value));
    return null;
  }
  return Number(value);
}

function inferredLegacyMode(params) {
  const tab = String(params.get("tab") || "").trim();
  if (tab === "history") return "history";
  if (tab || params.has("stage") || params.has("run_id") || params.has("key")) {
    return "studio";
  }
  return "inbox";
}

function inferredLegacyView(params) {
  const tab = String(params.get("tab") || "").trim();
  if (["logs", "artifacts"].includes(tab)) return tab;
  if (tab === "evidence") return "artifacts";
  if (["questions", "validation", "approvals", "request", "recovery"].includes(tab)) {
    return "recovery";
  }
  return "overview";
}

function decodeOperatorRoute(search, {knownWorkItems = null, knownRuns = null} = {}) {
  const params = new URLSearchParams(String(search || "").replace(/^\?/, ""));
  const warnings = [];
  const canonicalMode = String(params.get("mode") || "").trim();
  let mode = canonicalMode || inferredLegacyMode(params);
  const source = canonicalMode ? "canonical" : params.toString() ? "legacy" : "default";
  if (!OPERATOR_ROUTE_MODES.has(mode)) {
    warnings.push(routeWarning("invalid-value", "mode", mode));
    mode = "inbox";
  }
  const requestedView = String(params.get("view") || "").trim();
  let view = requestedView || inferredLegacyView(params);
  if (!OPERATOR_ROUTE_VIEWS.has(view)) {
    warnings.push(routeWarning("invalid-value", "view", view));
    view = "overview";
  }
  let workItem = routeIdentifier(params, "work_item", warnings);
  let runId = routeIdentifier(params, "run_id", warnings);
  let artifact = routeIdentifier(params, "artifact", warnings);
  if (!artifact && params.has("key")) artifact = routeIdentifier(params, "key", warnings);
  const requestedStage = String(params.get("stage") || "").trim();
  let stage = OPERATOR_ROUTE_STAGES.has(requestedStage) ? requestedStage : "";
  if (requestedStage && !stage) {
    warnings.push(routeWarning("invalid-value", "stage", requestedStage));
  }
  let attempt = routeAttempt(params, "attempt", warnings);
  const taskAttempt = routeAttempt(params, "task_attempt", warnings);
  if (attempt !== null && taskAttempt !== null) {
    warnings.push(routeWarning("ambiguous-detail", "attempt", attempt));
    attempt = null;
  }
  if (knownWorkItems && workItem && !knownWorkItems.includes(workItem)) {
    warnings.push(routeWarning("stale-value", "work_item", workItem));
    workItem = "";
    runId = "";
  }
  if (knownRuns && runId && !knownRuns.includes(runId)) {
    warnings.push(routeWarning("stale-value", "run_id", runId));
    runId = "";
  }
  if (mode === "history" && !runId) {
    warnings.push(routeWarning("missing-context", "run_id", ""));
    mode = workItem ? "studio" : "inbox";
  }
  if (mode === "inbox") {
    runId = "";
    stage = "";
    artifact = "";
    attempt = null;
    view = "overview";
  }
  const value = Object.freeze({
    mode,
    view,
    workItem,
    runId,
    stage,
    attempt,
    taskAttempt: mode === "inbox" ? null : taskAttempt,
    artifact
  });
  return Object.freeze({value, warnings: Object.freeze(warnings), source});
}

function encodeOperatorRoute(route) {
  const params = new URLSearchParams();
  const mode = OPERATOR_ROUTE_MODES.has(route?.mode) ? route.mode : "inbox";
  params.set("mode", mode);
  const view = OPERATOR_ROUTE_VIEWS.has(route?.view) ? route.view : "overview";
  if (mode !== "inbox" && view !== "overview") params.set("view", view);
  const fields = [
    ["work_item", OPERATOR_ROUTE_IDENTIFIER.test(route?.workItem || "") ? route.workItem : ""],
    ["run_id", OPERATOR_ROUTE_IDENTIFIER.test(route?.runId || "") ? route.runId : ""],
    ["stage", OPERATOR_ROUTE_STAGES.has(route?.stage) ? route.stage : ""],
    ["attempt", Number.isInteger(route?.attempt) && route.attempt > 0 ? route.attempt : null],
    ["task_attempt", Number.isInteger(route?.taskAttempt) && route.taskAttempt > 0 ? route.taskAttempt : null],
    ["artifact", OPERATOR_ROUTE_IDENTIFIER.test(route?.artifact || "") ? route.artifact : ""]
  ];
  for (const [key, raw] of fields) {
    if (raw === null || raw === undefined || raw === "") continue;
    params.set(key, String(raw));
  }
  return `?${params.toString()}`;
}
