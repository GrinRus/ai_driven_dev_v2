function renderRuntimeSelector() {
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
      const ready = runtime.provider_available && runtime.execution_command_available;
      const label = ready ? "ready" : "check";
      return `<option value="${escapeHtml(runtimeId)}"${selected}>${escapeHtml(runtimeId)} (${label})</option>`;
    })
  ].join("");
  setRunButtonState();
}

function scrollActiveStageIntoView() {
  const rail = document.getElementById("stageRail");
  if (!rail || !window.matchMedia("(max-width: 760px)").matches) return;
  if (document.body.classList.contains("terminal-handoff-mode")) return;
  if (document.body.classList.contains("terminal-repair-mode")) return;
  if (document.body.classList.contains("post-stage-next-action-mode")) return;
  const active = rail.querySelector(`[data-stage="${CSS.escape(state.activeStage)}"]`);
  active?.scrollIntoView({behavior: "auto", block: "nearest", inline: "center"});
}

function selectedRuntimeView() {
  if (state.readinessLoading) return null;
  return (state.readiness?.runtimes || []).find((runtime) => runtime.runtime_id === state.selectedRuntime) || null;
}

function selectedRuntimeReady() {
  const runtime = selectedRuntimeView();
  return Boolean(runtime && runtime.provider_available && runtime.execution_command_available);
}

function runtimeReadinessMessage() {
  if (!state.selectedRuntime) return "Select a runtime before this action can run.";
  if (state.readinessLoading) return "Checking runtime readiness before this action can run.";
  if (state.readinessError) return `Runtime readiness unavailable: ${state.readinessError}`;
  if (!selectedRuntimeReady()) return "Selected runtime is not ready for execution.";
  return "";
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
    document.getElementById("runtimeSelect").focus();
    toast("Select runtime first.");
    return false;
  }
  if (!selectedRuntimeReady()) {
    document.getElementById("runtimeSelect").focus();
    toast("Selected runtime is not ready.");
    return false;
  }
  return true;
}

function renderTopbar() {
  const dashboard = state.dashboard || {};
  const run = dashboard.run || {};
  const projectPath = document.getElementById("projectPath");
  const workItemChip = document.getElementById("workItemChip");
  const runChip = document.getElementById("runChip");
  const projectRoot = dashboard.project_root || "...";
  const workItemLabel = `Work item: ${dashboard.work_item || "unknown"}`;
  const runLabel = run.run_id ? `Run: ${run.run_id}` : "Run: none";
  projectPath.textContent = projectRoot;
  projectPath.title = projectRoot;
  workItemChip.textContent = workItemLabel;
  workItemChip.title = workItemLabel;
  runChip.textContent = runLabel;
  runChip.title = runLabel;
  const runtime = selectedRuntimeView();
  const ready = runtime ? runtime.provider_available && runtime.execution_command_available : false;
  const localStatus = document.getElementById("localStatus");
  if (state.readinessLoading) {
    localStatus.textContent = "Checking runtime readiness...";
    localStatus.className = "status-chip";
    return;
  }
  if (runtime) {
    const localStatusLabel = `${state.selectedRuntime}: ${ready ? "ready" : "needs check"}`;
    localStatus.textContent = localStatusLabel;
    localStatus.title = localStatusLabel;
    localStatus.className = ready ? "status-chip good" : "status-chip";
    return;
  }
  localStatus.textContent = state.readinessError ? "Runtime readiness unavailable" : "Local control-plane connected";
  localStatus.className = state.readinessError ? "status-chip" : "status-chip good";
}

