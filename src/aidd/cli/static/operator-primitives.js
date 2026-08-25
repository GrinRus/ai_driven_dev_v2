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
const SHARED_INTERACTION_STATES = Object.freeze([
  "loading",
  "empty",
  "partial",
  "error",
  "disabled",
  "selected",
  "pending",
  "conflict",
  "success",
  "offline",
  "unavailable",
  "reconnecting",
  "permission-denied",
  "focus",
  "keyboard"
]);
const SHARED_INTERACTION_STATE_CONTRACT = Object.freeze({
  loading: Object.freeze({role: "status", live: "polite", busy: true}),
  empty: Object.freeze({role: "status", live: "polite", busy: false}),
  partial: Object.freeze({role: "status", live: "polite", busy: false}),
  error: Object.freeze({role: "alert", live: "assertive", busy: false}),
  disabled: Object.freeze({role: "status", live: "polite", busy: false}),
  selected: Object.freeze({role: "status", live: "polite", busy: false}),
  pending: Object.freeze({role: "status", live: "polite", busy: true}),
  conflict: Object.freeze({role: "alert", live: "assertive", busy: false}),
  success: Object.freeze({role: "status", live: "polite", busy: false}),
  offline: Object.freeze({role: "status", live: "polite", busy: false}),
  unavailable: Object.freeze({role: "status", live: "polite", busy: false}),
  reconnecting: Object.freeze({role: "status", live: "polite", busy: true}),
  "permission-denied": Object.freeze({role: "alert", live: "assertive", busy: false}),
  focus: Object.freeze({role: "status", live: "polite", busy: false}),
  keyboard: Object.freeze({role: "status", live: "polite", busy: false})
});

function sharedInteractionState(value) {
  const stateName = String(value || "").trim();
  if (!SHARED_INTERACTION_STATE_CONTRACT[stateName]) {
    throw new Error(`Unknown shared interaction state: ${stateName || "empty"}`);
  }
  return stateName;
}

function validateSharedInteractionContract({
  state,
  accessibleName,
  statusText,
  primaryActionCount = 0,
  statusUsesColorOnly = false,
  clipped = false,
  focusLost = false
} = {}) {
  const stateName = sharedInteractionState(state);
  if (!String(accessibleName || "").trim()) {
    throw new Error("Shared interaction surface requires an accessible name");
  }
  if (!String(statusText || "").trim()) {
    throw new Error("Shared interaction surface requires visible status text");
  }
  if (primaryActionCount > 1) {
    throw new Error("Shared interaction surface allows one primary action");
  }
  if (statusUsesColorOnly) {
    throw new Error("Shared interaction status requires text, not color alone");
  }
  if (clipped) {
    throw new Error("Shared interaction labels must fit their rendered bounds");
  }
  if (focusLost) {
    throw new Error("Shared interaction surface must preserve focus");
  }
  return Object.freeze({
    state: stateName,
    ...SHARED_INTERACTION_STATE_CONTRACT[stateName]
  });
}

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
      <span data-status-text>${escapeHtml(visibleLabel)}</span>
    </span>
  `;
}

function renderPrimaryActionSlot({primaryAction = null, guidance = ""} = {}) {
  const action = primaryAction && String(primaryAction.action || "").trim()
    ? primaryAction
    : null;
  const content = action
    ? `<button class="decision-bar-primary-action" data-primary-action data-decision-action="${escapeHtml(action.action)}" type="button" ${action.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(action.label)}</button>`
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
  const sharedState = {
    action: "selected",
    "no-action": "disabled",
    pending: "pending",
    blocked: "error",
    complete: "success",
    stale: "conflict"
  }[stateName];
  validateSharedInteractionContract({
    state: sharedState,
    accessibleName: title,
    statusText: statusLabel,
    primaryActionCount: primaryAction ? 1 : 0
  });
  const legacyClass = legacyTone ? ` decision-summary ${escapeHtml(legacyTone)}` : "";
  return `
    <section class="decision-bar${legacyClass}" data-decision-bar="${escapeHtml(kind)}" data-state="${escapeHtml(stateName)}" data-interaction-region role="status" aria-live="polite">
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
  if (!STATE_SURFACE_STATES.has(stateName) && !SHARED_INTERACTION_STATE_CONTRACT[stateName]) {
    throw new Error(`Unknown state surface: ${stateName || "empty"}`);
  }
  const visibleTitle = String(title || "").trim();
  const visibleConsequence = String(consequence || "").trim();
  if (!visibleTitle || !visibleConsequence) {
    throw new Error("State surface requires a title and consequence");
  }
  const contract = validateSharedInteractionContract({
    state: stateName === "unavailable" ? "unavailable" : stateName,
    accessibleName: visibleTitle,
    statusText: stateName
  });
  const waiting = contract.busy;
  const role = contract.role;
  const live = contract.live;
  const recoveryAction = recovery && String(recovery.action || "").trim()
    ? `<button data-state-recovery="${escapeHtml(recovery.action)}" type="button" ${recovery.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(recovery.label)}</button>`
    : "";
  return `
    <section class="state-surface" data-state-surface="${escapeHtml(kind)}" data-state="${escapeHtml(stateName)}" data-interaction-region role="${role}" aria-live="${live}" aria-busy="${waiting ? "true" : "false"}"
      data-interaction-contract="shared-v1">
      <div class="state-surface-copy">
        ${renderStatusMarker({status: stateName === "error" || stateName === "conflict" || stateName === "permission-denied" ? "blocked" : waiting ? "pending" : "no-action", label: stateName})}
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
  primaryAction,
  showPrimary = true
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
  const recoveryStage = primaryAction.stage
    ? ` data-recovery-stage="${escapeHtml(primaryAction.stage)}"`
    : "";
  const repairExtension = primaryAction.action === "repair-extension"
    ? " data-repair-extension"
    : "";
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
      ${showPrimary
        ? `<div class="recovery-summary-primary" data-primary-recovery-slot>
        <button data-primary-action data-recovery-action="${escapeHtml(primaryAction.action)}"${recoveryStage}${repairExtension} type="button" ${primaryAction.enabled === false ? 'disabled aria-disabled="true"' : ""}>${escapeHtml(primaryAction.label)}</button>
      </div>`
        : `<div class="recovery-summary-primary recovery-summary-primary-readonly" data-recovery-primary-readonly><span>Action is available in the recovery decision panel above.</span></div>`}
    </section>
  `;
}
