const DECISION_BAR_STATES = new Set([
  "action",
  "pending",
  "blocked",
  "complete",
  "stale",
  "no-action"
]);
const STATE_SURFACE_STATES = new Set([
  "empty",
  "loading",
  "error",
  "reconnecting",
  "unavailable"
]);
const INBOX_ITEM_STATES = new Set([
  "blocking",
  "running",
  "ready",
  "terminal",
  "malformed"
]);
const GUIDED_STEP_STATES = new Set([
  "current",
  "complete",
  "invalid",
  "optional",
  "disabled"
]);
const RECOVERY_SUMMARY_KINDS = new Set([
  "question",
  "approval",
  "runtime",
  "validation",
  "intervention",
  "quality-gate"
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

function renderPrimaryActionSlot({primaryAction = null, guidance = ""} = {}) {
  const action = primaryAction && String(primaryAction.action || "").trim()
    ? primaryAction
    : null;
  const content = action
    ? `<button class="decision-bar-primary-action" data-decision-action="${escapeHtml(action.action)}" type="button" ${action.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(action.label)}</button>`
    : `<span class="decision-bar-no-action">${escapeHtml(guidance || "No action available")}</span>`;
  return `<div class="decision-bar-primary-slot" data-primary-slot>${content}</div>`;
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
  const legacyClass = legacyTone ? ` decision-summary ${escapeHtml(legacyTone)}` : "";
  return `
    <section class="decision-bar${legacyClass}" data-decision-bar="${escapeHtml(kind)}" data-state="${escapeHtml(stateName)}" role="status" aria-live="polite">
      <div class="decision-bar-copy decision-summary-copy">
        ${renderStatusMarker({status: stateName, label: statusLabel})}
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(body)}</p>
        ${renderPrimaryActionSlot({primaryAction, guidance})}
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

function renderStateSurface({kind, state: requestedState, title, consequence, recovery = null}) {
  const stateName = String(requestedState || "").trim();
  if (!STATE_SURFACE_STATES.has(stateName)) {
    throw new Error(`Unknown state surface: ${stateName || "empty"}`);
  }
  const visibleTitle = String(title || "").trim();
  const visibleConsequence = String(consequence || "").trim();
  if (!visibleTitle || !visibleConsequence) {
    throw new Error("State surface requires a title and consequence");
  }
  const waiting = stateName === "loading" || stateName === "reconnecting";
  const role = stateName === "error" ? "alert" : "status";
  const live = stateName === "error" ? "assertive" : "polite";
  const recoveryAction = recovery && String(recovery.action || "").trim()
    ? `<button data-state-recovery="${escapeHtml(recovery.action)}" type="button" ${recovery.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(recovery.label)}</button>`
    : "";
  return `
    <section class="state-surface" data-state-surface="${escapeHtml(kind)}" data-state="${escapeHtml(stateName)}" role="${role}" aria-live="${live}" aria-busy="${waiting ? "true" : "false"}">
      <div class="state-surface-copy">
        ${renderStatusMarker({status: stateName === "error" ? "blocked" : waiting ? "pending" : "no-action", label: stateName})}
        <strong>${escapeHtml(visibleTitle)}</strong>
        <p>${escapeHtml(visibleConsequence)}</p>
      </div>
      ${recoveryAction ? `<div class="state-surface-action">${recoveryAction}</div>` : ""}
    </section>
  `;
}

function renderInboxItem({
  id,
  state: requestedState,
  statusLabel,
  title,
  summary,
  route = "",
  primaryAction = null,
  metadata = []
}) {
  const stateName = String(requestedState || "").trim();
  if (!INBOX_ITEM_STATES.has(stateName)) {
    throw new Error(`Unknown Inbox Item state: ${stateName || "empty"}`);
  }
  const markerStatus = {
    blocking: "blocked",
    running: "pending",
    ready: "action",
    terminal: "complete",
    malformed: "stale"
  }[stateName];
  const action = primaryAction && String(primaryAction.action || "").trim()
    ? primaryAction
    : null;
  return `
    <article class="inbox-item" data-inbox-item="${escapeHtml(id)}" data-state="${escapeHtml(stateName)}" data-inbox-route="${escapeHtml(route)}">
      <div class="inbox-item-copy">
        ${renderStatusMarker({status: markerStatus, label: statusLabel})}
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(summary)}</p>
        ${metadata.length ? `<dl>${metadata.map((entry) => `<div><dt>${escapeHtml(entry.label)}</dt><dd>${escapeHtml(entry.value)}</dd></div>`).join("")}</dl>` : ""}
      </div>
      <div class="inbox-item-action">
        ${action ? `<button data-inbox-action="${escapeHtml(action.action)}" type="button" ${action.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(action.label)}</button>` : '<span class="inbox-item-no-action">No action available</span>'}
      </div>
    </article>
  `;
}

function renderGuidedField(stepId, field) {
  const fieldId = `guided-${stepId}-${field.id}`;
  if (field.type === "select") {
    return `
      <label for="${escapeHtml(fieldId)}">${escapeHtml(field.label)}</label>
      <select id="${escapeHtml(fieldId)}" name="${escapeHtml(field.id)}">
        ${(field.options || []).map((option) => `<option value="${escapeHtml(option.value)}" ${option.value === field.value ? "selected" : ""}>${escapeHtml(option.label)}</option>`).join("")}
      </select>
    `;
  }
  return `
    <label for="${escapeHtml(fieldId)}">${escapeHtml(field.label)}</label>
    <input id="${escapeHtml(fieldId)}" name="${escapeHtml(field.id)}" type="${escapeHtml(field.type || "text")}" value="${escapeHtml(field.value || "")}" ${field.invalid ? 'aria-invalid="true"' : ""}>
  `;
}

function renderGuidedStep({
  id,
  state: requestedState,
  title,
  explanation,
  fields,
  primaryAction,
  backAction,
  advanced = []
}) {
  const stateName = String(requestedState || "").trim();
  if (!GUIDED_STEP_STATES.has(stateName)) {
    throw new Error(`Unknown Guided Step state: ${stateName || "empty"}`);
  }
  if (!primaryAction?.action || !backAction?.action) {
    throw new Error("Guided Step requires explicit primary and Back actions");
  }
  return `
    <section class="guided-step" data-guided-step="${escapeHtml(id)}" data-state="${escapeHtml(stateName)}">
      <header class="guided-step-header">
        ${renderStatusMarker({status: stateName === "complete" ? "complete" : stateName === "invalid" ? "blocked" : stateName === "disabled" ? "no-action" : "action", label: stateName})}
        <h2>${escapeHtml(title)}</h2>
        <p>${escapeHtml(explanation)}</p>
      </header>
      <div class="guided-step-inputs">
        ${(fields || []).map((field) => `<div class="guided-step-field">${renderGuidedField(id, field)}</div>`).join("")}
      </div>
      <div class="guided-step-actions">
        <button class="secondary" data-guided-action="${escapeHtml(backAction.action)}" type="button" ${backAction.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(backAction.label || "Back")}</button>
        <button data-guided-action="${escapeHtml(primaryAction.action)}" type="button" ${primaryAction.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(primaryAction.label)}</button>
      </div>
      <details class="guided-step-advanced">
        <summary>Advanced</summary>
        <div>${advanced.map((item) => `<p>${escapeHtml(item)}</p>`).join("") || "<p>No advanced settings for this step.</p>"}</div>
      </details>
    </section>
  `;
}

function renderRecoverySummary({
  kind: requestedKind,
  status,
  statusLabel,
  title,
  consequence,
  decisiveFailure,
  evidence,
  primaryAction
}) {
  const kind = String(requestedKind || "").trim();
  if (!RECOVERY_SUMMARY_KINDS.has(kind)) {
    throw new Error(`Unknown Recovery Summary kind: ${kind || "empty"}`);
  }
  if (!decisiveFailure?.label || !decisiveFailure?.detail) {
    throw new Error("Recovery Summary requires one decisive failure");
  }
  if (!evidence?.path) throw new Error("Recovery Summary requires one evidence path");
  if (!primaryAction?.action || !primaryAction?.label) {
    throw new Error("Recovery Summary requires one primary recovery action");
  }
  return `
    <section class="decision-bar recovery-summary" data-decision-bar="recovery" data-recovery-summary="${escapeHtml(kind)}">
      <header class="recovery-summary-header">
        ${renderStatusMarker({status, label: statusLabel})}
        <h2>${escapeHtml(title)}</h2>
        <p>${escapeHtml(consequence)}</p>
      </header>
      <div class="recovery-summary-failure" data-decisive-failure>
        <span>${escapeHtml(decisiveFailure.label)}</span>
        <strong>${escapeHtml(decisiveFailure.detail)}</strong>
      </div>
      <div class="recovery-summary-evidence" data-evidence-path="${escapeHtml(evidence.path)}">
        <span>${escapeHtml(evidence.label || "Evidence")}</span>
        <code>${escapeHtml(evidence.path)}</code>
        <button class="secondary" data-tab-shortcut="evidence" type="button">Open Evidence</button>
      </div>
      <div class="recovery-summary-primary" data-primary-recovery-slot>
        <button data-recovery-action="${escapeHtml(primaryAction.action)}" type="button" ${primaryAction.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(primaryAction.label)}</button>
      </div>
    </section>
  `;
}
