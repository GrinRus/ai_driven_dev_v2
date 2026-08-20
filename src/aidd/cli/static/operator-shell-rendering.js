function renderRuntimeSelector() {
  const settings = document.getElementById("runtimeSettings");
  const readOnlyHistory = state.activeTab === "history" || state.workDetail === "runs";
  const terminalHandoff = Boolean(state.dashboard?.terminal_handoff);
  const readOnlySurface = readOnlyHistory || terminalHandoff;
  if (settings) settings.hidden = readOnlySurface;
  if (readOnlySurface) return;
  if (settings && !settings.dataset.initialized) {
    settings.open = false;
    settings.dataset.initialized = "true";
  }
  const select = document.getElementById("runtimeSelect");
  const runtimes = state.readinessLoading ? [] : (state.readiness?.runtimes || []);
  const runtimeIds = runtimes.map((runtime) => String(runtime.runtime_id || ""));
  const options = [
    `<option value="">${state.readinessLoading ? "Checking runtimes..." : "Select runtime"}</option>`
  ];
  if (state.selectedRuntime && !runtimeIds.includes(state.selectedRuntime)) {
    const label = state.readinessLoading
      ? "checking"
      : state.readinessError
        ? "unverified"
        : "not listed";
    options.push(
      `<option value="${escapeHtml(state.selectedRuntime)}" selected>${escapeHtml(state.selectedRuntime)} (${label})</option>`
    );
  }
  select.innerHTML = [
    ...options,
    ...runtimes.map((runtime) => {
      const runtimeId = String(runtime.runtime_id || "");
      const selected = runtimeId === state.selectedRuntime ? " selected" : "";
      const binary = runtime.binary?.status || "unknown";
      const command = runtime.execution_command?.status || "unknown";
      const label = `binary ${binary}; command ${command}`;
      return `<option value="${escapeHtml(runtimeId)}"${selected}>${escapeHtml(runtimeId)} (${label})</option>`;
    })
  ].join("");
  const selected = runtimes.find((runtime) => String(runtime.runtime_id || "") === state.selectedRuntime);
  if (state.runtimeSelectionRuntime !== state.selectedRuntime) {
    state.runtimeSelectionRuntime = state.selectedRuntime;
    state.runtimeModel = String(selected?.configured_model || "");
    state.runtimeReasoningEffort = String(selected?.configured_reasoning_effort || "");
    state.runtimeModelDirty = false;
    state.runtimeReasoningEffortDirty = false;
  }
  const supportedSelectors = new Set(selected?.capabilities?.supported_selectors || []);
  const modelInput = document.getElementById("runtimeModelInput");
  const effortInput = document.getElementById("runtimeReasoningEffortInput");
  if (modelInput) {
    modelInput.value = state.runtimeModel;
    modelInput.disabled = !supportedSelectors.has("model");
    modelInput.title = modelInput.disabled
      ? "The selected runtime does not advertise model selection."
      : "Optional runtime model override; blank keeps the configured/native default.";
  }
  if (effortInput) {
    effortInput.value = state.runtimeReasoningEffort;
    effortInput.disabled = !supportedSelectors.has("reasoning_effort");
    effortInput.title = effortInput.disabled
      ? "The selected runtime does not advertise reasoning effort selection."
      : "Optional runtime reasoning effort override; blank keeps the configured/native default.";
  }
  setRunButtonState();
}

function renderWorkItemTabs() {
  const host = document.getElementById("workItemTabs");
  if (!host) return;
  const isInbox = state.activeTab === "work" && state.workDetail === "project-home";
  const hasWorkItem = Boolean(state.dashboard?.work_item || state.activeRouteWorkItem);
  if (isInbox || !hasWorkItem) {
    host.replaceChildren();
    host.hidden = true;
    return;
  }
  host.hidden = false;
  const active = normalizeWorkItemTab(state.workItemTab);
  host.innerHTML = `
    <div class="work-item-tabs-list" role="tablist" aria-label="Work Item sections">
      ${WORK_ITEM_TABS.map((tab) => `
        <button
          class="work-item-tab${tab === active ? " active" : ""}"
          data-work-item-tab="${escapeHtml(tab)}"
          role="tab"
          type="button"
          aria-selected="${tab === active ? "true" : "false"}"
          aria-controls="intentContent"
          tabindex="${tab === active ? "0" : "-1"}">
          ${escapeHtml(WORK_ITEM_TAB_LABELS[tab])}
        </button>
      `).join("")}
    </div>
  `;
}

