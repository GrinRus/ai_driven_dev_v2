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
