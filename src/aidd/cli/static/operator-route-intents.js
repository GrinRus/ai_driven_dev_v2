const OPERATOR_ROUTE_INTENTS = Object.freeze({
  "inbox-work-item": Object.freeze({label: "Open in Studio", mode: "studio", view: "overview"}),
  "historical-run": Object.freeze({label: "Inspect run history", mode: "history", view: "overview"}),
  "parent-run": Object.freeze({label: "Inspect parent run", mode: "history", view: "overview"}),
  "child-work-item": Object.freeze({label: "Open child work item", mode: "studio", view: "overview"}),
  "run-artifacts": Object.freeze({label: "Inspect run artifacts", mode: "studio", view: "artifacts"})
});

function routeIntentIdentifier(value, field) {
  const normalized = String(value || "").trim();
  if (!OPERATOR_ROUTE_IDENTIFIER.test(normalized) || normalized === "." || normalized === "..") {
    throw new Error(`Route intent requires a safe ${field}`);
  }
  return normalized;
}

function resolveOperatorRouteIntent(intent, context = {}) {
  const definition = OPERATOR_ROUTE_INTENTS[intent];
  if (!definition) throw new Error(`Unknown operator route intent: ${intent || "empty"}`);
  const workItem = routeIntentIdentifier(context.workItem, "work item");
  const needsRun = ["historical-run", "parent-run", "run-artifacts"].includes(intent);
  const acceptsRun = needsRun || intent === "inbox-work-item";
  const runId = acceptsRun && context.runId
    ? routeIntentIdentifier(context.runId, "run id")
    : needsRun
      ? routeIntentIdentifier(context.runId, "run id")
      : "";
  const stage = OPERATOR_ROUTE_STAGES.has(context.stage) ? context.stage : "";
  const artifact = intent === "run-artifacts" && context.artifact
    ? routeIntentIdentifier(context.artifact, "artifact key")
    : "";
  return Object.freeze({
    intent,
    label: definition.label,
    route: Object.freeze({
      mode: definition.mode,
      view: definition.view,
      workItem,
      runId,
      stage,
      attempt: null,
      taskAttempt: null,
      artifact
    })
  });
}

function operatorRouteIntentHref(intent, context = {}) {
  const resolved = resolveOperatorRouteIntent(intent, context);
  return `/${encodeOperatorRoute(resolved.route)}`;
}