function runtimeSelectorPayload() {
  const runtime = selectedRuntimeView();
  const supported = new Set(runtime?.capabilities?.supported_selectors || []);
  const payload = {};
  if (runtime && Object.prototype.hasOwnProperty.call(runtime, "eligible")) {
    payload.require_runtime_revalidation = true;
    if (runtime.config_identity) payload.readiness_config_identity = runtime.config_identity;
    if (runtime.probe_observed_at_utc) {
      payload.readiness_probe_observed_at_utc = runtime.probe_observed_at_utc;
    }
  }
  const model = String(state.runtimeModel || "").trim();
  const reasoningEffort = String(state.runtimeReasoningEffort || "").trim();
  if (state.runtimeModelDirty && model && supported.has("model")) payload.model = model;
  if (state.runtimeReasoningEffortDirty && reasoningEffort && supported.has("reasoning_effort")) {
    payload.reasoning_effort = reasoningEffort;
  }
  return payload;
}

function scrollActiveStageIntoView() {
  const rail = document.getElementById("intentPhaseStepper")?.querySelector(".intent-phase-list");
  if (!rail || !window.matchMedia("(max-width: 760px)").matches) return;
  if (document.body.classList.contains("terminal-handoff-mode")) return;
  if (document.body.classList.contains("terminal-repair-mode")) return;
  if (document.body.classList.contains("post-stage-next-action-mode")) return;
  const active = rail.querySelector(`[data-stage="${CSS.escape(state.activeStage)}"]`);
  if (!active || rail.scrollWidth <= rail.clientWidth) return;
  const left = active.offsetLeft - (rail.clientWidth - active.clientWidth) / 2;
  rail.scrollTo({behavior: "auto", left: Math.max(0, left)});
}

function selectedRuntimeView() {
  if (state.readinessLoading) return null;
  return (state.readiness?.runtimes || []).find((runtime) => runtime.runtime_id === state.selectedRuntime) || null;
}

function focusRuntimeSelector() {
  const settings = document.getElementById("runtimeSettings");
  if (settings) settings.open = true;
  document.getElementById("runtimeSelect")?.focus();
}

function selectedRuntimeReady() {
  const runtime = selectedRuntimeView();
  if (!runtime) return false;
  if (Object.prototype.hasOwnProperty.call(runtime, "eligible")) {
    return runtime.eligible === true;
  }
  // Compatibility with pre-readiness payloads retained by older browser fixtures.
  return Boolean(runtime.provider_available && runtime.execution_command_available);
}

function runtimeReadinessMessage() {
  if (!state.selectedRuntime) return "Select a runtime before this action can run.";
  if (state.readinessLoading) return "Checking runtime readiness before this action can run.";
  if (state.readinessError) return `Runtime readiness unavailable: ${state.readinessError}`;
  if (!selectedRuntimeReady()) {
    return String(selectedRuntimeView()?.disabled_reason || "Selected runtime is not ready for execution.");
  }
  return "";
}

function renderContextualRunnerControl({actionLabel = "launch"} = {}) {
  const runtime = selectedRuntimeView();
  const runtimeLabel = state.selectedRuntime || "no Runner selected";
  const ready = selectedRuntimeReady();
  const reason = state.readinessLoading
    ? "Checking current readiness evidence."
    : state.readinessError
      ? `Readiness unavailable: ${state.readinessError}`
      : ready
        ? `Eligible for ${actionLabel}.`
        : runtime?.disabled_reason || "Choose an eligible Runner before this action.";
  return `
    <div class="contextual-runner-control" data-contextual-runner-control data-runner-eligible="${ready ? "true" : "false"}">
      <div class="contextual-runner-copy">
        <span class="eyebrow">Runner</span>
        <strong>${escapeHtml(runtimeLabel)}</strong>
        <span>${escapeHtml(reason)}</span>
      </div>
      <button class="secondary" data-open-runner type="button">${state.selectedRuntime ? "Change Runner" : "Choose Runner"}</button>
    </div>
  `;
}

