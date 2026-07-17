const DECISION_BAR_STATES = new Set([
  "action",
  "pending",
  "blocked",
  "complete",
  "stale",
  "no-action"
]);

function decisionBarState(value) {
  const stateName = String(value || "").trim();
  if (!DECISION_BAR_STATES.has(stateName)) {
    throw new Error(`Unknown decision bar state: ${stateName || "empty"}`);
  }
  return stateName;
}

function renderStatusMarker({status, label}) {
  const stateName = decisionBarState(status);
  const visibleLabel = String(label || "").trim();
  if (!visibleLabel) throw new Error("Status Marker requires visible status text");
  return `
    <span class="status-marker" data-status="${escapeHtml(stateName)}">
      <span class="status-marker-symbol" aria-hidden="true"></span>
      <span>${escapeHtml(visibleLabel)}</span>
    </span>
  `;
}

function renderDecisionBar({
  kind,
  status,
  statusLabel,
  title,
  body,
  guidance = "",
  primaryAction = null,
  metrics = [],
  legacyTone = ""
}) {
  const stateName = decisionBarState(status);
  const action = primaryAction && String(primaryAction.action || "").trim()
    ? primaryAction
    : null;
  const actionSlot = action
    ? `<button class="decision-bar-primary-action" data-decision-action="${escapeHtml(action.action)}" type="button" ${action.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(action.label)}</button>`
    : `<span class="decision-bar-no-action">${escapeHtml(guidance || "No action available")}</span>`;
  const legacyClass = legacyTone ? ` decision-summary ${escapeHtml(legacyTone)}` : "";
  return `
    <section class="decision-bar${legacyClass}" data-decision-bar="${escapeHtml(kind)}" data-state="${escapeHtml(stateName)}" role="status" aria-live="polite">
      <div class="decision-bar-copy decision-summary-copy">
        ${renderStatusMarker({status: stateName, label: statusLabel})}
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(body)}</p>
        <div class="decision-bar-primary-slot" data-primary-slot>${actionSlot}</div>
      </div>
      <div class="decision-bar-supporting decision-summary-metrics">
        ${metrics.map((metric) => {
          const metricClass = metric.tone ? ` ${escapeHtml(metric.tone)}` : "";
          return `
            <div class="decision-metric${metricClass}">
              <span>${escapeHtml(metric.label)}</span>
              <strong>${escapeHtml(metric.value)}</strong>
            </div>
          `;
        }).join("")}
      </div>
    </section>
  `;
}