function renderStageRail() {
  const stages = state.dashboard?.stages || [];
  const done = stages.filter((item) => item.status === "succeeded").length;
  document.getElementById("stageCounter").textContent = `${done}/${STAGES.length}`;
  document.getElementById("stageRail").innerHTML = stages.map((item, index) => {
    const isActive = item.stage === state.activeStage;
    const active = isActive ? " active" : "";
    const status = statusClass(item.status);
    const attemptCount = Number(item.attempt_count || 0);
    const retry = stageRetrySummary(item);
    const attemptTitle = attemptCount > 1
      ? retry.title
      : `${attemptCount || 0} attempt${attemptCount === 1 ? "" : "s"}`;
    const markers = [
      item.stale ? `<span class="small-badge warn" title="${escapeHtml(item.stale_reason || "downstream evidence is stale")}">stale</span>` : "",
      item.unresolved_blocking_count ? `<span class="small-badge warn">Q${item.unresolved_blocking_count}</span>` : "",
      item.validator_fail_count ? `<span class="small-badge bad">V${item.validator_fail_count}</span>` : "",
      attemptCount ? `<span class="small-badge ${retry ? "retried" : ""}" title="${escapeHtml(attemptTitle)}">${retry ? `retry ${escapeHtml(attemptCount)}x` : `${escapeHtml(attemptCount)}x`}</span>` : ""
    ].filter(Boolean).join("");
    const retryAria = retry ? `, ${retry.retryCount === 1 ? "1 retry" : `${retry.retryCount} retries`} recorded` : "";
    const nameId = `stage-${item.stage}-name`;
    const statusId = `stage-${item.stage}-status`;
    return `
      <button class="stage-card${active}${retry ? " retried" : ""}" data-stage="${escapeHtml(item.stage)}" type="button" aria-current="${isActive ? "step" : "false"}" aria-labelledby="${escapeHtml(nameId)} ${escapeHtml(statusId)}">
        <span class="stage-index">${index + 1}</span>
        <span class="stage-copy">
          <span id="${escapeHtml(nameId)}" class="stage-name">${escapeHtml(item.title)}</span>
          <span class="stage-subtitle">${escapeHtml(item.subtitle)}</span>
        </span>
        <span class="stage-markers">
          <span class="marker-dot ${escapeHtml(status)}" title="${escapeHtml(item.status)}"></span>
          ${markers}
          <span id="${escapeHtml(statusId)}" class="sr-only">${escapeHtml(`${item.status}${retryAria}`)}</span>
        </span>
      </button>
    `;
  }).join("");
  requestAnimationFrame(scrollActiveStageIntoView);
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
  if (item?.terminal_state === "completed") {
    const handoffStatus = workItemHandoffStatus(item);
    if (handoffStatus === "failed") return `QA not ready / ${item.stage_progress_label}`;
    if (handoffStatus === "completed-with-warning") return `QA risks / ${item.stage_progress_label}`;
    if (handoffStatus === "blocked") return `handoff blocked / ${item.stage_progress_label}`;
    return `flow complete / ${item.stage_progress_label}`;
  }
  return `${item?.active_stage || "not started"} / ${item?.stage_progress_label || `0/${STAGES.length}`}`;
}

function renderProjectSetRootChips(item) {
  const roots = item?.project_set_roots || [];
  if (!roots.length) return `<span class="small-badge">single root</span>`;
  return roots.slice(0, 3).map((root) => (
    `<span class="small-badge" title="${escapeHtml(root.root)}">${escapeHtml(root.root_id)}:${escapeHtml(root.relative_root)}</span>`
  )).join("");
}

function renderProjectHomeRail() {
  const host = document.getElementById("projectHomeRail");
  if (!host) return;
  const home = state.projectHome;
  if (!home) {
    host.innerHTML = `<div class="empty-state compact">Project Home loading...</div>`;
    return;
  }
  const current = currentWorkItemSummary();
  const items = projectHomeWorkItems();
  const projectsActive = state.activeTab === "work" && state.workDetail === "project-home";
  const workItemsActive = state.activeTab === "work" && state.workDetail !== "project-home";
  host.innerHTML = `
    <div class="project-home-tabs" role="group" aria-label="Project and work item navigation">
      <button data-tab-shortcut="project-home" class="${projectsActive ? "active" : ""}" aria-pressed="${projectsActive ? "true" : "false"}" type="button">Projects</button>
      <button data-tab-shortcut="overview" class="${workItemsActive ? "active" : ""}" aria-pressed="${workItemsActive ? "true" : "false"}" type="button">Work items</button>
    </div>
    <div class="rail-header small">
      <span>Active work items</span>
      <span class="counter">${escapeHtml(items.length)}</span>
    </div>
    <div class="work-item-board-rail">
      ${items.length ? items.slice(0, 6).map((item) => `
        <button class="work-item-card ${item.work_item === current?.work_item ? "active" : ""}" data-project-home-resume="${escapeHtml(item.work_item)}" type="button" aria-current="${item.work_item === current?.work_item ? "true" : "false"}">
          <span>
            <strong>${escapeHtml(item.work_item)}</strong>
            <small>${escapeHtml(workItemProgressText(item))}</small>
          </span>
          <span class="small-badge ${workItemStatusClass(item)}">${escapeHtml(workItemTerminalLabel(item))}</span>
        </button>
      `).join("") : `<div class="empty-state compact">No work items in this project.</div>`}
    </div>
  `;
}

function renderStageHeader() {
  const item = activeStageItem();
  const retry = stageRetrySummary(item);
  document.getElementById("stageTitle").textContent = item?.title || stageTitle(state.activeStage);
  document.getElementById("stageSubtitle").textContent = item?.subtitle || stageSubtitle(state.activeStage);
  document.getElementById("stageBadges").innerHTML = [
    `<span class="status-badge ${escapeHtml(statusClass(item?.status))}">${escapeHtml(item?.status || "pending")}</span>`,
    item?.stale ? `<span class="status-badge warn" title="${escapeHtml(item.stale_reason || "downstream evidence is stale")}">stale</span>` : "",
    `<span class="status-badge">Attempts ${escapeHtml(item?.attempt_count || 0)}</span>`,
    retry ? `<button class="badge-button retried" data-stage-recovery="validation" type="button" title="${escapeHtml(retry.title)}">Retry history</button>` : "",
    `<span class="status-badge">Validation ${escapeHtml(item?.validator_pass_count || 0)}/${escapeHtml(item?.validator_fail_count || 0)}</span>`
  ].filter(Boolean).join("");
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