function readinessBoolean(value) {
  if (value === true) return "yes";
  if (value === false) return "no";
  return "unknown";
}

function runtimeCapabilitySummary(runtime) {
  const capabilities = runtime?.capabilities || {};
  if (capabilities.status !== "known") return "unknown";
  return [
    `transport ${readinessText(capabilities.preferred_transport, "unknown")}`,
    `raw logs ${readinessBoolean(capabilities.supports_raw_log_stream)}`,
    `questions ${readinessBoolean(capabilities.supports_questions)}`,
    `permission policy ${readinessBoolean(capabilities.supports_permission_policy)}`,
    `live decisions ${readinessBoolean(capabilities.supports_live_decisions)}`
  ].join("; ");
}

function runtimeLatestLaunchSummary(runtime) {
  const launch = runtime?.latest_launch;
  if (!launch) return "No canonical launch evidence recorded";
  return `${launch.outcome} / ${launch.recorded_at_utc || "timestamp unavailable"} / ${launch.stage} attempt ${launch.attempt_number}`;
}

function renderRuntimeReadinessDimensions(runtime, {compact = false} = {}) {
  if (!runtime) return "";
  const binary = runtime.binary || {status: "unknown"};
  const command = runtime.execution_command || {status: "unknown", source: "default"};
  const authentication = runtime.authentication || {status: "unverified"};
  const rows = [
    ["Binary", `${binary.status}${binary.version ? ` / ${binary.version}` : ""}`],
    ["Execution command", `${command.status} / ${command.source || "unknown source"}`],
    ["Authentication evidence", `${authentication.status}${authentication.detail ? ` / ${authentication.detail}` : ""}`],
    ["Adapter capabilities", runtimeCapabilitySummary(runtime)],
    ["Eligibility", runtime.eligible === true ? "eligible" : runtime.disabled_reason || "not eligible"],
    ["Config identity", runtime.config_identity || "not reported"],
    ["Probe observed", runtime.probe_observed_at_utc || "not observed"],
    ["Latest launch", runtimeLatestLaunchSummary(runtime)]
  ];
  return `
    <span class="runtime-readiness-dimensions ${compact ? "compact" : ""}" data-runtime-readiness-dimensions>
      ${rows.map(([label, value]) => `<span><strong>${escapeHtml(label)}</strong>${escapeHtml(value)}</span>`).join("")}
    </span>
  `;
}

function renderProtectedWriteScope(scope = state.readiness?.protected_write_scope) {
  if (!scope) {
    return `<div class="panel-item"><strong>Protected write scope</strong><span>Unavailable until a Work Item context is selected.</span></div>`;
  }
  const prefixes = (scope.prefixes || []).join(", ") || "none authored";
  return `
    <div class="panel-item" data-protected-write-scope="${escapeHtml(scope.status)}">
      <strong>Protected write scope</strong>
      <span>${escapeHtml(scope.status)} / ${escapeHtml(prefixes)}</span>
      ${scope.source_path ? `<code>${escapeHtml(scope.source_path)}</code>` : ""}
      <small>${escapeHtml(scope.message || "")}</small>
    </div>
  `;
}

function readinessText(value, fallback = "not reported") {
  const text = String(value ?? "").trim();
  return text || fallback;
}

function timeoutSummary(runtime) {
  if (!runtime) return "not reported";
  const defaultTimeout = runtime.default_timeout_seconds ?? "";
  const defaultText = defaultTimeout === "" ? "default: inherited" : `default: ${defaultTimeout}s`;
  const stageTimeouts = Object.entries(runtime.stage_timeout_seconds || {});
  const stageText = stageTimeouts.length
    ? `stages: ${stageTimeouts.map(([stage, seconds]) => `${stage} ${seconds}s`).join(", ")}`
    : "stages: none";
  return `${defaultText}; ${stageText}`;
}

function readinessDetail(label, value, maxLength = 72) {
  const text = readinessText(value);
  return `
    <div class="panel-item">
      <strong>${escapeHtml(label)}</strong>
      <span title="${escapeHtml(text)}">${escapeHtml(compactPath(text, maxLength))}</span>
    </div>
  `;
}

function ensureRunnableRuntime() {
  if (!state.selectedRuntime) {
    focusRuntimeSelector();
    toast("Select runtime first.");
    return false;
  }
  if (!selectedRuntimeReady()) {
    focusRuntimeSelector();
    toast("Selected runtime is not ready.");
    return false;
  }
  return true;
}

function renderTopbar() {
  const dashboard = state.dashboard || {};
  const run = dashboard.run || {};
  const projectPath = document.getElementById("projectPath");
  const workItemChip = document.getElementById("intentChip");
  const runChip = document.getElementById("runChip");
  const projectRoot = dashboard.project_root || state.projectHome?.project_root || "...";
  const workItemLabel = dashboard.work_item
    ? `Work Item: ${dashboard.work_item}`
    : "Project inbox";
  const runLabel = dashboard.work_item
    ? (run.run_id ? `Run: ${run.run_id}` : "Run: not started")
    : "Choose a Work Item";
  projectPath.textContent = projectRoot;
  projectPath.title = projectRoot;
  workItemChip.textContent = workItemLabel;
  workItemChip.title = workItemLabel;
  runChip.textContent = runLabel;
  runChip.title = runLabel;
  const topContextProject = document.getElementById("topContextProject");
  const topContextWorkItem = document.getElementById("topContextIntent");
  const topContextRun = document.getElementById("topContextRun");
  if (topContextProject) topContextProject.textContent = projectPath.textContent || "Local Project";
  if (topContextWorkItem) topContextWorkItem.textContent = dashboard.work_item || "Choose a Work Item";
  if (topContextRun) topContextRun.textContent = run.run_id || "No run";
  const runtime = selectedRuntimeView();
  const ready = runtime ? selectedRuntimeReady() : false;
  const localStatus = document.getElementById("localStatus");
  if (state.readinessLoading) {
    localStatus.textContent = "Checking runtime readiness...";
    localStatus.className = "status-chip";
    return;
  }
  if (runtime) {
    const binary = runtime.binary?.status || "unknown";
    const command = runtime.execution_command?.status || "unknown";
    const localStatusLabel = `${state.selectedRuntime}: binary ${binary}; command ${command}`;
    localStatus.textContent = localStatusLabel;
    localStatus.title = localStatusLabel;
    localStatus.className = ready ? "status-chip good" : "status-chip";
    return;
  }
  localStatus.textContent = state.readinessError ? "Runtime readiness unavailable" : "Local control-plane connected";
  localStatus.className = state.readinessError ? "status-chip" : "status-chip good";
}

function renderStageRail() {
  // Stage navigation is rendered as the four-phase stepper in the active view.
}

function workItemHandoffStatus(item) {
  const handoff = state.dashboard?.terminal_handoff;
  if (!handoff || item?.work_item !== state.dashboard?.work_item) return "";
  return handoff.status || "";
}

function workItemStatusClass(item) {
  const handoffStatus = workItemHandoffStatus(item);
  if (handoffStatus === "failed") return "bad";
  if (handoffStatus === "completed-with-warning" || handoffStatus === "blocked") return "warn";
  const stateName = String(item?.terminal_state || "ready");
  if (stateName === "completed") return "good";
  if (stateName === "blocked") return "warn";
  if (stateName === "running") return "running";
  return "";
}

function workItemTerminalLabel(item) {
  const handoffStatus = workItemHandoffStatus(item);
  if (handoffStatus === "failed") return "qa not-ready";
  if (handoffStatus === "completed-with-warning") return "qa risks";
  if (handoffStatus === "blocked") return "blocked";
  return item?.terminal_state || "ready";
}

function projectHomeWorkItems() {
  return state.projectHome?.work_items || [];
}

function currentWorkItemSummary() {
  const workItem = state.dashboard?.work_item || state.projectHome?.selected_work_item || "";
  return projectHomeWorkItems().find((item) => item.work_item === workItem) || null;
}

function workItemProgressText(item) {
  const completed = Number(item?.stage_progress_count || 0);
  const total = Number(item?.stage_total_count || STAGES.length);
  const progress = `${completed} of ${total} stages complete`;
  const activeStage = stageTitle(item?.active_stage || "idea");
  if (item?.terminal_state === "completed") {
    const handoffStatus = workItemHandoffStatus(item);
    if (handoffStatus === "failed") return `QA not ready · ${progress}`;
    if (handoffStatus === "completed-with-warning") return `QA risks · ${progress}`;
    if (handoffStatus === "blocked") return `Handoff blocked · ${progress}`;
    return `Flow complete · ${progress}`;
  }
  if (item?.terminal_state === "blocked") {
    const blockers = Number(item?.blocker_count || 0);
    return `Blocked at ${activeStage} · ${blockers} blocker${blockers === 1 ? "" : "s"} · ${progress}`;
  }
  if (item?.terminal_state === "running") return `Running ${activeStage} · ${progress}`;
  return `Ready at ${activeStage} · ${progress}`;
}

function workflowProgressSummary({collapsed = false} = {}) {
  const stages = state.dashboard?.stages || [];
  if (!stages.length) return "";
  const completed = stages.filter((item) => item.status === "succeeded").length;
  const total = stages.length;
  const current = currentWorkItemSummary();
  const active = current?.active_stage || state.activeStage;
  const blockerCount = Number(current?.blocker_count || 0);
  const terminalState = current?.terminal_state || "ready";
  const stateLabel = terminalState === "blocked"
    ? `${blockerCount} blocker${blockerCount === 1 ? "" : "s"}`
    : terminalState === "running"
      ? `Working in ${stageTitle(active)}`
      : terminalState === "completed"
        ? "Flow complete"
        : `Ready at ${stageTitle(active)}`;
  const summary = `
    <div class="workflow-progress-summary">
      <div><strong>Workflow progress</strong><span>${escapeHtml(completed)} of ${escapeHtml(total)} stages complete</span></div>
      <span class="small-badge ${escapeHtml(workItemStatusClass(current))}">${escapeHtml(stateLabel)}</span>
    </div>
  `;
  const steps = `
    <ol class="workflow-progress-steps">
      ${stages.map((item, index) => {
        const activeStep = item.stage === state.activeStage;
        const status = statusClass(item.status);
        const selectable = activeStep || item.status !== "pending";
        const label = `${index + 1}. ${item.title} — ${item.status}`;
        return `
          <li>
            <button class="stage-progress-step ${escapeHtml(status)}${activeStep ? " active" : ""}" data-stage="${escapeHtml(item.stage)}" type="button" aria-current="${activeStep ? "step" : "false"}" aria-label="${escapeHtml(label)}" ${selectable ? "" : "disabled"}>
              <span>${escapeHtml(index + 1)}</span>
              <strong>${escapeHtml(item.title)}</strong>
            </button>
          </li>
        `;
      }).join("")}
    </ol>
  `;
  if (collapsed) {
    return `
      <details class="surface workflow-progress studio-workflow-progress" aria-label="Workflow progress">
        <summary>${summary}</summary>
        <p class="studio-workflow-progress-hint">Open the stage map to navigate retained stage evidence.</p>
        ${steps}
      </details>
    `;
  }
  return `<section class="surface workflow-progress" aria-label="Workflow progress">${summary}${steps}</section>`;
}

function renderProjectHomeRail() {
  // Project navigation is owned by the Inbox surface; no permanent rail exists.
}

function renderStageHeader() {
  // Stage title and status are part of the Intent context rendered by the active view.
}

function stageHasEvidence(stage) {
  return (state.dashboard?.stages || []).some((item) => item.stage === stage && Number(item.attempt_count || 0) > 0);
}

function tabHasQuestions() {
  const view = activeStageView()?.questions;
  const activeQuestions = view?.questions || [];
  const stageHasBlockers = (state.dashboard?.stages || []).some((item) =>
    Number(item.unresolved_blocking_count || 0) > 0
  );
  return activeQuestions.length > 0
    || stageHasBlockers
    || state.dashboard?.next_action?.action === "answer-questions";
}

function tabHasValidation() {
  const item = activeStageItem();
  const validation = activeStageView()?.diagnostics?.validation;
  const nextAction = state.dashboard?.next_action?.action || "";
  return Boolean(
    state.dashboard?.primary_validation_finding
    || validation?.primary_validation_finding
    || Number(item?.validator_fail_count || 0) > 0
    || Number(item?.validator_pass_count || 0) > 0
    || nextAction === "inspect-validation"
    || nextAction === "review-intervention"
  );
}

function tabHasRunEvidence() {
  return Boolean(
    state.dashboard?.run?.run_id
    || state.activeJobId
    || stageHasEvidence(state.activeStage)
  );
}

function tabHasArtifacts() {
  return Boolean(
    state.dashboard?.primary_artifact
    || (state.dashboard?.evidence_refs || []).length
    || (state.dashboard?.recent_artifacts || []).length
    || stageHasEvidence(state.activeStage)
  );
}

function tabHasApprovals() {
  const approvals = activeStageView()?.diagnostics?.approvals;
  return Boolean(
    Number(approvals?.pending_count || 0) > 0
    || Number(approvals?.requested_count || 0) > 0
    || Number(approvals?.approved_count || 0) > 0
    || Number(approvals?.denied_count || 0) > 0
  );
}

function tabHasRecovery() {
  const nextAction = state.dashboard?.next_action?.action || "";
  return Boolean(
    state.dashboard?.first_failure
    || (state.dashboard?.blockers || []).length
    || (state.dashboard?.recovery_actions || []).length
    || ["answer-questions", "inspect-validation", "review-intervention", "inspect-runtime-log"].includes(nextAction)
  );
}

function updateTabShortcutVisibility(visible) {
  document.querySelectorAll("[data-tab-shortcut]").forEach((button) => {
    const shortcut = button.dataset.tabShortcut || "";
    if (!VALID_TABS.includes(shortcut)) return;
    const mode = normalizeOperatorMode(shortcut).mode;
    button.hidden = !visible.has(mode);
  });
}

function updateContextualTabs() {
  const visible = new Set(OPERATOR_MODES);
  document.querySelectorAll("[data-tab]").forEach((button) => {
    const tab = button.dataset.tab;
    const isVisible = visible.has(tab);
    button.hidden = !isVisible;
  });
  updateTabShortcutVisibility(visible);
  if (!visible.has(state.activeTab)) {
    state.activeTab = tabHasRecovery() ? "recovery" : "work";
  }
  applyOperatorModeBodyClass();
}


function renderInlineMarkdown(value) {
  return escapeHtml(value).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderMarkdown(text) {
  const lines = String(text ?? "").split(/\r?\n/);
  let html = "";
  let inCode = false;
  let inList = false;
  const closeList = () => {
    if (inList) {
      html += "</ul>";
      inList = false;
    }
  };
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("```")) {
      if (inCode) {
        html += "</code></pre>";
        inCode = false;
      } else {
        closeList();
        html += "<pre><code>";
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      html += `${escapeHtml(line)}\n`;
      continue;
    }
    if (!trimmed) {
      closeList();
      continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      closeList();
      const level = Math.min(heading[1].length, 6);
      html += `<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`;
      continue;
    }
    const bullet = line.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += `<li>${renderInlineMarkdown(bullet[1])}</li>`;
      continue;
    }
    closeList();
    html += `<p>${renderInlineMarkdown(line)}</p>`;
  }
  closeList();
  if (inCode) html += "</code></pre>";
  return html || "<p>Empty document</p>";
}
